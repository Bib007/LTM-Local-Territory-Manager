import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from pdf_export import allocation_rows
from store import Store


class LoanDeletionTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = Store(folder.name)
        self.addCleanup(self.store.close)
        self.card = self.write('card.save', number='F42', temporary=True)['id']

    def write(self, action, **data):
        return self.store.mutate(action, data)

    def issue(self, name, day):
        return self.write('loan.issue', card_id=self.card, publisher_name=name, date=day, initial=True)['id']

    def remove(self, loan, **data):
        payload = {'history_revision': self.store.revision, **data}
        return self.write('delete', module='loans', id=loan, **payload)

    def s13(self):
        return allocation_rows(self.store.state(), 2026)[0]['allocations']

    def test_same_day_neighbor_archived_card_and_missing_publisher(self):
        older = self.issue('Fiktiv ældre', '2025-10-01')
        self.write('loan.finish', id=older, date='2025-10-02')
        mistaken = self.issue('Fiktiv forkert', '2025-10-04')
        self.write('loan.finish', id=mistaken, date='2025-10-04', complete=True, note='Fiktiv gyldig note')
        neighbor = self.issue('Fiktiv rigtig', '2025-10-04')
        self.write('loan.finish', id=neighbor, date='2025-10-05', complete=True)
        with self.store.transaction():
            self.store.put('cards', {**self.store.require('cards', self.card), 'archived': True})
            self.store.put('loans', {**self.store.require('loans', mistaken), 'publisher_id': 'fictional-unknown'})
        original = self.store.require('loans', mistaken)
        before = self.store.state()
        report = self.s13()

        removal = self.remove(mistaken)
        after = self.store.state()
        self.assertEqual([l['id'] for l in after['loans']], [older, neighbor])
        for module in ('completions', 'notes', 'archived_cards'):
            self.assertEqual(after[module], before[module])
        self.assertEqual(after['recovery'][0]['label'], 'F42 · 2025-10-04 → 2025-10-04')
        self.assertEqual(self.s13(), [report[0], report[2],
            {'person': '', 'assigned': None, 'completed': '2025-10-04'}])
        self.write('restore', **removal)
        self.assertEqual(self.store.require('loans', mistaken), original)
        self.assertEqual(self.s13(), report)

    def test_active_location_and_recovery_preserve_retained_completion(self):
        loan = self.issue('Fiktiv aktiv', '2025-10-04')
        self.write('loan.finish', id=loan, date='2025-10-06', complete=True, retain=True, note='Fiktiv note')
        original = self.store.require('loans', loan)
        before = self.store.state()
        with self.assertRaisesRegex(ValueError, 'hvor det fysiske kort ligger'):
            self.remove(loan)
        removal = self.remove(loan, location='folder')
        self.assertTrue(self.store.require('cards', self.card)['in_folder'])
        self.assertIsNone(self.store.active_loan(self.card))
        self.assertEqual(self.s13(), [{'person': '', 'assigned': None, 'completed': '2025-10-06'}])
        self.assertEqual(self.store.state()['completions'], before['completions'])
        self.assertEqual(self.store.state()['notes'], before['notes'])
        self.write('restore', **removal)
        self.assertEqual(self.store.active_loan(self.card), original)
        self.assertFalse(self.store.require('cards', self.card)['in_folder'])

        removal = self.remove(loan, location='box')
        self.assertFalse(self.store.require('cards', self.card)['in_folder'])
        new = self.issue('Fiktiv ny', '2025-10-07')
        with self.assertRaisesRegex(ValueError, 'allerede et nyt aktivt'):
            self.write('restore', **removal)
        self.assertEqual(self.store.active_loan(self.card)['id'], new)
        self.write('loan.finish', id=new, date='2025-10-08')
        with self.assertRaisesRegex(ValueError, 'overlapper'):
            self.write('restore', **removal)
        self.assertIsNone(self.store.active_loan(self.card))
        self.assertTrue(any(r['batch'] == removal['batch'] for r in self.store.recovery()))

    def test_stale_delete_is_rejected_after_return_and_cannot_touch_neighbor(self):
        old = self.issue('Fiktiv første', '2025-10-04')
        revision = self.store.revision
        self.write('loan.finish', id=old, date='2025-10-04')
        new = self.issue('Fiktiv anden', '2025-10-04')
        with self.assertRaisesRegex(ValueError, 'Historikken er ændret'):
            self.remove(old, history_revision=revision, location='folder')
        self.assertEqual(self.store.require('loans', old)['returned'], '2025-10-04')
        self.assertEqual(self.store.active_loan(self.card)['id'], new)
        self.assertFalse(self.store.recovery())

    def test_recovery_expires_and_still_preserves_completion(self):
        loan = self.issue('Fiktiv udløbet', '2025-10-04')
        self.write('loan.finish', id=loan, date='2025-10-05', complete=True)
        removal = self.remove(loan)
        expired = (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()
        with self.store.transaction():
            self.store.db.execute('UPDATE loans.records SET deleted_at=? WHERE id=?', (expired, loan))
        with self.assertRaisesRegex(ValueError, 'Gendannelsesperioden er udløbet'):
            self.write('restore', **removal)
        self.assertIsNone(self.store.get('loans', loan, deleted=True))
        self.assertEqual(self.s13(), [{'person': '', 'assigned': None, 'completed': '2025-10-05'}])
