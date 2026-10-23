"""Synthetic W61 regressions. No real location strings or credentials."""
import hashlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
import cleanup_location_examples as cleanup

EXAMPLE = b'Gammel Opdigtetvej'
SEED = b'<input name="road" placeholder="Skriv fx ' + EXAMPLE + b'">'


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.rules = cleanup.Rules(SEED)

    def test_legacy_and_translated_fields_and_test_abbreviations(self):
        field = lambda name, number: b'<input name="' + name + b'" placeholder="' + number + b'">'
        raw = SEED + field(b'postcode', b'9999') + field(b'from', b'12') + field(b'to', b'34')
        actual = self.rules.clean(raw)
        self.assertIn(b'placeholder="Vejnavn"', actual)
        self.assertIn(b'placeholder="Postnummer"', actual)
        self.assertIn(b'placeholder="Fra"', actual)
        self.assertIn(b'placeholder="Til"', actual)
        self.assertFalse(self.rules.remains(actual))
        translated = b"${I18n.attribute('placeholder',\"Skriv fx " + EXAMPLE + b'\")}'
        self.assertEqual(self.rules.clean(translated), b"${I18n.attribute('placeholder',\"Vejnavn\")}")
        self.assertEqual(self.rules.clean(b'Gl. Opdigtetvej / gl opdigtetvej'), b'Gl. Fiktivvej / gl Fiktivvej')

    def test_remove_translation_and_preserve_unrelated_content_and_binary(self):
        entry = b'  "Skriv fx ' + EXAMPLE + b'":"Example: ' + EXAMPLE + b'",\n  "Vejnavn":"Road name",\n'
        self.assertEqual(self.rules.clean(entry), b'  "Vejnavn":"Road name",\n')
        raw = b'unchanged numeric limit 9999; identifiers and UTF-8: \xc3\xa6\xc3\xb8\xc3\xa5'
        self.assertEqual(self.rules.clean(raw), raw)
        # Python tests can mention I18n without becoming JavaScript templates.
        python = b"# I18n.attribute(\nvalue = " + repr(SEED + b'<input name="postcode" placeholder="' + b'9999' + b'">').encode() + b'\n'
        compile(self.rules.clean(python), '<invented fixture>', 'exec')
        binary = b'\x00\xff' + EXAMPLE
        self.assertEqual(self.rules.clean(binary), binary)

    def make_archive(self, target, unsafe=False, bad_checksum=False):
        source = b"VERSION='9.9.0-beta.1'\n"
        payloads = {'distrikt/app/server.py': source, 'distrikt/app/road-search.js': SEED,
                    'distrikt/app/preserve.bin': b'\x00\xffPUBLIC_BINARY', 'distrikt/config.yaml': b'version: 9.9.0-beta.1\n'}
        manifest = ''.join(hashlib.sha256(raw).hexdigest() + '  ' + name + '\n' for name, raw in payloads.items()).encode()
        payloads['SHA256SUMS.txt'] = manifest.replace(b'  distrikt/app/server.py', b'  missing.py') if bad_checksum else manifest
        if unsafe:
            payloads['../outside.txt'] = b'never extract'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, raw in payloads.items():
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100755 << 16
                archive.writestr(info, raw)
        return payloads

    def test_real_zip_keeps_inventory_version_binary_metadata_and_updates_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = self.make_archive(root / 'old.zip')
            changed = cleanup.clean_zip(root / 'old.zip', root / 'new.zip', self.rules, '9.9.0-beta.1')
            self.assertEqual(set(changed), {'distrikt/app/road-search.js', 'SHA256SUMS.txt'})
            with zipfile.ZipFile(root / 'new.zip') as archive:
                self.assertEqual(archive.namelist(), list(original))
                self.assertEqual(archive.read('distrikt/app/preserve.bin'), original['distrikt/app/preserve.bin'])
                self.assertEqual(archive.read('distrikt/app/server.py'), original['distrikt/app/server.py'])
                self.assertEqual(archive.getinfo('distrikt/app/server.py').external_attr >> 16, 0o100755)
                cleanup.verify_manifests({name: archive.read(name) for name in archive.namelist()})
            self.assertEqual(cleanup.clean_zip(root / 'new.zip', root / 'again.zip', self.rules, '9.9.0-beta.1'), [])
            self.assertEqual((root / 'new.zip').read_bytes(), (root / 'again.zip').read_bytes())

    def test_archive_rejects_wrong_version_unsafe_path_and_broken_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_archive(root / 'old.zip')
            with self.assertRaisesRegex(ValueError, 'version'):
                cleanup.clean_zip(root / 'old.zip', root / 'new.zip', self.rules, '9.9.0-beta.2')
            self.make_archive(root / 'old.zip', unsafe=True)
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                cleanup.clean_zip(root / 'old.zip', root / 'new.zip', self.rules, '9.9.0-beta.1')
            self.make_archive(root / 'old.zip', bad_checksum=True)
            with self.assertRaisesRegex(ValueError, 'checksum'):
                cleanup.clean_zip(root / 'old.zip', root / 'new.zip', self.rules, '9.9.0-beta.1')

    def test_nested_manifest_hashes_converge(self):
        inner = hashlib.sha256(SEED).hexdigest().encode() + b'  app/road-search.js\n'
        outer = hashlib.sha256(inner).hexdigest().encode() + b'  nested/SHA256SUMS.txt\n'
        cleaned = cleanup.transform_payloads({'file': SEED, 'inner': inner, 'outer': outer}, self.rules)
        self.assertIn(hashlib.sha256(cleaned['file']).hexdigest().encode(), cleaned['inner'])
        self.assertIn(hashlib.sha256(cleaned['inner']).hexdigest().encode(), cleaned['outer'])

    def test_entire_git_history_branches_tags_and_manifest_are_clean_without_lost_commits(self):
        try:
            import git_filter_repo
        except ImportError:
            self.skipTest('Install the pinned cleanup-only tool for history integration test.')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cleanup.git(root, 'init', '--initial-branch=main')
            cleanup.git(root, 'config', 'user.name', 'Fixture')
            cleanup.git(root, 'config', 'user.email', 'fixture@example.invalid')
            (root / 'road.js').write_bytes(SEED)
            (root / 'SHA256SUMS.txt').write_text(hashlib.sha256(SEED).hexdigest() + '  road.js\n')
            cleanup.git(root, 'add', '.')
            cleanup.git(root, 'commit', '-m', 'First fictional version')
            cleanup.git(root, 'tag', 'v9.9.0-beta.1')
            cleanup.git(root, 'branch', 'develop')
            (root / 'preserve.txt').write_text('Preserve me')
            cleanup.git(root, 'add', '.')
            cleanup.git(root, 'commit', '-m', 'Second fictional version')
            before = cleanup.refs(root)
            count = cleanup.git(root, 'rev-list', '--all', '--count')
            self.assertGreater(cleanup.rewrite(root, self.rules), 0)
            self.assertEqual(set(cleanup.refs(root)), set(before))
            self.assertEqual(cleanup.git(root, 'rev-list', '--all', '--count'), count)
            self.assertFalse(any(self.rules.remains(raw) for _ident, raw in cleanup.blobs(root)))
            payloads = {name: cleanup.git(root, 'show', 'main:' + name) for name in ('road.js', 'SHA256SUMS.txt')}
            cleanup.verify_manifests(payloads)
            self.assertEqual(cleanup.git(root, 'show', 'main:preserve.txt'), b'Preserve me')


if __name__ == '__main__':
    unittest.main()
