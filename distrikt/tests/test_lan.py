import http.cookiejar
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from server import Server, acquire_lock
from access import Access, private_client

class LANTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
        self.server=Server(('127.0.0.1',0),self.s,access_host='192.168.1.77',password='Fiktiv-kode-12345')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.cookies=http.cookiejar.CookieJar();self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.s.close();self.temp.cleanup()
    def req(self,path,data=None,headers=None,client=None):
        h={'Host':'192.168.1.77:'+str(self.server.server_port)}
        if data is not None:h.update({'Content-Type':'application/json','X-Distrikt-Token':self.server.token})
        h.update(headers or {})
        req=urllib.request.Request(self.server.origin+path,json.dumps(data).encode() if data is not None else None,h)
        return (client or self.client).open(req,timeout=5)
    def login(self):return self.req('/api/login',{'password':'Fiktiv-kode-12345'})
    def test_ip_binding_never_needs_reverse_dns(self):
        with patch('socket.getfqdn',side_effect=RuntimeError('DNS must not be needed')):
            local=Server(('127.0.0.1',0),self.s)
        try:
            self.assertEqual(local.server_name,'127.0.0.1')
            self.assertGreater(local.server_port,0)
        finally:local.server_close()
    def test_login_page_does_not_expose_token(self):
        with self.req('/') as r:
            html=r.read().decode();self.assertIn('loginForm',html);self.assertNotIn(self.server.token,html)
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/api/state',headers={'X-Distrikt-Token':self.server.token})
        self.assertEqual(error.exception.code,401)
    def test_login_cookie_required_in_addition_to_token(self):
        with self.login() as r:
            cookie=r.headers['Set-Cookie'];self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie)
        with self.req('/') as r:
            html=r.read().decode();self.assertIn(self.server.token,html);self.assertIn('Log ud',html);self.assertNotIn('data-action="stop"',html)
        with self.req('/api/state',headers={'X-Distrikt-Token':self.server.token}) as r:self.assertEqual(json.load(r)['version'],'1.11.1')
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/api/state')
        self.assertEqual(error.exception.code,403)
    def test_wrong_password_and_foreign_origin_are_rejected(self):
        for data,headers in [({'password':'wrong'},{}),({'password':'Fiktiv-kode-12345'},{'Origin':'https://evil.example'})]:
            with self.assertRaises(urllib.error.HTTPError):self.req('/api/login',data,headers)
    def test_logout_revokes_session(self):
        self.login().close();self.req('/api/logout',{}).close()
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/state',headers={'X-Distrikt-Token':self.server.token})
    def test_no_ingress_or_proxy_trust(self):
        with self.assertRaises(urllib.error.HTTPError):self.req('/',headers={'Host':'ha.ui.nabu.casa'})
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/state',headers={'X-Forwarded-For':'127.0.0.1','X-Ingress-Path':'/api/hassio_ingress/x','X-Distrikt-Token':self.server.token})
        self.assertFalse(private_client('172.30.32.2'));self.assertFalse(private_client('8.8.8.8'));self.assertTrue(private_client('192.168.1.10'));self.assertTrue(private_client('10.8.0.2'))
    def test_server_cannot_be_stopped_from_ui(self):
        self.login().close()
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/shutdown',{})
    def test_credential_hash_and_lock(self):
        raw=(Path(self.temp.name)/'access.json').read_text();self.assertNotIn('Fiktiv-kode',raw)
        loaded=Access(self.temp.name);self.assertTrue(loaded.verify('Fiktiv-kode-12345'));self.assertFalse(loaded.verify('wrong'))
        path=Path(self.temp.name)/'test.lock';lock=acquire_lock(path)
        try:self.assertIsNotNone(lock);self.assertIsNone(acquire_lock(path))
        finally:lock.close()

    def test_front_qr_image_requires_lan_session(self):
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/card-qr.svg?card_id=fake')
        self.assertEqual(error.exception.code,401)
