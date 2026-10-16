"""Additive geographic storage/actions; existing v1 files retain their format."""
import csv
import io
import json
import re
import uuid
from datetime import datetime, timezone
from geography import valid_coordinate, valid_polygon, point_in_polygon, enclosing_outline, street_rows, in_number_range
from main_boundary import MainBoundaryStore


def stamp():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def text(value,limit=120,required=False):
    value=str(value or '').strip()
    if len(value)>limit or required and not value:raise ValueError('Udfyld feltet med en passende tekst.')
    return value

def address_key(a):return tuple(str(a.get(k,'')).casefold().strip() for k in ('postcode','road','number','floor','door'))

class GeoStore(MainBoundaryStore):
    def geo_info(self):
        if self._info_cache is not None:return self._info_cache
        rows=self.all('geo');self._info_cache={'addresses':sum(r.get('entity')=='address' for r in rows),'buildings':sum(r.get('entity')=='building' for r in rows),
            'roads':sum(r.get('entity')=='road' for r in rows),'downloads':[r for r in rows if r.get('entity')=='download'],
            'postcodes':[r for r in rows if r.get('entity')=='postcode_download'],
            'token_custom':bool((self.get('geo','config') or {}).get('token'))}
        return self._info_cache
    def geo_state(self):
        with self.lock:
            if self._geo_cache is not None:return self._geo_cache
            rows=self.all('geo');addresses=[r for r in rows if r.get('entity')=='address']
            owners={};polygons=[]
            for c in self.all('cards'):
                if c.get('archived'):continue
                owner={'card_id':c['id'],'card_number':c['number'],'reserved':bool(c.get('_deleted_at'))}
                for ident in c.get('address_ids',[]):owners[ident]=owner
                for old in c.get('geo_addresses',[]):owners[address_key(old)]=owner
                poly=c.get('geo_polygon') or []
                if len(poly)>=3 and not c.get('_deleted_at'):
                    polygons.append((c,poly,(min(p[0] for p in poly),min(p[1] for p in poly),max(p[0] for p in poly),max(p[1] for p in poly))))
            ignored={i['address_id']:i for i in self.all('ignored')};statuses={}
            for a in addresses:
                owner=owners.get(a['id']) or owners.get(address_key(a));item=dict(owner or {})
                if a['id'] in ignored:item['ignored_id']=ignored[a['id']]['id']
                item['within']=[]
                if not owner and not item.get('ignored_id') and not a.get('retired'):
                    x,y=a['lng'],a['lat']
                    for c,poly,(w,s,e,n) in polygons:
                        if w<=x<=e and s<=y<=n and point_in_polygon([x,y],poly):item['within'].append({'card_id':c['id'],'card_number':c['number']})
                statuses[a['id']]=item
            self._geo_cache={'addresses':addresses,'status':statuses,'buildings':[r for r in rows if r.get('entity')=='building'],
                'roads':[r for r in rows if r.get('entity')=='road'],'info':self.geo_info(),'main_boundary':self.main_boundary(),'main_boundary_download':self.get('geo','main-boundary-download'),
                'changes':[r for r in rows if r.get('entity')=='address_change']}
            return self._geo_cache
    def geo_mutate(self,action,data):
        if action.startswith('geo.main.'):return self.main_boundary_mutate(action,data)
        if action in ('geo.postcode.save','geo.postcode.road'):
            manifest=dict(data['manifest']);post=text(manifest.get('postcode'),4,True)
            if not re.fullmatch(r'\d{4}',post) or manifest.get('id')!='postcode:'+post or manifest.get('entity')!='postcode_download':raise ValueError('Ugyldig postnummerhentning.')
            if not isinstance(manifest.get('roads'),list) or len(manifest['roads'])>5000:raise ValueError('Ugyldig vejliste.')
            if action=='geo.postcode.road':
                records=data.get('records',[]);road=text(data.get('road'),120,True)
                if records:self.geo_mutate('geo.import',{'records':records,'source':'DAR / Datafordeleren','label':road+' · '+post,'complete_road':{'road':road,'postcode':post},'review_changes':True})
                else:self.geo_retire(road,post,set(),review=True)
            elif data.get('lines'):
                self.geo_mutate('geo.import',{'records':data['lines'],'source':'DAR / Datafordeleren','label':'Officielle veje · '+post})
            manifest['updated_at']=stamp();self.put('geo',manifest);return {}
        if action=='geo.token':
            value=text(data.get('token'),300)
            self.put('geo',{'id':'config','token':value});return {}
        if action=='geo.import_file':
            raw=data.get('content','')
            if not isinstance(raw,str) or len(raw)>12000000:raise ValueError('Importfilen er for stor.')
            if raw.lstrip().startswith(('{','[')):
                parsed=json.loads(raw)
                if isinstance(parsed,dict) and parsed.get('type')=='FeatureCollection':
                    records=[]
                    for f in parsed.get('features',[]):
                        props=f.get('properties') or {};geom=f.get('geometry') or {}
                        if geom.get('type')!='Point':raise ValueError('Adresse-GeoJSON skal have punkter i WGS84, ét pr. adresse/lejlighed.')
                        records.append(dict(props,lng=geom['coordinates'][0],lat=geom['coordinates'][1],entity='address'))
                elif isinstance(parsed,list):records=parsed
                else:raise ValueError('Brug en GeoJSON FeatureCollection eller en liste af adresser.')
            else:
                sample=raw[:4000]
                delimiter=';' if sample.split('\n',1)[0].count(';')>sample.split('\n',1)[0].count(',') else ','
                records=list(csv.DictReader(io.StringIO(raw.lstrip('\ufeff')),delimiter=delimiter))
                records=[dict(r,entity='address',road=r.get('road') or r.get('vejnavn'),number=r.get('number') or r.get('husnr'),postcode=r.get('postcode') or r.get('postnr'),
                    lat=r.get('lat') or r.get('latitude'),lng=r.get('lng') or r.get('longitude'),floor=r.get('floor') or r.get('etage',''),door=r.get('door') or r.get('doer','')) for r in records]
            return self.geo_mutate('geo.import',{'records':records,'label':data.get('name') or 'Lokal import','source':'Lokal import'})
        if action=='geo.import':
            records=data.get('records')
            if not isinstance(records,list) or not 1<=len(records)<=20000:raise ValueError('Importen skal indeholde 1–20.000 objekter.')
            source=text(data.get('source'),80,True);count=0;imported_ids=set();known_addresses={address_key(a):a for a in self.all('geo',deleted=True)+self.all('geo') if a.get('entity')=='address'}
            review=bool(data.get('review_changes'))
            known_roads={(a.get('road'),a.get('postcode')) for a in known_addresses.values()}
            for raw in records:
                if not isinstance(raw,dict):raise ValueError('Ugyldig importpost.')
                entity=raw.get('entity','address');item={'entity':entity,'source':source}
                if entity=='address':
                    point=valid_coordinate([raw.get('lng'),raw.get('lat')]);road=text(raw.get('road'),120,True);number=text(raw.get('number'),30,True)
                    from geography import number_key
                    number_key(number)
                    post=text(raw.get('postcode'),4,True)
                    if not re.fullmatch(r'\d{4}',post):raise ValueError('Hver adresse skal have et postnummer.')
                    floor=text(raw.get('floor'),20);door=text(raw.get('door'),30)
                    identifier=raw.get('id') or 'local:'+uuid.uuid5(uuid.NAMESPACE_URL,'|'.join([post,road.casefold(),number.casefold(),floor.casefold(),door.casefold()])).hex
                    item.update(id=text(identifier,160,True),road=road,number=number.upper(),postcode=post,floor=floor,door=door,lng=point[0],lat=point[1],
                        label=text(raw.get('label'),250) or f'{road} {number}'+(f', {floor} {door}'.rstrip() if floor or door else '')+f', {post}',
                        house_id=text(raw.get('house_id'),160) or '|'.join([post,road.casefold(),number.casefold()]),count=int(raw.get('count') or 1),
                        type=raw.get('type') or ('Lejlighed' if floor or door else 'Hus'),verified=bool(raw.get('verified',False)))
                    if item['type'] not in ('Hus','Lejlighed','Lejlighedskompleks','Butik','Kontor','Virksomhed','Andet') or not 1<=item['count']<=10000:raise ValueError('Kontrollér adressetype og besøgsantal.')
                    old=self.get('geo',item['id']) or known_addresses.get(address_key(item))
                    if old and old['id']!=item['id']:
                        item['source_id']=item['id'];item['id']=old['id']
                    known_addresses[address_key(item)]=item
                    if old and old.get('type_override'):item['type']=old['type'];item['type_override']=True
                elif entity in ('road','building'):
                    points=raw.get('points')
                    if not isinstance(points,list) or not 2<=len(points)<=15000:raise ValueError('Ugyldig vej- eller bygningsgeometri.')
                    points=[valid_coordinate(p) for p in points]
                    if entity=='building' and len(points)<4:raise ValueError('Ugyldig bygning.')
                    item.update(id=text(raw.get('id'),160,True),points=points,name=text(raw.get('name'),160),building_type=text(raw.get('building_type'),80),road_type=text(raw.get('road_type'),80))
                else:raise ValueError('Importen indeholder en ukendt objekttype.')
                item['downloaded_at']=stamp()
                if entity=='address' and review:
                    fields=('road','number','postcode','floor','door','lng','lat','count','type','retired')
                    differs=old and any(old.get(k)!=item.get(k) for k in fields)
                    if differs or (not old and (road,post) in known_roads):
                        before=self.get('geo',item['id'])
                        self.put('geo',{'id':'change:'+item['id'],'entity':'address_change','kind':'changed' if before else 'new','before':before,'after':item,'at':stamp()})
                        imported_ids.add(item['id']);count+=1;continue
                    if old:item=old
                self.put('geo',item)
                if entity=='address' and old and old.get('_deleted_at'):
                    self.db.execute('UPDATE geo.records SET deleted_at=NULL,batch=NULL WHERE id=?',(item['id'],))
                imported_ids.add(item['id']);count+=1
            complete=data.get('complete_road')
            if complete:
                self.geo_retire(complete['road'],complete['postcode'],imported_ids,review=review)
            download={'id':'download:'+uuid.uuid4().hex,'entity':'download','label':text(data.get('label'),160),'source':source,'date':stamp(),'count':count}
            if data.get('complete_road'):download['complete_road']=data['complete_road']
            if data.get('bbox'):download['bbox']=data['bbox']
            self.put('geo',download);return {'count':count}
        if action=='geo.manual':
            record=dict(data,entity='address',source='Manuelt indtastet',verified=False)
            record['id']=data.get('id') or 'manual:'+uuid.uuid4().hex
            return self.geo_mutate('geo.import',{'records':[record],'label':'Manuel adresse','source':'Manuelt indtastet'})
        if action=='geo.type':
            item=self.require('geo',data['id']);typ=data.get('type')
            if item.get('entity')!='address' or typ not in ('Hus','Lejlighed','Lejlighedskompleks','Butik','Kontor','Virksomhed','Andet'):raise ValueError('Ugyldig adressetype.')
            item['type']=typ;item['type_override']=True;self.put('geo',item)
            return {}
        if action=='geo.preview':
            return self.geo_preview(data)
        if action=='geo.assign':
            preview=self.geo_preview(data)
            if preview['conflicts']:raise ValueError('Nogle adresser findes på et andet kort eller i 48-timers gendannelse. Fjern dem fra valget først.')
            if preview['retired']:raise ValueError('Nogle adresser er ikke længere gældende hos DAR. Fjern dem fra valget først.')
            if preview['ignored']:raise ValueError('Nogle valgte adresser er markeret Se bort fra. Ophæv markeringen eller fjern dem fra valget.')
            members=preview['addresses']
            if not members:raise ValueError('Vælg mindst én adresse.')
            ident=data.get('card_id')
            if ident:c=self.require('cards',ident)
            else:
                result=self._mutate('card.save',{'number':data.get('number'),'name':data.get('name',''),'area_id':data.get('area_id',''),'kind':data.get('kind','Ukendt'),'temporary':True})
                c=self.require('cards',result['id'])
            rows=street_rows(members)
            self._mutate('card.save',dict(c,temporary=False,addresses=rows,map_color=data.get('map_color',c.get('map_color','#477596'))),geographic=True)
            c=self.require('cards',c['id']);c['address_ids']=[a['id'] for a in members];c['geo_addresses']=members
            polygon=data.get('polygon')
            c['geo_polygon']=valid_polygon(polygon,limit=5000) if polygon else enclosing_outline([[a['lng'],a['lat']] for a in members])
            c['geo_outline_source']='manual' if polygon else 'suggestion';c['geo_updated']=stamp();self.put('cards',c)
            return {'id':c['id'],'count':len(members),'visits':sum(a['count'] for a in members),'rows':rows}
        if action=='geo.boundary':
            c=self.require('cards',data['card_id']);c['geo_polygon']=valid_polygon(data['polygon'],limit=5000);c['geo_outline_source']='manual';self.put('cards',c);return {}
        if action=='ignore.save':
            a=self.require('geo',data['address_id'])
            if a.get('entity')!='address':raise ValueError('Vælg en adresse.')
            if any(a['id'] in c.get('address_ids',[]) or any(address_key(a)==address_key(old) for old in c.get('geo_addresses',[])) for c in self.all('cards')):
                raise ValueError('Adressen ligger allerede på et kort. Fjern den fra kortets valg først.')
            existing=next((i for i in self.all('ignored') if i['address_id']==a['id']),None)
            self.put('ignored',{'id':existing['id'] if existing else uuid.uuid4().hex,'address_id':a['id'],'label':a['label'],'reason':text(data.get('reason'),200,True),'date':stamp()})
            return {}
        raise ValueError('Ukendt geografisk handling.')
    def geo_retire(self,road,postcode,imported_ids,review=False):
        for old in self.all('geo'):
            if old.get('entity')=='address' and old.get('source') in ('DAR / Adressevælger','DAR / Datafordeleren') and old.get('road')==road and old.get('postcode')==postcode and old['id'] not in imported_ids:
                if review and not old.get('retired'):
                    self.put('geo',{'id':'change:'+old['id'],'entity':'address_change','kind':'retired','before':old,'after':dict(old,retired=True),'at':stamp()})
                elif not review:old['retired']=True;self.put('geo',old)
    def geo_preview(self,data):
        all_addresses=[a for a in self.all('geo') if a.get('entity')=='address']
        mode=data.get('mode','ids')
        if mode=='polygon':
            polygon=valid_polygon(data.get('polygon'),limit=5000)
            selected=[a for a in all_addresses if not a.get('retired') and point_in_polygon([a['lng'],a['lat']],polygon)]
        elif mode=='range':
            road=text(data.get('road'),120,True);post=text(data.get('postcode'),4,True)
            in_number_range(data.get('from'),data.get('from'),data.get('to'),data.get('parity','all'))
            selected=[a for a in all_addresses if not a.get('retired') and a['road'].casefold()==road.casefold() and a['postcode']==post and in_number_range(a['number'],data.get('from'),data.get('to'),data.get('parity','all'))]
        elif mode=='ids':
            ids=data.get('address_ids',[])
            if not isinstance(ids,list) or len(ids)>10000:raise ValueError('For mange adresser.')
            lookup={a['id']:a for a in all_addresses}
            if any(i not in lookup for i in ids):raise ValueError('En valgt adresse findes ikke længere. Opdater kortdata.')
            selected=[lookup[i] for i in dict.fromkeys(ids)]
        else:raise ValueError('Ukendt adressevalg.')
        # Different import IDs for the same physical unit must never inflate counts.
        unique={}
        for a in sorted(selected,key=lambda a:not a.get('verified')):unique.setdefault(address_key(a),a)
        selected=list(unique.values());reserved=self.all('cards');owners={}
        for c in reserved:
            if c.get('archived'):continue
            if c['id']==data.get('card_id'):continue
            for a in c.get('geo_addresses',[]):owners[address_key(a)]=c
            for ident in c.get('address_ids',[]):owners[ident]=c
        ignored={i['address_id'] for i in self.all('ignored')};ignored_keys={address_key(a) for a in all_addresses if a['id'] in ignored};conflicts=[];excluded=[]
        for a in selected:
            c=owners.get(a['id']) or owners.get(address_key(a))
            if c:conflicts.append({'id':a['id'],'card_number':c['number'],'deleted':bool(c.get('_deleted_at'))})
            if a['id'] in ignored or address_key(a) in ignored_keys:excluded.append(a['id'])
        return {'addresses':selected,'conflicts':conflicts,'ignored':excluded,'retired':[a['id'] for a in selected if a.get('retired')],'visits':sum(a['count'] for a in selected),'rows':street_rows(selected),'outline':enclosing_outline([[a['lng'],a['lat']] for a in selected]) if selected else []}
