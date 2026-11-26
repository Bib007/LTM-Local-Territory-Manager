"""Publisher deletion is explicit, authorized, recoverable and never orphans loans.

All data is fictional and stored in an isolated temporary SQLite database.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))

from profile_policy import mutation
from store import Store


class PublisherDeletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.addCleanup(self.store.close)

    def create(self, name='Fiktiv Person', group='Gruppe 01'):
        ident = self.store.mutate('publisher.save', {'name': name, 'group': group})['id']
        return self.store.require('publishers', ident)

    def expected(self, person):
        return {key: person.get(key, False if key == 'pioneer' else '')
                for key in ('name', 'group', 'group_role', 'pioneer')}

    def delete(self, person, **changes):
        payload = {'module': 'publishers', 'id': person['id'],
                   'confirmation': 'SLET FORKYNDER',
                   'expected': self.expected(person), **changes}
        return self.store.mutate('delete', payload)

    def test_empty_publisher_confirmed_deletion_changes_count_and_can_restore(self):
        person = self.create()
        self.assertEqual(len(self.store.state()['publishers']), 1)
        with self.assertRaisesRegex(ValueError, 'Bekræft'):
            self.delete(person, confirmation='')
        self.assertIsNotNone(self.store.get('publishers', person['id']))
        result = self.delete(person)
        self.assertIsNone(self.store.get('publishers', person['id']))
        self.assertEqual(len(self.store.state()['publishers']), 0)
        self.assertEqual(self.store.state()['recovery'][0]['batch'], result['batch'])
        self.store.mutate('restore', result)
        self.assertEqual(self.store.require('publishers', person['id'])['name'], person['name'])
        self.assertEqual(len(self.store.state()['publishers']), 1)

    def test_outdated_confirm_dialog_cannot_delete_edited_person(self):
        person = self.create()
        self.store.mutate('publisher.save', {'id': person['id'], 'name': 'Nyt Fiktivt Navn',
                                             'group': 'Gruppe 02'})
        with self.assertRaisesRegex(ValueError, 'ændret'):
            self.delete(person)
        self.assertEqual(self.store.require('publishers', person['id'])['name'], 'Nyt Fiktivt Navn')
        self.assertEqual(len(self.store.recovery()), 0)

    def test_active_and_returned_loans_and_recoverable_loans_block_deletion(self):
        card = self.store.mutate('card.save', {'number': 'F-501', 'temporary': True})['id']
        person = self.create()
        loan = self.store.mutate('loan.issue', {'card_id': card, 'publisher_id': person['id'],
                                               'date': '2026-01-10', 'initial': True})['id']
        with self.assertRaisesRegex(ValueError, 'historik'):
            self.delete(person)
        self.store.mutate('loan.finish', {'id': loan, 'date': '2026-01-11'})
        with self.assertRaisesRegex(ValueError, 'historik'):
            self.delete(person)
        self.store.mutate('delete', {'module': 'loans', 'id': loan,
                                      'history_revision': self.store.revision})
        with self.assertRaisesRegex(ValueError, 'historik'):
            self.delete(person)
        self.assertIsNotNone(self.store.get('publishers', person['id']))
        self.assertEqual(len(self.store.recovery()), 1, 'Only the deleted loan is recoverable')

    def test_restoring_publisher_does_not_duplicate_new_name(self):
        person = self.create()
        result = self.delete(person)
        newer = self.create()
        with self.assertRaisesRegex(ValueError, 'allerede'):
            self.store.mutate('restore', result)
        self.assertIsNone(self.store.get('publishers', person['id']))
        self.assertIsNotNone(self.store.get('publishers', newer['id']))

    def test_restoring_publisher_cannot_duplicate_service_group_function(self):
        person = self.create()
        self.store.mutate('publisher.save', {'id': person['id'], 'name': person['name'],
                                             'group': 'Gruppe 01', 'group_role': 'overseer'})
        person = self.store.require('publishers', person['id'])
        result = self.delete(person)
        self.store.mutate('publisher.save', {'name': 'Anden Fiktiv', 'group': 'Gruppe 01',
                                              'group_role': 'overseer'})
        with self.assertRaisesRegex(ValueError, 'samme gruppefunktion'):
            self.store.mutate('restore', result)
        self.assertIsNone(self.store.get('publishers', person['id']))

    def test_role_requires_publisher_deletion_and_loan_read(self):
        person = self.create()
        request = {'module': 'publishers', 'id': person['id'],
                   'confirmation': 'SLET FORKYNDER', 'expected': self.expected(person)}
        for rights in ({'publishers.view'}, {'publishers.view', 'publishers.manage'},
                       {'loans.view', 'publishers.view'}):
            with self.assertRaises(PermissionError):
                mutation({'id': 'fictional', 'permissions': rights}, 'delete', request, self.store)
        mutation({'id': 'fictional', 'permissions':
                  {'publishers.view', 'publishers.delete', 'loans.view'}},
                 'delete', request, self.store)
        self.assertIsNotNone(self.store.get('publishers', person['id']))


if __name__ == '__main__':
    unittest.main()
