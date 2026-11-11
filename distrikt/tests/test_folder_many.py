"""Bulk folder placement: isolated fictional records, never real territory data."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Barrier
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from profile_policy import ACTIONS, require


class BulkFolderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.person = self.store.mutate('publisher.save', {'name': 'Fiktiv forkynder'})['id']

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def card(self, number):
        return self.store.mutate('card.save', {
            'number': number, 'name': 'Fiktiv ' + number, 'temporary': True
        })['id']

    def move(self, ids):
        return self.store.mutate('folder.set_many', {
            'ids': ids, 'in_folder': True, 'expected_in_folder': False
        })

    def test_zero_one_many_and_repeated_click_do_not_duplicate_activity(self):
        cards = [self.card('F-201'), self.card('F-202'), self.card('F-203')]
        with self.assertRaisesRegex(ValueError, '1–500'):
            self.move([])
        self.assertTrue(all(not self.store.get('cards', i)['in_folder'] for i in cards))
        first = self.move([cards[0]])
        self.assertEqual(first, {'count': 1, 'updated': [cards[0]], 'skipped': []})
        others = self.move(cards[1:])
        self.assertEqual(others['count'], 2)
        self.assertEqual(others['updated'], cards[1:])
        again = self.move(cards)
        self.assertEqual(again['count'], 0)
        self.assertEqual(again['updated'], [])
        self.assertEqual(len(again['skipped']), 3)
        self.assertTrue(all('flyttet' in item['reason'] for item in again['skipped']))
        logs = [row for row in self.store.all('notes')
                if row.get('entity') == 'activity' and row.get('action') == 'folder.set_many']
        self.assertEqual(len(logs), 2, 'Repeated writes must not add activity events')

    def test_mixed_statuses_partial_failures_preserve_loans_and_history(self):
        valid1, valid2 = self.card('F-301'), self.card('F-302')
        already, assigned = self.card('F-303'), self.card('F-304')
        self.store.mutate('folder.set', {
            'ids': [already], 'in_folder': True, 'expected_in_folder': False
        })
        self.store.mutate('loan.issue', {
            'card_id': assigned, 'publisher_id': self.person,
            'date': date.today().isoformat(), 'initial': True
        })
        self.store.mutate('completion.record', {
            'card_id': valid1, 'date': date.today().isoformat()
        })
        loans = self.store.all('loans')
        history = self.store.all('completions')
        result = self.move([valid1, already, assigned, 'unknown-fictional-card', valid2])
        self.assertEqual(result['updated'], [valid1, valid2])
        self.assertEqual({item['id'] for item in result['skipped']},
                         {already, assigned, 'unknown-fictional-card'})
        self.assertTrue(all(self.store.get('cards', i)['in_folder'] for i in (valid1, valid2, already)))
        self.assertFalse(self.store.get('cards', assigned)['in_folder'])
        self.assertEqual(self.store.all('loans'), loans)
        self.assertEqual(self.store.all('completions'), history)

    def test_strict_contract_and_unchanged_cards_after_rejection(self):
        ident = self.card('F-401')
        invalid = [
            {'ids': []},
            {'ids': [ident, ident]},
            {'ids': [None]},
            {'ids': list(map(str, range(501)))},
            {'ids': [ident], 'in_folder': False},
            {'ids': [ident], 'in_folder': 'true'},
            {'ids': [ident], 'expected_in_folder': True},
        ]
        for data in invalid:
            with self.subTest(data=str(data)[:90]):
                with self.assertRaises(ValueError):
                    self.store.mutate('folder.set_many', {
                        'ids': [ident], 'in_folder': True,
                        'expected_in_folder': False, **data
                    })
                self.assertFalse(self.store.get('cards', ident)['in_folder'])
        self.assertEqual(ACTIONS['folder.set_many'], ACTIONS['folder.set'])
        with self.assertRaises(PermissionError):
            require({'cards.view', 'loans.view'}, ACTIONS['folder.set_many'])
        require({'cards.view', 'loans.view', 'loans.manage'}, ACTIONS['folder.set_many'])

    def test_two_concurrent_users_same_card_change_it_once(self):
        ident = self.card('F-501')
        barrier = Barrier(2)

        def session_action():
            barrier.wait(timeout=5)
            return self.move([ident])

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: session_action(), range(2)))
        self.assertEqual(sorted(row['count'] for row in outcomes), [0, 1])
        self.assertEqual(sum(len(row['skipped']) for row in outcomes), 1)
        self.assertTrue(self.store.get('cards', ident)['in_folder'])
        logs = [row for row in self.store.all('notes')
                if row.get('entity') == 'activity' and row.get('action') == 'folder.set_many']
        self.assertEqual(len(logs), 1)

    def test_two_concurrent_users_different_selections(self):
        first, second = self.card('F-601'), self.card('F-602')
        barrier = Barrier(2)

        def session_action(ids):
            barrier.wait(timeout=5)
            return self.move(ids)

        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(session_action, [first])
            b = pool.submit(session_action, [second])
            results = [a.result(), b.result()]
        self.assertEqual([r['count'] for r in results], [1, 1])
        self.assertTrue(self.store.get('cards', first)['in_folder'])
        self.assertTrue(self.store.get('cards', second)['in_folder'])


if __name__ == '__main__':
    unittest.main()
