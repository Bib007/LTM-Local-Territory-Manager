"""Synthetic visit-limit and ignored-suggestion contracts."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store, split_fingerprint

class SplitLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Store(self.tmp.name)
        with self.store.transaction():
            self.store.put('cards',{'id':'fictional-card','number':'101',
                'addresses':[{'road':'Fiktivvej','count':8}],
                'address_ids':['fictional-1','fictional-2'],'in_folder':False})
    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()
    def settings(self):
        return self.store.require('settings','config')
    def limit(self,value):
        self.store.mutate('settings.save',{'congregation':'Fiktiv menighed',
            'folder_minimum':0,'rural_minimum':0,'rural_mode':'auto',
            'split_visit_limit':value})
    def test_congregation_limit_does_not_change_setup_default(self):
        with self.store.transaction():
            c=dict(self.settings());c['setup_defaults']={'target':50};self.store.put('settings',c)
        self.limit(5)
        self.assertEqual(self.settings()['split_visit_limit'],5)
        self.assertEqual(self.settings()['setup_defaults']['target'],50)
        for value in (0,1001,5.5,'5',True):
            with self.assertRaises(ValueError):self.limit(value)
    def test_ignore_restore_and_expiration_after_input_change(self):
        self.limit(5)
        fingerprint=split_fingerprint(self.store.require('cards','fictional-card'),5)
        with self.assertRaises(ValueError):
            self.store.mutate('split.suggestion.ignore',{'card_id':'fictional-card','fingerprint':'stale','reason':'Fiktiv grund'})
        for reason in ('', 'a'*301):
            with self.assertRaises(ValueError):
                self.store.mutate('split.suggestion.ignore',{'card_id':'fictional-card','fingerprint':fingerprint,'reason':reason})
        self.store.mutate('split.suggestion.ignore',{'card_id':'fictional-card','fingerprint':fingerprint,'reason':'Skal undersøges ved næste grænsegennemgang'})
        self.assertEqual(self.settings()['split_suggestion_ignored']['fictional-card']['fingerprint'],fingerprint)
        self.limit(6)
        self.assertNotEqual(split_fingerprint(self.store.require('cards','fictional-card'),6),fingerprint)
        with self.assertRaises(ValueError):
            self.store.mutate('split.suggestion.ignore',{'card_id':'fictional-card','fingerprint':fingerprint,'reason':'Forældet'})
        self.store.mutate('split.suggestion.restore',{'card_id':'fictional-card'})
        self.assertFalse(self.settings()['split_suggestion_ignored'])
        with self.assertRaises(ValueError):
            self.store.mutate('split.suggestion.restore',{'card_id':'fictional-card'})
    def test_stale_card_edit_rejected_instead_of_silent_suppression(self):
        self.limit(4)
        old=split_fingerprint(self.store.require('cards','fictional-card'),4)
        with self.store.transaction():
            c=dict(self.store.require('cards','fictional-card'))
            c['addresses']=[{'road':'Fiktivvej','count':9}]
            self.store.put('cards',c)
        with self.assertRaises(ValueError):
            self.store.mutate('split.suggestion.ignore',{'card_id':'fictional-card','fingerprint':old,'reason':'Gammel vurdering'})

if __name__=='__main__':unittest.main()
