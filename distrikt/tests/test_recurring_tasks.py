"""Weekly local tasks: explicit completion, calendar dates and retained history."""
import copy
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from portable import snapshot, Restores

class FixedDate(date):
    current=date(2026,10,19)
    @classmethod
    def today(cls):return cls.current

class RecurringTaskTests(unittest.TestCase):
    def setUp(self):
        FixedDate.current=date(2026,10,19)
        self.clock=patch('workflow_store.date',FixedDate);self.clock.start();self.addCleanup(self.clock.stop)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.addCleanup(lambda:self.store.close())
    def create(self,weekday=0):
        return self.store.mutate('note.save',{'text':'Fiktiv ugentlig opgave <test>','recurrence':{'frequency':'weekly','weekday':weekday}})['id']
    def item(self,ident):return self.store.get('notes',ident)
    def complete(self,ident,due):return self.store.mutate('note.complete',{'id':ident,'due':due})

    def test_selected_day_is_inclusive_on_creation_and_reading_does_not_generate_tasks(self):
        ident=self.create();before=copy.deepcopy(self.item(ident));revision=self.store.revision
        self.assertEqual(before['recurrence']['next_due'],'2026-10-19')
        FixedDate.current=date(2026,11,5)
        self.store.state();self.store.state()
        self.assertEqual(self.item(ident),before);self.assertEqual(self.store.revision,revision)
        self.assertEqual(len(self.store.state()['notes']),1)
        other=self.create(4);self.assertEqual(self.item(other)['recurrence']['next_due'],'2026-11-06')

    def test_completion_keeps_text_link_and_history_and_skips_no_fake_completions(self):
        ident=self.create();before=copy.deepcopy(self.item(ident));FixedDate.current=date(2026,11,5)
        self.complete(ident,'2026-10-19');after=self.item(ident)
        self.assertEqual(after['text'],before['text']);self.assertEqual(after['card_id'],before['card_id'])
        self.assertEqual(after['recurrence']['next_due'],'2026-11-09');self.assertFalse(after['resolved'])
        self.assertEqual([(h['due'],h['date']) for h in after['task_history']],[('2026-10-19','2026-11-05')])
        self.assertEqual(self.store.all('cards'),[]);self.assertEqual(self.store.all('loans'),[])
        FixedDate.current=date(2026,11,9);self.complete(ident,'2026-11-09')
        self.assertEqual(self.item(ident)['recurrence']['next_due'],'2026-11-16')
        self.assertEqual(len(self.item(ident)['task_history']),2)

    def test_early_stale_duplicate_and_legacy_completion_are_rejected_without_changes(self):
        ident=self.create(2);before=copy.deepcopy(self.item(ident));revision=self.store.revision
        with self.assertRaises(ValueError):self.complete(ident,'2026-10-21')
        self.assertEqual(self.item(ident),before);self.assertEqual(self.store.revision,revision)
        FixedDate.current=date(2026,10,21);self.complete(ident,'2026-10-21')
        before=copy.deepcopy(self.item(ident));revision=self.store.revision
        with self.assertRaises(ValueError):self.complete(ident,'2026-10-21')
        with self.assertRaises(ValueError):self.store.mutate('note.resolve',{'id':ident,'resolved':True})
        self.assertEqual(self.item(ident),before);self.assertEqual(self.store.revision,revision)

    def test_completion_undo_restores_due_date_and_history_atomically(self):
        ident=self.create();before=copy.deepcopy(self.item(ident));self.complete(ident,'2026-10-19')
        self.store.mutate('workflow.undo',{});self.assertEqual(self.item(ident),before)

    def test_edit_disable_and_old_clients_preserve_history_and_regular_task_status(self):
        ident=self.create();self.complete(ident,'2026-10-19');before=copy.deepcopy(self.item(ident))
        self.store.mutate('note.save',{'id':ident,'text':'Fiktiv rettet tekst'})
        self.assertEqual(self.item(ident)['recurrence'],before['recurrence'])
        self.store.mutate('note.save',{'id':ident,'text':'Fiktiv rettet tekst','recurrence':None})
        self.assertNotIn('recurrence',self.item(ident));self.assertEqual(self.item(ident)['task_history'],before['task_history'])
        self.store.mutate('note.resolve',{'id':ident,'resolved':True});self.assertTrue(self.item(ident)['resolved'])
        for invalid in ({'frequency':'daily','weekday':0},{'frequency':'weekly','weekday':7},{'frequency':'weekly','weekday':True}):
            with self.assertRaises(ValueError):self.store.mutate('note.save',{'id':ident,'text':'Fiktiv','recurrence':invalid})
        self.assertTrue(self.item(ident)['resolved'])

    def test_backup_restart_and_restore_preserve_exact_schedule_and_history(self):
        ident=self.create();self.complete(ident,'2026-10-19');expected=copy.deepcopy(self.item(ident))
        payload=snapshot(self.store,'fictional-test');self.store.close();self.store=Store(self.temp.name)
        self.assertEqual(self.item(ident),expected)
        self.store.mutate('note.save',{'id':ident,'text':'Fiktiv ændring','recurrence':None})
        restores=Restores(self.store,'fictional-test');preview=restores.preview(payload);restores.apply(preview['token'])
        self.assertEqual(self.item(ident),expected)

if __name__=='__main__':unittest.main()
