import math
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from geography import valid_polygon

POLY=[[9.99,54.99],[10.01,54.99],[10.01,55.01],[9.99,55.01]]
class MainBoundaryTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def address(self,n,lng=10):
        self.s.mutate('geo.manual',{'road':'Fiktiv vej','number':str(n),'postcode':'9999','lng':lng,'lat':55})
        return next(a['id'] for a in self.s.geo_state()['addresses'] if a['number']==str(n))
    def save(self,poly=POLY):return self.s.mutate('geo.main.save',{'points':poly})
    def preview(self):return self.s.mutate('geo.main.prune.preview',{})
    def prune(self,p):return self.s.mutate('geo.main.prune',{'expected':p['expected']})
    def test_many_points_and_restart_preserve_all_details(self):
        points=[[10+.01*math.cos(i*2*math.pi/5000),55+.01*math.sin(i*2*math.pi/5000)] for i in range(5000)]
        self.assertEqual(self.save(points)['points'],5000)
        self.s.close();self.s=Store(self.tmp.name)
        self.assertEqual(len(self.s.geo_state()['main_boundary']['points']),5000)
        with self.assertRaises(ValueError):self.save(points+points[:1])
    def test_invalid_main_boundary_keeps_previous(self):
        self.save();before=self.s.main_boundary()
        for poly in ([[10,55],[10.01,55]],[[10,55],[10.02,55.02],[10.02,55],[10,55.02]],[[10,55],[99,55],[10,55.01]]):
            with self.assertRaises(ValueError):self.save(poly)
        self.assertEqual(before,self.s.main_boundary())
    def test_removes_only_unused_outside_preserves_edge_and_supports_recovery(self):
        inside=self.address(1);edge=self.address(2,10.01);outside=self.address(3,10.02)
        self.save();p=self.preview();self.assertEqual(p['count'],1);self.assertEqual(len(self.s.geo_state()['addresses']),3)
        r=self.prune(p);self.assertEqual({a['id'] for a in self.s.geo_state()['addresses']},{inside,edge})
        self.assertTrue(any(x['batch']==r['batch'] for x in self.s.recovery()))
        self.s.mutate('restore',r);self.assertIsNotNone(self.s.get('geo',outside))
    def test_protects_cards_ignore_ib_and_private_history(self):
        assigned=self.address(1,10.02);ignored=self.address(2,10.03);ib=self.address(3,10.04);unused=self.address(4,10.05)
        c=self.s.mutate('geo.assign',{'number':'120','address_ids':[assigned]})['id']
        person=self.s.mutate('publisher.save',{'name':'Fiktiv person'})['id']
        self.s.mutate('loan.issue',{'card_id':c,'publisher_id':person,'initial':True,'date':'2026-01-01'})
        self.s.mutate('ignore.save',{'address_id':ignored,'reason':'Fiktiv transformerstation'})
        self.s.mutate('ib.save',{'card_id':c,'road':'Fiktiv vej','number':'3','date':'2026-01-01'})
        self.save();before=self.s.state();p=self.preview();self.assertEqual(p['count'],1);self.assertEqual(len(p['protected']),3)
        self.prune(p);after=self.s.state()
        for m in ('cards','loans','ib','ignored','publishers','completions'):self.assertEqual(before[m],after[m])
        self.assertIsNone(self.s.get('geo',unused));self.assertIsNotNone(self.s.get('geo',assigned))
    def test_deleted_card_still_reserves_address(self):
        a=self.address(1,10.02);c=self.s.mutate('geo.assign',{'number':'120','address_ids':[a]})['id']
        self.s.mutate('delete',{'module':'cards','id':c});self.save();self.assertEqual(self.preview()['count'],0)
    def test_stale_preview_and_new_card_reject_cleanup(self):
        a=self.address(1,10.02);self.save();p=self.preview()
        self.s.mutate('geo.assign',{'number':'120','address_ids':[a]})
        with self.assertRaises(ValueError):self.prune(p)
        self.assertIsNotNone(self.s.get('geo',a))
        p=self.preview();self.save([[9.99,54.99],[10.1,54.99],[10.1,55.1],[9.99,55.1]])
        with self.assertRaises(ValueError):self.prune(p)
    def test_cleanup_requires_boundary(self):
        with self.assertRaises(ValueError):self.preview()
    def test_reimport_can_reintroduce_outside_and_be_pruned_again(self):
        a=self.address(1,10.02);self.save();self.prune(self.preview())
        self.address(1,10.02);self.assertIsNotNone(self.s.get('geo',a));self.assertEqual(self.preview()['count'],1)

if __name__=='__main__':unittest.main()
