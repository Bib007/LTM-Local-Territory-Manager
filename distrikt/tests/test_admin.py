"""Administrative changes using fictitious, isolated databases only."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store, MODULES
from pdf_export import allocation_rows

class AdminTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        self.p=self.s.mutate('publisher.save',{'name':'Fiktiv person'})['id']
        self.q=self.s.mutate('publisher.save',{'name':'Anden testperson'})['id']
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def card(self,n='120'):
        return self.s.mutate('card.save',{'number':n,'temporary':True})['id']
    def loan(self,c,start='2026-01-01'):
        return self.s.mutate('loan.issue',{'card_id':c,'publisher_id':self.p,'date':start,'initial':True})['id']
    def correct(self,l,day,p=None):
        data={'id':l,'assigned':day,'publisher_id':p or self.q}
        preview=self.s.mutate('loan.correct.preview',data)
        return self.s.mutate('loan.correct',dict(data,expected=preview['expected']))
    def test_quick_preview_and_creation(self):
        data={'numbers':'001\n120, 584;684 1-10','kind':'Land'}
        preview=self.s.mutate('card.bulk.preview',data)
        self.assertEqual(preview['count'],5);self.assertEqual(self.s.all('cards'),[])
        result=self.s.mutate('card.bulk.create',data)
        self.assertEqual(result['count'],5)
        self.assertEqual([c['number'] for c in self.s.all('cards')],preview['numbers'])
        self.assertTrue(all(c['temporary'] and c['kind']=='Land' for c in self.s.all('cards')))
    def test_duplicate_batch_is_atomic_and_reserves_deleted_numbers(self):
        c=self.card('A');self.s.mutate('delete',{'module':'cards','id':c})
        for numbers in ('1 2 1','1 a','1 B b'):
            self.assertTrue(self.s.mutate('card.bulk.preview',{'numbers':numbers})['duplicates'])
            with self.assertRaises(ValueError):self.s.mutate('card.bulk.create',{'numbers':numbers})
            self.assertEqual(self.s.all('cards'),[])

    def test_inclusive_range_padding_preview_and_creation(self):
        data={'numbering_mode':'range','range_start':'0','range_end':'300','range_digits':'4','kind':'Land'}
        before=self.s.revision;preview=self.s.mutate('card.bulk.preview',data)
        self.assertEqual(preview['count'],301);self.assertEqual(preview['numbers'][0],'0000')
        self.assertEqual(preview['numbers'][-1],'0300');self.assertEqual(preview['duplicates'],[])
        self.assertEqual(self.s.mutate('card.bulk.preview',dict(data,range_end='499'))['count'],500)
        self.assertEqual(self.s.all('cards'),[]);self.assertEqual(self.s.revision,before)
        self.assertEqual(self.s.mutate('card.bulk.create',data)['count'],301)
        self.assertEqual([c['number'] for c in self.s.all('cards')],preview['numbers'])

    def test_range_prefix_no_padding_and_single_number(self):
        for start,end,prefix,first,last,count in [(0,99,'k','k0','k99',100),(100,199,'b','b100','b199',100),(7,7,'Æ','Æ7','Æ7',1)]:
            result=self.s.mutate('card.bulk.preview',{'numbering_mode':'range','range_start':start,'range_end':end,'range_prefix':prefix})
            self.assertEqual((result['numbers'][0],result['numbers'][-1],result['count']),(first,last,count))
        data={'numbering_mode':'range','range_start':999999999,'range_end':999999999,'range_digits':29,'range_prefix':'k'}
        self.assertEqual(len(self.s.mutate('card.bulk.preview',data)['numbers'][0]),30)

    def test_range_duplicate_recheck_is_atomic_case_insensitive_and_reserves_deleted(self):
        data={'numbering_mode':'range','range_start':0,'range_end':2,'range_prefix':'k'}
        self.assertEqual(self.s.mutate('card.bulk.preview',data)['duplicates'],[])
        ident=self.card('K1');before=self.s.get('cards',ident)
        self.assertEqual(self.s.mutate('card.bulk.preview',data)['duplicates'],['k1'])
        with self.assertRaises(ValueError):self.s.mutate('card.bulk.create',data)
        self.assertEqual(self.s.all('cards'),[before])
        with self.s.transaction():self.s.put('cards',dict(before,archived=True))
        self.assertEqual(self.s.mutate('card.bulk.preview',data)['duplicates'],['k1'])
        with self.assertRaises(ValueError):self.s.mutate('card.bulk.create',data)
        self.s.mutate('delete',{'module':'cards','id':ident})
        with self.assertRaises(ValueError):self.s.mutate('card.bulk.create',data)
        self.assertEqual(self.s.all('cards'),[])

    def test_invalid_ranges_never_create_partial_records(self):
        base={'numbering_mode':'range','range_start':0,'range_end':1,'range_digits':0,'range_prefix':''}
        invalid=[{'range_start':-1},{'range_start':True},{'range_start':'0.5'},{'range_start':1000000000},
                 {'range_end':-1},{'range_start':2},{'range_end':500},{'range_digits':30},{'range_digits':-1},
                 {'range_prefix':'ab'},{'range_prefix':'7'},{'range_prefix':'<'},{'range_prefix':None},
                 {'numbering_mode':'unknown'}]
        for change in invalid:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):self.s.mutate('card.bulk.create',dict(base,**change))
                self.assertEqual(self.s.all('cards'),[])
    def test_quick_limit_and_invalid_area(self):
        for data in ({'numbers':' '.join(map(str,range(501)))},{'numbers':'1','area_id':'absent'},{'numbers':'1','kind':'Bad'}):
            with self.assertRaises(ValueError):self.s.mutate('card.bulk.create',data)
        self.assertEqual(self.s.all('cards'),[])
    def test_bulk_preserves_identity_placement_private_and_geographic_data(self):
        a=self.card();b=self.card('121');l=self.loan(a)
        self.s.mutate('ib.save',{'card_id':a,'road':'Fiktiv vej','number':'1','date':'2026-01-01'})
        with self.s.transaction():
            c=self.s.get('cards',a);c.update(address_ids=['fake-address'],geo_addresses=[{'id':'fake-address'}],geo_polygon=[[1,1],[2,1],[2,2]],future_field='keep');self.s.put('cards',c)
        before=self.s.state();data={'ids':[a,b],'kind':'Land'}
        preview=self.s.mutate('card.bulk.edit.preview',data)
        self.assertEqual(len(preview['changes']),2);self.assertEqual(before,self.s.state())
        self.s.mutate('card.bulk.edit',dict(data,expected=preview['expected']))
        after=self.s.state()
        for module in ('loans','ib','publishers','completions'):self.assertEqual(before[module],after[module])
        for c in before['cards']:
            expected=dict(c,kind='Land');self.assertEqual(expected,self.s.get('cards',c['id']))
        self.assertEqual(self.s.active_loan(a)['id'],l)
    def test_bulk_stale_preview_rejected(self):
        c=self.card();data={'ids':[c],'kind':'By'};preview=self.s.mutate('card.bulk.edit.preview',data)
        self.s.mutate('card.save',dict(self.s.get('cards',c),name='Rettet imens'))
        with self.assertRaises(ValueError):self.s.mutate('card.bulk.edit',dict(data,expected=preview['expected']))
        self.assertEqual(self.s.get('cards',c)['kind'],'Ukendt')
    def test_bulk_missing_card_no_partial_write(self):
        c=self.card()
        with self.assertRaises(ValueError):self.s.mutate('card.bulk.edit',{'ids':[c,'absent'],'kind':'By'})
        self.assertEqual(self.s.get('cards',c)['kind'],'Ukendt')
    def test_active_correction_updates_s13_and_preserves_card(self):
        c=self.card();l=self.loan(c);before=self.s.get('cards',c)
        self.correct(l,'2026-02-01')
        loan=self.s.get('loans',l)
        self.assertEqual(loan['assigned'],'2026-02-01');self.assertEqual(loan['cycle_start'],'2026-02-01');self.assertEqual(loan['publisher_id'],self.q)
        self.assertEqual(before,self.s.get('cards',c))
        row=allocation_rows(self.s.state(),2026)[0]['allocations'][0]
        self.assertEqual(row['assigned'],'2026-02-01')
    def test_correction_preserves_retained_cycles_and_completion_dates(self):
        c=self.card();l=self.loan(c)
        for day in ('2026-03-01','2026-05-01'):
            self.s.mutate('loan.finish',{'id':l,'date':day,'complete':True,'retain':True})
        before=self.s.all('completions');self.correct(l,'2026-02-01')
        events=sorted(self.s.all('completions'),key=lambda e:e['date'])
        self.assertEqual([e['date'] for e in events],[e['date'] for e in before])
        self.assertEqual(events[0]['assigned'],'2026-02-01');self.assertEqual(events[1]['assigned'],'2026-03-01')
        self.assertEqual(self.s.get('loans',l)['cycle_start'],'2026-05-01')
        self.assertEqual(self.s.get('cards',c)['last_completed'],'2026-05-01')
    def test_closed_correction_preserves_return_and_final_cycle(self):
        c=self.card();l=self.loan(c)
        self.s.mutate('loan.finish',{'id':l,'date':'2026-03-01','complete':True,'retain':False})
        self.correct(l,'2026-02-01')
        self.assertEqual(self.s.get('loans',l)['returned'],'2026-03-01');self.assertEqual(self.s.get('loans',l)['cycle_start'],'2026-02-01')
        self.assertFalse(self.s.get('cards',c)['in_folder']);self.assertIsNone(self.s.active_loan(c))
    def test_correction_keeps_cycle_after_history_removal(self):
        c=self.card();l=self.loan(c)
        self.s.mutate('loan.finish',{'id':l,'date':'2026-03-01','complete':True,'retain':True})
        with self.s.transaction():self.s.db.execute('DELETE FROM completions.records')
        self.correct(l,'2026-02-01')
        self.assertEqual(self.s.get('loans',l)['cycle_start'],'2026-03-01')
        with self.assertRaises(ValueError):self.correct(l,'2026-04-01')
    def test_invalid_chronology_and_overlap_rejected(self):
        c=self.card();l=self.loan(c)
        self.s.mutate('loan.finish',{'id':l,'date':'2026-03-01','complete':True,'retain':False})
        newer=self.loan(c,'2026-04-01');before=self.s.state()
        for ident,day in ((l,'2026-03-02'),(newer,'2026-02-01'),(newer,'2999-01-01')):
            with self.assertRaises(ValueError):self.correct(ident,day)
        self.assertEqual(before,self.s.state())
    def test_correction_stale_preview_rejected(self):
        c=self.card();l=self.loan(c);data={'id':l,'publisher_id':self.q,'assigned':'2026-02-01'}
        preview=self.s.mutate('loan.correct.preview',data)
        self.s.mutate('loan.finish',{'id':l,'date':'2026-03-01','retain':True,'complete':True})
        with self.assertRaises(ValueError):self.s.mutate('loan.correct',dict(data,expected=preview['expected']))
        self.assertEqual(self.s.get('loans',l)['assigned'],'2026-01-01')
    def test_storage_read_only_totals_and_no_private_payload(self):
        c=self.card();self.loan(c)
        self.s.mutate('geo.manual',{'road':'Private-address-sentinel','number':'1','postcode':'9999','lng':10,'lat':55})
        before=self.s.state();info=self.s.storage_info()
        self.assertEqual(info['categories']['address']['count'],1);self.assertEqual(info['postcodes'][0]['postcode'],'9999')
        self.assertEqual(len(info['files']),len(MODULES));self.assertEqual(info['total_bytes'],sum((Path(self.tmp.name)/(n+'.sqlite3')).stat().st_size for n in MODULES.values()))
        self.assertNotIn('Private-address-sentinel',json.dumps(info));self.assertNotIn('Fiktiv person',json.dumps(info))
        self.assertEqual(before,self.s.state())

if __name__=='__main__':unittest.main()
