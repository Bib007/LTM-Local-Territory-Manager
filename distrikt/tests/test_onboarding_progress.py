"""Successful local writes advance setup; invented records only."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store

ANSWERS={'mode':'desk','boundary':'later','cards':'numbers','ib':'later'}
PROFILE={'orientation':'landscape','paper':'cut','mode':'full','width':146,'height':94,'x':0,'y':0}

class OnboardingProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.addCleanup(lambda:self.store.close())

    def start(self):self.store.mutate('setup.onboarding.save',{'answers':ANSWERS,'tour_completed':True})
    def tasks(self):return self.store.get('settings','config')['onboarding'].get('tasks',{})
    def settings(self,**changes):
        data={k:v for k,v in self.store.get('settings','config').items() if k in ('congregation','folder_minimum','rural_minimum','rural_mode','require_revision')}
        data.update(changes);return self.store.mutate('settings.save',data)

    def test_new_zero_default_does_not_migrate_existing_values_or_progress(self):
        self.assertEqual(self.store.get('settings','config')['folder_minimum'],0)
        self.assertEqual(self.store.get('settings','config')['rural_minimum'],0)
        self.start();self.settings(folder_minimum=37,rural_minimum=8,rural_mode='manual')
        self.store.mutate('setup.onboarding.task',{'task':'sharing','status':'skipped'})
        before=copy.deepcopy(self.store.get('settings','config'))
        self.store.close();self.store=Store(self.temp.name)
        self.assertEqual(self.store.get('settings','config'),before)
        self.assertEqual(self.tasks()['sharing'],'skipped')

    def test_saved_name_and_explicit_zero_choice_not_opening_or_unrelated_save(self):
        self.start();self.assertEqual(self.tasks(),{})
        self.store.state();self.assertEqual(self.tasks(),{})
        self.settings(congregation='Fiktiv menighed')
        self.assertEqual(self.tasks(),{'congregation':'done'})
        self.settings(folder_minimum=0,folder_minimum_confirmed=True)
        self.assertEqual(self.tasks()['folder'],'done')
        self.store.mutate('setup.onboarding.task',{'task':'folder','status':'pending'})
        self.settings(congregation='Fiktiv menighed rettet')
        self.assertEqual(self.tasks()['folder'],'pending','Unrelated save must not undo an explicit reset')
        self.settings(folder_minimum=12);self.assertEqual(self.tasks()['folder'],'done')

    def test_invalid_save_and_card_preview_do_not_advance(self):
        self.start();before=copy.deepcopy(self.store.state());revision=self.store.revision
        with self.assertRaises(ValueError):self.settings(folder_minimum=-1,folder_minimum_confirmed=True)
        self.assertEqual(self.tasks(),{});self.assertEqual(self.store.revision,revision)
        self.store.mutate('card.bulk.preview',{'numbers':'FIKTIV-1 FIKTIV-2'})
        self.assertEqual(self.tasks(),{});self.assertEqual(self.store.all('cards'),[])
        self.store.mutate('card.bulk.create',{'numbers':'FIKTIV-1 FIKTIV-2'})
        self.assertEqual(self.tasks()['numbers'],'done');self.assertEqual(len(self.store.all('cards')),2)

    def test_publisher_progress_is_in_same_transaction_and_undo(self):
        self.start();self.store.mutate('publisher.save',{'name':'Fiktiv forkynder'})
        self.assertEqual(self.tasks()['publisher'],'done')
        self.store.mutate('workflow.undo',{})
        self.assertEqual(self.store.all('publishers'),[]);self.assertNotIn('publisher',self.tasks())
        self.store.mutate('setup.onboarding.task',{'task':'publisher','status':'skipped'})
        self.store.mutate('publisher.save',{'name':'Anden fiktiv forkynder'})
        self.assertEqual(self.tasks()['publisher'],'skipped')

    def test_printing_needs_two_saved_profiles_and_backup_needs_recorded_download(self):
        self.start();self.store.mutate('print.profile.save',{'side':'front','profile':PROFILE})
        self.assertNotIn('printing',self.tasks())
        self.store.mutate('print.profile.save',{'side':'back','profile':dict(PROFILE,mode='data')})
        self.assertEqual(self.tasks()['printing'],'done');self.assertNotIn('backup',self.tasks())
        self.store.mutate('backup.record',{'id':'fictional-created','status':'created'})
        self.assertNotIn('backup',self.tasks(),'ZIP creation alone is not a completed transfer')
        self.store.mutate('backup.record',{});self.assertEqual(self.tasks()['backup'],'done')
        self.assertNotIn('desk',self.tasks());self.assertNotIn('sharing',self.tasks())

    def test_guide_completion_recognizes_already_saved_data_without_changing_it(self):
        self.settings(congregation='Fiktiv menighed',folder_minimum=0,folder_minimum_confirmed=True)
        self.store.mutate('publisher.save',{'name':'Fiktiv forkynder'})
        self.store.mutate('card.save',{'number':'FIKTIV','temporary':True})
        before={m:copy.deepcopy(self.store.all(m)) for m in ('cards','publishers','loans','ib')}
        self.start();self.assertEqual(self.tasks(),{'congregation':'done','folder':'done','publisher':'done','numbers':'done'})
        for module,rows in before.items():self.assertEqual(self.store.all(module),rows)

if __name__=='__main__':unittest.main()
