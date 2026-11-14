"""Fictional street-line/DAR suggestions with normal atomic card saving."""
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from street_suggestions import ranges, includes


class StreetSuggestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        self.card=self.s.mutate('card.save',{'number':'F001','addresses':[{'road':'Fictional road','numbers':'1–5 (ulige)','count':4,'type':'Hus'}]})['id']
        self.records=[dict(id='a'+str(i),entity='address',road='Fictional road',number=n,floor=f,door='',postcode='9999',lng=10+i*.001,lat=55,count=1,type='Hus') for i,(n,f) in enumerate([('1',''),('3',''),('3','1'),('5',''),('2',''),('7','')])]
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def fetch(self,complete=True):
        self.s.mutate('geo.import',dict(records=self.records,source='DAR / Datafordeleren',label='Fictional complete road',**({'complete_road':{'road':'Fictional road','postcode':'9999'}} if complete else {})))
    def preview(self,**extra):return self.s.mutate('geo.preview',dict(mode='street_lines',card_id=self.card,postcodes=['9999'],**extra))
    def save(self,preview,**extra):return self.s.mutate('geo.assign',dict(card_id=self.card,address_ids=[a['id'] for a in preview['addresses']],street_expected=preview['street_expected'],source_expected=preview['source_expected'],postcodes=['9999'],**extra))
    def test_plan_and_preview_are_read_only_and_select_every_apartment(self):
        before=deepcopy(self.s.state());plan=self.preview(planning_only=True)
        self.assertEqual(plan['roads'],[{'road':'Fictional road','postcode':'9999'}]);self.assertEqual(self.s.state(),before)
        self.fetch();before=deepcopy(self.s.state());preview=self.preview(source_expected=plan['source_expected'])
        self.assertEqual([a['id'] for a in preview['addresses']],['a0','a1','a2','a3']);self.assertEqual(preview['visits'],4)
        self.assertGreaterEqual(len(preview['outline']),3);self.assertEqual(self.s.state(),before)
    def test_planning_reuses_complete_local_roads_and_refresh_is_opt_in(self):
        before=deepcopy(self.s.state())
        plan=self.preview(planning_only=True)
        self.assertEqual(plan['download_roads'],plan['roads'])
        self.assertEqual(plan['local_roads'],[])
        self.assertEqual(self.s.state(),before)
        self.fetch(False)  # A partial/individually imported road must not count as complete.
        self.assertEqual(self.preview(planning_only=True)['download_roads'],plan['roads'])
        self.fetch(True)
        before=deepcopy(self.s.state())
        cached=self.preview(planning_only=True)
        self.assertEqual(cached['local_roads'],plan['roads'])
        self.assertEqual(cached['download_roads'],[])
        self.assertEqual(self.preview(planning_only=True,refresh_downloaded=True)['download_roads'],plan['roads'])
        self.assertEqual(self.s.state(),before)
        self.assertEqual([a['id'] for a in self.preview()['addresses']],['a0','a1','a2','a3'])
        with self.assertRaisesRegex(ValueError,'DAR-opdatering'):
            self.preview(planning_only=True,refresh_downloaded='true')

    def test_planning_downloads_only_missing_roads_without_confusing_postcodes(self):
        self.fetch()
        c=self.s.require('cards',self.card)
        extra=[dict(road='Other fictional road',numbers='2–4',count=2,type='Hus'),
               dict(road='Fictional road',numbers='1–5',count=4,type='Hus')]
        self.s.mutate('card.save',{**c,'addresses':c['addresses']+extra})
        plan=self.s.mutate('geo.preview',{'mode':'street_lines','card_id':self.card,
                                          'postcodes':['9999','9999','8888'],'planning_only':True})
        self.assertEqual(plan['local_roads'],[{'road':'Fictional road','postcode':'9999'}])
        self.assertEqual(plan['download_roads'],[{'road':'Other fictional road','postcode':'9999'},
                                                 {'road':'Fictional road','postcode':'8888'}])
        self.assertEqual(plan['roads'],plan['local_roads']+plan['download_roads'])

    def test_save_preserves_history_and_imprecise_ib_date(self):
        self.fetch();loan=self.s.mutate('loan.issue',{'card_id':self.card,'publisher_name':'Fictional person','date':'2025-01-01','initial':True})['id']
        ib=self.s.mutate('ib.save',{'card_id':self.card,'road':'Fictional road','number':'1','date_text':'marts 2024'})['id']
        before=deepcopy(self.s.all('loans'));self.save(self.preview())
        c=self.s.require('cards',self.card);self.assertEqual(c['address_ids'],['a0','a1','a2','a3']);self.assertTrue(c['front_revision'])
        self.assertEqual(self.s.all('loans'),before);self.assertEqual(self.s.active_loan(self.card)['id'],loan)
        self.assertEqual(self.s.require('ib',ib)['date_text'],'marts 2024');self.assertEqual(self.s.require('ib',ib)['date'],'')
    def test_postcodes_and_precise_ranges_are_required(self):
        for posts in ([],[''],['999'],['9999','9999']):
            with self.assertRaises(ValueError):self.s.mutate('geo.preview',{'mode':'street_lines','card_id':self.card,'postcodes':posts,'planning_only':True})
        for value in ('1–5 og resten','5-1','1-5 (unknown)',''):
            with self.assertRaises(ValueError):ranges(value)
        self.assertEqual(ranges('1A-3B (odd); 8'),[('1A','3B','odd'),('8','8','all')])
    def test_whole_street_and_only_odd_note_keep_every_apartment(self):
        self.fetch();c=self.s.require('cards',self.card)
        for wording,expected in [('hele vejen',list('012345')),('hele vejen (kun ulige)',['0','1','2','3','5']),('1-5 (kun lige numre)',['4'])]:
            self.s.mutate('card.save',{**c,'addresses':[{**c['addresses'][0],'numbers':wording}]})
            preview=self.preview();self.assertEqual([a['id'] for a in preview['addresses']],['a'+i for i in expected])
    def test_ampersand_street_sides_do_not_fill_excluded_even_numbers(self):
        parts=ranges('23-29 & 24-26')
        self.assertEqual([n for n in range(23,31) if any(includes(str(n),part) for part in parts)],[23,24,25,26,27,29])
        self.assertEqual([n for n in range(23,28) if any(includes(str(n),part) for part in ranges('23-25 & 24-26'))],[23,24,25,26])
        self.assertEqual(ranges('2-8 (kun lige) og 1-9 (kun ulige)'),[('2','8','even'),('1','9','odd')])
    def test_partial_data_and_empty_matching_range_are_rejected(self):
        self.fetch(False)
        with self.assertRaisesRegex(ValueError,'Hent hver'):self.preview()
        self.fetch();c=self.s.require('cards',self.card);self.s.mutate('card.save',{**c,'addresses':[{**c['addresses'][0],'numbers':'90-99'}]})
        with self.assertRaisesRegex(ValueError,'ingen aktive'):self.preview()
    def test_changed_street_lines_and_changed_geo_invalidate_approval(self):
        self.fetch();p=self.preview();c=self.s.require('cards',self.card)
        self.s.mutate('card.save',{**c,'addresses':[{**c['addresses'][0],'numbers':'1-3'}]})
        before=deepcopy(self.s.state())
        with self.assertRaisesRegex(ValueError,'vejlinjer er ændret'):self.save(p)
        self.assertEqual(self.s.state(),before)
        p=self.preview();a=self.s.require('geo','a0')
        with self.s.lock,self.s.transaction():self.s.put('geo',{**a,'lat':55.001})
        before=deepcopy(self.s.state())
        with self.assertRaisesRegex(ValueError,'Adressegrundlaget'):self.save(p)
        self.assertEqual(self.s.state(),before)
    def test_existing_ownership_is_visible_and_blocks_assignment(self):
        self.fetch();self.s.mutate('geo.assign',{'number':'F002','address_ids':['a0']});p=self.preview()
        self.assertEqual(p['conflicts'][0]['card_number'],'F002');before=deepcopy(self.s.state())
        with self.assertRaises(ValueError):self.save(p)
        self.assertEqual(self.s.state(),before)
    def test_manual_year_only_date_never_invents_month_or_day(self):
        for value in ('2024','marts 2024'):
            ident=self.s.mutate('ib.save',{'card_id':self.card,'road':'Fictional road','number':value,'date':'2026-01-01','date_text':value})['id']
            item=self.s.require('ib',ident);self.assertEqual((item['date'],item['date_text']),('',value))


if __name__=='__main__':unittest.main()
