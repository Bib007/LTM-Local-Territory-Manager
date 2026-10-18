"""Public rectangular DAR queries; exact polygon filtering and checkpoints stay local."""
import copy
import math
from datetime import datetime, timezone
from admin_store import signature
from address_checkpoint import GRAPHQL_SOURCE, checkpoint_source, require_source
from dar_download import road_lines
from geography import wgs84_to_utm32, point_in_polygon
from postcode import HOST, BASE, Paused, SourceUnavailable, SourceTimeout, rest_addresses, rest_road_lines

def boundary_tiles(points):
    projected=[]
    for i,a in enumerate(points):
        b=points[(i+1)%len(points)]
        steps=max(1,math.ceil(max(abs(a[0]-b[0]),abs(a[1]-b[1]))/.01))
        for j in range(steps):projected.append(wgs84_to_utm32(a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps))
    w=math.floor(min(p[0] for p in projected)-100);e=math.ceil(max(p[0] for p in projected)+100)
    s=math.floor(min(p[1] for p in projected)-100);n=math.ceil(max(p[1] for p in projected)+100)
    if (e-w)*(n-s)>2500*1000000:raise ValueError('Grænsen omslutter et for stort område til denne hentning (maks. 2.500 km²).')
    tiles=[{'bbox':[x,y,min(x+3000,e),min(y+3000,n)],'status':'pending','count':0} for y in range(s,n,3000) for x in range(w,e,3000)]
    if len(tiles)>500:raise ValueError('Grænsen kræver for mange udsnit. Brug et mindre område.')
    return tiles

def smaller_tiles(tile):
    """Partition a timed-out tile; never change completed checkpoints."""
    w,s,e,n=tile['bbox'];depth=tile.get('split_depth',0)
    if depth>=2 or min(e-w,n-s)<=750:return []
    x=(w+e)/2;y=(s+n)/2
    return [{'bbox':bbox,'status':'pending','count':0,'split_depth':depth+1}
        for bbox in ([w,s,x,y],[x,s,e,y],[w,y,x,n],[x,y,e,n])]

class BoundaryDownload:
    def boundary(self,data,progress):
        with self.store.lock:
            boundary=copy.deepcopy(self.store.main_boundary())
            manifest=copy.deepcopy(self.store.get('geo','main-boundary-download'))
        if not boundary:raise ValueError('Kontrollér og gem den samlede grænse først.')
        points=boundary['points'];key=signature(points)
        if manifest and manifest.get('boundary_key')==key and not data.get('refresh'):
            require_source(manifest,self.source_id(),self.source_schema())
            if checkpoint_source(manifest)==GRAPHQL_SOURCE and manifest.get('point_query_version')!=2:
                # Earlier point-status filters could certify empty tiles. Fetch
                # them again at a new snapshot, preserving stored local data.
                data={**data,'refresh':True}
        if not manifest or manifest.get('boundary_key')!=key or data.get('refresh'):
            manifest={'id':'main-boundary-download','entity':'boundary_download','boundary_key':key,'points':points,
                'snapshot':datetime.now(timezone.utc).isoformat(timespec='seconds'),'source_id':self.source_id(),'schema_sha256':self.source_schema(),'point_query_version':2,'review_changes':bool(data.get('refresh')),'tiles':boundary_tiles(points)}
        require_source(manifest,self.source_id(),self.source_schema())
        manifest['status']='running';self.store.mutate('geo.main.download.save',{'manifest':manifest})
        tiles=manifest['tiles'];total=len(tiles);done=sum(t['status']=='done' for t in tiles)
        stop_reason=''
        temporal={'Status':3,'VirkningFra':manifest['snapshot'],'RegistreringFra':manifest['snapshot']}
        try:
            index=0
            while index<len(tiles):
                tile=tiles[index]
                if tile['status']=='done':index+=1;continue
                self.check_cancel();progress(completed=done,total=total,message=f'Henter udsnit {index+1} af {total} indenfor grænsen…')
                w,s,e,n=tile['bbox'];params=dict(temporal,Vest=w,Syd=s,Oest=e,Nord=n)
                try:
                    if checkpoint_source(manifest)==GRAPHQL_SOURCE:
                        result=self.graph_adapter(manifest['snapshot'],manifest.get('schema_sha256')).tile(tile['bbox'])
                        addresses=result['addresses'];lines=road_lines(result['roads'])
                    else:
                        expected=self.request(HOST,BASE+'adresse',dict(params,format='json',count='true'))
                        if isinstance(expected,dict):expected=expected.get('count')
                        if type(expected)!=int or expected<0:raise ValueError('DAR-kilden gav ikke et gyldigt kontroltal.')
                        items=[] if expected==0 else self.rest_pages('adresse',params,lambda count:progress(message=f'Udsnit {index+1}/{total} · {count} adresser læst'))
                        if len(items)!=expected:raise ValueError('Antal adresser matcher ikke kildens kontroltal. Udsnittet skal genprøves.')
                        addresses=rest_addresses(items,None,None)
                        if len(addresses)!=expected:raise ValueError('Kilden indeholdt adresser med forkert status. Udsnittet skal genprøves.')
                    addresses=[a for a in addresses if point_in_polygon([a['lng'],a['lat']],points)]
                    if checkpoint_source(manifest)!=GRAPHQL_SOURCE:
                        selected={a['id'] for a in addresses};roads={}
                        for item in items:
                            if 'dar:'+item['id_lokalId'] not in selected:continue
                            road=(item.get('husnummer') or {}).get('navngivenVej') or {}
                            if road.get('id_lokalId'):roads[road['id_lokalId']]=road
                        lines=rest_road_lines(roads.values())
                    self.check_cancel();tile.update(status='done',count=len(addresses),address_ids=[a['id'] for a in addresses]);tile.pop('error',None)
                    self.store.mutate('geo.main.download.tile',{'manifest':manifest,'records':addresses,'lines':lines})
                    done+=1
                except SourceTimeout as err:
                    self.check_cancel();children=smaller_tiles(tile)
                    if children and len(tiles)+3<=500:
                        tiles[index:index+1]=children;total=len(tiles)
                        self.store.mutate('geo.main.download.save',{'manifest':manifest})
                        progress(completed=done,total=total,message=f'Udsnit {index+1} fik timeout. Området er delt i fire mindre udsnit; fortsætter…')
                        continue
                    tile.update(status='error',error=str(err));stop_reason=f'Hentningen er stoppet ved udsnit {index+1}. '+str(err)
                    self.store.mutate('geo.main.download.save',{'manifest':manifest})
                    progress(completed=done,total=total,message=stop_reason)
                    break
                except SourceUnavailable as err:
                    tile.update(status='error',error=str(err));stop_reason=f'Hentningen er stoppet ved udsnit {index+1}. '+str(err)
                    self.store.mutate('geo.main.download.save',{'manifest':manifest})
                    progress(completed=done,total=total,message=stop_reason)
                    break
                except ValueError as err:
                    tile.update(status='error',error=str(err));self.store.mutate('geo.main.download.save',{'manifest':manifest})
                progress(completed=done,total=total);index+=1
            manifest['status']='complete' if done==total else 'partial'
            manifest['empty_result']=done==total and not any(t.get('address_ids') for t in tiles)
        except Paused:
            manifest['status']='paused';self.store.mutate('geo.main.download.save',{'manifest':manifest});raise
        self.store.mutate('geo.main.download.save',{'manifest':manifest})
        warnings=[f"Udsnit {i+1}: {t.get('error','Afventer hentning')}" for i,t in enumerate(tiles) if t['status']!='done']
        with self.store.lock:
            count=sum(a.get('entity')=='address' and not a.get('retired') and point_in_polygon([a['lng'],a['lat']],points) for a in self.store.all('geo'))
        if manifest.get('empty_result'):
            warnings.append('DAR returnerede ingen adresser indenfor den gemte grænse. Kontrollér grænsen, og prøv en enkelt vej. En kontrolleret forbindelse bekræfter ikke, at adresser er hentet.')
        return {'count':count,'complete':done==total,'warnings':warnings,'empty':bool(manifest.get('empty_result')),
            'fetched_count':len({ident for tile in tiles for ident in tile.get('address_ids',[])}),
            'bbox':[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)],
            'note':f'{count} lokale adresser indenfor grænsen · {done}/{total} udsnit. '+('Ingen adresser fundet. Kontrollér grænsen, og prøv en enkelt vej.' if manifest.get('empty_result') else 'Alle udsnit er hentet og kontrolleret.' if done==total else (stop_reason+' Færdige udsnit er bevaret. Fortsæt senere under Samlet distriktsgrænse.' if stop_reason else 'Hentningen er ufuldstændig. Fortsæt for at genprøve de manglende udsnit.'))}
