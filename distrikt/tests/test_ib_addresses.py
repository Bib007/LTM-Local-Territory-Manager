"""Exact local IB selection; fictional cards/units in temporary databases."""
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store

class IBAddressTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        records=[dict(id='unit-a',entity='address',road='Eksempelvej',number='42B',floor='1',door='tv',postcode='9999',lng=10,lat=55,count=1),dict(id='unit-b',entity='address',road='Eksempelvej',number='42B',floor='1',door='th',postcode='9999',lng=10,lat=55,count=1),dict(id='neighbor',entity='address',road='Anden vej',number='9',postcode='9999',lng=10.01,lat=55.01,count=1)]
        self.s.mutate('geo.import',{'records':records,'source':'Fiktive testdata'})
        self.c=self.s.mutate('geo.assign',{'address_ids':['unit-a','unit-b'],'number':'120'})['id']
        self.s.mutate('revision.approve',{'card_id':self.c,'side':'front'})
        self.s.mutate('revision.approve',{'card_id':self.c,'side':'back'})
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def save(self,**extra):
        payload={'card_id':self.c,'address_id':'unit-a','road':'Wrong input ignored','number':'999','date':date.today().isoformat()};payload.update(extra)
        return self.s.mutate('ib.save',payload)
    def test_exact_apartment_canonicalized_without_changing_counts_or_front(self):
        before=self.s.get('cards',self.c);result=self.save();ib=self.s.get('ib',result['id']);after=self.s.get('cards',self.c)
        self.assertEqual(ib['address_id'],'unit-a');self.assertEqual(ib['road'],'Eksempelvej');self.assertEqual(ib['number'],'42B, 1 tv')
        self.assertEqual(before['addresses'],after['addresses']);self.assertEqual(before['geo_addresses'],after['geo_addresses'])
        self.assertFalse(after['front_revision']);self.assertTrue(after['back_revision'])
        self.s.close();self.s=Store(self.tmp.name);self.assertEqual(self.s.get('ib',result['id']),ib)
        self.assertEqual(len(list(Path(self.tmp.name).glob('*.sqlite3'))),11)
    def test_foreign_address_and_duplicate_are_rejected_atomically(self):
        before=self.s.get('cards',self.c)
        with self.assertRaisesRegex(ValueError,'ikke på'):self.save(address_id='neighbor')
        self.assertEqual(self.s.all('ib'),[]);self.assertEqual(self.s.get('cards',self.c),before)
        result=self.save()
        with self.assertRaisesRegex(ValueError,'allerede'):self.save()
        self.save(id=result['id']);self.assertEqual(len(self.s.all('ib')),1)
        self.save(address_id='unit-b');self.assertEqual(len(self.s.all('ib')),2)
    def test_manual_edit_clears_old_binding_and_temporary_cards_remain_supported(self):
        result=self.save()
        self.save(id=result['id'],address_id='',road='Eksempelvej',number='42B')
        self.assertNotIn('address_id',self.s.get('ib',result['id']))
        temporary=self.s.mutate('card.save',{'number':'584','temporary':True})['id']
        ib=self.s.mutate('ib.save',{'card_id':temporary,'road':'Fysisk kortvej','number':'1A','date':date.today().isoformat()})['id']
        self.assertEqual(self.s.get('ib',ib)['number'],'1A')

if __name__=='__main__':unittest.main()
