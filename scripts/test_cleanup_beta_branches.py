"""Fictional refs only; no GitHub requests or repository writes."""
import subprocess
import unittest
from cleanup_beta_branches import plan, archive_and_delete, INTEGRATION


class CleanupTests(unittest.TestCase):
    def test_permanent_branches_are_preserved_and_moved_refs_rejected(self):
        expected = {'feature/example': 'a' * 40}
        current = dict(expected, main='m', develop='d', beta='b')
        self.assertEqual(plan(expected, current), expected)
        current['feature/example'] = 'c' * 40
        with self.assertRaises(ValueError):
            plan(expected, current)
        with self.assertRaises(ValueError):
            plan({'main': 'm'}, {'main': 'm'})

    def test_new_work_stops_cleanup_and_already_deleted_refs_are_safe(self):
        with self.assertRaises(ValueError):
            plan({}, {'feature/new': 'n'})
        self.assertEqual(plan({'feature/removed': 'x'}, {'main': 'm'}), {})
        self.assertEqual(plan({}, {INTEGRATION: 'i'}), {INTEGRATION: 'i'})

    def test_archives_precede_atomic_leased_deletion(self):
        calls = []
        archive_and_delete({'feature/example': 'a' * 40}, calls.append)
        self.assertIn('a' * 40 + ':refs/tags/archive/beta-20261123/feature/example', calls[0])
        self.assertIn('--force-with-lease=refs/heads/feature/example:' + 'a' * 40, calls[1])
        self.assertIn('--atomic', calls[0])
        self.assertIn('--atomic', calls[1])
        self.assertEqual(calls[1][-1], ':refs/heads/feature/example')

    def test_failed_archive_never_attempts_deletion(self):
        calls = []
        def fail(args):
            calls.append(args)
            raise subprocess.CalledProcessError(1, args)
        with self.assertRaises(subprocess.CalledProcessError):
            archive_and_delete({'feature/example': 'a'}, fail)
        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
