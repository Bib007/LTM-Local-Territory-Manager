"""Offline regressions for the combined task/role and area-colour changes."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from profile_policy import mutation, state_for


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
            raw = dict(store.state(), beta=True)
            user = {'id': 'user-fictional', 'name': 'Fictional', 'onboarded': True,
                    'revision': 1, 'permissions': {'cards.view'}}
            result = state_for(raw, user)
            self.assertEqual(result['areas'][0]['map_color'], '#123456')
            self.assertNotIn('overdue_message_template', result['settings'])


if __name__ == '__main__':
    unittest.main()
