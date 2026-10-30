"""Fictional snapshots: do not lose independent edits or hide real collisions."""
import copy
import concurrent.futures
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from concurrent_edits import reconcile,commit_reviewed
from edit_snapshots import EditSnapshots
from portable import Restores,snapshot
from store import Store


class ConcurrentEditsTests(unittest.TestCase):
    def test_different_fields_and_separate_records_do_not_conflict(self):
        base={'id':'fictional','name':'A','area':'1','system':'kept'}
        current={'id':'fictional','name':'B','area':'1','system':'new server value'}
        draft={'id':'fictional','name':'A','area':'2','system':'untrusted'}
        before=copy.deepcopy((base,current,draft));result=reconcile(base,current,draft,('name','area'))
        self.assertEqual(result['record'],{'id':'fictional','name':'B','area':'2','system':'new server value'})
        self.assertEqual(result['conflicts'],[]);self.assertEqual((base,current,draft),before)

    def test_same_change_is_not_a_conflict_but_different_changes_preserve_every_version(self):
        base={'name':'Original'};saved={'name':'Første'}
        self.assertEqual(reconcile(base,saved,{'name':'Første'},('name',))['conflicts'],[])
        result=reconcile(base,saved,{'name':'Anden'},('name',))
        self.assertEqual(result['record']['name'],'Anden')
        self.assertEqual(result['conflicts'],[{'field':'name','base':{'present':True,'value':'Original'},'saved':{'present':True,'value':'Første'},'incoming':{'present':True,'value':'Anden'}}])

    def test_missing_null_false_and_number_are_distinct(self):
        r=reconcile({'x':None},{'x':False},{'x':0},('x',))
        self.assertEqual(len(r['conflicts']),1);self.assertEqual(r['record']['x'],0)
        r=reconcile({'x':None},{},{'x':'Ny'},('x',))
        self.assertFalse(r['conflicts'][0]['saved']['present'])
        r=reconcile({'x':'Gammel'},{'x':'Ændret'},{},('x',))
        self.assertNotIn('x',r['record']);self.assertFalse(r['conflicts'][0]['incoming']['present'])

    def test_nested_collections_are_atomic_and_results_do_not_share_references(self):
        base={'roads':['A']};current={'roads':['A','B']};incoming={'roads':['A','C']}
        r=reconcile(base,current,incoming,('roads',));self.assertEqual(len(r['conflicts']),1)
        r['record']['roads'].append('D');self.assertEqual(incoming['roads'],['A','C'])
        self.assertEqual(r['conflicts'][0]['saved']['value'],['A','B'])

    def test_only_explicit_fields_can_change_and_bad_inputs_fail(self):
        r=reconcile({'id':'1','name':'A'},{'id':'1','name':'A'},{'id':'2','name':'B'},('name',))
        self.assertEqual(r['record']['id'],'1');self.assertEqual(r['record']['name'],'B')
        with self.assertRaises(ValueError):reconcile({}, {}, {}, ('_revision',))
        with self.assertRaises(ValueError):reconcile({}, {}, {'x':float('nan')}, ('x',))

    def test_two_threads_save_different_fields_without_losing_either(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            try:
                base={'id':'fictional-note','text':'Fiktiv','resolved':False,'task':True}
                with store.transaction():store.put('notes',base)
                barrier=threading.Barrier(2)
                def save(actor,changes):
                    proposed={**base,**changes};barrier.wait(timeout=5)
                    return commit_reviewed(store,'notes',base['id'],base,proposed,('text','resolved'),actor,lambda db,row:db.put('notes',row))
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    futures=[pool.submit(save,'fictional-a',{'text':'Fiktiv ændring'}),pool.submit(save,'fictional-b',{'resolved':True})]
                    self.assertEqual([f.result(timeout=10)['conflicts'] for f in futures],[0,0])
                saved=store.require('notes',base['id']);self.assertEqual(saved['text'],'Fiktiv ændring');self.assertTrue(saved['resolved'])
                self.assertEqual([x for x in store.all('settings') if x.get('entity')=='edit-conflict'],[])
            finally:store.close()

    def test_collision_is_recorded_atomically_and_never_exposed_as_an_area(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            try:
                base={'id':'fictional-note','text':'Start','task':True}
                with store.transaction():store.put('notes',base)
                for actor,text in [('fictional-a','Første'),('fictional-b','Anden')]:
                    result=commit_reviewed(store,'notes',base['id'],base,{**base,'text':text},('text',),actor,lambda db,row:db.put('notes',row))
                self.assertEqual(result['conflicts'],1);self.assertEqual(store.require('notes',base['id'])['text'],'Anden')
                conflict=next(x for x in store.all('settings') if x.get('entity')=='edit-conflict')
                self.assertEqual((conflict['base']['value'],conflict['saved']['value'],conflict['incoming']['value']),('Start','Første','Anden'))
                self.assertEqual(conflict['incoming_actor_id'],'fictional-b');self.assertFalse(conflict['resolved'])
                self.assertFalse(any(x['id']==conflict['id'] for x in store.state()['areas']))
            finally:store.close()

    def test_failed_notice_rolls_back_the_record_and_all_notices(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            try:
                base={'id':'fictional-note','text':'Start','task':True}
                with store.transaction():store.put('notes',{**base,'text':'Første'})
                real_put=store.put
                def fail_notice(module,row):
                    if row.get('entity')=='edit-conflict':raise RuntimeError('Synthetic storage failure')
                    return real_put(module,row)
                with patch.object(store,'put',side_effect=fail_notice),self.assertRaises(RuntimeError):
                    commit_reviewed(store,'notes',base['id'],base,{**base,'text':'Anden'},('text',),'fictional-b',lambda db,row:db.put('notes',row))
                self.assertEqual(store.require('notes',base['id'])['text'],'Første')
                self.assertEqual([x for x in store.all('settings') if x.get('entity')=='edit-conflict'],[])
            finally:store.close()

    def test_two_concurrent_conflicting_saves_keep_both_and_survive_backup(self):
        with tempfile.TemporaryDirectory() as source,tempfile.TemporaryDirectory() as target:
            store=Store(source);restored=Store(target)
            try:
                base={'id':'fictional-note','text':'Start','task':True}
                with store.transaction():store.put('notes',base)
                barrier=threading.Barrier(2)
                def save(actor,value):
                    barrier.wait(timeout=5)
                    return commit_reviewed(store,'notes',base['id'],base,{**base,'text':value},('text',),actor,lambda db,row:db.put('notes',row))
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    results=[pool.submit(save,'fictional-a','Første'),pool.submit(save,'fictional-b','Anden')]
                    self.assertEqual(sorted(f.result(timeout=10)['conflicts'] for f in results),[0,1])
                conflict=next(x for x in store.all('settings') if x.get('entity')=='edit-conflict')
                self.assertEqual({conflict['saved']['value'],conflict['incoming']['value']},{'Første','Anden'})
                restore=Restores(restored,'fictional');preview=restore.preview(snapshot(store,'fictional'));restore.apply(preview['token'])
                self.assertEqual(restored.require('settings',conflict['id']),conflict)
                self.assertEqual(restored.require('notes',base['id']),store.require('notes',base['id']))
            finally:store.close();restored.close()

    def test_session_bound_bases_reconcile_two_real_concurrent_transactions(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);snapshots=EditSnapshots()
            try:
                base={'id':'fictional-note','text':'Start','resolved':False,'task':True}
                with store.transaction():store.put('notes',base)
                tokens={actor:snapshots.create(actor,'notes',base['id'],store.require('notes',base['id'])) for actor in ('a','b')}
                barrier=threading.Barrier(2)
                def save(actor,value):
                    with snapshots.claim(tokens[actor],actor,'notes',base['id']) as server_base:
                        barrier.wait(timeout=5)
                        return commit_reviewed(store,'notes',base['id'],server_base,{**server_base,'text':value},('text',),actor,lambda db,row:db.put('notes',row))
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    futures=[pool.submit(save,'a','Første'),pool.submit(save,'b','Anden')]
                    self.assertEqual(sorted(f.result(timeout=10)['conflicts'] for f in futures),[0,1])
                notice=next(x for x in store.all('settings') if x.get('entity')=='edit-conflict')
                self.assertEqual(notice['base']['value'],'Start')
                self.assertEqual({notice['saved']['value'],notice['incoming']['value']},{'Første','Anden'})
                for actor in tokens:
                    with self.assertRaises(ValueError):
                        with snapshots.claim(tokens[actor],actor,'notes',base['id']):pass
            finally:store.close()

    def test_an_already_saved_identical_change_does_not_write_again(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            try:
                base={'id':'fictional-note','text':'Start','task':True}
                with store.transaction():store.put('notes',base)
                proposal={**base,'text':'Samme'}
                commit_reviewed(store,'notes',base['id'],base,proposal,('text',),'fictional-a',lambda db,row:db.put('notes',row))
                revision=store.revision
                result=commit_reviewed(store,'notes',base['id'],base,proposal,('text',),'fictional-b',lambda db,row:self.fail('Unchanged record must not be rewritten'))
                self.assertFalse(result['changed']);self.assertEqual(store.revision,revision)
            finally:store.close()


if __name__=='__main__':unittest.main()
