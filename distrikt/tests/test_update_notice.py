"""Published update notice checks: synthetic releases only, no GitHub or user data."""
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from update_notice import (RELEASES, UpdateChecker, asset_names, select_release,
                           track_for, version_key)


def published(version, prerelease=False, assets=(), published_at='2026-11-17T12:00:00Z'):
    tag = 'v' + version
    return {
        'tag_name': tag, 'html_url': RELEASES + '/tag/' + tag,
        'draft': False, 'prerelease': prerelease, 'published_at': published_at,
        'assets': [
            {'name': filename, 'state': 'uploaded', 'size': 1024,
             'browser_download_url': RELEASES + '/download/' + tag + '/' + filename}
            for filename in assets
        ],
    }


class UpdateSelectionTests(unittest.TestCase):
    def test_numeric_order_and_channel_separation(self):
        self.assertGreater(version_key('1.12.19-beta.30'), version_key('1.12.19-beta.9'))
        self.assertGreater(version_key('1.12.19'), version_key('1.12.19-beta.999'))
        self.assertIsNone(version_key('1.12.19-beta.1-rc'))
        versions = [
            published('1.12.20', assets=('LTM-Windows-v1.12.20-Setup.exe',)),
            published('1.12.19-beta.9', True),
            published('1.12.19-beta.10', True,
                      assets=('LTM-Home-Assistant-v1.12.19-beta.10.zip',)),
            published('1.12.19-beta.30', True),
        ]
        beta = select_release(versions, '1.12.19-beta.8', 'home-assistant')
        self.assertEqual(beta['version'], '1.12.19-beta.30')
        self.assertEqual(beta['channel'], 'beta')
        self.assertFalse(beta['file_available'])
        self.assertEqual(beta['url'], RELEASES)
        stable = select_release(versions, '1.12.19', 'windows-app')
        self.assertEqual(stable['version'], '1.12.20')
        self.assertTrue(stable['file_available'])
        self.assertTrue(stable['url'].endswith('LTM-Windows-v1.12.20-Setup.exe'))
        self.assertIsNone(select_release(versions, '1.12.20', 'windows-app'))
        self.assertIsNone(select_release(versions, '1.12.19-beta.30', 'home-assistant'))

    def test_platform_file_and_fallback(self):
        version = '1.12.21-beta.2'
        files = (
            'LTM-macOS-v' + version + '-AppleSilicon.dmg',
            'LTM-macOS-v' + version + '-Intel.dmg',
            'LTM-macOS-server-v' + version + '.zip',
            'LTM-Home-Assistant-v' + version + '.zip',
        )
        rows = [published(version, True, files)]
        arm = select_release(rows, '1.12.21-beta.1', 'macos-app', 'arm64')
        intel = select_release(rows, '1.12.21-beta.1', 'macos-app', 'x86_64')
        self.assertTrue(arm['url'].endswith('-AppleSilicon.dmg'))
        self.assertTrue(intel['url'].endswith('-Intel.dmg'))
        server = select_release(rows, '1.12.21-beta.1', 'macos-server', 'arm64')
        self.assertTrue(server['url'].endswith('-server-v' + version + '.zip'))
        ha = select_release(rows, '1.12.21-beta.1', 'home-assistant')
        self.assertTrue(ha['url'].endswith('-Assistant-v' + version + '.zip'))
        windows = select_release(rows, '1.12.21-beta.1', 'windows-app')
        self.assertEqual(windows['url'], RELEASES)
        unknown = select_release(rows, '1.12.21-beta.1', 'macos-app', 'unrecognized-cpu')
        self.assertEqual(unknown['url'], RELEASES)
        self.assertEqual(track_for(True, 'win32', True), 'home-assistant')
        self.assertEqual(track_for(False, 'darwin', False), 'macos-app')
        self.assertEqual(track_for(False, 'win32', True), 'windows-server')
        self.assertEqual(track_for(False, 'linux', False), 'other')
        self.assertEqual(asset_names('windows-server', version), ['LTM-Windows-server-v' + version + '.zip'])

    def test_unreleased_malformed_and_untrusted_links_fail_closed(self):
        version = '1.12.20'
        file = 'LTM-Windows-v' + version + '-Setup.exe'
        candidate = published(version, assets=(file,))
        malformed = [
            {**candidate, 'draft': True},
            {**candidate, 'published_at': None},
            {**candidate, 'html_url': 'https://attacker.example/steal'},
            {**candidate, 'tag_name': 'v1.12.20+unpublished'},
        ]
        self.assertIsNone(select_release(malformed, '1.12.19', 'windows-app'))
        invalid_asset = published(version, assets=(file,))
        invalid_asset['assets'][0]['browser_download_url'] = 'https://attacker.example/fake.exe'
        result = select_release([invalid_asset], '1.12.19', 'windows-app')
        self.assertEqual(result['url'], RELEASES)
        self.assertFalse(result['file_available'])
        invalid_asset['assets'][0]['browser_download_url'] = RELEASES + '/download/v1.12.19/' + file
        self.assertEqual(select_release([invalid_asset], '1.12.19', 'windows-app')['url'], RELEASES)
        self.assertIsNone(select_release([published('1.12.20-beta.3', True)],
                                         '1.12.19', 'windows-app'))
        self.assertIsNone(select_release([candidate], '1.12.19-beta.2', 'windows-app'))

    def test_offline_is_nonblocking_cached_and_no_private_input_is_sent(self):
        calls = []
        start = threading.Event()
        release = threading.Event()
        now = [100.0]

        def fetch():
            calls.append('public-feed-only')
            start.set()
            release.wait(2)
            raise OSError('Simulated offline')
        checker = UpdateChecker('1.12.19', system='win32', fetcher=fetch,
                                clock=lambda: now[0])
        self.assertEqual(checker.check(), {'checking': True})
        self.assertTrue(start.wait(1))
        self.assertEqual(checker.check(), {'checking': True})
        release.set()
        for _ in range(100):
            if checker.check() is None:
                break
            threading.Event().wait(0.005)
        self.assertIsNone(checker.check())
        self.assertEqual(calls, ['public-feed-only'])
        now[0] += 200
        self.assertIsNone(checker.check())
        self.assertEqual(len(calls), 1)

    def test_successful_check_cache_uses_no_local_user_data(self):
        calls = []
        event = threading.Event()
        def fetch():
            calls.append('public')
            event.set()
            return [published('1.12.20', assets=('LTM-Home-Assistant-v1.12.20.zip',))]
        checker = UpdateChecker('1.12.19', home_assistant=True, fetcher=fetch)
        self.assertEqual(checker.check(), {'checking': True})
        self.assertTrue(event.wait(1))
        for _ in range(100):
            result = checker.check()
            if result is None or 'checking' not in result:
                break
            threading.Event().wait(0.005)
        self.assertEqual(result['version'], '1.12.20')
        self.assertEqual(result['platform'], 'home-assistant')
        self.assertEqual(calls, ['public'])
        self.assertEqual(checker.check(), result)


if __name__ == '__main__':
    unittest.main()
