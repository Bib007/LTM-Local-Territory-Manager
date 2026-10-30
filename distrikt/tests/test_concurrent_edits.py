"""Fictional snapshots: do not lose independent edits or hide real collisions."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from concurrent_edits import reconcile


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


if __name__=='__main__':unittest.main()
