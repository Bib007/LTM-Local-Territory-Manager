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
from server import Server, acquire_lock, VERSION
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
    def test_beta_reset_endpoint_requires_beta_login_token_and_idle_downloads(self):
        self.login().close();self.s.mutate('card.save',{'number':'FAKE','temporary':True})
        payload={'confirmation':'NULSTIL BETA','revision':self.s.revision}
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/api/beta/reset',payload)
        self.assertEqual(error.exception.code,404)
        self.assertEqual(len(self.s.state()['cards']),1)
        self.server.beta=True
        with self.req('/api/state',headers={'X-Distrikt-Token':self.server.token}) as response:self.assertTrue(json.load(response)['beta'])
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/api/beta/reset',payload,{'X-Distrikt-Token':'wrong'})
        self.assertEqual(error.exception.code,403)
        self.server.downloads.active='FAKE_DOWNLOAD'
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/api/beta/reset',payload)
        self.assertEqual(error.exception.code,400)
        self.server.downloads.active=None
        with self.req('/api/beta/reset',payload) as response:result=json.load(response)
        self.assertEqual(self.s.state()['cards'],[])
        with self.req('/api/restore/safety?name='+result['safety_backup'],headers={'X-Distrikt-Token':self.server.token}) as response:self.assertTrue(response.read().startswith(b'PK'))
        with self.req('/api/state',headers={'X-Distrikt-Token':self.server.token}) as response:self.assertEqual(response.status,200)
        self.req('/api/logout',{}).close()
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/api/beta/reset',payload)
        self.assertEqual(error.exception.code,401)

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
        with self.req('/api/state',headers={'X-Distrikt-Token':self.server.token}) as r:self.assertEqual(json.load(r)['version'],VERSION)
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/api/state')
        self.assertEqual(error.exception.code,403)
    def test_wrong_password_and_foreign_origin_are_rejected(self):
        for data,headers in [({'password':'wrong'},{}),({'password':'Fiktiv-kode-12345'},{'Origin':'https://evil.example'})]:
            with self.assertRaises(urllib.error.HTTPError):self.req('/api/login',data,headers)
    def test_logout_revokes_session(self):
        self.login().close();self.req('/api/logout',{}).close()
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/state',headers={'X-Distrikt-Token':self.server.token})
    def test_beta_and_stable_cookies_work_together_on_the_same_host(self):
        with tempfile.TemporaryDirectory() as folder:
            beta_store=Store(folder)
            with patch.dict('os.environ',{'LTM_CHANNEL':'beta'}):beta=Server(('127.0.0.1',0),beta_store,access_host='192.168.1.77',password='Fiktiv-beta-12345')
            thread=threading.Thread(target=beta.serve_forever,daemon=True);thread.start()
            def beta_req(path,data=None):
                headers={'Host':'192.168.1.77:'+str(beta.server_port),'X-Distrikt-Token':beta.token}
                if data is not None:headers['Content-Type']='application/json'
                return self.client.open(urllib.request.Request(beta.origin+path,json.dumps(data).encode() if data is not None else None,headers),timeout=5)
            try:
                with self.login() as response:self.assertIn('distrikt_session=',response.headers['Set-Cookie'])
                with beta_req('/api/login',{'password':'Fiktiv-beta-12345'}) as response:self.assertIn('distrikt_beta_session=',response.headers['Set-Cookie'])
                self.s.mutate('card.save',{'number':'120','temporary':True})
                with self.req('/api/state',headers={'X-Distrikt-Token':self.server.token}) as response:self.assertEqual(len(json.load(response)['cards']),1)
                with beta_req('/api/state') as response:self.assertEqual(json.load(response)['cards'],[])
                beta_store.mutate('card.save',{'number':'BETA-FAKE','temporary':True})
                with beta_req('/api/beta/reset',{'confirmation':'NULSTIL BETA','revision':beta_store.revision}) as response:self.assertEqual(response.status,200)
                self.assertEqual(beta_store.state()['cards'],[]);self.assertEqual(len(self.s.state()['cards']),1)
                with beta_req('/api/logout',{}) as response:self.assertIn('distrikt_beta_session=',response.headers['Set-Cookie'])
                with self.req('/api/state',headers={'X-Distrikt-Token':self.server.token}) as response:self.assertEqual(response.status,200)
                with self.assertRaises(urllib.error.HTTPError):beta_req('/api/state')
            finally:beta.shutdown();beta.server_close();thread.join();beta_store.close()
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

    def test_navigation_language_asset_keeps_lan_login_boundary(self):
        with self.req('/') as response:
            login=response.read().decode()
            self.assertIn('id="loginPassword"',login)
            self.assertIn('for="loginPassword"',login)
            self.assertIn('id="loginLanguage"',login)
            self.assertIn('src="/login.js"',login)
            self.assertNotIn('src="/i18n.js"',login)
        with self.req('/login.js') as response:
            self.assertIn(b'const LoginText=',response.read())
            self.assertEqual(response.headers['Cache-Control'],'no-store')
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/app.js')
        self.assertEqual(error.exception.code,401)
        with self.assertRaises(urllib.error.HTTPError) as error:self.req('/i18n.js')
        self.assertEqual(error.exception.code,401)
        self.login().close()
        with self.req('/i18n.js') as response:
            self.assertIn(b'const I18n=',response.read())
            self.assertEqual(response.headers['Cache-Control'],'no-store')
        with self.req('/brand-logo.svg') as response:
            self.assertEqual(response.headers['Content-Type'],'image/svg+xml')
            self.assertIn(b'Local Territory Manager',response.read())
        with self.req('/') as response:
            html=response.read().decode()
            self.assertIn('data-action="logout" data-ui="Log ud"',html)
            self.assertNotIn('data-action="stop"',html)
