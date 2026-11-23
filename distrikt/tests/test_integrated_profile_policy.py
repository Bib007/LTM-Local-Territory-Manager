"""Offline regressions for the combined task/role and area-colour changes."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from profile_policy import mutation, state_for
from profile_edits import capture, ReviewedMutation


class IntegratedPolicyTests(unittest.TestCase):
    def test_task_undo_checks_ownership_without_breaking_state_reads(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            self.addCleanup(store.close)
            card = store.mutate('card.save', {'number': 'F1', 'temporary': True})['id']
            note = store.mutate('note.save', {'card_id': card, 'text': 'Fictional task'})['id']
            store.mutate('note.resolve', {'id': note, 'resolved': True})
            store._undo['actor_id'] = 'user-fictional'
            user = {'id': 'user-fictional', 'permissions': {'notes.view', 'notes.edit'}}
            mutation(user, 'workflow.undo', {}, store)
            with self.assertRaises(PermissionError):
                mutation(dict(user, id='user-other'), 'workflow.undo', {}, store)

    def test_card_readers_receive_area_colours_without_settings_access(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            self.addCleanup(store.close)
            store.mutate('area.save', {'name': 'Fictional area', 'map_color': '#123456'})
            raw = dict(store.state(), beta=True, address_task={})
            user = {'id': 'user-fictional', 'name': 'Fictional', 'onboarded': True,
                    'revision': 1, 'permissions': {'cards.view'}}
            result = state_for(raw, user)
            self.assertEqual(result['areas'][0]['map_color'], '#123456')
            self.assertNotIn('overdue_message_template', result['settings'])

    def test_workflow_settings_follow_profile_access_and_remain_reviewable(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            self.addCleanup(store.close)
            store.mutate('settings.save', {'history_years': 5, 'overdue_message_template': 'Fictional {kort}'})
            user = {'id': 'user-fictional', 'name': 'Fictional', 'onboarded': True, 'revision': 1}
            raw = dict(store.state(), beta=True, address_task={})
            admin = state_for(raw, dict(user, permissions={'settings.manage'}))
            self.assertEqual(admin['settings']['history_years'], 5)
            self.assertEqual(admin['settings']['overdue_message_template'], 'Fictional {kort}')
            viewer = state_for(raw, dict(user, permissions={'publishers.view', 'loans.view'}))
            self.assertEqual(viewer['settings']['overdue_message_template'], 'Fictional {kort}')
            reader = state_for(raw, dict(user, permissions={'history.view'}))
            self.assertEqual(reader['settings']['history_years'], 5)
            self.assertNotIn('overdue_message_template', reader['settings'])
            for field, first, second in [('history_years', 6, 7),
                                        ('overdue_message_template', 'First {kort}', 'Second {kort}')]:
                base = capture(store)
                store.mutate('settings.save', {field: first})
                review = ReviewedMutation(base, 'user-fictional')
                store.mutate('settings.save', {field: second}, review=review)
                self.assertEqual([row['field'] for row in review.conflicts], [field])
                self.assertEqual(store.require('settings', 'config')[field], second)
                self.assertEqual(review.conflicts[0]['saved']['value'], first)
                self.assertEqual(review.conflicts[0]['incoming']['value'], second)


if __name__ == '__main__':
    unittest.main()
