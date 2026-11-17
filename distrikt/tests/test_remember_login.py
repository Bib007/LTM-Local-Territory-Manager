"""Restart-safe login over the real LAN/HA-style HTTP path, using fictional accounts."""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from access import Access
from profile_accounts import ProfileAccounts, SESSION_LIFETIME
from remembered_sessions import REMEMBER_LIFETIME
from server import Server
from store import Store

LAN_PASSWORD = 'Fiktiv-kode-12345'
PROFILE_PASSWORD = 'Fiktiv-profil-12345'


class RememberedLoginHTTPTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'LTM_CHANNEL': 'stable'})
        self.env.start()
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)
        self.server = None

    def tearDown(self):
        self.stop()
        self.store.close()
        self.tmp.cleanup()
        self.env.stop()

    def start(self):
        # A loopback-only test listener with the same private access-host path
        # that Home Assistant starts; never reach a real HA installation.
        self.server = Server(('127.0.0.1', 0), self.store,
                             access_host='192.168.1.77', password=LAN_PASSWORD)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(5)
            self.server = None

    def request(self, path, data=None, cookie='', csrf='', extra=None):
        headers = {'Host': '192.168.1.77:' + str(self.server.server_port)}
        if cookie:
            headers['Cookie'] = cookie
        if csrf:
            headers['X-Distrikt-Token'] = csrf
        if data is not None:
            headers.update({'Content-Type': 'application/json',
                            'Origin': 'http://' + headers['Host']})
        headers.update(extra or {})
        request = urllib.request.Request(
            self.server.origin + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers=headers)
        try:
            reply = urllib.request.urlopen(request, timeout=8)
        except urllib.error.HTTPError as error:
            reply = error
        with reply:
            return reply.status, dict(reply.headers.items()), reply.read()

    def login(self, profile=False, remember=False):
        payload = ({'name': 'Fiktiv admin', 'password': PROFILE_PASSWORD} if profile
                   else {'password': LAN_PASSWORD})
        if remember:
            payload['remember'] = True
        status, headers, body = self.request('/api/login', payload)
        self.assertEqual((status, json.loads(body)), (200, {'ok': True}))
        cookie = headers['Set-Cookie'].split(';', 1)[0]
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertIn('SameSite=Strict', headers['Set-Cookie'])
        self.assertIn('Max-Age=' + ('604800' if remember else '43200'), headers['Set-Cookie'])
        token = cookie.split('=', 1)[1]
        csrf = self.server.profiles.csrf(token) if profile else self.server.token
        return cookie, csrf, token

    def test_normal_lan_reload_works_and_restart_does_not_restore_plain_login(self):
        self.start()
        cookie, csrf, token = self.login()
        self.assertIn(b'app.js', self.request('/', cookie=cookie)[2])
        self.assertEqual(self.request('/api/state', cookie=cookie, csrf=csrf)[0], 200)
        self.assertFalse((Path(self.tmp.name) / 'login-remembered-access.json').exists())
        self.stop()
        self.start()
        self.assertIn(b'loginForm', self.request('/', cookie=cookie)[2])
        self.assertEqual(self.request('/api/state', cookie=cookie, csrf=self.server.token)[0], 401)

    def test_opted_in_lan_reload_restart_logout_and_expiry(self):
        self.start()
        cookie, csrf, token = self.login(remember=True)
        path = Path(self.tmp.name) / 'login-remembered-access.json'
        self.assertTrue(path.exists())
        text = path.read_text()
        self.assertNotIn(token, text)
        self.assertNotIn(LAN_PASSWORD, text)
        if os.name != 'nt':
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertIn(b'app.js', self.request('/', cookie=cookie)[2])
        self.stop()
        self.start()
        self.assertIn(b'app.js', self.request('/', cookie=cookie)[2])
        self.assertEqual(self.request('/api/state', cookie=cookie, csrf=self.server.token)[0], 200)
        self.assertEqual(self.request('/api/logout', {}, cookie, self.server.token)[0], 200)
        self.assertIn(b'loginForm', self.request('/', cookie=cookie)[2])
        self.stop()
        self.start()
        self.assertEqual(self.request('/api/state', cookie=cookie, csrf=self.server.token)[0], 401)
        cookie, csrf, token = self.login(remember=True)
        record = self.server.access.remembered.records
        for item in record.values():
            item['until'] = self.server.access.remembered.clock() - 1
        self.server.access.remembered._replace(record)
        self.stop()
        self.start()
        self.assertIn(b'loginForm', self.request('/', cookie=cookie)[2])

    def test_profile_remembered_session_rechecks_csrf_rights_and_reset(self):
        accounts = ProfileAccounts(self.tmp.name)
        admin_id = accounts.bootstrap('Fiktiv admin', PROFILE_PASSWORD)
        self.start()
        cookie, csrf, token = self.login(profile=True, remember=True)
        self.assertIn('ltm_profiles=', cookie)
        self.assertIn(b'app.js', self.request('/', cookie=cookie)[2])
        self.stop()
        self.start()
        self.assertIn(b'app.js', self.request('/', cookie=cookie)[2])
        self.assertEqual(self.request('/api/state', cookie=cookie, csrf=csrf)[0], 403)
        fresh_csrf = self.server.profiles.csrf(token)
        self.assertEqual(self.request('/api/state', cookie=cookie, csrf=fresh_csrf)[0], 200)
        self.assertEqual(self.request('/api/profiles/admin', cookie=cookie, csrf=fresh_csrf)[0], 200)
        profile = self.server.accounts.overview(token)['users'][0]
        self.server.accounts.save_user(token, profile['name'], profile['roles'],
                                       admin_id, password='Fiktiv-ny-kode-12345')
        self.assertEqual(self.request('/api/state', cookie=cookie, csrf=fresh_csrf)[0], 401)
        self.stop()
        self.start()
        self.assertIn(b'loginForm', self.request('/', cookie=cookie)[2])
        record_text = (Path(self.tmp.name) / 'login-remembered-profiles.json').read_text()
        self.assertNotIn(token, record_text)
        self.assertNotIn(PROFILE_PASSWORD, record_text)

    def test_profile_logout_and_denied_rights_survive_restart(self):
        accounts = ProfileAccounts(self.tmp.name)
        accounts.bootstrap('Fiktiv admin', PROFILE_PASSWORD)
        admin = accounts.login('Fiktiv admin', PROFILE_PASSWORD, 'fictional-admin')
        role = accounts.save_role(admin, 'Fiktiv læser', ['cards.view'])
        accounts.save_user(admin, 'Fiktiv læser', [role], password='Fiktiv-laeser-12345')
        self.start()
        payload = {'name': 'Fiktiv læser', 'password': 'Fiktiv-laeser-12345',
                   'remember': True}
        status, headers, _ = self.request('/api/login', payload)
        self.assertEqual(status, 200)
        cookie = headers['Set-Cookie'].split(';')[0]
        token = cookie.split('=', 1)[1]
        self.assertEqual(self.request('/api/profiles/admin',
                                      cookie=cookie, csrf=self.server.profiles.csrf(token))[0], 403)
        self.stop()
        self.start()
        csrf = self.server.profiles.csrf(token)
        self.assertEqual(self.request('/api/profiles/admin', cookie=cookie, csrf=csrf)[0], 403)
        self.assertEqual(self.request('/api/logout', {}, cookie, csrf)[0], 200)
        self.stop()
        self.start()
        self.assertIn(b'loginForm', self.request('/', cookie=cookie)[2])


class RememberedLoginLifetimeTests(unittest.TestCase):
    def test_profile_expiry_is_absolute_and_plain_sessions_remain_twelve_hours(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {'LTM_CHANNEL': 'stable'}):
            now = [1000]
            account = lambda: ProfileAccounts(root, clock=lambda: now[0],
                                              wall_clock=lambda: now[0])
            first = account()
            first.bootstrap('Fiktiv admin', PROFILE_PASSWORD)
            plain = first.login('Fiktiv admin', PROFILE_PASSWORD, 'fictional-client')
            remembered = first.login('Fiktiv admin', PROFILE_PASSWORD, 'fictional-client',
                                     remember=True)
            self.assertEqual(first.sessions[plain]['expires'], now[0] + SESSION_LIFETIME)
            self.assertEqual(first.sessions[remembered]['expires'], now[0] + REMEMBER_LIFETIME)
            second = account()
            with self.assertRaises(PermissionError):
                second.authorize(plain, 'cards.view')
            self.assertTrue(second.authorize(remembered, 'cards.view'))
            now[0] += REMEMBER_LIFETIME + 1
            with self.assertRaises(PermissionError):
                second.authorize(remembered, 'cards.view')

    def test_lan_rotated_password_cannot_resurrect_old_lease(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {'LTM_CHANNEL': 'stable'}):
            first = Access(root, LAN_PASSWORD)
            token = first.login(LAN_PASSWORD, 'fictional-client', remember=True)
            self.assertTrue(Access(root, LAN_PASSWORD).valid('distrikt_session=' + token))
            self.assertFalse(Access(root, 'Fiktiv-anden-kode-12345').valid('distrikt_session=' + token))
            self.assertFalse(Access(root, LAN_PASSWORD).valid('distrikt_session=' + token))

    def test_stable_and_beta_persistent_tokens_are_isolated_even_if_root_is_shared(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {'LTM_CHANNEL': 'stable'}):
                stable = Access(root, LAN_PASSWORD)
                token = stable.login(LAN_PASSWORD, 'fictional-client', remember=True)
                self.assertTrue(stable.valid('distrikt_session=' + token))
            with patch.dict(os.environ, {'LTM_CHANNEL': 'beta'}):
                beta = Access(root, LAN_PASSWORD)
                self.assertFalse(beta.valid('distrikt_beta_session=' + token))
                beta_token = beta.login(LAN_PASSWORD, 'fictional-client', remember=True)
                self.assertTrue(beta.valid('distrikt_beta_session=' + beta_token))
            self.assertFalse(stable.valid('distrikt_beta_session=' + beta_token))
            with patch.dict(os.environ, {'LTM_CHANNEL': 'stable'}):
                self.assertFalse(Access(root, LAN_PASSWORD).valid('distrikt_session=' + beta_token))
                self.assertTrue(Access(root, LAN_PASSWORD).valid('distrikt_session=' + token))


if __name__ == '__main__':
    unittest.main()
