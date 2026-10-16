"""Whole congregation boundary and reversible cleanup of unused public addresses."""
from collections import Counter
import json
import re
import uuid
from admin_store import signature
from geography import valid_polygon, point_in_polygon

class MainBoundaryStore:
    def main_boundary(self):return self.get('geo','main-boundary')
    def main_boundary_preview(self):
        from geo_store import address_key
        boundary=self.main_boundary()
        if not boundary:raise ValueError('Tegn og gem den samlede distriktsgrænse først.')
        poly=boundary['points'];w=min(p[0] for p in poly);e=max(p[0] for p in poly);s=min(p[1] for p in poly);n=max(p[1] for p in poly)
        addresses=[a for a in self.all('geo') if a.get('entity')=='address']
        outside=[a for a in addresses if not (w<=a['lng']<=e and s<=a['lat']<=n and point_in_polygon([a['lng'],a['lat']],poly))]
        cards=self.all('cards')+self.all('cards',deleted=True);ignored=self.all('ignored')+self.all('ignored',deleted=True);ibs=self.all('ib')+self.all('ib',deleted=True)
        owners={}
        for c in cards:
            for ident in c.get('address_ids',[]):owners[ident]=c['number']
            for a in c.get('geo_addresses',[]):owners[address_key(a)]=c['number']
        ignored_ids={i['address_id'] for i in ignored};removable=[];protected=[]
        for a in outside:
            owner=owners.get(a['id']) or owners.get(address_key(a))
            reason=('Kort '+owner) if owner else 'Se bort fra' if a['id'] in ignored_ids else ''
            clean=lambda value:re.sub(r'[\s.,]+','',str(value or '').casefold())
            if not reason and any(i.get('address_id')==a['id'] or i.get('road','').casefold().strip()==a['road'].casefold().strip() and clean(i.get('number')) in (clean(a['number']),clean(' '.join([a['number'],a.get('floor',''),a.get('door','')])) ) for i in ibs):reason='IB'
            if reason:protected.append({'id':a['id'],'label':a['label'],'reason':reason})
            else:removable.append(a)
        return {'removable':removable,'protected':protected,'outside':len(outside),'expected':signature([boundary,outside,cards,ignored,ibs]),'roads':[{'road':road,'count':count} for road,count in sorted(Counter(a['road'] for a in removable).items())]}
    def main_boundary_mutate(self,action,data):
        from geo_store import stamp
        if action=='geo.main.import.preview':
            from boundary_import import preview_boundary
            return preview_boundary(data.get('content',''),data.get('scope','main'))
        if action in ('geo.main.download.save','geo.main.download.tile'):
            manifest=dict(data['manifest']);boundary=self.main_boundary()
            if not boundary or manifest.get('boundary_key')!=signature(boundary['points']):raise ValueError('Grænsen er ændret. Start en ny hentning til den gemte grænse.')
            if manifest.get('id')!='main-boundary-download' or manifest.get('entity')!='boundary_download' or not isinstance(manifest.get('tiles'),list) or not 1<=len(manifest['tiles'])<=500:raise ValueError('Ugyldigt grænseudtræk.')
            if action.endswith('.tile'):
                records=data.get('records',[])
                if any(not point_in_polygon([a['lng'],a['lat']],boundary['points']) for a in records):raise ValueError('Udtrækket indeholder adresser udenfor grænsen.')
                for offset in range(0,len(records),20000):self.geo_mutate('geo.import',{'records':records[offset:offset+20000],'source':'DAR / Datafordeleren','label':'Samlet distriktsgrænse','review_changes':manifest.get('review_changes',False)})
                lines=data.get('lines',[])
                for offset in range(0,len(lines),20000):self.geo_mutate('geo.import',{'records':lines[offset:offset+20000],'source':'DAR / Datafordeleren','label':'Officielle vejlinjer · samlet grænse'})
            if manifest.get('status')=='complete':
                if any(t.get('status')!='done' for t in manifest['tiles']):raise ValueError('Grænseudtrækket er endnu ikke komplet.')
                seen={ident for tile in manifest['tiles'] for ident in tile.get('address_ids',[])}
                for a in self.all('geo'):
                    if a.get('entity')=='address' and a.get('verified') and a.get('source','').startswith('DAR') and not a.get('retired') and a['id'] not in seen and a.get('source_id') not in seen and point_in_polygon([a['lng'],a['lat']],boundary['points']):
                        if manifest.get('review_changes'):
                            self.put('geo',{'id':'change:'+a['id'],'entity':'address_change','kind':'retired','before':a,'after':dict(a,retired=True,retired_at=stamp()),'at':stamp()})
                        else:a['retired']=True;a['retired_at']=stamp();self.put('geo',a)
            manifest['updated_at']=stamp();self.put('geo',manifest);return {}
        if action=='geo.main.save':
            points=valid_polygon(data.get('points'),limit=5000)
            if len({tuple(p) for p in points})!=len(points):raise ValueError('Et hjørne er gentaget. Fjern det ekstra punkt; grænsen lukkes automatisk.')
            self.put('geo',{'id':'main-boundary','entity':'main_boundary','points':points,'updated_at':stamp()})
            return {'points':len(points)}
        if action in ('geo.main.prune.preview','geo.main.prune'):
            preview=self.main_boundary_preview()
            if action.endswith('preview'):return {k:v for k,v in preview.items() if k!='removable'}|{'count':len(preview['removable'])}
            if data.get('expected')!=preview['expected']:raise ValueError('Grænsen eller adresserne er ændret. Kontrollér oprydningen igen.')
            batch='outside:'+uuid.uuid4().hex
            for a in preview['removable']:self.mark_deleted('geo',a['id'],batch,stamp())
            return {'count':len(preview['removable']),'batch':batch}
        raise ValueError('Ukendt handling for samlet grænse.')
