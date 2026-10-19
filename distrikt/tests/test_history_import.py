"""Fictional completions only: local parsing, review and atomic additions."""
import base64
import io
import sys
import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from portable import digest
from history_import import csv_text,source
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
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app/vendor_py/pypdf-6.10.0.zip'))
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

if __name__=='__main__':unittest.main()
