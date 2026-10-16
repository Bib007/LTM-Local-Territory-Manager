import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store, MODULES
from pdf_export import s13_pdf, allocation_rows

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        self.publisher=self.s.mutate('publisher.save',{'name':'Testperson'})['id']
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def make_card(self,number='120',**extra):
        data={'number':number,'temporary':True,'kind':'By'};data.update(extra)
        return self.s.mutate('card.save',data)['id']
    def issue(self,c,initial=False):
        return self.s.mutate('loan.issue',{'card_id':c,'publisher_id':self.publisher,'date':date.today().isoformat(),'initial':initial})['id']
    def test_separate_files_and_persistence(self):
        c=self.make_card();self.issue(c,True);before=self.s.state()
        self.assertEqual(len(list(Path(self.tmp.name).glob('*.sqlite3'))),len(MODULES))
        self.s.close();self.s=Store(self.tmp.name)
        after=self.s.state()
        for module in ('cards','publishers','loans','ib','visits','completions'):self.assertEqual(before[module],after[module])
    def test_no_folder_issuance_except_initial(self):
        c=self.make_card()
        with self.assertRaises(ValueError):self.issue(c)
        self.s.mutate('folder.set',{'ids':[c],'in_folder':True});l=self.issue(c)
        self.assertFalse(self.s.get('cards',c)['in_folder'])
        with self.assertRaises(ValueError):self.issue(c,True)
        self.s.mutate('loan.finish',{'id':l,'date':date.today().isoformat(),'complete':True,'retain':False})
        self.assertFalse(self.s.get('cards',c)['in_folder']);self.assertEqual(len(self.s.all('completions')),1)
    def test_retained_card_starts_new_cycle(self):
        c=self.make_card();l=self.issue(c,True)
        self.s.mutate('loan.finish',{'id':l,'date':date.today().isoformat(),'complete':True,'retain':True})
        self.assertTrue(self.s.active_loan(c));self.assertEqual(len(self.s.all('completions')),1)
        self.assertEqual(len(allocation_rows(self.s.state(),date.today().year+(date.today().month>=9))[0]['allocations']),2)
    def test_atomic_folder_update(self):
        a=self.make_card('1');b=self.make_card('2');self.issue(b,True)
        with self.assertRaises(ValueError):self.s.mutate('folder.set',{'ids':[a,b],'in_folder':True})
        self.assertFalse(self.s.get('cards',a)['in_folder'])
    def test_duplicate_numbers_and_resurrection(self):
        c=self.make_card('120')
        with self.assertRaises(ValueError):self.make_card('120')
        l=self.issue(c,True);self.s.mutate('ib.save',{'card_id':c,'road':'Testvej','number':'4A','date':date.today().isoformat()})
        deletion=self.s.mutate('delete',{'module':'cards','id':c})
        self.assertEqual(self.s.all('cards'),[]);self.assertEqual(self.s.all('loans'),[]);self.assertEqual(self.s.all('ib'),[])
        with self.assertRaises(ValueError):self.make_card('120')
        self.s.mutate('restore',deletion);self.assertEqual(self.s.active_loan(c)['id'],l);self.assertEqual(len(self.s.all('ib')),1)
    def test_ib_only_changes_back(self):
        c=self.make_card();self.s.mutate('ib.save',{'card_id':c,'road':'Testvej','number':'1','date':date.today().isoformat()})
        self.assertTrue(self.s.get('cards',c)['back_revision']);self.assertFalse(self.s.get('cards',c)['front_revision'])
        self.assertEqual(self.s.get('cards',c)['addresses'],[])
    def test_revision_guards_only_when_enabled(self):
        c=self.make_card();self.s.mutate('ib.save',{'card_id':c,'road':'Vej','number':'1','date':date.today().isoformat()})
        cfg=self.s.get('settings','config');cfg['require_revision']=True;self.s.mutate('settings.save',cfg)
        with self.assertRaises(ValueError):self.issue(c,True)
        self.s.mutate('revision.approve',{'card_id':c,'side':'back'});self.issue(c,True)
    def test_edit_keeps_identity_and_history(self):
        c=self.make_card();l=self.issue(c,True)
        self.s.mutate('card.save',dict(self.s.get('cards',c),temporary=False,addresses=[{'road':'Eksempelvej','numbers':'1–5 (ulige)','count':3,'type':'Hus'}]))
        self.assertEqual(self.s.active_loan(c)['id'],l);self.assertTrue(self.s.get('cards',c)['front_revision'])
    def test_expiry_removes_recovery(self):
        c=self.make_card();self.s.mutate('delete',{'module':'cards','id':c})
        with self.s.transaction():self.s.db.execute("UPDATE cards.records SET deleted_at='2000-01-01T00:00:00+00:00' WHERE id=?",(c,))
        self.s.purge_expired();self.assertIsNone(self.s.get('cards',c,deleted=True));self.assertEqual(self.s.recovery(),[])
    def test_cleanup_preserves_active_and_latest_date(self):
        c=self.make_card();old='2000-01-02'
        with self.s.transaction():
            self.s.put('loans',{'id':'old-active','card_id':c,'publisher_id':self.publisher,'assigned':old,'cycle_start':old,'returned':None})
            self.s.put('loans',{'id':'old-finished','card_id':c,'publisher_id':self.publisher,'assigned':old,'cycle_start':old,'returned':'2000-02-01'})
            self.s.create_completion(self.s.get('cards',c),'2000-02-01','old-finished')
        result=self.s.mutate('history.cleanup',{});self.assertEqual(result['count'],2)
        self.assertTrue(self.s.get('loans','old-active'));self.assertIsNone(self.s.get('loans','old-finished'))
        self.assertEqual(self.s.get('cards',c)['last_completed'],'2000-02-01')
        self.s.mutate('restore',{'batch':result['batch']});self.assertTrue(self.s.get('loans','old-finished'))
    def test_no_false_allocation_after_completed_return(self):
        c=self.make_card();l=self.issue(c,True);self.s.mutate('loan.finish',{'id':l,'date':date.today().isoformat(),'complete':True,'retain':False})
        rows=allocation_rows(self.s.state(),date.today().year+(date.today().month>=9));self.assertEqual(len(rows[0]['allocations']),1)
    def test_pdf_pages_and_text(self):
        for n in range(21):self.make_card(str(n))
        pdf=s13_pdf(self.s.state(),2027);self.assertTrue(pdf.startswith(b'%PDF-1.4'));self.assertIn(b'/Count 2',pdf);self.assertIn(b'2026/2027',pdf)
    def test_areas_can_be_removed_without_deleting_cards(self):
        a=self.s.mutate('area.save',{'name':'Eksempelby by'})['id'];c=self.make_card(area_id=a)
        self.s.mutate('area.delete',{'id':a});self.assertEqual(self.s.get('cards',c)['area_id'],'')
    def test_invalid_map_and_polygon_rejected(self):
        c=self.make_card()
        with self.assertRaises(ValueError):self.s.mutate('map.save',{'image':'data:image/svg+xml;base64,SGVsbG8='})
        with self.assertRaises(ValueError):self.s.mutate('map.outline',{'card_id':c,'points':[[float('nan'),0],[0,3],[3,0]]})
    def test_unknown_extension_fields_preserved(self):
        c=self.make_card();item=self.s.get('cards',c);item['future_field']={'version':2}
        with self.s.transaction():self.s.put('cards',item)
        self.s.mutate('card.save',dict(item,name='Nyt navn'))
        self.assertEqual(self.s.get('cards',c)['future_field'],{'version':2})

    def test_area_recovery_respects_new_assignment(self):
        a=self.s.mutate('area.save',{'name':'Eksempelby by'})['id'];b=self.s.mutate('area.save',{'name':'Eksempelby land'})['id']
        c=self.make_card('120',area_id=a);d=self.make_card('121',area_id=a)
        deletion=self.s.mutate('area.delete',{'id':a})
        with self.assertRaises(ValueError):self.s.mutate('area.save',{'name':'Eksempelby by'})
        self.s.mutate('card.save',dict(self.s.get('cards',d),area_id=b))
        self.s.mutate('restore',deletion)
        self.assertEqual(self.s.get('cards',c)['area_id'],a);self.assertEqual(self.s.get('cards',d)['area_id'],b)
    def test_new_empty_module_does_not_replace_existing_data(self):
        c=self.make_card();l=self.issue(c,True);self.s.close()
        (Path(self.tmp.name)/'ib.sqlite3').unlink()
        self.s=Store(self.tmp.name)
        self.assertEqual(self.s.active_loan(c)['id'],l);self.assertEqual(self.s.all('ib'),[])
    def test_unknown_database_format_stops_before_any_creation(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as other:
            path=Path(other)/'kort.sqlite3'
            db=sqlite3.connect(path);db.execute('PRAGMA user_version=9');db.commit();db.close();before=path.read_bytes()
            with self.assertRaises(RuntimeError):Store(other)
            self.assertEqual(path.read_bytes(),before);self.assertEqual(len(list(Path(other).glob('*.sqlite3'))),1)
    def test_s13_does_not_show_later_year_completion(self):
        state={'cards':[{'id':'c','number':'120','last_completed':'2026-10-01'}], 'publishers':[{'id':'p','name':'Testperson'}],
            'loans':[{'id':'l','card_id':'c','publisher_id':'p','assigned':'2026-07-01','cycle_start':'2026-07-01','returned':'2026-10-01'}],
            'completions':[{'id':'e','card_id':'c','loan_id':'l','assigned':'2026-07-01','date':'2026-10-01','previous_completed':'2025-05-01'}]}
        rows=allocation_rows(state,2026)
        self.assertIsNone(rows[0]['allocations'][0]['completed']);self.assertEqual(rows[0]['previous'],'2025-05-01')

if __name__=='__main__':unittest.main()
