"""Fictional completions only: local parsing, review and atomic additions."""
import base64
import io
import sys
import tempfile
import unittest
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from portable import digest
from history_import import csv_text,source,FULL_HEADERS
from pdf_export import s13_pdf

class HistoryImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        self.card=self.s.mutate('card.save',{'number':'001','addresses':[{'road':'Fiktivvej','numbers':'1','count':17,'type':'Hus'}]})['id']
        self.day=(date.today()-timedelta(days=30)).isoformat()
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def preview(self,rows):return self.s.mutate('setup.history-import.preview',{'name':'fiktion.csv','content':csv_text(rows)})
    def apply(self,p,**extra):return self.s.mutate('setup.history-import.apply',{'token':p['token'],'confirm':'IMPORTÉR HISTORIK',**extra})
    def test_preview_no_writes_or_network_then_completion_does_not_invent_visits(self):
        before=digest(self.s);rev=self.s.revision
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network')):p=self.preview([['001',self.day]])
        self.assertEqual((digest(self.s),self.s.revision),(before,rev));self.assertEqual((p['count'],p['errors']),(1,0))
        self.assertEqual(self.apply(p)['count'],1);entry=self.s.all('completions')[0]
        self.assertEqual((entry['date'],entry['loan_id'],entry['visits'],entry['visits_unknown']),(self.day,None,0,True))
        self.assertEqual(self.s.require('cards',self.card)['last_completed'],self.day);self.assertFalse(self.s.all('loans'))
        self.assertEqual(self.preview([['001',self.day]])['count'],0)
    def test_duplicates_known_dates_and_two_year_boundary_are_visible(self):
        self.s.mutate('completion.record',{'card_id':self.card,'date':self.day})
        p=self.preview([['001',self.day],['001',self.s.history_cutoff()],['001',self.s.history_cutoff()],['001','2001-01-01']])
        self.assertEqual([r['status'] for r in p['rows']],['duplicate','ready','duplicate','outside'])
        self.assertEqual(p['count'],1)
    def test_any_error_blocks_whole_batch_and_current_loans_are_preserved(self):
        publisher=self.s.mutate('publisher.save',{'name':'Fiktiv forkynder'})['id']
        self.s.mutate('loan.issue',{'card_id':self.card,'publisher_id':publisher,'date':self.day,'initial':True})
        loans=self.s.all('loans');p=self.preview([['001',self.day],['unknown',self.day]])
        before=digest(self.s)
        with self.assertRaisesRegex(ValueError,'Ret alle fejl'):self.apply(p)
        self.assertEqual(digest(self.s),before)
        p=self.preview([['001',self.day]]);self.apply(p);self.assertEqual(self.s.all('loans'),loans)
    def test_out_of_order_import_keeps_existing_records_and_nearest_previous(self):
        older=(date.today()-timedelta(days=100)).isoformat();middle=(date.today()-timedelta(days=60)).isoformat()
        self.s.mutate('completion.record',{'card_id':self.card,'date':self.day});old=self.s.all('completions')[0]
        self.apply(self.preview([['001',middle],['001',older]]));entries=sorted(self.s.all('completions'),key=lambda e:e['date'])
        self.assertEqual(entries[1]['previous_completed'],older);self.assertEqual(entries[2],old)
        self.assertEqual(self.s.require('cards',self.card)['last_completed'],self.day)
    def test_confirmation_staleness_replay_and_expiration(self):
        p=self.preview([['001',self.day]])
        with self.assertRaises(ValueError):self.apply(p,confirm='yes')
        self.s.mutate('publisher.save',{'name':'Opdigtet person'})
        with self.assertRaisesRegex(ValueError,'ændret'):self.apply(p)
        p=self.preview([['001',self.day]]);self.apply(p)
        with self.assertRaises(ValueError):self.apply(p)
        p=self.preview([['001',self.day]]);self.s._setup_previews[p['token']]['until']=0
        with self.assertRaises(ValueError):self.apply(p)
    def test_recovery_conflicts_unknown_ambiguous_numbers_and_future(self):
        self.s.mutate('completion.record',{'card_id':self.card,'date':self.day});entry=self.s.all('completions')[0]
        self.s.mutate('delete',{'module':'completions','id':entry['id']})
        p=self.preview([['001',self.day],['missing',self.day],['001','2999-01-01'],['001','31.02.26']])
        self.assertEqual(p['errors'],4);self.assertIn('Gendan',p['rows'][0]['message'])
    def test_archived_cards_and_danish_dates_keep_leading_zero(self):
        c=self.s.require('cards',self.card)
        with self.s.transaction():self.s.put('cards',{**c,'archived':True})
        d=date.fromisoformat(self.day);p=self.preview([['001',d.strftime('%d.%m.%y')]])
        self.assertTrue(p['rows'][0]['archived']);self.assertEqual(p['rows'][0]['date'],self.day);self.apply(p)
    def test_flattened_ltm_s13_and_original_fillable_form_are_read_locally(self):
        self.s.mutate('completion.record',{'card_id':self.card,'date':self.day})
        year=date.fromisoformat(self.day).year+(date.fromisoformat(self.day).month>=9)
        raw=s13_pdf(self.s.state(),year)
        data={'name':'opdigtet.pdf','content':base64.b64encode(raw).decode()}
        p=self.s.mutate('setup.history-import.preview',data)
        self.assertEqual(p['count'],0);self.assertEqual(p['rows'][0]['number'],'001');self.assertEqual(p['rows'][0]['date'],self.day)
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app/vendor_py'))
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app/vendor_py/pypdf-6.21.4.zip'))
        from pypdf import PdfReader,PdfWriter
        writer=PdfWriter(clone_from=str(Path(__file__).resolve().parents[1]/'templates/S-13-fillable.pdf'))
        writer.update_page_form_field_values(writer.pages[0],{'row_01.number':'001','row_01.assignment_1.completed':date.fromisoformat(self.day).strftime('%d.%m.%Y')})
        stream=io.BytesIO();writer.write(stream)
        p=self.s.mutate('setup.history-import.preview',{'name':'blanket.pdf','content':base64.b64encode(stream.getvalue()).decode()})
        self.assertEqual(p['rows'][0]['date'],self.day)
    def test_bad_pdf_scan_and_oversized_or_wrong_sources_fail_closed(self):
        for data in [{'name':'x.pdf','content':base64.b64encode(b'%PDF-not-valid').decode()},{'name':'x.jpg','content':'anything'},{'name':'x.csv','content':'x'*2000001},{'name':'x.csv','content':'kortnummer;dato\n001;"unclosed'}]:
            with self.assertRaises(ValueError):self.s.mutate('setup.history-import.preview',data)
        self.assertFalse(self.s.all('completions'))
    def test_rollback_after_mid_batch_failure(self):
        p=self.preview([['001',self.day],['001',(date.today()-timedelta(days=40)).isoformat()]])
        original=self.s.put;calls=[]
        def fail(module,item):
            if module=='completions':
                calls.append(item)
                if len(calls)==2:raise ValueError('Fictional failure')
            return original(module,item)
        before=digest(self.s)
        with patch.object(self.s,'put',side_effect=fail):
            with self.assertRaisesRegex(ValueError,'Fictional failure'):self.apply(p)
        self.assertEqual(digest(self.s),before)

class S13LoanImportTests(unittest.TestCase):
    setUp=HistoryImportTests.setUp
    tearDown=HistoryImportTests.tearDown
    apply=HistoryImportTests.apply
    def preview(self,rows):return self.s.mutate('setup.history-import.preview',{'name':'fiktiv.csv','content':csv_text(rows,FULL_HEADERS)})
    def ago(self,days):return (date.today()-timedelta(days=days)).isoformat()
    def card2(self):return self.s.mutate('card.save',{'number':'002'})['id']
    def test_new_and_existing_names_closed_and_active_loans_preserve_location_and_allow_return(self):
        other=self.card2();person=self.s.mutate('publisher.save',{'name':'Fiktiv B'})['id']
        with self.s.transaction():
            for ident in (self.card,other):self.s.put('cards',{**self.s.require('cards',ident),'in_folder':True})
        before=digest(self.s);rev=self.s.revision
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network')):
            p=self.preview([['001','','Fiktiv Æ A',self.ago(80),self.ago(30)],['002','','fiktiv b',self.ago(20),'']])
        self.assertEqual((digest(self.s),self.s.revision),(before,rev));self.assertEqual((p['count'],p['loan_count'],p['publisher_count'],p['errors']),(1,2,1,0))
        result=self.apply(p);self.assertEqual(result['loans'],2);self.assertEqual(len(self.s.all('publishers')),2)
        self.assertTrue(self.s.require('cards',self.card)['in_folder']);self.assertFalse(self.s.require('cards',other)['in_folder'])
        active=self.s.active_loan(other);self.assertEqual(active['publisher_id'],person)
        closed=next(l for l in self.s.all('loans') if l['card_id']==self.card);event=self.s.all('completions')[0]
        self.assertEqual((closed['returned'],event['loan_id'],event['assigned'],event['visits_unknown']),(self.ago(30),closed['id'],self.ago(80),True))
        self.s.mutate('loan.finish',{'id':active['id'],'date':date.today().isoformat(),'complete':True,'retain':False})
        self.assertFalse(self.s.active_loan(other));self.assertEqual(len(self.s.all('completions')),2)
    def test_reimport_deduplicates_loans_people_and_completions(self):
        rows=[['001','','Fiktiv A',self.ago(80),self.ago(30)]];self.apply(self.preview(rows));before=digest(self.s)
        p=self.preview(rows+rows);self.assertEqual((p['count'],p['loan_count'],p['publisher_count'],p['errors']),(0,0,0,0))
        self.assertTrue(all(r['status']=='duplicate' for r in p['rows']))
        with self.assertRaises(ValueError):self.apply(p)
        self.assertEqual(digest(self.s),before)
    def test_known_completion_is_linked_without_recount_or_changing_visit_estimate(self):
        self.s.mutate('completion.record',{'card_id':self.card,'date':self.ago(30)});old=self.s.all('completions')[0]
        p=self.preview([['001','','Fiktiv A',self.ago(80),self.ago(30)]]);self.assertEqual((p['count'],p['linked_count'],p['loan_count']),(0,1,1))
        self.apply(p);event=self.s.all('completions')[0];self.assertEqual(event['id'],old['id']);self.assertEqual(event['visits'],old['visits']);self.assertEqual(event['date'],old['date']);self.assertTrue(event['loan_id'])
    def test_existing_closed_loan_can_gain_missing_completion_without_rewriting_loan(self):
        person=self.s.mutate('publisher.save',{'name':'Fiktiv A'})['id'];ident=self.s.mutate('loan.issue',{'card_id':self.card,'publisher_id':person,'date':self.ago(80),'initial':True})['id']
        self.s.mutate('loan.finish',{'id':ident,'date':self.ago(30),'complete':False,'retain':False});old=self.s.require('loans',ident)
        p=self.preview([['001','','Fiktiv A',self.ago(80),self.ago(30)]]);self.assertEqual((p['count'],p['loan_count'],p['publisher_count']),(1,0,0));self.apply(p)
        self.assertEqual(self.s.require('loans',ident),old);self.assertEqual(self.s.all('completions')[0]['loan_id'],ident)
    def test_same_completion_in_plain_and_allocation_rows_counts_once(self):
        p=self.preview([['001',self.ago(30),'','',''],['001','','Fiktiv A',self.ago(80),self.ago(30)]])
        self.assertEqual(p['count'],1);self.assertEqual(p['rows'][0]['status'],'duplicate');self.apply(p);self.assertEqual(len(self.s.all('completions')),1)
    def test_overlaps_two_active_loans_and_shared_end_dates_block_the_whole_batch(self):
        for rows in [
            [['001','','Fiktiv A',self.ago(80),''],['001','','Fiktiv B',self.ago(20),'']],
            [['001','','Fiktiv A',self.ago(80),self.ago(30)],['001','','Fiktiv B',self.ago(60),self.ago(20)]],
            [['001','','Fiktiv A',self.ago(80),self.ago(30)],['001','','Fiktiv B',self.ago(30),self.ago(30)]]]:
            before=digest(self.s);p=self.preview(rows);self.assertGreater(p['errors'],0)
            with self.assertRaises(ValueError):self.apply(p)
            self.assertEqual(digest(self.s),before)
    def test_adjacent_closed_and_active_allocations_are_not_overlaps(self):
        p=self.preview([['001','','Fiktiv A',self.ago(80),self.ago(30)],['001','','Fiktiv A',self.ago(30),'']]);self.assertEqual(p['errors'],0);self.apply(p)
        self.assertEqual(len(self.s.all('publishers')),1);self.assertEqual(len(self.s.all('loans')),2);self.assertIsNotNone(self.s.active_loan(self.card))
    def test_active_loans_survive_two_year_cutoff_but_old_closed_loans_do_not_create_names(self):
        self.card2();p=self.preview([['001','','Fiktiv gammel','2001-01-01','2001-02-01'],['002','','Fiktiv aktiv','2001-01-01','']])
        self.assertEqual((p['count'],p['loan_count'],p['publisher_count'],p['errors']),(0,1,1,0));self.assertEqual(p['rows'][0]['status'],'outside');self.apply(p)
        self.assertEqual([p['name'] for p in self.s.all('publishers')],['Fiktiv aktiv'])
    def test_ambiguous_or_recoverable_names_and_invalid_dates_require_correction(self):
        person=self.s.mutate('publisher.save',{'name':'Fiktiv dobbelt'})['id']
        with self.s.transaction():self.s.put('publishers',{'id':'fictional-duplicate','name':'Fiktiv dobbelt'})
        removed=self.s.mutate('publisher.save',{'name':'Fiktiv slettet'})['id']
        with self.s.transaction():self.s.mark_deleted('publishers',removed,'fictional-recovery',datetime.now(timezone.utc).isoformat())
        rows=[['001','','Fiktiv dobbelt',self.ago(80),''],['001','','Fiktiv slettet',self.ago(80),''],['001','','',self.ago(80),''],['001','','Fiktiv A','',self.ago(20)],['001','','Fiktiv A',self.ago(20),self.ago(80)],['001','','Fiktiv A','2999-01-01',''],['001',self.day,'Fiktiv A',self.ago(80),self.ago(20)]]
        p=self.preview(rows);self.assertEqual(p['errors'],len(rows));self.assertFalse(self.s.all('loans'))
    def test_archived_active_loan_and_recoverable_loan_are_blocked(self):
        with self.s.transaction():self.s.put('cards',{**self.s.require('cards',self.card),'archived':True})
        self.assertEqual(self.preview([['001','','Fiktiv A',self.ago(80),'']])['errors'],1)
        with self.s.transaction():self.s.put('cards',{**self.s.require('cards',self.card),'archived':False})
        self.apply(self.preview([['001','','Fiktiv A',self.ago(80),self.ago(30)]]));loan=self.s.all('loans')[0];self.s.mutate('delete',{'module':'loans','id':loan['id']})
        self.assertEqual(self.preview([['001','','Fiktiv A',self.ago(80),self.ago(30)]])['errors'],1)
    def test_mid_batch_failure_rolls_back_new_names_loans_events_and_card_location(self):
        other=self.card2();p=self.preview([['001','','Fiktiv A',self.ago(80),self.ago(30)],['002','','Fiktiv B',self.ago(20),'']]);before=digest(self.s);original=self.s.put;calls=[]
        def fail(module,item):
            if module=='loans':
                calls.append(item)
                if len(calls)==2:raise ValueError('Fictional allocation failure')
            return original(module,item)
        with patch.object(self.s,'put',side_effect=fail):
            with self.assertRaises(ValueError):self.apply(p)
        self.assertEqual(digest(self.s),before)
    def test_flattened_s13_preserves_names_dates_and_detects_existing_retained_cycles(self):
        other=self.card2();person=self.s.mutate('publisher.save',{'name':'Fiktiv Æ <A>'})['id']
        loan=self.s.mutate('loan.issue',{'card_id':self.card,'publisher_id':person,'date':self.ago(80),'initial':True})['id']
        self.s.mutate('loan.finish',{'id':loan,'date':self.ago(20),'complete':True,'retain':True})
        year=date.today().year+(date.today().month>=9);raw=s13_pdf(self.s.state(),year);payload={'name':'fiktion.pdf','content':base64.b64encode(raw).decode()}
        duplicate=self.s.mutate('setup.history-import.preview',payload);self.assertEqual((duplicate['count'],duplicate['loan_count'],duplicate['publisher_count'],duplicate['errors']),(0,0,0,0))
        with tempfile.TemporaryDirectory() as root:
            target=Store(root)
            try:
                target.mutate('card.save',{'number':'001'});target.mutate('card.save',{'number':'002'})
                p=target.mutate('setup.history-import.preview',payload);self.assertEqual((p['count'],p['loan_count'],p['publisher_count'],p['errors']),(1,2,1,0))
                target.mutate('setup.history-import.apply',{'token':p['token'],'confirm':'IMPORTÉR HISTORIK'})
                self.assertEqual(target.all('publishers')[0]['name'],'Fiktiv Æ <A>');self.assertEqual(len(target.all('loans')),2)
            finally:target.close()

    def test_original_fillable_s13_reads_unicode_names_and_unreturned_allocations(self):
        self.card2();folder=Path(__file__).resolve().parents[1]
        sys.path.insert(0,str(folder/'app/vendor_py'));sys.path.insert(0,str(folder/'app/vendor_py/pypdf-6.21.4.zip'))
        from pypdf import PdfWriter
        writer=PdfWriter(clone_from=str(folder/'templates/S-13-fillable.pdf'))
        writer.update_page_form_field_values(writer.pages[0],{'row_01.number':'001','row_01.assignment_1.person':'Fiktiv Ω A','row_01.assignment_1.assigned':self.ago(80),'row_01.assignment_1.completed':self.ago(30),'row_02.number':'002','row_02.assignment_1.person':'Fiktiv B','row_02.assignment_1.assigned':self.ago(20)})
        stream=io.BytesIO();writer.write(stream)
        p=self.s.mutate('setup.history-import.preview',{'name':'fiktiv-blanket.pdf','content':base64.b64encode(stream.getvalue()).decode()})
        self.assertEqual((p['count'],p['loan_count'],p['publisher_count'],p['errors']),(1,2,2,0));self.apply(p)
        self.assertIn('Fiktiv Ω A',[p['name'] for p in self.s.all('publishers')]);self.assertEqual(sum(not l.get('returned') for l in self.s.all('loans')),1)

if __name__=='__main__':unittest.main()
