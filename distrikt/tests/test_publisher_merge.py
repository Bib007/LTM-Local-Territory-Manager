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
from profile_edits import ReviewedMutation,capture

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

    def test_group_import_matches_whitespace_aliases_once_and_keeps_aliases(self):
        self.s.mutate('publisher.save',{'id':self.b,'name':'Fiktiv  Person'})
        self.request['name']='Fiktiv Person'
        self.merge()
        aliases=self.s.require('publishers',self.a)['aliases']
        for name in ('Fiktiv Person','Fiktiv  Person'):
            plan=self.s.mutate('setup.publisher-import.preview',{'name':'fiction.csv',
                'content':'navn;tjenestegruppe\n'+name+';Fiktiv ny gruppe'})
            self.assertEqual((plan['invalid'],plan['new'],plan['errors']),(0,0,[]))
            self.s.mutate('setup.publisher-import.apply',{'token':plan['token'],'confirm':'IMPORTÉR GRUPPER'})
            person=self.s.require('publishers',self.a)
            self.assertEqual((person['name'],person['aliases']),('Fiktiv Person',aliases))
        plan=self.s.mutate('setup.publisher-import.preview',{'name':'fiction.csv',
            'content':'navn\nFiktiv Person\nFiktiv  Person'})
        self.assertEqual(plan['invalid'],1)

    def test_chained_aliases_reused_by_both_imports_without_renaming(self):
        self.merge()
        other=self.s.mutate('publisher.save',{'name':'Fiktiv tredje'})['id']
        request={'target_id':self.a,'source_id':other,'name':'Fiktiv endelig'}
        preview=self.s.mutate('publisher.merge.preview',request)
        self.s.mutate('publisher.merge',{**request,'expected':preview['expected']})
        aliases=self.s.require('publishers',self.a)['aliases']
        self.assertEqual(set(aliases),{'Fiktiv Person','fiktiv p','Fiktiv Person Samlet','Fiktiv tredje'})
        for index,name in enumerate(aliases):
            number='ALIAS-'+str(index)
            card=self.s.mutate('card.save',{'number':number,'temporary':True})['id']
            plan=self.s.mutate('setup.history-import.preview',{'name':'fiction.csv',
                'content':csv_text([[number,'',name,self.day,'']],FULL_HEADERS)})
            self.assertEqual((plan['publisher_count'],plan['loan_count'],plan['errors']),(0,1,0))
            self.s.mutate('setup.history-import.apply',{'token':plan['token'],'confirm':'IMPORTÉR HISTORIK'})
            self.assertEqual(self.s.active_loan(card)['publisher_id'],self.a)
        plan=self.s.mutate('setup.publisher-import.preview',{'name':'fiction.csv',
            'content':'navn;tjenestegruppe\nfiktiv p;Fiktiv ny gruppe'})
        self.assertEqual((plan['new'],plan['update'],plan['invalid']),(0,1,0))
        self.s.mutate('setup.publisher-import.apply',{'token':plan['token'],'confirm':'IMPORTÉR GRUPPER'})
        person=self.s.require('publishers',self.a)
        self.assertEqual((person['name'],person['aliases']),('Fiktiv endelig',aliases))
        self.assertEqual(len(self.s.all('publishers')),1)

    def test_all_loan_states_and_completions_survive_merge_and_undo(self):
        for index in range(2):
            card=self.s.mutate('card.save',{'number':'CLOSED-'+str(index),'temporary':True})['id']
            loan=self.s.mutate('loan.issue',{'card_id':card,'publisher_id':self.b,'date':self.day,'initial':True})['id']
            self.s.mutate('loan.finish',{'id':loan,'date':date.today().isoformat(),'complete':True})
            if index:self.s.mutate('delete',{'module':'loans','id':loan,'history_revision':self.s.revision})
        before={m:[self.s.all(m),self.s.all(m,deleted=True)] for m in ('publishers','loans','completions')}
        self.merge()
        self.assertTrue(all(l['publisher_id']==self.a for l in self.s.all('loans')+self.s.all('loans',deleted=True)))
        self.assertEqual([self.s.all('completions'),self.s.all('completions',deleted=True)],before['completions'])
        self.s.mutate('workflow.undo',{})
        for module,rows in before.items():
            for deleted,expected in enumerate(rows):
                self.assertEqual(sorted(self.s.all(module,deleted=bool(deleted)),key=lambda r:r['id']),sorted(expected,key=lambda r:r['id']))

    def test_loan_change_and_recovery_invalidate_preview(self):
        preview=self.preview()
        batch=self.s.mutate('delete',{'module':'loans','id':self.loan,'history_revision':self.s.revision,'location':'box'})
        before=digest(self.s)
        with self.assertRaisesRegex(ValueError,'ændret'):
            self.s.mutate('publisher.merge',{**self.request,'expected':preview['expected']})
        self.assertEqual(digest(self.s),before)
        preview=self.preview();self.s.mutate('restore',batch);before=digest(self.s)
        with self.assertRaisesRegex(ValueError,'ændret'):
            self.s.mutate('publisher.merge',{**self.request,'expected':preview['expected']})
        self.assertEqual(digest(self.s),before)

    def test_profile_precommit_failure_restores_source_and_every_reference(self):
        preview=self.preview();before=digest(self.s);revision=self.s.revision
        undo=self.s._undo
        def fail(observed):raise OSError('Fiktiv profilfejl')
        review=ReviewedMutation(capture(self.s),'fictional',fail)
        with self.assertRaisesRegex(OSError,'Fiktiv profilfejl'):
            self.s.mutate('publisher.merge',{**self.request,'expected':preview['expected']},review=review)
        self.assertEqual((digest(self.s),self.s.revision),(before,revision))
        self.assertIs(self.s._undo,undo)

    def test_preview_uses_current_names_and_retains_only_first_group_attributes(self):
        self.s.mutate('publisher.save',{'id':self.a,'name':'Fiktiv aktuel','group':'Fiktiv gruppe','group_role':'assistant','pioneer':False})
        self.s.mutate('publisher.save',{'id':self.b,'name':'Fiktiv anden','group':'Anden gruppe','group_role':'overseer','pioneer':True})
        preview=self.preview()
        self.assertEqual((preview['target_name'],preview['source_name']),('Fiktiv aktuel','Fiktiv anden'))
        self.merge();person=self.s.require('publishers',self.a)
        self.assertEqual((person['group'],person['group_role'],person['pioneer']),('Fiktiv gruppe','assistant',False))

if __name__=='__main__':unittest.main()
