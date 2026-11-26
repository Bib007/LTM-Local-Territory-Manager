"""Desk-only fictional registers, literal intervals and unknown visit counts."""
from copy import deepcopy
import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store


class ManualCardImportTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
    def tearDown(self):self.s.close();self.temp.cleanup()
    def preview(self,text):return self.s.mutate('setup.card-import.preview',{'name':'fiktiv.csv','content':text})
    def apply(self,plan):return self.s.mutate('setup.card-import.apply',{'token':plan['token'],'confirm':'IMPORTÉR KORT'})

    def test_register_only_and_interval_preserve_identity_without_geo_or_guessed_visits(self):
        before=self.s.revision
        plan=self.preview('kortnummer;vejnavn;husnummer\nF001;;\nF002;Fiktiv vej;1–19\n')
        self.assertEqual(plan['errors'],[]);self.assertEqual((plan['addresses'],plan['manual_lines'],plan['register_cards']),(0,1,1))
        self.assertEqual(plan['unknown_cards'],2);self.assertEqual(plan['visits'],0)
        self.assertEqual(self.s.revision,before);self.assertEqual(self.s.all('cards'),[])
        self.apply(plan);cards={c['number']:c for c in self.s.all('cards')}
        self.assertTrue(cards['F001']['temporary']);self.assertFalse(cards['F001']['front_revision'])
        interval=cards['F002'];self.assertEqual(interval['addresses'],[{'road':'Fiktiv vej','numbers':'1–19','count':0,'type':'Hus','count_unknown':True}])
        self.assertEqual(interval['imported_addresses'],[]);self.assertEqual(self.s.all('geo'),[])
        self.s.mutate('completion.record',{'card_id':interval['id'],'date':'2026-10-01'})
        event=self.s.all('completions')[0];self.assertTrue(event['visits_unknown']);self.assertEqual(event['visits'],0)

    def test_explicit_visit_count_is_preserved_without_expanding_interval(self):
        plan=self.preview('kortnummer;vejnavn;husnummer;besøg\nF001;Fiktiv vej;1-19;8')
        self.assertEqual(plan['errors'],[]);self.assertEqual(plan['visits'],8);self.assertEqual(plan['unknown_cards'],0)
        self.apply(plan);card=self.s.all('cards')[0]
        self.assertEqual(len(card['addresses']),1);self.assertEqual(card['addresses'][0]['count'],8)
        self.s.mutate('completion.record',{'card_id':card['id'],'date':'2026-10-01'})
        self.assertEqual(self.s.all('completions')[0]['visits'],8);self.assertFalse(self.s.all('completions')[0].get('visits_unknown'))

    def test_later_geo_selection_preserves_card_and_unknown_history_and_manual_ib(self):
        plan=self.preview('kortnummer;vejnavn;husnummer\nF001;Fiktiv vej;1-19');self.apply(plan)
        card=self.s.all('cards')[0];ident=card['id']
        self.s.mutate('completion.record',{'card_id':ident,'date':'2026-10-01'})
        old_events=deepcopy(self.s.all('completions'))
        self.s.mutate('ib.save',{'card_id':ident,'road':'Fiktiv vej','number':'7','date':'2026-10-01'})
        old_ib=deepcopy(self.s.all('ib'))
        self.s.mutate('geo.import',{'records':[{'id':'fake-7','entity':'address','road':'Fiktiv vej','number':'7','postcode':'9999','lng':10,'lat':55,'count':1}], 'source':'Fiktiv prøve'})
        self.s.mutate('geo.assign',{'card_id':ident,'address_ids':['fake-7']})
        saved=self.s.require('cards',ident);self.assertEqual(saved['number'],'F001');self.assertEqual(saved['address_ids'],['fake-7'])
        self.assertFalse(any(a.get('count_unknown') for a in saved['addresses']))
        self.assertEqual(self.s.all('completions'),old_events);self.assertEqual(self.s.all('ib'),old_ib)
        self.assertEqual(len(self.s.all('cards')),1)

    def test_xlsx_mixed_precise_and_manual_rows_keep_unknown_total(self):
        from test_card_import import xlsx_file
        plan=self.s.mutate('setup.card-import.preview',xlsx_file([
            ['F107','','','By','Fiktiv vej','1','','','9999','Hus',''],
            ['F107','','','','Fiktiv vej','3-19','','','','Hus',''],
        ]))
        self.assertEqual(plan['errors'],[])
        self.assertEqual((plan['addresses'],plan['manual_lines'],plan['visits'],plan['unknown_cards']),(1,1,1,1))
        self.apply(plan);saved=self.s.all('cards')[0]
        self.assertEqual(len(saved['imported_addresses']),1)
        self.assertEqual(len(saved['addresses']),2)
        self.s.mutate('completion.record',{'card_id':saved['id'],'date':'2026-10-01'})
        self.assertTrue(self.s.all('completions')[0]['visits_unknown'])
        self.assertEqual(self.s.all('completions')[0]['visits'],0)

    def test_editing_imported_count_keeps_its_exact_address_metadata_in_sync(self):
        self.apply(self.preview('kortnummer;vejnavn;husnummer;postnummer\nF107;Fiktiv vej;7;9999'))
        saved=self.s.all('cards')[0]
        self.s.mutate('card.save',{**saved,'addresses':[dict(saved['addresses'][0],count=0,count_unknown=True)]})
        unknown=self.s.all('cards')[0]
        self.assertTrue(unknown['imported_addresses'][0]['count_unknown'])
        self.assertEqual(unknown['imported_addresses'][0]['count'],0)
        self.s.mutate('card.save',{**unknown,'addresses':[dict(saved['addresses'][0],count=3)]})
        known=self.s.all('cards')[0]
        self.assertNotIn('count_unknown',known['imported_addresses'][0])
        self.assertEqual(known['imported_addresses'][0]['count'],3)
        self.assertEqual(known['imported_addresses'][0]['postcode'],'9999')

    def test_count_can_be_completed_normally_and_bad_partial_rows_block_all(self):
        self.apply(self.preview('kortnummer;vejnavn;husnummer\nF001;Fiktiv vej;1-19'))
        card=self.s.all('cards')[0];rows=[dict(a,count=8) for a in card['addresses']]
        for row in rows:row.pop('count_unknown',None)
        self.s.mutate('card.save',{**card,'addresses':rows});self.assertFalse(self.s.all('cards')[0]['addresses'][0].get('count_unknown'))
        plan=self.preview('kortnummer;vejnavn;husnummer\nF002;;\nF003;Fiktiv vej;')
        self.assertEqual(len(plan['errors']),1)
        with self.assertRaises(ValueError):self.apply(plan)
        self.assertEqual(len(self.s.all('cards')),1)

if __name__=='__main__':unittest.main()
