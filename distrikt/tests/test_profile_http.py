"""Actual loopback HTTP with fictional accounts; no external connections."""
import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from profile_accounts import ProfileAccounts
from profile_http import ProfilePreviewServer
from store import Store

class ProfileHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.accounts=ProfileAccounts(self.tmp.name)
        self.accounts.bootstrap('Fiktiv admin','Fiktiv-password-123')
        self.store=Store(self.tmp.name);self.server=ProfilePreviewServer(self.accounts,self.store)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(5);self.store.close();self.tmp.cleanup()
    def request(self,path,data=None,cookie='',csrf='',origin=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        headers={'Cookie':cookie,'X-LTM-CSRF':csrf}
        if data is not None:headers.update({'Content-Type':'application/json','Origin':origin or self.server.origin})
        connection.request('POST' if data is not None else 'GET',path,json.dumps(data) if data is not None else None,headers)
        response=connection.getresponse();raw=response.read();result=(response.status,dict(response.getheaders()),json.loads(raw) if response.getheader('Content-Type','').startswith('application/json') else raw)
        connection.close();return result
    def login(self,name='Fiktiv admin',password='Fiktiv-password-123'):
        status,headers,_=self.request('/api/profiles/login',{'name':name,'password':password});self.assertEqual(status,200)
        self.assertIn('HttpOnly',headers['Set-Cookie']);self.assertIn('SameSite=Strict',headers['Set-Cookie'])
        cookie=headers['Set-Cookie'].split(';')[0]
        status,_,session=self.request('/api/profiles/session',cookie=cookie);self.assertEqual(status,200)
        return cookie,session['csrf']
    def test_admin_creates_role_user_and_restricted_session_cannot_bypass(self):
        cookie,csrf=self.login()
        status,_,role=self.request('/api/profiles/roles/save',{'name':'Kortlæser','permissions':['cards.view']},cookie,csrf);self.assertEqual(status,200)
        status,_,user=self.request('/api/profiles/users/save',{'name':'Fiktiv læser','roles':[role['id']],'password':'Fiktiv-password-456'},cookie,csrf);self.assertEqual(status,200)
        reader,reader_csrf=self.login('Fiktiv læser','Fiktiv-password-456')
        status,_,session=self.request('/api/profiles/session',cookie=reader);self.assertEqual(set(session['overview']['records']),{'cards'})
        self.assertNotIn('hash',str(session));self.assertNotIn('password',str(session))
        self.assertEqual(self.request('/api/profiles/admin',cookie=reader)[0],403)
        self.assertEqual(self.request('/api/profiles/roles/save',{'name':'Hæv rettigheder','permissions':['users.manage']},reader,reader_csrf)[0],403)
        self.assertEqual(self.request('/api/state',cookie=reader)[0],404)
        self.assertEqual(self.request('/api/export/backup',cookie=reader)[0],404)
        status,_,_=self.request('/api/profiles/users/save',{'id':user['id'],'name':'Fiktiv læser','roles':[role['id']],'disabled':True},cookie,csrf);self.assertEqual(status,200)
        self.assertEqual(self.request('/api/profiles/session',cookie=reader)[0],403)
    def test_csrf_origin_and_logout(self):
        cookie,csrf=self.login();other,other_csrf=self.login()
        data={'name':'Denied','permissions':['cards.view']}
        self.assertEqual(self.request('/api/profiles/roles/save',data,cookie,'')[0],403)
        self.assertEqual(self.request('/api/profiles/roles/save',data,cookie,other_csrf)[0],403)
        self.assertEqual(self.request('/api/profiles/roles/save',data,cookie,csrf,'http://evil.invalid')[0],403)
        self.assertEqual(self.request('/api/profiles/logout',{},cookie,csrf)[0],200)
        self.assertEqual(self.request('/api/profiles/session',cookie=cookie)[0],403)
        self.assertEqual(self.request('/api/profiles/session',cookie=other)[0],200)
    def test_anonymous_access_static_page_and_no_bootstrap(self):
        self.assertEqual(self.request('/api/profiles/admin')[0],403)
        self.assertEqual(self.request('/api/profiles/session')[0],403)
        status,headers,page=self.request('/');self.assertEqual(status,200)
        self.assertIn(b'profile-preview.js',page);self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertEqual(self.request('/api/profiles/bootstrap',{'name':'Intruder','password':'Fiktiv-password-123'})[0],403)
    def test_last_admin_protection_through_http(self):
        cookie,csrf=self.login();_,_,admin=self.request('/api/profiles/admin',cookie=cookie)
        user=admin['users'][0]
        self.assertEqual(self.request('/api/profiles/users/save',{**user,'disabled':True},cookie,csrf)[0],400)
        self.assertEqual(self.request('/api/profiles/session',cookie=cookie)[0],200)

if __name__=='__main__':unittest.main()
