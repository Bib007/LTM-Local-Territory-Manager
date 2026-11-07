"""Offline tests for native LTM app entry and static asset paths."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(APP))
import desktop_entry
import resource_paths


class NativeDesktopTests(unittest.TestCase):
    def test_source_asset_paths(self):
        self.assertEqual(resource_paths.app_dir(), APP)
        self.assertEqual(resource_paths.templates_dir(), APP.parent / 'templates')
        self.assertEqual(resource_paths.vendor_dir(), APP / 'vendor_py')

    def test_frozen_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, 'frozen', True, create=True), patch.object(sys, '_MEIPASS', directory, create=True):
                self.assertEqual(resource_paths.app_dir(), Path(directory) / 'app')
                self.assertEqual(resource_paths.templates_dir(), Path(directory) / 'templates')
                self.assertEqual(resource_paths.vendor_dir(), Path(directory) / 'app' / 'vendor_py')

    def test_local_start(self):
        with patch.object(desktop_entry.server, 'main') as start:
            desktop_entry.main(['--data-dir', '/tmp/fictional', '--no-browser'])
        start.assert_called_once_with(['--data-dir', '/tmp/fictional', '--no-browser'])

    def test_isolated_pdf_worker(self):
        with patch.object(desktop_entry.runpy, 'run_module') as worker, patch.object(desktop_entry.server, 'main') as start:
            desktop_entry.main(['--ltm-read-s13'])
        worker.assert_called_once_with('s13_reader', run_name='__main__')
        start.assert_not_called()
