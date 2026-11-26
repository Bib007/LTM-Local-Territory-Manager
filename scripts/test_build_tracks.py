#!/usr/bin/env python3
"""Contracts for the five unpublishable-by-default release track packages."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

import build_tracks


class ReleaseTrackTests(unittest.TestCase):
    def test_each_track_is_complete_and_platform_scoped(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for track,(title,prefix) in build_tracks.TRACKS.items():
                with self.subTest(track=track):
                    path=build_tracks.build(track,root)
                    self.assertTrue(path.is_file())
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),path.with_suffix('.zip.sha256').read_text().split()[0])
                    with zipfile.ZipFile(path) as archive:
                        names=set(archive.namelist())
                        self.assertIsNone(archive.testzip())
                        self.assertIn(prefix+'/START-HERE.md',names)
                        self.assertIn('SHA256SUMS.txt',names)
                        self.assertFalse(any(name.endswith(('.sqlite','.sqlite3','.db')) for name in names))
                        if track=='home-assistant':
                            self.assertIn(prefix+'/distrikt/config.yaml',names)
                            # The add-on manifest describes the complete Home Assistant
                            # payload, so it belongs next to the add-on folder rather than
                            # inside it.  The archive-root manifest covers this track ZIP.
                            self.assertIn(prefix+'/SHA256SUMS.txt',names)
                        else:
                            suffix='.command' if track.startswith('macos') else '.cmd'
                            role='App' if track.endswith('app') else 'Server'
                            self.assertIn(prefix+'/Distrikt/Start-LTM-'+role+suffix,names)
                            self.assertNotIn(prefix+'/Distrikt/Start-LTM-'+('Server' if role=='App' else 'App')+suffix,names)


if __name__=='__main__':unittest.main(verbosity=2)
