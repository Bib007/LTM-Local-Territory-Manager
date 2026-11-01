"""Synthetic tests for private edit bases; no HTTP endpoints are enabled."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from edit_snapshots import EditSnapshots


class EditSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.snapshots = EditSnapshots(ttl=10, capacity=2, clock=lambda:self.now)
        self.record = {'id':'fictional', 'name':'Start', 'nested':['A']}
        self.token = self.snapshots.create('session-a','cards','fictional',self.record)

    def test_base_is_copied_and_can_be_claimed_only_once(self):
        self.record['nested'].append('changed')
        with self.snapshots.claim(self.token,'session-a','cards','fictional') as base:
            self.assertEqual(base['nested'],['A'])
            base['name']='local change'
        with self.assertRaises(ValueError):
            with self.snapshots.claim(self.token,'session-a','cards','fictional'): pass

    def test_other_session_or_record_cannot_read_or_consume(self):
        for values in [('session-b','cards','fictional'),('session-a','ib','fictional'),('session-a','cards','other')]:
            with self.assertRaises(ValueError):
                with self.snapshots.claim(self.token,*values): pass
        with self.snapshots.claim(self.token,'session-a','cards','fictional') as base:
            self.assertEqual(base['name'],'Start')

    def test_failed_transaction_can_retry_without_mutated_base(self):
        with self.assertRaises(RuntimeError):
            with self.snapshots.claim(self.token,'session-a','cards','fictional') as base:
                base['name']='changed'
                raise RuntimeError('fictional failure')
        with self.snapshots.claim(self.token,'session-a','cards','fictional') as base:
            self.assertEqual(base['name'],'Start')

    def test_inflight_snapshot_cannot_be_claimed_twice(self):
        with self.snapshots.claim(self.token,'session-a','cards','fictional'):
            with self.assertRaises(ValueError):
                with self.snapshots.claim(self.token,'session-a','cards','fictional'): pass

    def test_expiry_capacity_and_logout(self):
        self.snapshots.create('session-b','cards','fictional',self.record)
        with self.assertRaises(ValueError):self.snapshots.create('session-c','cards','fictional',self.record)
        self.snapshots.revoke_session('session-a')
        with self.assertRaises(ValueError):
            with self.snapshots.claim(self.token,'session-a','cards','fictional'): pass
        token=self.snapshots.create('session-c','cards','fictional',self.record)
        self.now=10
        with self.assertRaises(ValueError):
            with self.snapshots.claim(token,'session-c','cards','fictional'): pass
        self.snapshots.create('session-c','cards','fictional',self.record)

    def test_expired_inflight_failure_is_not_retryable(self):
        with self.assertRaises(RuntimeError):
            with self.snapshots.claim(self.token,'session-a','cards','fictional'):
                self.now=11
                raise RuntimeError('fictional failure')
        with self.assertRaises(ValueError):
            with self.snapshots.claim(self.token,'session-a','cards','fictional'): pass


if __name__=='__main__':unittest.main()
