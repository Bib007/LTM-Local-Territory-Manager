"""Fictional fixtures only: editable, additive S-13 assignment grid."""
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from portable import digest
from profile_policy import mutation


class HistoryGridTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)
        self.card = self.store.mutate('card.save', {'number': 'FIK-01'})['id']
        self.person = self.store.mutate('publisher.save', {'name': 'Fiktiv Forkynder'})['id']

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def ago(self, days):
        return (date.today() - timedelta(days=days)).isoformat()

    def edit(self, action='history.grid.add', **kwargs):
        return self.store.mutate(action, {'revision': self.store.revision, **kwargs})

    def add(self, start=100, end=None, completed=False, person=None):
        return self.edit(card_id=self.card, publisher_id=person or self.person,
                         assigned=self.ago(start), returned=self.ago(end) if end is not None else None,
                         completed=completed)['id']

    def test_completed_historical_loan_only_creates_one_linked_unknown_visits(self):
        first = self.add(400, 350, True)
        second = self.add(200, 150, True)
        loans = sorted(self.store.all('loans'), key=lambda x: x['assigned'])
        self.assertEqual([x['id'] for x in loans], [first, second])
        self.assertEqual(len(self.store.all('completions')), 2)
        self.assertEqual({e['loan_id'] for e in self.store.all('completions')}, {first, second})
        self.assertTrue(all(e['visits_unknown'] and e['visits'] == 0 for e in self.store.all('completions')))
        self.assertEqual(self.store.require('cards', self.card)['last_completed'], self.ago(150))
        with self.assertRaisesRegex(ValueError, 'allerede'):
            self.add(400, 350, True)
        self.assertEqual(len(self.store.all('completions')), 2)

    def test_active_stays_active_until_return_and_does_not_invent_completion(self):
        loan = self.add(90)
        self.assertEqual(self.store.active_loan(self.card)['id'], loan)
        self.assertFalse(self.store.require('cards', self.card)['in_folder'])
        self.assertFalse(self.store.all('completions'))
        self.edit('history.grid.edit', id=loan, field='returned', date=self.ago(40))
        self.assertIsNone(self.store.active_loan(self.card))
        self.assertEqual(self.store.require('loans', loan)['returned'], self.ago(40))
        self.assertFalse(self.store.all('completions'))

    def test_known_unlinked_completion_is_linked_never_duplicated(self):
        self.store.mutate('completion.record', {'card_id': self.card, 'date': self.ago(10)})
        original = self.store.all('completions')[0]
        loan = self.add(100, 10, True)
        events = self.store.all('completions')
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['id'], original['id'])
        self.assertEqual(events[0]['loan_id'], loan)
        self.assertEqual(events[0]['visits'], original['visits'])

    def test_edit_linked_return_moves_one_event_and_last_completed(self):
        loan = self.add(200, 100, True)
        self.edit('history.grid.edit', id=loan, field='returned', date=self.ago(90))
        event = self.store.all('completions')[0]
        self.assertEqual(event['date'], self.ago(90))
        self.assertEqual(self.store.require('loans', loan)['returned'], self.ago(90))
        self.assertEqual(self.store.require('cards', self.card)['last_completed'], self.ago(90))
        self.assertEqual(len(self.store.all('completions')), 1)
        with self.assertRaisesRegex(ValueError, 'kan ikke slettes'):
            self.edit('history.grid.edit', id=loan, field='returned', date=None)

    def test_date_edit_updates_assigned_in_first_cycle_only(self):
        loan = self.add(100, 40, True)
        self.edit('history.grid.edit', id=loan, field='assigned', date=self.ago(110))
        self.assertEqual(self.store.require('loans', loan)['cycle_start'], self.ago(110))
        self.assertEqual(self.store.all('completions')[0]['assigned'], self.ago(110))

    def test_overlap_future_and_out_of_order_rejected_without_changes(self):
        loan = self.add(200, 100)
        before = digest(self.store)
        for kwargs in (
            dict(start=150, end=90),
            dict(start=50, end=60),
            dict(start=-1, end=None),
        ):
            with self.assertRaises(ValueError):
                self.add(**kwargs)
            self.assertEqual(digest(self.store), before)
        with self.assertRaises(ValueError):
            self.edit('history.grid.edit', id=loan, field='returned', date=self.ago(250))
        self.assertEqual(digest(self.store), before)

    def test_stale_parallel_user_rejected_and_undo_restores(self):
        stale = self.store.revision
        loan = self.add(100, 50)
        before = digest(self.store)
        with self.assertRaisesRegex(ValueError, 'ændret'):
            self.store.mutate('history.grid.edit', {'revision': stale, 'id': loan, 'field': 'returned', 'date': self.ago(40)})
        self.assertEqual(digest(self.store), before)
        self.assertTrue(self.store.state()['undo_available'])
        self.store.mutate('workflow.undo', {})
        self.assertFalse(self.store.all('loans'))

    def test_existing_active_and_recovered_loans_not_overwritten(self):
        existing = self.add(120)
        before = digest(self.store)
        with self.assertRaises(ValueError):
            self.add(60)
        self.assertEqual(digest(self.store), before)
        self.store.mutate('delete', {'module': 'loans', 'id': existing,
                                    'history_revision': self.store.revision, 'location': 'box'})
        with self.assertRaisesRegex(ValueError, 'Gendan ved fejl'):
            self.add(120)
        self.assertIsNone(self.store.active_loan(self.card))

    def test_permissions_reject_write_without_required_rights(self):
        user = {'permissions': frozenset(('cards.view', 'loans.view', 'publishers.view', 'history.view')),
                'id': 'user-fictive'}
        before = digest(self.store)
        with self.assertRaises(PermissionError):
            mutation(user, 'history.grid.add', {'card_id': self.card}, self.store)
        self.assertEqual(digest(self.store), before)

    def test_rollback_of_multirecord_action_and_no_network(self):
        before = digest(self.store)
        original = self.store.put
        def broken(module, item):
            if module == 'completions':
                raise ValueError('Fiktiv fejl under gemning')
            return original(module, item)
        with patch.object(self.store, 'put', side_effect=broken), patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')):
            with self.assertRaisesRegex(ValueError, 'Fiktiv fejl'):
                self.add(80, 30, True)
        self.assertEqual(digest(self.store), before)


if __name__ == '__main__':
    unittest.main()
