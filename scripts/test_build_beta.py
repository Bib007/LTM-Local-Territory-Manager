"""HA beta packaging with invented files; no user installation or credentials."""
import contextlib
import hashlib
import io
import tempfile
from pathlib import Path
import unittest
import zipfile
import build_beta as beta
import test_build_release as fixtures

class BetaBuildTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.ReleaseArchiveTests();self.fixture.setUp()
        self.add=self.fixture.add;self.root=self.fixture.root
        self.add('distrikt/app/server.py',"VERSION='9.9.0-beta.1'\n")
        self.add('distrikt/config.yaml','name: Distrikt\nversion: "9.9.0-beta.1"\nslug: distrikt\nboot: auto\nports:\n  8787/tcp: 8787\nwebui: "http://[HOST]:[PORT:8787]/"\n')
        self.add('distrikt/run.sh','#!/bin/sh\nset -euo pipefail\npython app/server.py --port 8787 --data-dir /data/distrikt\n')
        self.add('distrikt/app/index.html','<title>Local Territory Manager – JW</title><body><b>LTM</b>')
        self.changelog=self.fixture.changelog.replace('9.9.0','9.9.0-beta.1')
        self.add('CHANGELOG.md',self.changelog)
        self.add('distrikt/CHANGELOG.md',self.changelog)
        self.add('docs/BETA.md','# Fiktiv betavejledning\n')
    def tearDown(self):self.fixture.tearDown()
    def build(self,name):
        with contextlib.redirect_stdout(io.StringIO()):return beta.build(self.root/name,self.root/(name+'-assets'))
    def test_separate_identity_port_data_cookie_and_source_unchanged(self):
        before=(self.root/'distrikt/config.yaml').read_bytes();files=beta.entries()
        cfg=files['distrikt/config.yaml'][0].decode();run=files['distrikt/run.sh'][0].decode()
        self.assertIn('name: Distrikt Beta',cfg);self.assertIn('slug: distrikt_beta',cfg);self.assertIn('boot: manual',cfg)
        self.assertIn('8788/tcp: 8788',cfg);self.assertIn('[PORT:8788]',cfg);self.assertIn('--port 8788',run)
        self.assertIn('/data/distrikt-beta',run);self.assertIn('export LTM_CHANNEL=beta',run)
        self.assertIn('#beta',files['repository.yaml'][0].decode());self.assertIn(b'LTM Beta',files['distrikt/app/index.html'][0])
        self.assertIn(b'betaChannel',files['distrikt/app/index.html'][0])
        self.assertIn('distrikt/icon.png',files);self.assertIn('distrikt/logo.png',files)
        self.assertEqual((self.root/'distrikt/config.yaml').read_bytes(),before)
    def test_reproducible_program_only_archive(self):
        first=self.build('first');second=self.build('second')
        self.assertEqual(first.read_bytes(),second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            names=archive.namelist();self.assertIn('distrikt/app/server.py',names);self.assertIn('repository.yaml',names);self.assertIn('SHA256SUMS.txt',names)
            self.assertFalse(any(n.startswith(('.github/','data/','Distrikt-lokal/')) or n.endswith(('.sqlite3','.db')) for n in names))
            self.assertFalse(any(b'DO_NOT_PACKAGE_PRIVATE_TEST_RECORD' in archive.read(n) for n in names))
            self.assertEqual(archive.getinfo('distrikt/run.sh').external_attr>>16&0o777,0o755)
    def test_rejects_stable_version_and_nonempty_output(self):
        output=self.root/'occupied';output.mkdir();(output/'keep.txt').write_text('preserve')
        with self.assertRaises(ValueError):beta.build(output,self.root/'assets')
        self.assertEqual((output/'keep.txt').read_text(),'preserve')
        self.add('distrikt/app/server.py',"VERSION='9.9.0'\n");self.add('distrikt/config.yaml','version: "9.9.0"\n')
        with self.assertRaisesRegex(ValueError,'numbered beta'):beta.entries()

    def test_beta_changelog_history_and_checksum_match_source(self):
        with zipfile.ZipFile(self.build('changelog')) as archive:
            raw=archive.read('distrikt/CHANGELOG.md')
            self.assertEqual(raw,self.changelog.encode())
            self.assertIn(b'## 9.8.0',raw)
            manifest=archive.read('SHA256SUMS.txt').decode()
            self.assertIn(hashlib.sha256(raw).hexdigest()+'  distrikt/CHANGELOG.md\n',manifest)

    def test_beta_rejects_stale_changelog(self):
        self.add('distrikt/CHANGELOG.md','# Fictional old beta changes\n')
        with self.assertRaisesRegex(ValueError,'changelogs differ'):self.build('stale')

if __name__=='__main__':unittest.main()
