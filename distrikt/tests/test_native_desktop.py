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

    def test_installer_language_is_used_only_as_first_browser_hint(self):
        import server
        with tempfile.TemporaryDirectory() as folder:
            already_running = {'url': 'http://127.0.0.1:8787', 'version': server.VERSION}
            with patch.object(server, 'running', return_value=already_running), patch.object(server.webbrowser, 'open') as browser:
                server.main(['--data-dir', folder, '--language', 'da'])
                browser.assert_called_with('http://127.0.0.1:8787?ltm_start_language=da')
                server.main(['--data-dir', folder, '--language', 'en'])
                browser.assert_called_with('http://127.0.0.1:8787?ltm_start_language=en')
                server.main(['--data-dir', folder])
                browser.assert_called_with('http://127.0.0.1:8787')

    def test_beta_installation_identity_stays_separate_and_stable_id_is_preserved(self):
        setup=(APP.parents[1]/'scripts/LTM.iss').read_text()
        self.assertIn('"{{B7195427-A9D7-4BE6-8BC6-5D629688DD97}"',setup)
        self.assertIn('"{{B7195427-A9D7-4BE6-8BC6-5D629688DD98}"',setup)
        self.assertIn('DefaultDirName={localappdata}\\Programs\\{#InstallFolder}',setup)
        self.assertIn('#define InstallFolder "LTM-Beta"',setup)
        self.assertIn('VersionInfoVersion={#NumericVersion}',setup)

    def test_isolated_pdf_worker(self):
        with patch.object(desktop_entry.runpy, 'run_module') as worker, patch.object(desktop_entry.server, 'main') as start:
            desktop_entry.main(['--ltm-read-s13'])
        worker.assert_called_once_with('s13_reader', run_name='__main__')
        start.assert_not_called()
