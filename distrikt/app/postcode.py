"""Public DAR REST paging for a whole postcode, with local checkpoints.

This official REST service is scheduled to retire on 15 January 2027.
Only public postcode/road identifiers are sent. Private cards are never read here.
"""
import copy
import re
from datetime import datetime, timezone
from geography import decode_dar, utm32_to_wgs84

HOST='services.datafordeler.dk'
BASE='/DAR/DAR/3.0.0/rest/'
PAGE_SIZE=100

class Paused(Exception):pass

class SourceUnavailable(ValueError):
    """Source-wide failure: stop bulk iteration after bounded request retries."""
    pass

class SourceTimeout(SourceUnavailable):pass

def rest_addresses(items,postcode,road):
    normalized=[]
    for raw in items:
        if str(raw.get('status'))!='3':continue
        h=raw.get('husnummer') or {}
        # A named road can cross postcode boundaries. Filter before conversion.
        post=str((h.get('postnummer') or {}).get('postnr') or '')
        if postcode is not None and post!=postcode:continue
        named=h.get('navngivenVej') or {}
        name=named.get('vejnavn')
        if road is not None and name!=road:raise ValueError('Vejopslaget gav et andet vejnavn. Hentningen blev ikke gemt.')
        if not name or not re.fullmatch(r'\d{4}',post):raise ValueError('En adresse mangler vejnavn eller postnummer.')
        wkt=(h.get('adgangspunkt') or {}).get('position','')
        m=re.fullmatch(r'POINT\s*\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*\)',wkt)
        if not m:raise ValueError('En adresse mangler et gyldigt adgangspunkt. Vejen er endnu ikke komplet.')
        item={'id_lokalid':raw['id_lokalId'],'status':'3','adressebetegnelse':raw.get('adressebetegnelse',''),
            'etagebetegnelse':raw.get('etagebetegnelse'),'doerbetegnelse':raw.get('dørbetegnelse'),
            'husnummer':{'id_lokalid':h['id_lokalId'],'vejnavn':name,'husnummertekst':h['husnummertekst'],
                'postnummer':{'postnr':post},'adgangspunkt':{'geometri':{'coordinates':[float(m[1]),float(m[2])],
                    'crs':{'properties':{'name':'EPSG:25832'}}}}}}
        normalized.append(item)
    return decode_dar(normalized)

def rest_road_lines(roads):
    output=[]
    for r in roads:
        wkt=r.get('vejnavnebeliggenhed_vejnavnelinje') or ''
        if not re.match(r'^(MULTILINESTRING|LINESTRING)\s*\(',wkt):continue
        for i,part in enumerate(re.findall(r'\(([^()]+)\)',wkt)):
            try:points=[utm32_to_wgs84(*map(float,p.strip().split())) for p in part.split(',')]
            except (ValueError,TypeError):continue
            if len(points)>=2:output.append({'id':f"dar-road:{r['id_lokalId']}:{i}",'entity':'road',
                'name':r['vejnavn'],'points':points,'road_type':'official'})
    return output

class PostcodeDownload:
    def rest_pages(self,endpoint,params,progress,check=True):
        rows=[];seen=set()
        for page in range(1,2001):
            if check:self.check_cancel()
            batch=self.request(HOST,BASE+endpoint,dict(params,format='json',page=page,pagesize=PAGE_SIZE))
            if not isinstance(batch,list) or len(batch)>PAGE_SIZE:raise ValueError('DAR-kilden gav et ukendt sideformat.')
            if not batch:return rows
            ids=[r.get('id_lokalId') for r in batch]
            if any(not i or i in seen for i in ids) or len(set(ids))!=len(ids):
                raise ValueError('DAR-kilden gentog en side. Eksisterende lokale data er bevaret; prøv igen.')
            seen.update(ids);rows.extend(batch);progress(len(rows))
            if len(batch)<PAGE_SIZE:return rows
        raise ValueError('DAR-udtrækket er for stort til én hentning.')

    def discover_postcode(self,post,progress):
        self.check_cancel();progress(message='Finder postnummer og den officielle vejliste…',completed=0,total=0)
        snapshot=datetime.now(timezone.utc).isoformat(timespec='seconds')
        temporal={'VirkningFra':snapshot,'RegistreringFra':snapshot,'Status':3}
        posts=self.request(HOST,BASE+'postnummer',dict(temporal,Postnr=post,format='json'))
        if not isinstance(posts,list) or len(posts)!=1 or str(posts[0].get('postnr'))!=post:
            raise ValueError('Postnummeret kunne ikke findes entydigt i DAR.')
        roads=self.rest_pages('navngivenvej',dict(temporal,Postnummer=posts[0]['id_lokalId'],MedDybde='false'),
            lambda count:progress(message=f'Finder den officielle vejliste… {count} veje fundet'))
        if not roads:raise ValueError('Ingen gældende veje fundet i postnummeret.')
        if any(not r.get('vejnavn') for r in roads):raise ValueError('Vejlisten var ufuldstændig.')
        manifest={'id':'postcode:'+post,'entity':'postcode_download','postcode':post,'name':posts[0].get('navn',''),
            'snapshot':snapshot,'source':'DAR / Datafordeleren','status':'running','roads':[
                {'id':r['id_lokalId'],'road':r['vejnavn'],'status':'pending','count':0} for r in sorted(roads,key=lambda r:r['vejnavn'].casefold())]}
        # Store the official road geometry immediately, without any OSM dependency.
        lines=rest_road_lines(roads)
        self.store.mutate('geo.postcode.save',{'manifest':manifest,'lines':lines})
        return manifest

    def bulk_road(self,road,post,progress):
        with self.store.lock:manifest=copy.deepcopy(self.store.get('geo','postcode:'+post))
        if not manifest:manifest=self.discover_postcode(post,progress)
        matches=[r for r in manifest['roads'] if r['road'].casefold()==road.casefold()]
        if len(matches)!=1:raise ValueError('Vejen kunne ikke findes entydigt i den officielle vejliste.')
        progress(message='Henter den lange vej i flere sider…',total=0,completed=0)
        items=self.rest_pages('adresse',{'NavngivenVej':matches[0]['id'],'Status':3},
            lambda count:progress(message=f'Henter {road}… {count} adresser læst'))
        return rest_addresses(items,post,matches[0]['road'])

    def postcode(self,data,progress):
        post=str(data.get('postcode','')).strip()
        if not re.fullmatch(r'\d{4}',post):raise ValueError('Skriv et firecifret postnummer.')
        ident='postcode:'+post
        with self.store.lock:manifest=copy.deepcopy(self.store.get('geo',ident))
        if data.get('refresh') or not manifest:manifest=self.discover_postcode(post,progress)
        temporal={'VirkningFra':manifest['snapshot'],'RegistreringFra':manifest['snapshot'],'Status':3}
        total=len(manifest['roads']);done=sum(r['status']=='done' for r in manifest['roads'])
        manifest['status']='running';self.store.mutate('geo.postcode.save',{'manifest':manifest})
        try:
            for r in manifest['roads']:
                if r['status']=='done':continue
                self.check_cancel()
                progress(message=f"Henter {r['road']} · {post}…",completed=done,total=total,postcode=post)
                try:
                    items=self.rest_pages('adresse',dict(temporal,NavngivenVej=r['id']),
                        lambda count:progress(message=f"Henter {r['road']}… {count} adresser læst"))
                    addresses=rest_addresses(items,post,r['road'])
                    r.update(status='done',count=len(addresses));r.pop('error',None)
                    # Address import, retirement and checkpoint commit in one local transaction.
                    self.store.mutate('geo.postcode.road',{'manifest':manifest,'road':r['road'],'records':addresses})
                    done+=1
                except ValueError as e:
                    r.update(status='error',error=str(e));self.store.mutate('geo.postcode.save',{'manifest':manifest})
                progress(completed=done,total=total)
            manifest['status']='complete' if done==total else 'partial'
        except Paused:
            manifest['status']='paused';self.store.mutate('geo.postcode.save',{'manifest':manifest});raise
        self.store.mutate('geo.postcode.save',{'manifest':manifest})
        with self.store.lock:
            points=[[a['lng'],a['lat']] for a in self.store.all('geo') if a.get('entity')=='address' and a.get('postcode')==post and not a.get('retired')]
        bbox=[min(p[0] for p in points)-.001,min(p[1] for p in points)-.001,max(p[0] for p in points)+.001,max(p[1] for p in points)+.001] if points else None
        count=sum(r['count'] for r in manifest['roads'] if r['status']=='done')
        warnings=[r['road']+': '+r.get('error','Afventer hentning') for r in manifest['roads'] if r['status']!='done']
        return {'postcode':post,'roads_downloaded':done,'roads_total':total,'count':count,'bbox':bbox,'warnings':warnings,
            'complete':done==total,'note':f"{count} adresser · {done} af {total} veje i {post} {manifest['name']}. "+
                ('Alle veje i DAR-udtrækket er behandlet.' if done==total else 'Fortsæt / genprøv for at hente de manglende veje.')}
