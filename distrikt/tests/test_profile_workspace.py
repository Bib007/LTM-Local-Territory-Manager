"""Profile boundary against real local accounts and SQLite, fictional data only."""
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from profile_accounts import ProfileAccounts
from profile_workspace import ProfileWorkspace
from edit_snapshots import EditSnapshots
from store import Store


class ProfileWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.accounts=ProfileAccounts(self.tmp.name)
        self.accounts.bootstrap('Fiktiv admin','Fiktiv-password-123')
        self.admin=self.accounts.login('Fiktiv admin','Fiktiv-password-123','a')
        self.role=self.accounts.save_role(self.admin,'Fiktiv rolle',['cards.view','cards.edit'])
        self.user=self.accounts.save_user(self.admin,'Fiktiv bruger',[self.role],password='Fiktiv-password-456')
        self.token=self.accounts.login('Fiktiv bruger','Fiktiv-password-456','b')
        self.store=Store(self.tmp.name);self.snapshots=EditSnapshots()
        self.workspace=ProfileWorkspace(self.accounts,self.store,self.snapshots)
        with self.store.transaction():
            self.store.put('cards',{'id':'card','name':'Fiktivt kort','number':'X1','future_private':'DO-NOT-EXPOSE'})
            self.store.put('ib',{'id':'ib','card_id':'card','road':'Fiktiv vej','number':'12','date':'2026-01-01'})
            self.store.put('notes',{'id':'note','text':'Fiktiv privat opgave'})
            self.store.put('notes',{'id':'log','entity':'activity','text':'Fiktiv log'})
            self.store.put('publishers',{'id':'publisher','name':'Fiktiv person'})
            for module,field in [('cards','name'),('ib','road')]:
                self.store.put('settings',{'id':'conflict-'+module,'entity':'edit-conflict','module':module,
                    'record_id':'card' if module=='cards' else 'ib','field':field,'resolved':False,
                    'saved':{'present':True,'value':'Fiktiv tidligere tekst'}})

    def tearDown(self):
        self.store.close();self.tmp.cleanup()

    def permissions(self, values):self.accounts.save_role(self.admin,'Fiktiv rolle',values,self.role)

    def test_card_reader_gets_neither_private_modules_nor_new_fields(self):
        result=self.workspace.overview(self.token)
        self.assertEqual(set(result['records']),{'cards'})
        self.assertEqual(result['records']['cards'],[{'id':'card','number':'X1','name':'Fiktivt kort'}])
        self.assertNotIn('DO-NOT-EXPOSE',str(result))
        self.assertNotIn('settings',result);self.assertNotIn('recovery',result)
        self.assertNotIn('hash',str(result));self.assertNotIn(self.token,str(result))

    def test_current_roles_apply_to_existing_sessions_and_admin_is_not_implicit(self):
        self.permissions(['users.manage'])
        self.assertEqual(self.workspace.overview(self.token)['records'],{})
        self.assertEqual(self.workspace.conflicts(self.token),[])
        self.permissions(['ib.view'])
        self.assertEqual(set(self.workspace.overview(self.token)['records']),{'ib'})
        self.assertEqual([r['id'] for r in self.workspace.conflicts(self.token)],['conflict-ib'])

    def test_notes_do_not_include_activity_and_copies_do_not_mutate_storage(self):
        self.permissions(['notes.view'])
        result=self.workspace.overview(self.token)
        self.assertEqual([r['id'] for r in result['records']['notes']],['note'])
        result['records']['notes'][0]['text']='Changed copy'
        self.assertEqual(self.store.require('notes','note')['text'],'Fiktiv privat opgave')

    def test_review_requires_view_and_edit_and_records_authenticated_actor(self):
        self.assertEqual([r['id'] for r in self.workspace.conflicts(self.token)],['conflict-cards'])
        self.assertFalse(self.store.require('settings','conflict-cards')['resolved'])
        with self.assertRaises(PermissionError):self.workspace.acknowledge_conflict(self.token,'conflict-ib')
        self.permissions(['cards.view'])
        with self.assertRaises(PermissionError):self.workspace.acknowledge_conflict(self.token,'conflict-cards')
        self.permissions(['cards.edit'])
        with self.assertRaises(PermissionError):self.workspace.acknowledge_conflict(self.token,'conflict-cards')
        self.permissions(['cards.view','cards.edit'])
        self.assertTrue(self.workspace.acknowledge_conflict(self.token,'conflict-cards'))
        self.assertEqual(self.store.require('settings','conflict-cards')['reviewed_by'],self.user)
        self.assertFalse(self.workspace.acknowledge_conflict(self.token,'conflict-cards'))

    def test_unknown_conflict_fields_remain_private(self):
        with self.store.transaction():
            row=self.store.require('settings','conflict-cards');row['future_private']='DO-NOT-EXPOSE';self.store.put('settings',row)
        self.assertNotIn('DO-NOT-EXPOSE',str(self.workspace.conflicts(self.token)))
        with self.store.transaction():
            row=self.store.require('settings','conflict-cards');row['field']='future_private';self.store.put('settings',row)
        self.assertEqual(self.workspace.conflicts(self.token),[])
        with self.assertRaises(PermissionError):self.workspace.acknowledge_conflict(self.token,'conflict-cards')

    def test_edit_snapshot_comes_from_store_and_is_session_bound(self):
        draft=self.workspace.begin_edit(self.token,'cards','card')
        self.assertEqual(draft['record']['name'],'Fiktivt kort')
        self.assertNotIn('future_private',draft['record'])
        draft['record']['name']='Browser change'
        with self.assertRaises(ValueError):
            with self.snapshots.claim(draft['snapshot'],self.admin,'cards','card'):pass
        with self.snapshots.claim(draft['snapshot'],self.token,'cards','card') as base:
            self.assertEqual(base['name'],'Fiktivt kort')
        with self.assertRaises(PermissionError):self.workspace.begin_edit(self.token,'ib','ib')

    def test_disabled_session_cannot_read_review_or_start_edit(self):
        self.accounts.save_user(self.admin,'Fiktiv bruger',[self.role],self.user,disabled=True)
        for call in (lambda:self.workspace.overview(self.token),lambda:self.workspace.conflicts(self.token),
                     lambda:self.workspace.begin_edit(self.token,'cards','card'),
                     lambda:self.workspace.acknowledge_conflict(self.token,'conflict-cards')):
            with self.assertRaises(PermissionError):call()

    def test_role_change_cannot_interleave_with_authorized_operation(self):
        attempting=threading.Event()
        def revoke():
            attempting.set();self.permissions([])
        with ThreadPoolExecutor(max_workers=1) as pool:
            with self.accounts.authorized_session(self.token) as user:
                future=pool.submit(revoke)
                self.assertTrue(attempting.wait(3))
                self.assertFalse(future.done())
                self.assertIn('cards.view',user['permissions'])
                self.assertTrue(self.workspace.overview(self.token)['records']['cards'])
            future.result(timeout=5)
        self.assertEqual(self.workspace.overview(self.token)['records'],{})


if __name__=='__main__':unittest.main()
