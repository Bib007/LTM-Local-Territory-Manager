"""Local backup receipts contain no paths, credentials or invented success."""
import copy
import os
import sys
import tempfile
import time
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from portable import snapshot, Restores

class BackupHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.addCleanup(self.store.close)
    def config(self):return self.store.get('settings','config')
    def record(self,**data):return self.store.mutate('backup.record',data)

    def test_created_is_not_a_transfer_and_client_paths_are_not_stored(self):
        self.record(id='fictional-1',status='created',path='DO-NOT-STORE',token='DO-NOT-STORE')
        self.assertNotIn('last_backup',self.config())
        self.assertEqual(self.config()['backup_history'][0]['status'],'created')
        self.assertNotIn('DO-NOT-STORE',str(self.store.state()))
        self.record(id='fictional-1',status='download_started')
        self.assertIn('last_backup',self.config())
        self.assertEqual(len(self.config()['backup_history']),1)
        self.assertEqual(self.config()['backup_history'][0]['status'],'download_started')

    def test_file_receipt_idempotency_and_invalid_transitions(self):
        self.record(id='fictional-2',status='created');self.record(id='fictional-2',status='file_saved')
        before=copy.deepcopy(self.config());revision=self.store.revision
        self.record(id='fictional-2',status='file_saved')
        self.assertEqual(self.config(),before);self.assertEqual(self.store.revision,revision)
        for data in ({'id':'unknown','status':'file_saved'},{'id':'fictional-2','status':'created'},
                     {'id':'fictional-2','status':'download_started'},{'id':'../private','status':'created'},
                     {'status':'not-a-status'}):
            with self.assertRaises(ValueError):self.record(**data)
        self.assertEqual(self.config(),before)

    def test_legacy_receipt_stays_compatible_and_history_is_bounded(self):
        self.record();self.assertEqual(self.config()['backup_history'][0]['status'],'download_started')
        for i in range(105):self.record(id=f'fictional-{i}',status='created')
        history=self.config()['backup_history'];self.assertEqual(len(history),100)
        self.assertEqual(history[0]['id'],'fictional-5');self.assertIn('last_backup',self.config())

    def test_snooze_is_next_calendar_day_and_success_clears_it(self):
        self.store.mutate('backup.snooze',{})
        tomorrow=(date.today()+timedelta(days=1)).isoformat()
        self.assertEqual(self.config()['backup_snoozed_until'],tomorrow)
        self.record(id='fictional-3',status='created')
        self.assertEqual(self.config()['backup_snoozed_until'],tomorrow)
        self.record(id='fictional-3',status='download_started')
        self.assertNotIn('backup_snoozed_until',self.config())

    def test_history_restores_with_snapshot_not_current_installation(self):
        self.record();expected=copy.deepcopy(self.config());payload=snapshot(self.store,'fictional-test')
        self.record(id='later-failed',status='created')
        restores=Restores(self.store,'fictional-test');preview=restores.preview(payload)
        restores.apply(preview['token'])
        self.assertEqual(self.config(),expected)

    @unittest.skipUnless(hasattr(time,'tzset'),'Host timezone selection is not available on Windows')
    def test_reminder_day_uses_server_calendar_with_midnight_and_dst(self):
        try:
            with patch.dict(os.environ,{'TZ':'Europe/Copenhagen'}):
                time.tzset()
                for stamp,expected in (('2026-10-01T22:30:00+00:00','2026-10-02'),('2026-12-01T23:30:00+00:00','2026-12-02')):
                    with self.store.transaction():self.store.put('settings',{**self.config(),'last_backup':stamp})
                    before=copy.deepcopy(self.config());self.assertEqual(self.store.state()['backup_last_day'],expected);self.assertEqual(self.config(),before)
        finally:time.tzset()

if __name__=='__main__':unittest.main()
