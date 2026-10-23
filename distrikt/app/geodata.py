"""Explicit public-data downloads, kept locally. No card, IB or publisher uploads."""
import json
import re
import socket
import http.client
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from geography import decode_dar, valid_coordinate
from postcode import PostcodeDownload, Paused, SourceUnavailable, SourceTimeout
from boundary_download import BoundaryDownload
from dar_download import DarDownload
from address_source import Datafordeler
from address_checkpoint import GRAPHQL_SOURCE

PUBLIC_TOKEN='adressevaelger123'  # Public token recommended by KDS as of 6 Oct 2026.

class Downloads(PostcodeDownload,BoundaryDownload,DarDownload):
    def __init__(self,store,address_source=None):
        self.store=store;self.jobs={};self.lock=threading.Lock();self.active=None;self.cancel_event=threading.Event()
        self.suggestion_cache={}
        self._received_addresses=set()
        self.address_source=address_source if address_source is not None else (Datafordeler(store.root) if store is not None else None)
    def start(self,kind,data):
        if kind not in ('road','area','osm','postcode','boundary'):raise ValueError('Ukendt hentning.')
        with self.lock:
            if self.active:raise ValueError('En hentning kører allerede. Vent på den før næste område.')
            ident=uuid.uuid4().hex
            self.cancel_event.clear()
            self._received_addresses.clear()
            self.jobs[ident]={'id':ident,'kind':kind,'status':'running','message':'Forbereder hentning af offentlige data…','completed':0,'total':0}
            if kind!='osm':self.jobs[ident]['received_count']=0
            self.active=ident
        thread=threading.Thread(target=self.run,args=(ident,kind,dict(data)),daemon=True);thread.start()
        return {'job_id':ident}
    def status(self,ident=None):
        with self.lock:
            ident=ident or self.active
            if not ident:return {'status':'idle'}
            if ident not in self.jobs:raise ValueError('Hentningen findes ikke i denne session.')
            result=dict(self.jobs[ident])
            started=result.pop('request_started',None);label=result.pop('request_label','');result.pop('request_timeout',None)
            if result['status']=='running' and started is not None:
                result['waiting']=True
                result['message']+=f' · {label}: venter på svar'
            return result
    def received_addresses(self,identities):
        """Count actual public addresses, never requests, guesses or duplicates."""
        with self.lock:
            if self.active:
                self._received_addresses.update(identities)
                self.jobs[self.active]['received_count']=len(self._received_addresses)
    def update(self,ident,**values):
        if 'message' in values and 'activity' not in values:values['activity']=None
        with self.lock:self.jobs[ident].update(values)
    def pause(self,ident):
        with self.lock:
            if ident!=self.active or self.jobs[ident]['kind'] not in ('postcode','boundary'):raise ValueError('Ingen adressehentning at sætte på pause.')
            self.cancel_event.set();self.jobs[ident]['message']='Sætter på pause efter det aktuelle opslag…'
        return {'ok':True}
    def check_cancel(self):
        if self.cancel_event.is_set():raise Paused()
    def run(self,ident,kind,data):
        try:
            if kind=='road':result=self.road(data,lambda **kw:self.update(ident,**kw))
            elif kind=='postcode':result=self.postcode(data,lambda **kw:self.update(ident,**kw))
            elif kind=='boundary':result=self.boundary(data,lambda **kw:self.update(ident,**kw))
            else:result=self.area(data,kind=='area',lambda **kw:self.update(ident,**kw))
            self.update(ident,status='done',result=result,message='Offentlige data er gemt lokalt. Dine kort er ikke ændret.')
        except Paused:self.update(ident,status='paused',message='Hentningen er sat på pause. Færdige veje eller udsnit er gemt; fortsæt under Kortdata eller Samlet distriktsgrænse.')
        except ValueError as e:self.update(ident,status='error',message=str(e))
        except Exception:self.update(ident,status='error',message='Hentning mislykkedes. Eksisterende lokale data er bevaret; prøv igen senere.')
        finally:
            with self.lock:self.active=None;self._received_addresses.clear()
    def request(self,host,path,params=None,query=None):
        if host not in ('adressevaelger.dk','overpass-api.de','services.datafordeler.dk'):raise ValueError('Ukendt datakilde.')
        url='https://'+host+path
        if params:url+='?'+urllib.parse.urlencode(params)
        if query:url+='?'+urllib.parse.urlencode({'data':query})
        req=urllib.request.Request(url,headers={'User-Agent':'DistriktLocal/1.8.4','Accept':'application/json'})
        # Bulk DAR reads are idempotent. Retry individual pages, never imports.
        attempts=3 if host=='services.datafordeler.dk' else 1
        with self.lock:
            job_id=self.active
            stage=self.jobs[job_id]['message'] if job_id else ''
            boundary_job=bool(job_id and self.jobs[job_id].get('kind')=='boundary' and host=='services.datafordeler.dk')
        timeout=120 if boundary_job else 45
        label=('DAR-kontroltal' if (params or {}).get('count') else 'DAR-adresseside '+str((params or {}).get('page',1)))
        for attempt in range(attempts):
            if attempts>1:self.check_cancel()
            delay=(2,5)[min(attempt,1)]
            error_type=SourceUnavailable
            try:
                with self.lock:
                    if job_id and self.active==job_id:self.jobs[job_id].update(request_started=time.monotonic(),request_label=label,request_timeout=timeout)
                with urllib.request.urlopen(req,timeout=timeout) as response:
                    raw=response.read(18000001)
                if len(raw)>18000000:raise ValueError('Området er for stort. Hent et mindre kortudsnit.')
                result=json.loads(raw)
                with self.lock:
                    if job_id and self.active==job_id and not self.cancel_event.is_set():self.jobs[job_id]['message']=stage
                break
            except urllib.error.HTTPError as e:
                if e.code in (401,403):raise SourceUnavailable('Adressekilden afviste adgang. Kontrollér den lokale adgangsopsætning under Kortdata.') from None
                if e.code==429:
                    message='Datakilden begrænser antallet af opslag. Vent og fortsæt hentningen senere.'
                    retry_after=e.headers.get('Retry-After','') if e.headers else ''
                    # Do not retry before a long server-specified cooldown.
                    if retry_after and (not retry_after.isdigit() or int(retry_after)>60):raise SourceUnavailable(message) from None
                    delay=max(60,int(retry_after) if retry_after.isdigit() else 60)
                elif e.code in (408,500,502,503,504):
                    if e.code in (408,504):error_type=SourceTimeout
                    message=f'Datakilden er midlertidigt utilgængelig (HTTP {e.code}). Fortsæt hentningen senere.'
                    retry_after=e.headers.get('Retry-After','') if e.headers else ''
                    if retry_after:
                        if not retry_after.isdigit() or int(retry_after)>60:raise SourceUnavailable(message) from None
                        delay=max(delay,int(retry_after))
                else:raise SourceUnavailable(f'Datakilden afviste opslaget (HTTP {e.code}). Eksisterende lokale data er bevaret.') from None
            except (socket.timeout,TimeoutError):
                error_type=SourceTimeout
                message=f'Datakilden svarede ikke inden for {timeout} sekunder. Fortsæt for at genprøve udsnittet.'
            except (OSError,http.client.HTTPException) as e:
                if isinstance(getattr(e,'reason',None),(socket.timeout,TimeoutError)):error_type=SourceTimeout
                message=(f'Datakilden svarede ikke inden for {timeout} sekunder. Fortsæt for at genprøve udsnittet.' if isinstance(getattr(e,'reason',None),(socket.timeout,TimeoutError)) else 'Forbindelsen til datakilden blev afbrudt eller kunne ikke oprettes. Kontrollér internet og fortsæt hentningen.')
            except (json.JSONDecodeError,UnicodeDecodeError):
                message='Datakilden returnerede et ugyldigt svar. Fortsæt hentningen senere.'
            finally:
                with self.lock:
                    if job_id:
                        for field in ('request_started','request_label','request_timeout'):self.jobs[job_id].pop(field,None)
            if boundary_job and error_type is SourceTimeout:raise SourceTimeout(message) from None
            if attempt==attempts-1:
                suffix=' Automatisk genprøvet 2 gange.' if attempts>1 else ''
                raise error_type(message+suffix) from None
            with self.lock:
                if job_id and self.active==job_id:self.jobs[job_id]['message']=stage+' '+message.split('. ')[0]+f' · genprøver om {delay} sekunder ({attempt+1}/2)…'
            if self.cancel_event.wait(delay):raise Paused()
        if not isinstance(result,(dict,list,int)):raise ValueError('Datakilden gav et ukendt svar.')
        if isinstance(result,dict) and result.get('status') not in (None,'ok'):raise ValueError('Adressekilden fandt ikke et entydigt resultat. Kontrollér vejnavn og postnummer.')
        return result
    def token(self):
        with self.store.lock:cfg=self.store.get('geo','config') or {}
        return cfg.get('token') or PUBLIC_TOKEN
    def suggest(self,road,postcode=''):
        road=str(road).strip();post=str(postcode).strip()
        if not 2<=len(road)<=40:raise ValueError('Skriv mindst to tegn og højst 40 tegn i vejnavnet.')
        if post and not re.fullmatch(r'\d{4}',post):raise ValueError('Skriv et firecifret postnummer.')
        token=self.token();key=(road.casefold(),post,token)
        with self.lock:cached=self.suggestion_cache.get(key)
        if cached and time.monotonic()-cached[0]<300:return cached[1]
        params={'vejnavn':road,'maal':'navngivenvejpostnummer','maksimum':12,'token':token}
        if post:params['postnummer']=post
        result=self.request('adressevaelger.dk','/soeg',params);suggestions=[]
        for hit in result.get('fund',[]):
            name=str(hit.get('vejnavn',''));p=str(hit.get('postnr',''))
            if hit.get('type')!='navngivenvejpostnummer' or not name or not re.fullmatch(r'\d{4}',p) or post and p!=post:continue
            suggestions.append({'road':name,'postcode':p,'city':str(hit.get('postdistrikt','')),'label':name+' · '+p+' '+str(hit.get('postdistrikt',''))})
        output={'suggestions':suggestions}
        with self.lock:
            if len(self.suggestion_cache)>=100:self.suggestion_cache.clear()
            self.suggestion_cache[key]=(time.monotonic(),output)
        return output
    def road(self,data,progress):
        road=str(data.get('road','')).strip();post=str(data.get('postcode','')).strip()
        if not 1<=len(road)<=80 or not re.fullmatch(r'\d{4}',post):raise ValueError('Skriv et vejnavn og et firecifret postnummer.')
        if self.source_id()==GRAPHQL_SOURCE:
            progress(message='Henter den komplette vej via DAR GraphQL…')
            loaded=self.graph_adapter().named_road(road,post)
            addresses=loaded['addresses'];source='DAR / Datafordeleren'
        else:
            # Legacy spelling resolution must not gate the independent GraphQL API.
            # Never select a random fuzzy neighbour when using the older source.
            suggestions=self.suggest(road,post)['suggestions']
            exact=[s for s in suggestions if s['road'].casefold()==road.casefold()]
            chosen=exact if len(exact)==1 else suggestions
            if len(chosen)!=1:raise ValueError('Vælg det officielle vejnavn i forslagene under søgefeltet.')
            road=chosen[0]['road']
            token=self.token();params={'vejnavn':road,'postnummer':post,'maksimum':200,'token':token};source='DAR / Adressevælger'
            progress(message='Finder gældende DAR-adresser på vejen…')
            found=self.request('adressevaelger.dk','/adresser/soeg',params).get('fund',[])
            addresses=[]
            if found and len(found)<200 and all(x.get('type')=='adresse' for x in found):
                ids=[x['id'] for x in found];progress(total=len(ids))
                for offset in range(0,len(ids),30):
                    result=self.request('adressevaelger.dk','/adresser',{'id_lokalids':','.join(ids[offset:offset+30]),'token':token})
                    items=result.get('adresser',[])
                    if {a.get('id_lokalid') for a in items}!={a for a in ids[offset:offset+30]}:raise ValueError('Adressekilden returnerede et ufuldstændigt opslag. Prøv igen senere.')
                    decoded=decode_dar(items);self.received_addresses(a['id'] for a in decoded)
                    addresses += decoded;progress(completed=min(offset+30,len(ids)),message='Henter adresser og kendte lejligheder…')
            else:
                houses=self.request('adressevaelger.dk','/husnumre/soeg',params).get('fund',[])
                if not houses or len(houses)>=200 or not all(h.get('type')=='husnummer' for h in houses):
                    addresses=self.bulk_road(road,post,progress);source='DAR / Datafordeleren'
                else:
                    progress(total=len(houses))
                    for i,h in enumerate(houses):
                        items=self.request('adressevaelger.dk','/husnumre/'+h['id']+'/adresser',{'token':token}).get('adresser',[])
                        decoded=decode_dar(items);self.received_addresses(a['id'] for a in decoded)
                        addresses+=decoded;progress(completed=i+1,message='Henter husnumre med alle kendte lejligheder…')
        # Reject fuzzy neighbouring streets/postcodes rather than silently choose one.
        roads=sorted({a['road'] for a in addresses if a['postcode']==post})
        if len(roads)!=1:raise ValueError('Søgningen matcher flere eller ingen veje. Brug det præcise vejnavn og postnummer.')
        addresses=[a for a in addresses if a['road']==roads[0] and a['postcode']==post]
        if not addresses:raise ValueError('Ingen gældende adresser med koordinater blev fundet.')
        self.received_addresses(a['id'] for a in addresses)
        progress(activity='Kontrollerer og gemmer adresser lokalt…')
        result=self.store.mutate('geo.import',{'records':addresses,'label':roads[0]+' · '+post,'source':source,'complete_road':{'road':roads[0],'postcode':post},'review_changes':True})
        bbox=[min(a['lng'] for a in addresses)-.001,min(a['lat'] for a in addresses)-.001,max(a['lng'] for a in addresses)+.001,max(a['lat'] for a in addresses)+.001]
        warnings=[]
        if data.get('include_osm'):
            progress(message='Adresser er gemt. Henter veje og bygninger omkring dem…')
            try:self.area({'bbox':bbox},False,progress)
            except ValueError as e:warnings.append(str(e))
        return dict(result,road=roads[0],postcode=post,bbox=bbox,warnings=warnings)
    def area(self,data,with_addresses,progress):
        bbox=data.get('bbox')
        if not isinstance(bbox,list) or len(bbox)!=4:raise ValueError('Vælg et kortudsnit.')
        w,s=valid_coordinate(bbox[:2]);e,n=valid_coordinate(bbox[2:])
        if w>=e or s>=n or (e-w)*(n-s)>0.003:raise ValueError('Zoom tættere på. Hent ét mindre område ad gangen, højst ca. 20 km².')
        bounds=f'{s},{w},{n},{e}'
        query=f'[out:json][timeout:15];(way["building"]({bounds});way["highway"]({bounds});way["waterway"~"^(river|stream|canal)$"]({bounds});way["railway"="rail"]({bounds}););out tags geom;'
        progress(message='Henter offentlige veje, bygninger, vandløb og jernbaner til det viste udsnit…')
        osm_warnings=[]
        try:
            result=self.request('overpass-api.de','/api/interpreter',query=query)
            if result.get('remark'):raise ValueError('Kortkilden returnerede en ufuldstændig hentning. Zoom tættere på og prøv igen.')
        except ValueError as error:
            if not with_addresses or self.source_id()!=GRAPHQL_SOURCE:raise
            result={'elements':[]};osm_warnings.append('Kortbaggrund: '+str(error))
        records=[];roads=set()
        for item in result.get('elements',[]):
            tags=item.get('tags',{});points=[[p['lon'],p['lat']] for p in item.get('geometry',[]) if p and 'lon' in p]
            if len(points)<2:continue
            points=[valid_coordinate(p) for p in points]
            if 'building' in tags:typ='building'
            elif 'highway' in tags:typ='road'
            elif tags.get('waterway') in ('river','stream','canal') or tags.get('railway')=='rail':typ='divider'
            else:continue
            if typ=='building' and len(points)<4:continue
            records.append({'id':'osm:'+str(item['id']),'entity':typ,'points':points,'source':'OpenStreetMap','name':tags.get('name',''),
                'building_type':tags.get('building',''),'road_type':tags.get('highway','')})
            if typ=='divider':records[-1].update(divider_type=tags.get('waterway') if tags.get('waterway') in ('river','stream','canal') else 'rail',layer=tags.get('layer','0'),bridge=tags.get('bridge',''),tunnel=tags.get('tunnel',''))
            if typ=='road' and tags.get('name'):roads.add(tags['name'])
        if not records and not (with_addresses and self.source_id()==GRAPHQL_SOURCE):raise ValueError('Ingen veje, bygninger, vandløb eller jernbaner fundet. Prøv et andet udsnit.')
        saved=self.store.mutate('geo.import',{'records':records,'label':'Lokalt kortudsnit','source':'OpenStreetMap','bbox':[w,s,e,n]}) if records else {'count':0}
        if with_addresses and self.source_id()==GRAPHQL_SOURCE:
            addresses=self.graph_viewport([w,s,e,n],progress)
            addresses['warnings']=osm_warnings+addresses['warnings']
            if osm_warnings:addresses['note']+=' Kortbaggrunden er ufuldstændig; DAR-kontrollen er udført særskilt.'
            return dict(saved,**addresses)
        warnings=[];road_results=[]
        if with_addresses:
            post=str(data.get('postcode','')).strip()
            if not re.fullmatch(r'\d{4}',post):raise ValueError('Kortdata er gemt. Angiv postnummer for at hente DAR-adresser til vejene.')
            if len(roads)>45:raise ValueError('Kortdata er gemt, men området har over 45 vejnavne. Zoom tættere på for at hente adresser.')
            for i,road in enumerate(sorted(roads)):
                progress(message=f'Henter DAR-adresser for vej {i+1} af {len(roads)}…',total=len(roads),completed=i)
                try:road_results.append(self.road({'road':road,'postcode':post},lambda **kw:None))
                except ValueError as e:warnings.append(road+': '+str(e))
            progress(completed=len(roads))
        return dict(saved,roads_downloaded=len(road_results),warnings=warnings,complete=False,
                    note='Veje, bygninger, vandløb og jernbaner er fra OSM. Kun succesfuldt hentede DAR-veje har en komplet vej-adresseliste. Kontrollér manglende veje og adresser.')
