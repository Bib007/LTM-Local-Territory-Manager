"""Fictional identities in isolated databases; merge preserves references and undo."""
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from profile_policy import mutation
from history_import import csv_text,FULL_HEADERS
from portable import digest

class PublisherMergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=Store(self.tmp.name);self.addCleanup(self.s.close)
        self.a=self.s.mutate('publisher.save',{'name':'Fiktiv Person','group':'Gruppe A','pioneer':True})['id']
        self.b=self.s.mutate('publisher.save',{'name':'fiktiv p'})['id']
        self.card=self.s.mutate('card.save',{'number':'F-001','temporary':True})['id']
        self.day=(date.today()-timedelta(days=20)).isoformat()
        self.loan=self.s.mutate('loan.issue',{'card_id':self.card,'publisher_id':self.b,'date':self.day,'initial':True})['id']
        self.request={'target_id':self.a,'source_id':self.b,'name':'Fiktiv Person Samlet'}
    def preview(self):return self.s.mutate('publisher.merge.preview',self.request)
    def merge(self):return self.s.mutate('publisher.merge',{**self.request,'expected':self.preview()['expected']})
    def test_lifecycle_reimport_aliases_and_undo(self):
        before=digest(self.s);rev=self.s.revision;self.preview()
        self.assertEqual((digest(self.s),self.s.revision),(before,rev))
        self.merge();p=self.s.require('publishers',self.a)
        self.assertEqual((p['name'],p['group'],p['pioneer']),('Fiktiv Person Samlet','Gruppe A',True))
        self.assertEqual(set(p['aliases']),{'Fiktiv Person','fiktiv p'})
        self.assertIsNone(self.s.get('publishers',self.b,deleted=True))
        self.assertEqual(self.s.require('loans',self.loan)['publisher_id'],self.a)
        self.s.mutate('workflow.undo',{})
        self.assertEqual(self.s.require('loans',self.loan)['publisher_id'],self.b)
        self.assertEqual(self.s.require('publishers',self.a)['name'],'Fiktiv Person')
        self.assertIsNotNone(self.s.get('publishers',self.b))
        self.merge()
        rows=[['F-001','','fiktiv p',self.day,'']]
        plan=self.s.mutate('setup.history-import.preview',{'name':'fiction.csv','content':csv_text(rows,FULL_HEADERS)})
        self.assertEqual((plan['publisher_count'],plan['loan_count'],plan['errors']),(0,0,0))
        with self.assertRaisesRegex(ValueError,'allerede'):
            self.s.mutate('publisher.save',{'name':'fiktiv p'})
    def test_deleted_loans_keep_recovery_metadata_and_completions(self):
        self.s.mutate('loan.finish',{'id':self.loan,'date':date.today().isoformat(),'complete':True})
        events=self.s.all('completions')
        batch=self.s.mutate('delete',{'module':'loans','id':self.loan,'history_revision':self.s.revision})
        old=self.s.all('loans',deleted=True)[0]
        self.merge();updated=self.s.all('loans',deleted=True)[0]
        self.assertEqual(updated,{**old,'publisher_id':self.a})
        self.assertEqual(self.s.all('completions'),events)
        self.s.mutate('restore',batch)
        self.assertEqual(self.s.require('loans',self.loan)['publisher_id'],self.a)
    def test_stale_preview_and_failure_are_atomic(self):
        preview=self.preview()
        self.s.mutate('publisher.save',{'id':self.b,'name':'Ny fiktiv person'})
        before=digest(self.s)
        with self.assertRaisesRegex(ValueError,'ændret'):
            self.s.mutate('publisher.merge',{**self.request,'expected':preview['expected']})
        self.assertEqual(digest(self.s),before)
        preview=self.preview();original=self.s.put
        def fail(module,record):
            if module=='loans':raise RuntimeError('fictional failure')
            return original(module,record)
        with patch.object(self.s,'put',side_effect=fail):
            with self.assertRaises(RuntimeError):self.s.mutate('publisher.merge',{**self.request,'expected':preview['expected']})
        self.assertEqual(digest(self.s),before)
    def test_roles_and_third_identity_collision(self):
        rights={'loans.view','loans.manage','publishers.view','publishers.manage'}
        for action in ('publisher.merge.preview','publisher.merge'):
            mutation({'id':'fictional','permissions':rights},action,self.request,self.s)
            for missing in rights:
                with self.assertRaises(PermissionError):mutation({'id':'fictional','permissions':rights-{missing}},action,self.request,self.s)
        self.s.mutate('publisher.save',{'name':self.request['name']})
        with self.assertRaisesRegex(ValueError,'allerede'):self.preview()
    def test_unknown_import_creates_default_group(self):
        content=csv_text([['F-001','','Ny fiktiv import',self.day,'']],FULL_HEADERS)
        # Use a free card rather than overwrite the existing active allocation.
        self.s.mutate('loan.finish',{'id':self.loan,'date':self.day})
        other=self.s.mutate('card.save',{'number':'F-002','temporary':True})['id']
        content=content.replace('F-001','F-002')
        plan=self.s.mutate('setup.history-import.preview',{'name':'fiction.csv','content':content})
        self.assertEqual(plan['errors'],0)
        self.s.mutate('setup.history-import.apply',{'token':plan['token'],'confirm':'IMPORTÉR HISTORIK'})
        p=next(p for p in self.s.all('publishers') if p['name']=='Ny fiktiv import')
        self.assertEqual(p['group'],'Ikke i en tjenestegruppe')
        self.assertEqual(self.s.active_loan(other)['publisher_id'],p['id'])

if __name__=='__main__':unittest.main()
