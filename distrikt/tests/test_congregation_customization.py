"""Congregation-local terminology and optional carry-folder workflow.

Only fictional, temporary data. Old DBs need no migration.
"""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from profile_policy import state_for


class CongregationCustomizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.addCleanup(self.store.close)

    def config(self):
        return self.store.get('settings', 'config')

    def test_legacy_configuration_defaults_to_using_folder(self):
        self.assertNotIn('folder_enabled', self.config())
        self.assertNotIn('location_labels', self.config())
        card = self.store.mutate('card.save', {'number':'F101','temporary':True})['id']
        with self.assertRaisesRegex(ValueError, 'mappen'):
            self.store.mutate('loan.issue', {'card_id':card,
                'publisher_name':'Fiktiv forkynder','date':date.today().isoformat()})

    def test_no_folder_allows_issue_from_home_and_preserves_card_placements(self):
        first = self.store.mutate('card.save', {'number':'F101','temporary':True})['id']
        second = self.store.mutate('card.save', {'number':'F102','temporary':True})['id']
        self.store.mutate('folder.set', {'ids':[second], 'in_folder':True})
        self.store.mutate('settings.save', {
            'folder_enabled':False, 'location_labels':{
                'home':'Hjemme', 'issued':'Ude', 'folder':'Med i mødelokalet'}})
        self.assertFalse(self.config()['folder_enabled'])
        self.assertEqual(self.config()['location_labels']['home'],'Hjemme')
        self.assertTrue(self.store.get('cards',second)['in_folder'],
                        'Hiding folder workflow never rewrites or loses real placements')
        with self.assertRaisesRegex(ValueError, 'slået fra'):
            self.store.mutate('folder.set', {'ids':[first],'in_folder':True})
        loan = self.store.mutate('loan.issue', {'card_id':first,
            'publisher_name':'Fiktiv forkynder','date':date.today().isoformat()})
        self.assertTrue(loan['id'])
        self.assertFalse(self.store.get('cards',first)['in_folder'])
        self.assertTrue(self.store.get('cards',second)['in_folder'])
        self.store.mutate('settings.save', {'folder_enabled':True})
        self.assertEqual(self.config()['location_labels']['issued'],'Ude')
        self.assertTrue(self.store.get('cards',second)['in_folder'])
        self.store.close()
        self.store=Store(self.tmp.name)
        self.assertEqual(self.config()['location_labels']['home'],'Hjemme')

    def test_validation_and_rollback_prevent_broken_labels_or_mode(self):
        original=self.config()
        for labels in ({'other':'Misbrugt'}, {'home':'x'*49},
                       {'home':'\x00'}, {'home':17}, ['Hjemme']):
            with self.subTest(labels=labels):
                with self.assertRaisesRegex(ValueError,'Stednavne'):
                    self.store.mutate('settings.save',{'location_labels':labels})
                self.assertEqual(self.config(),original)
        for invalid in (None,0,'false',1):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError,'mappe'):
                    self.store.mutate('settings.save',{'folder_enabled':invalid})
                self.assertEqual(self.config(),original)
        self.store.mutate('settings.save',{'location_labels':{'home':'  Hjemme  ','folder':''}})
        self.assertEqual(self.config()['location_labels'],{'home':'Hjemme'})

    def test_card_viewers_receive_only_presentational_settings(self):
        self.store.mutate('settings.save',{'folder_enabled':False,
            'location_labels':{'home':'Hjemme'}, 'publisher_card_guidance':{
                'member':2,'pioneer':4,'assistant':4,'overseer':6}})
        raw={**self.store.state(), 'version':'0.0.0-fictional', 'beta':False}
        reader=state_for(raw,{'permissions':{'cards.view'},'id':'reader','name':'Fiktiv læser','revision':0,'onboarded':True,'desk_only':False})
        self.assertEqual(reader['settings']['folder_enabled'],False)
        self.assertEqual(reader['settings']['location_labels'],{'home':'Hjemme'})
        self.assertNotIn('publisher_card_guidance',reader['settings'])
        denied=state_for(raw,{'permissions':set(),'id':'denied','name':'Fiktiv uden adgang','revision':0,'onboarded':True,'desk_only':False})
        self.assertNotIn('location_labels',denied['settings'])
        self.assertNotIn('folder_enabled',denied['settings'])


if __name__ == '__main__':
    unittest.main()
