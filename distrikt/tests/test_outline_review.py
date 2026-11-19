"""Fictional DAR geometry; neighbour changes need specific atomic approval."""
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from geography import point_in_polygon
from portable import digest
from territory_outline import meets

class OutlineReviewTests(unittest.TestCase):
    scale=111320*math.cos(math.radians(55))
    def point(self,x,y):return [round(10+x/self.scale,7),round(55+y/111320,7)]
    def rectangle(self,x0,y0,x1,y1):return [self.point(x0,y0),self.point(x1,y0),self.point(x1,y1),self.point(x0,y1)]
    def address(self,ident,x,y):
        lng,lat=self.point(x,y)
        return dict(id=ident,entity='address',postcode='9999',road='Fiktivvej',number=ident,lng=lng,lat=lat,count=1,type='Hus')
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=Store(self.tmp.name);self.addCleanup(self.s.close)
        self.target=self.s.mutate('card.save',{'number':'F001','temporary':True})['id']
        self.neighbor=self.s.mutate('card.save',{'number':'F002','temporary':True})['id']
        self.records=[self.address('1',-40,0),self.address('3',40,0),self.address('2',0,70)]
        with self.s.transaction():
            for a in self.records:self.s.put('geo',a)
            self.s.put('cards',{**self.s.require('cards',self.neighbor),'geo_polygon':self.rectangle(-10,-500,10,500),'address_ids':['2'],'geo_addresses':[self.records[2]]})
        self.request={'card_id':self.target,'address_ids':['1','3'],'suggest_outline':True}
    def preview(self):return self.s.mutate('geo.preview',self.request)
    def save(self,p,**extra):return self.s.mutate('geo.assign',{'card_id':self.target,'address_ids':['1','3'],'polygon':p['outline'],'outline_expected':p['outline_expected'],**extra})
    def test_no_write_preview_requires_approval_and_preserves_owned_records(self):
        before=digest(self.s);p=self.preview();self.assertEqual(digest(self.s),before)
        self.assertEqual(p['outline_status'],'neighbors');self.assertEqual(len(p['outline_changes']),1)
        with self.assertRaisesRegex(ValueError,'Godkend'):self.save(p)
        self.assertEqual(digest(self.s),before)
        self.save(p,approve_neighbors=True)
        target=self.s.require('cards',self.target);neighbor=self.s.require('cards',self.neighbor)
        self.assertFalse(meets(target['geo_polygon'],neighbor['geo_polygon'],0))
        self.assertEqual(neighbor['address_ids'],['2']);self.assertEqual(neighbor['geo_addresses'],[self.records[2]])
        self.assertTrue(point_in_polygon(self.point(0,70),neighbor['geo_polygon']))
        self.assertTrue(neighbor['front_revision'])
    def test_neighbor_edit_invalidates_preview_and_rollback_covers_both_cards(self):
        p=self.preview()
        self.s.mutate('geo.boundary',{'card_id':self.neighbor,'polygon':self.rectangle(-11,-500,11,500)})
        before=digest(self.s)
        with self.assertRaisesRegex(ValueError,'ændret'):self.save(p,approve_neighbors=True)
        self.assertEqual(digest(self.s),before)
        p=self.preview();original=self.s.put
        def fail(module,item):
            if module=='cards' and item['id']==self.target:raise RuntimeError('fictional failure')
            return original(module,item)
        with patch.object(self.s,'put',side_effect=fail):
            with self.assertRaises(RuntimeError):self.save(p,approve_neighbors=True)
        self.assertEqual(digest(self.s),before)
    def test_unknown_neighbor_addresses_explain_block_without_changing_anything(self):
        with self.s.transaction():self.s.put('cards',{**self.s.require('cards',self.neighbor),'address_ids':[],'geo_addresses':[]})
        before=digest(self.s);p=self.preview()
        self.assertEqual(p['outline_status'],'unavailable');self.assertEqual(p['outline_changes'],[])
        self.assertIn('mangler kendte adressekoordinater',p['outline_reason']);self.assertEqual(p['outline_reason_number'],'F002')
        self.assertEqual(digest(self.s),before)
    def test_ordinary_proposal_leaves_neighbors_unchanged(self):
        with self.s.transaction():self.s.put('cards',{**self.s.require('cards',self.neighbor),'geo_polygon':self.rectangle(-10,50,10,90)})
        neighbor=self.s.require('cards',self.neighbor);p=self.preview()
        self.assertEqual(p['outline_status'],'clear');self.assertFalse(p['outline_changes'])
        self.save(p);self.assertEqual(self.s.require('cards',self.neighbor),neighbor)
    def test_recorded_and_new_dar_entrances_both_stay_inside_neighbor(self):
        with self.s.transaction():self.s.put('geo',self.address('2',0,110))
        p=self.preview();self.assertEqual(p['outline_status'],'neighbors')
        polygon=p['outline_changes'][0]['polygon']
        self.assertTrue(point_in_polygon(self.point(0,70),polygon))
        self.assertTrue(point_in_polygon(self.point(0,110),polygon))

    def test_same_coordinate_is_not_misreported_as_neighbor_block(self):
        with self.s.transaction():self.s.put('geo',self.address('9',-40,0))
        p=self.preview();self.assertEqual(p['outline_status'],'unavailable');self.assertIn('samme koordinat',p['outline_reason'])
        self.assertFalse(p['outline_changes'])

if __name__=='__main__':unittest.main()
