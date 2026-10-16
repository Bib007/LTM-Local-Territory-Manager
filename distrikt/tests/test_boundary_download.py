import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from geodata import Downloads
from geography import wgs84_to_utm32,utm32_to_wgs84
from boundary_download import boundary_tiles,smaller_tiles
from postcode import HOST,BASE,Paused,SourceUnavailable,SourceTimeout
from test_postcode import unit

POLY=[[8.995,54.995],[9.035,54.995],[9.035,55.005],[8.995,55.005]]
class BoundaryDownloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name);self.d=Downloads(self.s)
        self.s.mutate('geo.main.save',{'points':POLY})
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def run_download(self):return self.d.boundary({},lambda **kw:None)
    def mock_source(self,rows,error_tile=None,bad_count=False):
        calls=[];west=min(t['bbox'][0] for t in boundary_tiles(POLY))
        def request(host,path,params=None,query=None):
            self.assertEqual((host,path),(HOST,BASE+'adresse'))
            self.assertEqual(set(params)-{'format','count','page','pagesize'},{'Nord','Syd','Oest','Vest','Status','VirkningFra','RegistreringFra'})
            calls.append(copy.deepcopy(params))
            if error_tile is not None and params['Vest']!=west:raise ValueError('Fiktiv kildefejl')
            if params.get('count'):return {'count':len(rows)+(1 if bad_count else 0)}
            start=(params['page']-1)*params['pagesize'];return copy.deepcopy(rows[start:start+params['pagesize']])
        self.d.request=request;return calls
    def test_projection_roundtrip_and_tile_bounds(self):
        for p in [[9,55],[9.61,55.5],[9.65,55.70],[12.57,55.68]]:
            back=utm32_to_wgs84(*wgs84_to_utm32(*p))
            self.assertAlmostEqual(back[0],p[0],places=5);self.assertAlmostEqual(back[1],p[1],places=5)
        self.assertEqual(len(boundary_tiles(POLY)),1)
        with self.assertRaises(ValueError):boundary_tiles([[8,54.5],[13,54.5],[13,58],[8,58]])
    def test_all_postcodes_apartments_paging_filter_and_private_preservation(self):
        c=self.s.mutate('card.save',{'number':'120','temporary':True})['id'];p=self.s.mutate('publisher.save',{'name':'Fiktiv person'})['id']
        self.s.mutate('loan.issue',{'card_id':c,'publisher_id':p,'date':'2026-01-01','initial':True})
        self.s.mutate('ib.save',{'card_id':c,'road':'Privat testvej','number':'1','date':'2026-01-01'})
        before=self.s.state();rows=[unit('a'),unit('b',floor='1',door='tv'),unit('c',number='3',post='8888'),unit('outside','5')]
        rows[-1]['husnummer']['adgangspunkt']['position']='POINT(510000 6094791.420874)'
        rows[0]['husnummer']['navngivenVej'].update(id_lokalId='road',vejnavnebeliggenhed_vejnavnelinje='LINESTRING(500000 6094791.42,500020 6094791.42)')
        calls=self.mock_source(rows)
        with patch('postcode.PAGE_SIZE',2):result=self.run_download()
        self.assertTrue(result['complete']);self.assertEqual(result['count'],3);self.assertTrue(any(p.get('page',0)>1 for p in calls))
        self.assertEqual(self.s.geo_info()['roads'],1);self.assertEqual({a['postcode'] for a in self.s.geo_state()['addresses']},{'9999','8888'})
        for module in ('cards','publishers','loans','completions','ib','ignored','visits'):self.assertEqual(before[module],self.s.state()[module])
        self.assertFalse(any('points' in p or 'Privat' in str(p) for p in calls))
    def test_bad_control_count_or_coordinates_never_marks_tile_complete(self):
        for bad in ('count','coordinates'):
            rows=[unit('a')]
            if bad=='coordinates':rows[0]['husnummer']['adgangspunkt']['position']='POINT EMPTY'
            self.mock_source(rows,bad_count=bad=='count');result=self.run_download()
            self.assertFalse(result['complete']);self.assertEqual(self.s.geo_info()['addresses'],0)
            self.assertEqual(self.s.get('geo','main-boundary-download')['status'],'partial')
    def test_pause_restart_resumes_only_unfinished_tiles_and_no_duplicate_units(self):
        # Broader boundary creates two adjacent tiles. Fake endpoint repeats a shared unit.
        global POLY
        original=POLY;POLY=[[8.995,54.995],[9.075,54.995],[9.075,55.005],[8.995,55.005]]
        try:
            self.s.mutate('geo.main.save',{'points':POLY});self.assertEqual(len(boundary_tiles(POLY)),2)
            self.mock_source([unit('a')])
            def progress(**kw):
                if kw.get('completed')==1:self.d.cancel_event.set()
            with self.assertRaises(Paused):self.d.boundary({},progress)
            self.assertEqual(self.s.get('geo','main-boundary-download')['status'],'paused');self.assertEqual(self.s.geo_info()['addresses'],1)
            self.s.close();self.s=Store(self.tmp.name);self.d=Downloads(self.s);calls=self.mock_source([unit('a')]);result=self.run_download()
            self.assertTrue(result['complete']);self.assertEqual(result['count'],1);self.assertEqual(len({p['Vest'] for p in calls}),1)
        finally:POLY=original
    def test_source_failure_stops_remaining_tiles_and_resume_keeps_completed(self):
        points=[[8.995,54.995],[9.16,54.995],[9.16,55.005],[8.995,55.005]]
        self.s.mutate('geo.main.save',{'points':points})
        tiles=boundary_tiles(points);self.assertGreaterEqual(len(tiles),4)
        calls=[]
        def source(host,path,params=None,query=None):
            calls.append(params['Vest'])
            if params['Vest']!=tiles[0]['bbox'][0]:raise SourceUnavailable('Fiktiv timeout. Automatisk genprøvet 2 gange.')
            return 0 if params.get('count') else []
        self.d.request=source
        result=self.run_download();self.assertFalse(result['complete'])
        self.assertIn('stoppet ved udsnit 2',result['note'])
        self.assertEqual(set(calls),{tiles[0]['bbox'][0],tiles[1]['bbox'][0]})
        manifest=self.s.get('geo','main-boundary-download')
        self.assertEqual(manifest['status'],'partial')
        self.assertEqual([t['status'] for t in manifest['tiles'][:3]],['done','error','pending'])
        before_snapshot=manifest['snapshot'];calls.clear()
        self.s.close();self.s=Store(self.tmp.name);self.d=Downloads(self.s)
        def restored(host,path,params=None,query=None):
            calls.append(params['Vest']);return 0 if params.get('count') else []
        self.d.request=restored
        self.assertTrue(self.run_download()['complete'])
        self.assertNotIn(tiles[0]['bbox'][0],calls)
        self.assertEqual(self.s.get('geo','main-boundary-download')['snapshot'],before_snapshot)

    def test_small_tiles_partition_parent_and_limit_depth(self):
        tile={'bbox':[0,0,3000,3000]}
        children=smaller_tiles(tile)
        self.assertEqual(len(children),4)
        self.assertEqual(sum((t['bbox'][2]-t['bbox'][0])*(t['bbox'][3]-t['bbox'][1]) for t in children),9000000)
        self.assertEqual(children[0]['bbox'],[0,0,1500,1500])
        grandchildren=smaller_tiles(children[0]);self.assertEqual(len(grandchildren),4)
        self.assertEqual(smaller_tiles(grandchildren[0]),[])
        self.assertEqual(smaller_tiles({'bbox':[0,0,500,1000]}),[])
    def test_timeout_splits_only_failed_tile_and_completes(self):
        points=[[8.995,54.995],[9.16,54.995],[9.16,55.035],[8.995,55.035]]
        self.s.mutate('geo.main.save',{'points':points})
        original=boundary_tiles(points);first=original[0]['bbox'];second=original[1]['bbox'];calls=[]
        def source(host,path,params=None,query=None):
            bbox=[params['Vest'],params['Syd'],params['Oest'],params['Nord']];calls.append(bbox)
            if bbox==second:raise SourceTimeout('Fiktiv timeout')
            return 0 if params.get('count') else []
        self.d.request=source;result=self.run_download()
        self.assertTrue(result['complete']);manifest=self.s.get('geo','main-boundary-download')
        self.assertEqual(len(manifest['tiles']),len(original)+3)
        self.assertEqual(calls.count(first),1)
        self.assertNotIn(second,[t['bbox'] for t in manifest['tiles']])
        self.assertTrue(all(t['status']=='done' for t in manifest['tiles']))
    def test_all_timeout_stops_at_smallest_tile_and_persists_split_on_restart(self):
        points=[[8.995,54.995],[9.16,54.995],[9.16,55.035],[8.995,55.035]]
        self.s.mutate('geo.main.save',{'points':points});calls=[]
        def source(*args,**kwargs):calls.append(1);raise SourceTimeout('Fiktiv timeout')
        self.d.request=source;self.assertFalse(self.run_download()['complete']);self.assertEqual(len(calls),3)
        manifest=self.s.get('geo','main-boundary-download');bbox=manifest['tiles'][0]['bbox']
        self.assertEqual(manifest['tiles'][0]['split_depth'],2)
        self.s.close();self.s=Store(self.tmp.name);self.d=Downloads(self.s);calls.clear()
        self.d.request=source;self.assertFalse(self.run_download()['complete']);self.assertEqual(len(calls),1)
        self.assertEqual(self.s.get('geo','main-boundary-download')['tiles'][0]['bbox'],bbox)

    def test_empty_count_needs_no_address_page(self):
        calls=self.mock_source([]);self.assertTrue(self.run_download()['complete'])
        self.assertTrue(all(p.get('count')=='true' for p in calls))

    def test_changed_boundary_rejects_stale_checkpoint_and_outside_records(self):
        self.mock_source([]);self.run_download();manifest=self.s.get('geo','main-boundary-download')
        with self.assertRaises(ValueError):self.s.mutate('geo.main.download.tile',{'manifest':manifest,'records':[{'lng':10,'lat':55}]})
        self.s.mutate('geo.main.save',{'points':[[9.1,55],[9.2,55],[9.2,55.1],[9.1,55.1]]})
        with self.assertRaises(ValueError):self.s.mutate('geo.main.download.save',{'manifest':manifest})
    def test_geojson_import_is_preview_only_and_rejects_invalid_geometry(self):
        before=self.s.main_boundary();content=json.dumps({'type':'Feature','geometry':{'type':'Polygon','coordinates':[POLY+POLY[:1]]}})
        result=self.s.mutate('geo.main.import.preview',{'content':content});self.assertEqual(result['points'],POLY);self.assertEqual(self.s.main_boundary(),before)
        for geom in ({'type':'MultiPolygon','coordinates':[[POLY]]},{'type':'Polygon','coordinates':[POLY,POLY]},{'type':'Polygon','coordinates':[[[10,55],[100,55],[10,56]]]}):
            with self.assertRaises(ValueError):self.s.mutate('geo.main.import.preview',{'content':json.dumps(geom)})

    def test_complete_refresh_retires_missing_dar_units_but_not_manual_or_outside(self):
        from postcode import rest_addresses
        records=rest_addresses([unit('old')],None,None)
        self.s.mutate('geo.import',{'records':records,'source':'DAR / Datafordeleren','label':'Fiktiv tidligere kilde'})
        self.s.mutate('geo.manual',{'road':'Manuel testvej','number':'1','postcode':'9999','lng':9,'lat':55})
        c=self.s.mutate('geo.assign',{'number':'120','address_ids':['dar:old']})['id'];before=self.s.get('cards',c)
        self.mock_source([],bad_count=True);self.run_download();self.assertFalse(self.s.get('geo','dar:old').get('retired'))
        self.mock_source([]);self.run_download();self.assertTrue(self.s.get('geo','dar:old')['retired'])
        self.assertEqual(before,self.s.get('cards',c));self.assertFalse(next(a for a in self.s.geo_state()['addresses'] if a['road']=='Manuel testvej').get('retired'))

if __name__=='__main__':unittest.main()
