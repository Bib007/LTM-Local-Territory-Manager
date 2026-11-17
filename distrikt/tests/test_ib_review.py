"""IB revision prompts on return, persistence, idempotency and role boundaries.

All cards, people and IB addresses in these tests are fictional.
"""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from profile_accounts import DESK_PERMISSIONS
from profile_policy import mutation, state_for
from store import Store


class IBReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.day = date.today().isoformat()
        self.card_id = self.store.mutate('card.save', {'number': 'F-IB-101', 'temporary': True})['id']
        self.loan_id = self.store.mutate('loan.issue', {
            'card_id': self.card_id, 'publisher_name': 'Fiktiv forkynder',
            'date': self.day, 'initial': True,
        })['id']
        self.ib_id = self.store.mutate('ib.save', {
            'card_id': self.card_id, 'road': 'Eksempelvej', 'number': '12',
            'date': self.day,
        })['id']

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def return_card(self, **updates):
        data = {'id': self.loan_id, 'date': self.day, 'complete': False,
                'retain': False, 'revise_ib': True}
        data.update(updates)
        return self.store.mutate('loan.finish', data)

    def reviews(self):
        return self.store.state()['ib_reviews']

    def projected(self, user):
        # The HTTP server supplies this marker before applying profile filtering.
        return state_for({**self.store.state(), 'beta': True}, user)

    def test_yes_creates_only_one_review_and_never_edits_ib(self):
        original_ib = self.store.all('ib')
        original_card = self.store.get('cards', self.card_id)
        self.return_card()
        rows = self.reviews()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], 'ib-review:' + self.loan_id)
        self.assertEqual(rows[0]['card_id'], self.card_id)
        self.assertFalse(rows[0]['resolved'])
        self.assertEqual(self.store.all('ib'), original_ib)
        self.assertEqual(self.store.get('cards', self.card_id)['back_revision'],
                         original_card['back_revision'])
        self.assertEqual(self.store.get('loans', self.loan_id)['returned'], self.day)
        with self.assertRaisesRegex(ValueError, 'allerede afleveret'):
            self.return_card()
        self.assertEqual(len(self.reviews()), 1)
        self.store.close()
        self.store = Store(self.temp.name)
        self.assertEqual(self.reviews(), rows, 'The follow-up survives a legacy database restart')
        self.store.mutate('ib.review.resolve', {'id': rows[0]['id']})
        self.assertTrue(self.reviews()[0]['resolved'])
        self.assertEqual(self.store.all('ib'), original_ib)
        with self.assertRaisesRegex(ValueError, 'allerede afsluttet'):
            self.store.mutate('ib.review.resolve', {'id': rows[0]['id']})

    def test_no_and_older_clients_leave_no_followup(self):
        self.assertEqual(self.reviews(), [], 'Older databases have an empty projection')
        self.store.close()
        self.store = Store(self.temp.name)
        self.assertEqual(self.reviews(), [], 'No migration creates synthetic follow-ups')
        self.return_card(revise_ib=False)
        self.assertEqual(self.reviews(), [])
        self.assertEqual(self.store.get('ib', self.ib_id)['number'], '12')

        another = self.store.mutate('card.save', {'number': 'F-IB-102', 'temporary': True})['id']
        loan = self.store.mutate('loan.issue', {
            'card_id': another, 'publisher_name': 'Fiktiv forkynder',
            'date': self.day, 'initial': True,
        })['id']
        # A pre-upgrade client is still accepted and means No.
        self.store.mutate('loan.finish', {
            'id': loan, 'date': self.day, 'complete': False, 'retain': False,
        })
        self.assertEqual(self.reviews(), [])

    def test_invalid_and_interrupted_returns_are_atomic(self):
        original_ib = self.store.all('ib')
        for invalid in ('yes', 1, None):
            with self.subTest(value=invalid):
                with self.assertRaisesRegex(ValueError, 'Ja eller Nej'):
                    self.return_card(revise_ib=invalid)
                self.assertIsNone(self.store.get('loans', self.loan_id)['returned'])
                self.assertEqual(self.reviews(), [])
        with self.assertRaises(ValueError):
            self.return_card(date='2099-01-01')
        with self.assertRaisesRegex(ValueError, 'kun oprettes ved indlevering'):
            self.return_card(retain=True)
        self.assertIsNone(self.store.get('loans', self.loan_id)['returned'])
        self.assertEqual(self.reviews(), [])

        original_put = self.store.put

        def fail_review(module, item):
            if module == 'notes' and item.get('id') == 'ib-review:' + self.loan_id:
                raise RuntimeError('Simulated local write failure')
            return original_put(module, item)

        with patch.object(self.store, 'put', side_effect=fail_review):
            with self.assertRaisesRegex(RuntimeError, 'Simulated local write failure'):
                self.return_card()
        self.assertIsNone(self.store.get('loans', self.loan_id)['returned'])
        self.assertEqual(self.reviews(), [])
        self.assertEqual(self.store.all('ib'), original_ib)
        self.return_card()
        self.assertEqual(len(self.reviews()), 1, 'Retry after rollback succeeds exactly once')

    @staticmethod
    def user(rights, *, desk=False):
        return {'id': 'fictional-account', 'name': 'Fiktiv bruger',
                'permissions': set(rights), 'desk_only': desk,
                'language': 'da', 'revision': 1, 'onboarded': True}

    def test_desk_can_answer_yes_but_cannot_read_or_finish_ib(self):
        desk = self.user(DESK_PERMISSIONS, desk=True)
        data = {'id': self.loan_id, 'date': self.day, 'complete': False,
                'retain': False, 'revise_ib': True}
        mutation(desk, 'loan.finish', data, self.store)
        self.return_card(**data)
        self.assertEqual(self.projected(desk)['ib_reviews'], [])
        with self.assertRaises(PermissionError):
            mutation(desk, 'ib.review.resolve', {'id': 'ib-review:' + self.loan_id}, self.store)

        reader = self.user({'cards.view', 'ib.view'})
        projection = self.projected(reader)
        self.assertEqual(len(projection['ib_reviews']), 1)
        self.assertEqual(projection['notes'], [], 'No private note text leaks to IB readers')
        with self.assertRaises(PermissionError):
            mutation(reader, 'ib.review.resolve', {'id': projection['ib_reviews'][0]['id']}, self.store)

        editor = self.user({'cards.view', 'ib.view', 'ib.edit'})
        mutation(editor, 'ib.review.resolve', {'id': projection['ib_reviews'][0]['id']}, self.store)
        self.store.mutate('ib.review.resolve', {'id': projection['ib_reviews'][0]['id']})
        self.assertTrue(self.projected(editor)['ib_reviews'][0]['resolved'])
        self.assertEqual(self.projected(self.user({'cards.view'}))['ib_reviews'], [])

    def test_completion_only_accepts_system_created_ib_review(self):
        fake_note = self.store.mutate('note.save', {
            'card_id': self.card_id, 'text': 'Fiktiv almindelig opgave',
        })['id']
        with self.assertRaisesRegex(ValueError, 'Vælg en IB-opfølgning'):
            self.store.mutate('ib.review.resolve', {'id': fake_note})
        self.assertFalse(self.store.get('notes', fake_note)['resolved'])


if __name__ == '__main__':
    unittest.main()
