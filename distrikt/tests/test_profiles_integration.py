"""The real server, temporary SQLite files, and fictional local accounts only."""
import concurrent.futures
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from server import Server
from store import Store
from profile_policy import GET,POST,PERMISSIONS
from profile_recovery import export_accounts,restore_accounts
from portable import snapshot

class ProfilesIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
        self.card=self.store.mutate('card.save',{'number':'F101','name':'Opdigtet kort','temporary':True})['id']
        self.note=self.store.mutate('note.save',{'text':'Opdigtet privat opgave','card_id':self.card})['id']
        self.server=Server(('127.0.0.1',0),self.store)
        self.server.accounts.bootstrap('Fiktiv admin','Fiktiv-password-123')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.admin=self.login('Fiktiv admin','Fiktiv-password-123')

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.store.close();self.temp.cleanup()

    def request(self,path,data=None,session=None,extra=None):
        headers={'Origin':self.server.origin}
        if session:headers.update(Cookie=session['cookie'],**{'X-Distrikt-Token':session['csrf']})
        if data is not None:headers['Content-Type']='application/json'
        headers.update(extra or {})
        req=urllib.request.Request(self.server.origin+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        return urllib.request.urlopen(req,timeout=10)

    def value(self,path,data=None,session=None):
        if path in ('/api/profiles/users/save','/api/profiles/roles/save') and 'edit_snapshot' not in data:
            data={**data,'edit_snapshot':self.value('/api/profiles/admin',session=session)['edit_snapshot']}
        with self.request(path,data,session) as response:return json.load(response)

    def login(self,name,password):
        with self.request('/api/login',{'name':name,'password':password}) as response:
            self.assertTrue(json.load(response)['ok']);cookie=response.headers['Set-Cookie'].split(';')[0]
        token=cookie.split('=',1)[1]
        return {'cookie':cookie,'csrf':self.server.profiles.csrf(token),'token':token}

    def reader(self,rights):
        role=self.value('/api/profiles/roles/save',{'name':'Fiktiv rolle','permissions':rights},self.admin)['id']
        user=self.value('/api/profiles/users/save',{'name':'Fiktiv bruger','password':'Fiktiv-password-456','roles':[role]},self.admin)['id']
        return self.login('Fiktiv bruger','Fiktiv-password-456'),role,user

    def state(self,session):return self.value('/api/state',session=session)

    def change(self,session,base,action,data):
        return self.value('/api/mutate',{'action':action,'data':data,'profile_snapshot':base['profile']['snapshot'],'include_state':True},session)

    def test_normal_app_login_and_every_sensitive_route_is_denied_to_card_reader(self):
        reader,_,_=self.reader(['cards.view']);state=self.state(reader)
        self.assertEqual(state['cards'][0]['name'],'Opdigtet kort')
        self.assertEqual(state['notes'],[]);self.assertEqual(state['ib'],[])
        for path in GET:
            if path in ('/api/state','/api/profiles/session','/api/profiles/conflicts'):continue
            with self.subTest(path=path),self.assertRaises(urllib.error.HTTPError) as error:self.request(path,session=reader)
            self.assertEqual(error.exception.code,403)
        for path in POST:
            if path in ('/api/logout','/api/profiles/heartbeat','/api/profiles/intro/complete','/api/profiles/conflicts/acknowledge','/api/mutate'):continue
            with self.subTest(path=path),self.assertRaises(urllib.error.HTTPError) as error:self.request(path,{},reader)
            self.assertEqual(error.exception.code,403)
        for action,data in [('card.save',{'id':self.card,'number':'bad'}),('delete',{'module':'cards','id':self.card}),('geo.token',{'token':'Fictional'}),('unknown.future.action',{})]:
            with self.subTest(action=action),self.assertRaises(urllib.error.HTTPError) as error:self.change(reader,state,action,data)
            self.assertEqual(error.exception.code,403)

    def test_management_permission_does_not_grant_data_or_backup(self):
        manager,_,_=self.reader(['users.manage'])
        state=self.state(manager)
        for name in ('cards','loans','publishers','notes','ib','visits','completions','recovery'):self.assertEqual(state[name],[])
        self.assertNotIn('Opdigtet',json.dumps(state))
        self.assertTrue(self.value('/api/profiles/admin',session=manager)['users'])
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/export/backup',session=manager)
        self.assertEqual(error.exception.code,403)

    def test_two_real_http_sessions_merge_independent_card_changes_and_keep_conflicts(self):
        second=self.login('Fiktiv admin','Fiktiv-password-123')
        a=self.state(self.admin);b=self.state(second);initial=a['cards'][0]
        barrier=threading.Barrier(2)
        def save(session,base,changes):
            barrier.wait();return self.change(session,base,'card.save',{**initial,**changes})
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            futures=[pool.submit(save,self.admin,a,{'name':'Første rettelse'}),pool.submit(save,second,b,{'kind':'By'})]
            for f in futures:f.result()
        saved=self.store.require('cards',self.card)
        self.assertEqual((saved['name'],saved['kind']),('Første rettelse','By'))
        self.assertEqual(self.value('/api/profiles/conflicts',session=second),[])
        a=self.state(self.admin);b=self.state(second);current=a['cards'][0]
        self.change(self.admin,a,'card.save',{**current,'name':'Forslag A'})
        result=self.change(second,b,'card.save',{**current,'name':'Forslag B'})
        self.assertTrue(self.store.require('cards',self.card)['front_revision'])
        self.assertEqual(result['state']['profile']['conflicts'],1)
        rows=self.value('/api/profiles/conflicts',session=second)
        self.assertEqual((rows[0]['base']['value'],rows[0]['saved']['value'],rows[0]['incoming']['value']),('Første rettelse','Forslag A','Forslag B'))
        self.assertTrue(self.value('/api/profiles/conflicts/acknowledge',{'id':rows[0]['id']},second)['changed'])
        self.assertEqual(self.value('/api/profiles/conflicts',session=second),[])
        self.assertEqual(self.store.require('cards',self.card)['name'],'Forslag B')

    def test_conflict_failure_rolls_back_normal_write_and_its_activity(self):
        second=self.login('Fiktiv admin','Fiktiv-password-123');a=self.state(self.admin);b=self.state(second)
        self.change(self.admin,a,'note.save',{'id':self.note,'card_id':self.card,'text':'Første'})
        before=list(self.store.activity());original=self.store.put
        def fail(module,row):
            if row.get('entity')=='edit-conflict':raise OSError('Fictional disk failure')
            return original(module,row)
        with patch.object(self.store,'put',side_effect=fail):
            with self.assertRaises(urllib.error.HTTPError) as error:self.change(second,b,'note.save',{'id':self.note,'card_id':self.card,'text':'Anden'})
        self.assertEqual(error.exception.code,500)
        self.assertEqual(self.store.require('notes',self.note)['text'],'Første');self.assertEqual(self.store.activity(),before)
        result=self.change(second,b,'note.save',{'id':self.note,'card_id':self.card,'text':'Anden'})
        self.assertEqual(result['state']['profile']['conflicts'],1)

    def test_stale_unchanged_number_is_not_revalidated_as_a_new_number(self):
        second=self.login('Fiktiv admin','Fiktiv-password-123');a=self.state(self.admin);b=self.state(second)
        self.change(self.admin,a,'card.save',{**a['cards'][0],'number':'F102'})
        self.store.mutate('card.save',{'number':'F101','temporary':True})
        result=self.change(second,b,'card.save',{**b['cards'][0],'name':'Fiktiv samtidig rettelse'})
        saved=self.store.require('cards',self.card)
        self.assertEqual((saved['number'],saved['name']),('F102','Fiktiv samtidig rettelse'))
        self.assertEqual(result['state']['profile']['conflicts'],0)

    def test_snapshot_capacity_failure_cannot_commit_an_unacknowledgeable_write(self):
        state=self.state(self.admin);before=self.store.require('cards',self.card)
        self.server.profiles.bases.capacity=len(self.server.profiles.bases._items)
        with self.assertRaises(urllib.error.HTTPError):self.change(self.admin,state,'card.save',{**state['cards'][0],'name':'Må ikke gemmes'})
        self.assertEqual(self.store.require('cards',self.card),before)

    def test_account_admin_forms_merge_and_preserve_access_conflicts_without_granting_them(self):
        reader,role,user=self.reader(['cards.view'])
        second=self.login('Fiktiv admin','Fiktiv-password-123')
        a=self.value('/api/profiles/admin',session=self.admin);b=self.value('/api/profiles/admin',session=second)
        self.value('/api/profiles/roles/save',{'id':role,'name':'Nyt fiktivt rollenavn','permissions':['cards.view'],'edit_snapshot':a['edit_snapshot']},self.admin)
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':['cards.view','notes.view'],'edit_snapshot':b['edit_snapshot']},second)
        self.assertEqual(self.server.accounts.data['roles'][role]['name'],'Nyt fiktivt rollenavn')
        self.assertIn('notes.view',self.server.accounts.data['roles'][role]['permissions'])
        a=self.value('/api/profiles/admin',session=self.admin);b=self.value('/api/profiles/admin',session=second)
        for session,base,rights in [(self.admin,a,['cards.view']), (second,b,['cards.view','ib.view'])]:
            self.value('/api/profiles/roles/save',{'id':role,'name':'Nyt fiktivt rollenavn','permissions':rights,'edit_snapshot':base['edit_snapshot']},session)
        self.assertEqual(self.server.accounts.data['roles'][role]['permissions'],['cards.view'])
        rows=self.value('/api/profiles/conflicts',session=self.admin)
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['module'],'roles')
        self.assertEqual(self.value('/api/profiles/conflicts',session=reader),[])
        self.value('/api/profiles/conflicts/acknowledge',{'id':rows[0]['id']},self.admin)
        self.assertEqual(self.value('/api/profiles/conflicts',session=self.admin),[])

    def test_conflicting_password_resets_never_return_credential_material(self):
        _,role,user=self.reader(['cards.view']);second=self.login('Fiktiv admin','Fiktiv-password-123')
        a=self.value('/api/profiles/admin',session=self.admin);b=self.value('/api/profiles/admin',session=second)
        for session,base,password in [(self.admin,a,'Fiktiv-password-AAA'),(second,b,'Fiktiv-password-BBB')]:
            self.value('/api/profiles/users/save',{'id':user,'name':'Fiktiv bruger','roles':[role],'password':password,'edit_snapshot':base['edit_snapshot']},session)
        rows=self.value('/api/profiles/conflicts',session=self.admin)
        self.assertEqual(rows[0]['field'],'credential')
        public=json.dumps(rows)
        private=self.server.accounts.data['users'][user]
        self.assertNotIn(private['hash'],public);self.assertNotIn(private['salt'],public)
        self.login('Fiktiv bruger','Fiktiv-password-AAA')
        with self.assertRaises(urllib.error.HTTPError):self.login('Fiktiv bruger','Fiktiv-password-BBB')

    def test_session_bound_bases_and_csrf_and_current_rights(self):
        reader,role,user=self.reader(['cards.view','cards.edit'])
        other=self.login('Fiktiv bruger','Fiktiv-password-456');base=self.state(reader)
        with self.assertRaises(urllib.error.HTTPError) as error:self.change(other,base,'card.save',base['cards'][0])
        self.assertEqual(error.exception.code,400)
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/state',session=reader,extra={'X-Distrikt-Token':self.admin['csrf']})
        self.assertEqual(error.exception.code,403)
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':['cards.view']},self.admin)
        with self.assertRaises(urllib.error.HTTPError) as error:self.change(reader,base,'card.save',{**base['cards'][0],'name':'Afvist'})
        self.assertEqual(error.exception.code,403)
        self.value('/api/profiles/users/save',{'id':user,'name':'Fiktiv bruger','roles':[role],'disabled':True},self.admin)
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/state',session=reader)
        self.assertEqual(error.exception.code,401)

    def test_real_backup_keeps_conflicts_but_not_accounts_and_data_restore_keeps_login(self):
        before=self.state(self.admin)
        with self.request('/api/export/backup',session=self.admin) as response:payload=response.read()
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:self.assertNotIn('profiles.json',archive.namelist())
        preview=self.server.restores.preview(payload)
        self.server.restores.apply(preview['token'])
        self.assertEqual(self.state(self.admin)['profile']['user'],before['profile']['user'])
        path=Path(self.temp.name)/'fictional-account-backup.json'
        export_accounts(self.server.accounts,path)
        ident=self.server.accounts.recover_admin('Fiktiv gendannelse','Fiktiv-password-789')
        self.assertIn(ident,self.server.accounts.data['users'])
        restore_accounts(self.server.accounts,path)
        self.assertNotIn(ident,self.server.accounts.data['users'])
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/state',session=self.admin)
        self.admin=self.login('Fiktiv admin','Fiktiv-password-123')
        self.assertEqual(len(self.state(self.admin)['cards']),1)

class ProfileActivationTests(unittest.TestCase):
    def test_existing_lan_login_must_authorize_activation_and_data_is_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);store.mutate('card.save',{'number':'F201','temporary':True})
            server=Server(('127.0.0.1',0),store,access_host='127.0.0.1',password='Fiktiv-old-password')
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(path,data,cookie=''):
                return urllib.request.urlopen(urllib.request.Request(server.origin+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json','Origin':server.origin,'Cookie':cookie,'X-Distrikt-Token':server.token}),timeout=10)
            try:
                data={'name':'Fiktiv ejer','password':'Fiktiv-new-password','confirmation':'AKTIVÉR PROFILER'}
                with self.assertRaises(urllib.error.HTTPError):request('/api/profiles/activate',data)
                with request('/api/login',{'password':'Fiktiv-old-password'}) as response:cookie=response.headers['Set-Cookie'].split(';')[0]
                with request('/api/profiles/activate',data,cookie) as response:self.assertTrue(json.load(response)['ok'])
                self.assertEqual(store.all('cards')[0]['number'],'F201')
                with self.assertRaises(urllib.error.HTTPError):request('/api/login',{'password':'Fiktiv-old-password'})
                with request('/api/login',{'name':'Fiktiv ejer','password':'Fiktiv-new-password'}) as response:self.assertTrue(json.load(response)['ok'])
            finally:server.shutdown();server.server_close();thread.join();store.close()

if __name__=='__main__':unittest.main()
