"""Fictional-only tests for reversible follow-up dismissals."""
import concurrent.futures
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from profile_policy import mutation, state_for


class Actor:
    conflicts = []

    def __init__(self, ident, name):
        self.actor, self.actor_name = ident, name

    def prepare(self, store, action, data):
        return data

    def finish(self, store, touched):
        pass


class FollowupIgnoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        a = self.store.mutate('card.save', {'number': 'F100', 'temporary': True})['id']
        b = self.store.mutate('card.save', {'number': 'F101', 'temporary': True})['id']
        self.key = json.dumps(['checks', 'overlap', *sorted([a, b])], separators=(',', ':'))

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def record(self):
        return self.store.state()['followup_ignores'][0]

    def write(self, actor, ignored, token=''):
        return self.store.mutate('followup.ignore', {
            'key': self.key, 'ignored': ignored, 'expected_token': token,
            '_actor_id': 'forged', '_actor_name': 'Forged client',
        }, review=actor)

    def test_reversible_state_original_history_reload_and_actor_integrity(self):
        self.assertEqual(self.store.state()['followup_ignores'], [])
        self.write(Actor('user-a', 'Fiktiv Alice'), True)
        first = self.record()
        self.assertTrue(first['ignored'])
        self.assertEqual(first['history'][0]['actor_name'], 'Fiktiv Alice')
        self.assertEqual(first['history'][0]['actor_id'], 'user-a')
        self.assertNotIn('Forged client', str(first))
        self.assertEqual(len(first['history']), 1)

        self.store.close()
        self.store = Store(self.temp.name)
        self.assertEqual(self.record(), first, 'Persistent status and original event survive restart')
        self.write(Actor('user-b', 'Fiktiv Bo'), False, first['token'])
        second = self.record()
        self.assertFalse(second['ignored'])
        self.assertNotEqual(first['token'], second['token'])
        self.assertEqual(second['history'][:1], first['history'])
        self.assertEqual(second['history'][1]['actor_name'], 'Fiktiv Bo')
        self.assertTrue(second['history'][1]['at'])
        self.write(Actor('user-a', 'Fiktiv Alice'), True, second['token'])
        self.assertEqual([e['ignored'] for e in self.record()['history']], [True, False, True])

    def test_critical_categories_and_invalid_keys_do_not_create_suppressions(self):
        bad = [
            ['reprint', 'a', 'front'],
            ['addresses', 'change'],
            ['loans', 'loan'],
            ['checks', 'a', 'boundary'],
            ['checks', 'overlap', 'fake', 'unknown'],
            ['checks', 'overlap', *list(reversed(json.loads(self.key)[2:]))],
        ]
        for parts in bad:
            with self.subTest(parts=parts), self.assertRaises(ValueError):
                self.store.mutate('followup.ignore', {
                    'key': json.dumps(parts, separators=(',', ':')),
                    'ignored': True, 'expected_token': '',
                })
        self.assertEqual(self.store.state()['followup_ignores'], [])

    def test_concurrent_editors_cannot_overwrite_each_other(self):
        def attempt(actor):
            try:
                self.write(actor, True)
                return 'ok'
            except ValueError:
                return 'stale'
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, [Actor('a', 'Fiktiv A'), Actor('b', 'Fiktiv B')]))
        self.assertEqual(sorted(results), ['ok', 'stale'])
        self.assertEqual(len(self.record()['history']), 1)
        with self.assertRaisesRegex(ValueError, 'anden bruger'):
            self.write(Actor('c', 'Fiktiv C'), False, '')
        self.assertEqual(len(self.record()['history']), 1)

    def test_profile_state_filters_readers_and_edit_authorization(self):
        self.write(Actor('a', 'Fiktiv A'), True)
        base = self.store.state()
        # The HTTP state endpoint adds this channel flag before profile filtering.
        base['beta'] = False
        def user(rights):
            return {'id': 'user-viewer', 'name': 'Fiktiv læser', 'onboarded': True,
                    'revision': 1, 'permissions': set(rights)}
        hidden = state_for(base, user(['cards.view']))
        self.assertEqual(hidden['followup_ignores'], [])
        reader = user(['cards.view', 'geo.view'])
        self.assertEqual(len(state_for(base, reader)['followup_ignores']), 1)
        with self.assertRaises(PermissionError):
            mutation(reader, 'followup.ignore', {'key': self.key}, self.store)
        editor = user(['cards.view', 'geo.view', 'geo.edit'])
        mutation(editor, 'followup.ignore', {'key': self.key}, self.store)


if __name__ == '__main__':
    unittest.main()
