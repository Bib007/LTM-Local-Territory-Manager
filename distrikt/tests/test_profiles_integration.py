"""The real server, temporary SQLite files, and fictional local accounts only."""
import concurrent.futures
import io
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from server import Server,stop_running
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

    def test_incomplete_login_body_does_not_hold_global_account_lock(self):
        entered=threading.Event();handler_class=self.server.RequestHandlerClass
        original_setup=handler_class.setup
        def setup(handler):
            original_setup(handler);stream=handler.rfile
            class ObservedReader:
                def read(self,length=-1):entered.set();return stream.read(length)
                def __getattr__(self,name):return getattr(stream,name)
            handler.rfile=ObservedReader()
        with patch.object(handler_class,'setup',setup):
            connection=socket.create_connection(self.server.server_address,timeout=2)
            try:
                request=('POST /api/login HTTP/1.0\r\nHost: '+self.server.origin.split('://')[1]+'\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{').encode()
                connection.sendall(request);self.assertTrue(entered.wait(2))
                self.assertEqual(self.state(self.admin)['cards'][0]['id'],self.card)
                connection.sendall(b'}');connection.recv(4096)
            finally:connection.close()

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

    def test_boundary_report_respects_report_geo_and_ib_permissions(self):
        self.store.mutate('geo.main.save',{'points':[[9.99,54.99],[10.01,54.99],[10.01,55.01],[9.99,55.01]]})
        self.store.mutate('geo.manual',{'road':'Fiktiv vej','number':'1','postcode':'9999','lng':10,'lat':55})
        address=self.store.geo_state()['addresses'][0]['id']
        card=self.store.mutate('geo.assign',{'number':'120','address_ids':[address]})['id']
        self.store.mutate('ib.save',{'card_id':card,'road':'Fiktiv vej','number':'1','address_id':address,'date':'2026-01-01'})
        self.assertEqual(self.state(self.admin)['boundary_report'],{'visits':1,'ib':1})
        reader,role,_=self.reader(['reports.view'])
        self.assertNotIn('boundary_report',self.state(reader))
        rights=['reports.view','cards.view','geo.view']
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':rights},self.admin)
        self.assertEqual(self.state(reader)['boundary_report'],{'visits':1})
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':rights+['ib.view']},self.admin)
        self.assertEqual(self.state(reader)['boundary_report'],{'visits':1,'ib':1})

    def test_group_fields_merge_under_profiles_and_import_requires_current_rights(self):
        ident=self.store.mutate('publisher.save',{'name':'Fiktiv gruppeperson'})['id']
        second=self.login('Fiktiv admin','Fiktiv-password-123')
        a=self.state(self.admin);b=self.state(second)
        self.change(self.admin,a,'publisher.save',{'id':ident,'name':'Fiktiv nyt navn','group':'','group_role':'','pioneer':False})
        result=self.change(second,b,'publisher.save',{'id':ident,'name':'Fiktiv gruppeperson','group':'G01','group_role':'assistant','pioneer':True})
        person=self.store.require('publishers',ident)
        self.assertEqual(person['name'],'Fiktiv nyt navn');self.assertEqual(person['group'],'G01');self.assertTrue(person['pioneer'])
        self.assertEqual(self.value('/api/profiles/conflicts',session=self.admin),[])
        reader,role,user=self.reader(['publishers.view','publishers.manage'])
        state=self.state(reader);self.assertEqual(state['publishers'][0]['group_role'],'assistant')
        with self.request('/api/setup/publisher-template.xlsx',session=reader) as response:self.assertTrue(response.read().startswith(b'PK'))
        plan=self.change(reader,state,'setup.publisher-import.preview',{'name':'fiktiv.csv','content':'navn;tjenestegruppe\nFiktiv B;G02'})['result']
        role_value=next(r for r in self.value('/api/profiles/admin',session=self.admin)['roles'] if r['id']==role)
        self.value('/api/profiles/roles/save',{**role_value,'permissions':['publishers.view']},self.admin)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.change(reader,self.state(reader),'setup.publisher-import.apply',{'token':plan['token'],'confirm':'IMPORTÉR GRUPPER'})
        self.assertEqual(error.exception.code,403);self.assertEqual(len(self.store.all('publishers')),1)

    def test_different_group_edits_preserve_evidence_and_do_not_grant_account_access(self):
        ident=self.store.mutate('publisher.save',{'name':'Fiktiv gruppeperson','group':'G01'})['id']
        a=self.state(self.admin);second=self.login('Fiktiv admin','Fiktiv-password-123');b=self.state(second)
        self.change(self.admin,a,'publisher.save',{'id':ident,'name':'Fiktiv gruppeperson','group':'G02'})
        self.change(second,b,'publisher.save',{'id':ident,'name':'Fiktiv gruppeperson','group':'G03'})
        reviews=self.value('/api/profiles/conflicts',session=self.admin)
        rows=reviews['rows'] if isinstance(reviews,dict) else reviews
        row=next(r for r in rows if r['module']=='publishers' and r['field']=='group')
        self.assertEqual(row['base']['value'],'G01');self.assertEqual(row['saved']['value'],'G02');self.assertEqual(row['incoming']['value'],'G03')
        self.assertEqual(len(self.server.accounts.data['users']),1)

    def test_public_date_preview_requires_source_read_rights_and_is_read_only(self):
        import base64
        from test_publication_dates import plain_png
        from test_sharing import FakeDrive
        self.server.sharing.drive=FakeDrive()
        with self.store.transaction():
            card=self.store.require('cards',self.card);card['geo_polygon']=[[10,55],[10.1,55],[10.1,55.1]];self.store.put('cards',card)
        reader,_,_=self.reader(['cards.view','geo.view','sharing.manage'])
        with self.assertRaises(urllib.error.HTTPError) as error:self.value('/api/share/prepare',{'card_id':self.card},reader)
        self.assertEqual(error.exception.code,403)
        recipe=self.value('/api/share/prepare',{'card_id':self.card},self.admin);before=self.store.revision
        data={'card_id':self.card,'fingerprint':recipe['fingerprint'],'date_fingerprint':recipe['date_fingerprint'],'png':'data:image/png;base64,'+base64.b64encode(plain_png()).decode()}
        result=self.value('/api/share/date-preview',data,self.admin)
        self.assertTrue(result['png'].startswith('data:image/png;base64,'))
        self.assertEqual(self.store.revision,before);self.assertFalse(self.server.sharing.images.directory.exists())
        self.value('/api/share/publish',{**data,'png':result['png'],'render_revision':7,'date_updates':True},self.admin)
        self.assertTrue(self.store.require('maps','publication:'+self.card)['date_updates'])
        self.assertNotIn('Fiktiv admin',str(recipe))

    def test_normal_app_login_and_every_sensitive_route_is_denied_to_card_reader(self):
        reader,_,_=self.reader(['cards.view']);state=self.state(reader)
        self.assertEqual(state['cards'][0]['name'],'Opdigtet kort')
        self.assertEqual(state['notes'],[]);self.assertEqual(state['ib'],[])
        for path in GET:
            if not GET[path]:continue
            with self.subTest(path=path),self.assertRaises(urllib.error.HTTPError) as error:self.request(path,session=reader)
            self.assertEqual(error.exception.code,403)
        for path in POST:
            if not POST[path]:continue
            with self.subTest(path=path),self.assertRaises(urllib.error.HTTPError) as error:self.request(path,{},reader)
            self.assertEqual(error.exception.code,403)
        for action,data in [('card.save',{'id':self.card,'number':'bad'}),('delete',{'module':'cards','id':self.card}),('geo.token',{'token':'Fictional'}),('unknown.future.action',{})]:
            with self.subTest(action=action),self.assertRaises(urllib.error.HTTPError) as error:self.change(reader,state,action,data)
            self.assertEqual(error.exception.code,403)

    def test_runtime_test_uses_current_settings_permission_and_no_private_payload(self):
        from runtime_status import RuntimeStatus
        sent=[]
        self.server.runtime_status=RuntimeStatus(self.server.address_schedule,'fictional',True,enabled=True,token='fictional-secret',
            pressure=lambda:{'available':True,'high':False},transport=lambda *args:sent.append(args))
        self.server.runtime_status.publish()
        reader,role,_=self.reader(['settings.manage'])
        self.assertTrue(self.state(reader)['runtime_status']['available'])
        self.assertTrue(self.value('/api/runtime/test',{},reader)['ok'])
        self.assertEqual(sent[-1],('events/ltm_status_test',{'entity_id':'sensor.ltm_beta_drift'},'fictional-secret'))
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':['cards.view']},self.admin)
        self.assertNotIn('runtime_status',self.state(reader))
        for path,data in [('/api/runtime/status',None),('/api/runtime/test',{})]:
            with self.assertRaises(urllib.error.HTTPError) as error:self.request(path,data,reader)
            self.assertEqual(error.exception.code,403)
        self.assertEqual(len(sent),2,'Revoked access cannot send another event')

    def test_excel_ib_template_manual_import_and_postcode_merge_use_current_rights(self):
        with self.request('/api/setup/ib-template.xlsx',session=self.admin) as response:
            self.assertTrue(response.read().startswith(b'PK'))
        base=self.state(self.admin)
        preview=self.change(self.admin,base,'setup.ib.preview',{'content':'kortnummer;vejnavn;husnummer\nF101;Fiktiv vej;2'})['result']
        with self.assertRaises(urllib.error.HTTPError):self.change(self.admin,base,'setup.ib.apply',{'token':preview['token'],'confirm':'IMPORTÉR IB'})
        self.change(self.admin,self.state(self.admin),'setup.ib.apply',{'token':preview['token'],'confirm':'IMPORTÉR IB','acknowledge':True})
        other=self.login('Fiktiv admin','Fiktiv-password-123');initial=self.state(self.admin);other_initial=self.state(other);ib=initial['ib'][0]
        self.assertEqual(ib['missing_fields'],['postcode'])
        self.change(self.admin,initial,'ib.save',{**ib,'postcode':'9999'})
        self.change(other,other_initial,'ib.save',{**ib,'date':'2026-10-02','postcode':''})
        merged=self.state(self.admin);saved=merged['ib'][0]
        self.assertEqual((saved['postcode'],saved['date']),('9999','2026-10-02'))
        self.assertEqual(saved['missing_fields'],[]);self.assertEqual(merged['profile']['conflicts'],0)
        # Conflicting edits retain both postcodes and their true observed base.
        other_merged=self.state(other)
        self.change(self.admin,merged,'ib.save',{**saved,'postcode':'9998'})
        self.change(other,other_merged,'ib.save',{**saved,'postcode':'9997'})
        review=self.value('/api/profiles/conflicts',session=self.admin)
        self.assertTrue(any(r['field']=='postcode' for r in review))

    def test_management_permission_does_not_grant_data_or_backup(self):
        manager,_,_=self.reader(['users.manage'])
        state=self.state(manager)
        for name in ('cards','loans','publishers','notes','ib','visits','completions','recovery'):self.assertEqual(state[name],[])
        self.assertNotIn('Opdigtet',json.dumps(state))
        self.assertTrue(self.value('/api/profiles/admin',session=manager)['users'])
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/export/backup',session=manager)
        self.assertEqual(error.exception.code,403)

    def test_backup_notice_is_separate_from_settings_and_export_and_changes_in_session(self):
        reader,role,_=self.reader(['settings.manage'])
        state=self.state(reader)
        self.assertIsNone(state['backup_status']);self.assertIsNone(state['backup_last_day'])
        for key in ('last_backup','backup_snoozed_until','backup_history'):self.assertNotIn(key,state['settings'])
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':['backup.notify']},self.admin)
        state=self.state(reader)
        self.assertIsInstance(state['backup_status'],dict)
        self.assertEqual(state['cards'],[])
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/export/backup',session=reader)
        self.assertEqual(error.exception.code,403)
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':[]},self.admin)
        self.assertIsNone(self.state(reader)['backup_status'])

    def test_connection_and_sharing_permissions_expose_only_their_own_status(self):
        reader,role,_=self.reader(['connections.manage'])
        with patch.object(self.server.sharing,'status',return_value={'connected':True,'account':'Fiktiv konto','cards':[{'card_id':self.card,'number':'F101'}]}):
            self.assertEqual(self.value('/api/connections/drive',session=reader),{'connected':True,'account':'Fiktiv konto'})
            with self.assertRaises(urllib.error.HTTPError):self.request('/api/share/status',session=reader)
            self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':['sharing.manage','cards.view']},self.admin)
            status=self.value('/api/share/status',session=reader)
            self.assertNotIn('account',status);self.assertEqual(len(status['cards']),1)
            with self.assertRaises(urllib.error.HTTPError):self.request('/api/connections/drive',session=reader)

    def test_desktop_updater_stops_profiles_without_a_browser_session(self):
        # run.json is an OS-owner-only local file, not a profile/data credential.
        for path,headers in [('/api/shutdown',{'X-Distrikt-Token':'fictional-wrong-token'}),
                             ('/api/state',{'X-Distrikt-Token':self.server.token}),
                             ('/api/shutdown',{'X-Distrikt-Token':self.server.token,'Origin':'https://example.invalid'})]:
            with self.subTest(path=path,headers=tuple(headers)),self.assertRaises(urllib.error.HTTPError) as error:
                self.request(path,{} if path.endswith('shutdown') else None,extra=headers)
            self.assertIn(error.exception.code,(401,403))
        (self.store.root/'run.json').write_text(json.dumps({'url':self.server.origin,'token':self.server.token}))
        with patch.dict(os.environ,{'http_proxy':'http://127.0.0.1:1','HTTP_PROXY':'http://127.0.0.1:1','no_proxy':'','NO_PROXY':''}):
            self.assertTrue(stop_running(self.store.root))
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())

    def test_loan_manager_can_select_existing_name_but_cannot_create_publishers(self):
        publisher=self.store.mutate('publisher.save',{'name':'Fiktiv Forkynder'})['id']
        second_card=self.store.mutate('card.save',{'number':'F102','temporary':True})['id']
        reader,_,_=self.reader(['cards.view','loans.view','loans.manage','publishers.view'])
        base=self.state(reader)
        data={'card_id':self.card,'publisher_name':'  FIKTIV FORKYNDER  ','date':base['today'],'initial':True}
        self.change(reader,base,'loan.issue',data)
        self.assertEqual(self.store.active_loan(self.card)['publisher_id'],publisher)
        base=self.state(reader)
        with self.assertRaises(urllib.error.HTTPError) as error:self.change(reader,base,'loan.issue',{**data,'card_id':second_card,'publisher_name':'Fiktiv ny person'})
        self.assertEqual(error.exception.code,403)
        self.assertEqual(len(self.store.all('publishers')),1)
        self.change(reader,base,'loan.issue',{'card_id':second_card,'publisher_id':publisher,'date':base['today'],'initial':True})
        with self.assertRaises(urllib.error.HTTPError) as error:self.change(reader,self.state(reader),'loan.issue',data)
        self.assertEqual(error.exception.code,400)

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

    def make_card_conflict(self):
        second=self.login('Fiktiv admin','Fiktiv-password-123');a=self.state(self.admin);b=self.state(second)
        self.change(self.admin,a,'card.save',{**a['cards'][0],'name':'Fiktiv A'})
        self.change(second,b,'card.save',{**b['cards'][0],'name':'Fiktiv B'})
        return self.value('/api/profiles/conflicts',session=self.admin)[0]

    def test_choose_earlier_conflict_runs_normal_validation_and_keeps_all_evidence(self):
        row=self.make_card_conflict()
        data={'id':row['id'],'choice':'saved','review_snapshot':row['review_snapshot']}
        self.assertTrue(self.value('/api/profiles/conflicts/resolve',data,self.admin)['ok'])
        self.assertEqual(self.store.require('cards',self.card)['name'],'Fiktiv A')
        self.assertTrue(self.store.require('cards',self.card)['front_revision'])
        evidence=self.store.require('settings',row['id'])
        self.assertTrue(evidence['resolved']);self.assertEqual(evidence['selected'],'saved')
        self.assertEqual((evidence['base']['value'],evidence['saved']['value'],evidence['incoming']['value']),('Opdigtet kort','Fiktiv A','Fiktiv B'))
        self.assertEqual(self.value('/api/profiles/conflicts',session=self.admin),[])
        with self.assertRaises(urllib.error.HTTPError):self.value('/api/profiles/conflicts/resolve',data,self.admin)

    def test_conflict_choice_does_not_overwrite_a_later_change_or_other_session(self):
        row=self.make_card_conflict();data={'id':row['id'],'choice':'saved','review_snapshot':row['review_snapshot']}
        second=self.login('Fiktiv admin','Fiktiv-password-123')
        with self.assertRaises(urllib.error.HTTPError):self.value('/api/profiles/conflicts/resolve',data,second)
        base=self.state(self.admin);self.change(self.admin,base,'card.save',{**base['cards'][0],'name':'Fiktiv nyere'})
        with self.assertRaises(urllib.error.HTTPError) as error:self.value('/api/profiles/conflicts/resolve',data,self.admin)
        self.assertEqual(error.exception.code,400)
        self.assertEqual(self.store.require('cards',self.card)['name'],'Fiktiv nyere')
        self.assertFalse(self.store.require('settings',row['id'])['resolved'])

    def test_conflict_choice_rechecks_rights_and_ack_failure_rolls_back_the_choice(self):
        row=self.make_card_conflict();editor,role,_=self.reader(['cards.view','cards.edit'])
        edit=self.value('/api/profiles/conflicts',session=editor)[0]
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':['cards.view']},self.admin)
        with self.assertRaises(urllib.error.HTTPError) as error:self.value('/api/profiles/conflicts/resolve',{'id':edit['id'],'choice':'saved','review_snapshot':edit['review_snapshot']},editor)
        self.assertEqual(error.exception.code,403)
        before=list(self.store.activity());put=self.store.put
        def fail(module,value):
            if value.get('id')==row['id'] and value.get('resolved'):raise OSError('Fictional disk failure')
            return put(module,value)
        data={'id':row['id'],'choice':'saved','review_snapshot':row['review_snapshot']}
        with patch.object(self.store,'put',side_effect=fail),self.assertRaises(urllib.error.HTTPError):self.value('/api/profiles/conflicts/resolve',data,self.admin)
        self.assertEqual(self.store.require('cards',self.card)['name'],'Fiktiv B')
        self.assertEqual(self.store.activity(),before);self.assertFalse(self.store.require('settings',row['id'])['resolved'])
        self.value('/api/profiles/conflicts/resolve',data,self.admin)

    def test_account_backup_restore_has_password_preview_lease_and_keeps_territory_data(self):
        with self.request('/api/profiles/backup',session=self.admin) as response:
            backup=json.load(response);self.assertIn('attachment',response.headers['Content-Disposition'])
        self.assertEqual(backup['format'],'ltm-account-backup');self.assertNotIn('Fiktiv-password-123',json.dumps(backup))
        second=self.login('Fiktiv admin','Fiktiv-password-123')
        with self.assertRaises(urllib.error.HTTPError):self.value('/api/profiles/backup/preview',{'backup':backup,'password':'Fiktiv-forkert-password'},self.admin)
        preview=self.value('/api/profiles/backup/preview',{'backup':backup,'password':'Fiktiv-password-123'},self.admin)
        self.assertEqual((preview['users'],preview['roles']),(1,1))
        data={'snapshot':preview['snapshot'],'confirmation':'GENDAN KONTI'}
        with self.assertRaises(urllib.error.HTTPError):self.value('/api/profiles/backup/apply',data,second)
        self.value('/api/profiles/roles/save',{'name':'Fiktiv ekstra rolle','permissions':['cards.view']},self.admin)
        with self.assertRaises(urllib.error.HTTPError):self.value('/api/profiles/backup/apply',data,self.admin)
        preview=self.value('/api/profiles/backup/preview',{'backup':backup,'password':'Fiktiv-password-123'},self.admin)
        with self.assertRaises(urllib.error.HTTPError):self.value('/api/profiles/backup/apply',{'snapshot':preview['snapshot'],'confirmation':'Forkert'},self.admin)
        result=self.value('/api/profiles/backup/apply',{'snapshot':preview['snapshot'],'confirmation':'GENDAN KONTI'},self.admin)
        self.assertTrue(result['login_required'])
        for session in (self.admin,second):
            with self.assertRaises(urllib.error.HTTPError):self.state(session)
        self.admin=self.login('Fiktiv admin','Fiktiv-password-123')
        self.assertEqual(len(self.server.accounts.data['roles']),1)
        self.assertEqual(self.state(self.admin)['cards'][0]['number'],'F101')
        self.assertEqual(len(list(self.store.root.glob('accounts-before-restore-*.json'))),1)

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

    def test_geographic_save_preserves_an_independent_color_and_boundary(self):
        addresses=[{'id':'fictional-'+str(i),'road':'Fiktivvej','number':str(i),'postcode':'9999','lng':10+i*.001,'lat':55,'count':1} for i in (1,2)]
        self.store.mutate('geo.import',{'records':addresses,'source':'Fictional test'})
        polygon=[[10,54.99],[10.02,54.99],[10.02,55.02],[10,55.02]]
        self.store.mutate('geo.assign',{'card_id':self.card,'address_ids':['fictional-1'],'polygon':polygon,'map_color':'#123456'})
        second=self.login('Fiktiv admin','Fiktiv-password-123');a=self.state(self.admin);b=self.state(second)
        self.change(self.admin,a,'card.color',{'card_id':self.card,'map_color':'#abcdef'})
        a=self.state(self.admin);new_polygon=[[9.99,54.99],[10.02,54.99],[10.02,55.03],[9.99,55.03]]
        self.change(self.admin,a,'geo.boundary',{'card_id':self.card,'polygon':new_polygon})
        result=self.change(second,b,'geo.assign',{'card_id':self.card,'address_ids':['fictional-1','fictional-2'],'polygon':polygon,'map_color':'#123456'})
        actual=self.store.require('cards',self.card)
        self.assertEqual(actual['map_color'],'#abcdef');self.assertEqual(actual['geo_polygon'],new_polygon)
        self.assertEqual(set(actual['address_ids']),{'fictional-1','fictional-2'})
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
        self.value('/api/profiles/conflicts/resolve',{'id':rows[0]['id'],'choice':'incoming','review_snapshot':rows[0]['review_snapshot']},self.admin)
        self.login('Fiktiv bruger','Fiktiv-password-BBB')
        with self.assertRaises(urllib.error.HTTPError):self.login('Fiktiv bruger','Fiktiv-password-AAA')

    def test_conflict_choice_cannot_remove_the_last_administrator(self):
        second=self.login('Fiktiv admin','Fiktiv-password-123')
        a=self.value('/api/profiles/admin',session=self.admin);b=self.value('/api/profiles/admin',session=second)
        role=a['roles'][0]['id']
        for session,base,rights in [(self.admin,a,['users.manage','cards.view']),(second,b,['cards.view'])]:
            self.value('/api/profiles/roles/save',{'id':role,'name':'Administrator','permissions':rights,'edit_snapshot':base['edit_snapshot']},session)
        row=self.value('/api/profiles/conflicts',session=self.admin)[0]
        before=self.server.accounts.path.read_bytes()
        with self.assertRaises(urllib.error.HTTPError):self.value('/api/profiles/conflicts/resolve',{'id':row['id'],'choice':'incoming','review_snapshot':row['review_snapshot']},self.admin)
        self.assertEqual(self.server.accounts.path.read_bytes(),before)
        self.assertTrue(self.value('/api/profiles/admin',session=self.admin)['users'])

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

    def assign_task(self,owner,before=None,**extra):
        return self.change(self.admin,self.state(self.admin),'note.save',{'id':self.note,'card_id':self.card,'text':'Fictional assigned task','assignee_id':owner,'assignee_before':before,**extra})

    def test_task_ownership_directory_and_private_self_label(self):
        session,role,user=self.reader(['cards.view','notes.view','notes.edit'])
        self.assign_task(user)
        admin=self.state(self.admin)
        self.assertTrue(all(set(u)=={'id','name'} for u in admin['task_users']))
        own=self.state(session);note=next(n for n in own['notes'] if n['id']==self.note)
        self.assertTrue(note['assigned']);self.assertTrue(note['assignee_self'])
        self.assertNotIn('assignee_id',note);self.assertNotIn('task_users',own)
        self.assertNotIn('users.manage',own['profile']['permissions'])
        self.assertEqual(own['loans'],[]);self.assertEqual(own['ib'],[])
        # Another reader may know that the task is assigned, not who owns it.
        other_id=self.server.accounts.save_user(self.admin['token'],'Fictional other',[role],password='Fictional-password-789')
        other=self.login('Fictional other','Fictional-password-789')
        state=self.state(other);other_note=next(n for n in state['notes'] if n['id']==self.note)
        self.assertTrue(other_note['assigned']);self.assertFalse(other_note['assignee_self'])
        self.assertNotIn(user,json.dumps(state));self.assertNotIn('Fiktiv bruger',json.dumps(state))

    def test_task_ownership_rejects_unauthorized_and_invalid_assignments(self):
        session,role,user=self.reader(['cards.view','notes.view','notes.edit'])
        revision=self.store.revision
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.change(session,self.state(session),'note.save',{'id':self.note,'card_id':self.card,'text':'Forbidden','assignee_id':user,'assignee_before':None})
        self.assertEqual(error.exception.code,403);self.assertEqual(self.store.revision,revision)
        for owner in ['user-'+'0'*32,['invalid']]:
            with self.assertRaises(urllib.error.HTTPError) as error:self.assign_task(owner)
            self.assertEqual(error.exception.code,400)
        self.assertNotIn('assignee_id',self.store.require('notes',self.note))
        self.assertEqual(self.store.require('notes',self.note)['text'],'Opdigtet privat opgave')

    def test_task_ownership_explicit_change_cannot_overwrite_new_owner(self):
        session,role,user=self.reader(['cards.view','notes.view','notes.edit'])
        second=self.login('Fiktiv admin','Fiktiv-password-123');stale=self.state(second)
        self.assign_task(user)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.change(second,stale,'note.save',{'id':self.note,'card_id':self.card,'text':'Stale owner change','assignee_id':self.server.accounts.authorize(self.admin['token'],'users.manage'),'assignee_before':None})
        self.assertEqual(error.exception.code,400)
        self.assertEqual(self.store.require('notes',self.note)['assignee_id'],user)
        # Ordinary note edits omit ownership and preserve the current owner.
        self.change(session,self.state(session),'note.save',{'id':self.note,'card_id':self.card,'text':'Edited by assigned reader'})
        self.change(second,self.state(second),'note.save',{'id':self.note,'card_id':self.card,'text':'Ordinary edit'})
        self.assertEqual(self.store.require('notes',self.note)['assignee_id'],user)

    def test_task_ownership_disabled_account_and_clear(self):
        session,role,user=self.reader(['cards.view','notes.view','notes.edit'])
        self.assign_task(user)
        self.server.accounts.save_user(self.admin['token'],'Fiktiv bruger',[role],ident=user,disabled=True)
        self.assertNotIn(user,[u['id'] for u in self.state(self.admin)['task_users']])
        self.change(self.admin,self.state(self.admin),'note.save',{'id':self.note,'card_id':self.card,'text':'Retains inactive owner'})
        self.assign_task(None,before=user)
        with self.assertRaises(urllib.error.HTTPError) as error:self.assign_task(user)
        self.assertEqual(error.exception.code,400)
        note=next(n for n in self.state(self.admin)['notes'] if n['id']==self.note)
        self.assertFalse(note['assigned']);self.assertIsNone(note['assignee_id'])

    def test_task_ownership_followup_is_unique_and_completion_keeps_assignment(self):
        session,role,user=self.reader(['cards.view','notes.view','notes.edit'])
        key=json.dumps(['checks',self.card,'area'])
        self.assign_task(user,followup_key=key,recurrence={'frequency':'weekly','weekday':__import__('datetime').date.today().weekday()})
        before=len(self.store.state()['notes'])
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.change(self.admin,self.state(self.admin),'note.save',{'text':'Duplicate follow-up','followup_key':key})
        self.assertEqual(error.exception.code,400);self.assertEqual(len(self.store.state()['notes']),before)
        note=self.store.require('notes',self.note)
        self.change(session,self.state(session),'note.complete',{'id':self.note,'due':note['recurrence']['next_due']})
        note=self.store.require('notes',self.note)
        self.assertEqual(note['assignee_id'],user);self.assertEqual(note['followup_key'],key)
        self.assertEqual(len(note['task_history']),1)
        self.assertTrue(self.store.require('cards',self.card)['temporary'])
        # No account identity escapes through a note edit-base response.
        base=self.server.profiles.workspace.begin_edit(session['token'],'notes',self.note)
        self.assertNotIn(user,json.dumps(base))

    def test_task_ownership_directory_requires_note_access(self):
        session,role,user=self.reader(['users.manage'])
        state=self.state(session)
        self.assertNotIn('task_users',state);self.assertEqual(state['notes'],[])


    def test_task_ownership_undo_rechecks_account_management(self):
        session,role,user=self.reader(['cards.view','notes.view','notes.edit'])
        admin_id=self.server.accounts.authorize(self.admin['token'],'users.manage')
        roles=self.server.accounts.data['users'][admin_id]['roles']
        self.server.accounts.save_user(self.admin['token'],'Fiktiv bruger',roles,ident=user)
        self.assign_task(user)
        self.server.accounts.save_user(session['token'],'Fiktiv admin',[role],ident=admin_id)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.change(self.admin,self.state(self.admin),'workflow.undo',{})
        self.assertEqual(error.exception.code,403)
        self.assertEqual(self.store.require('notes',self.note)['assignee_id'],user)


    def test_task_ownership_text_conflict_choice_retains_private_assignment(self):
        session,role,user=self.reader(['cards.view','notes.view','notes.edit'])
        self.assign_task(user)
        a=self.state(self.admin);b=self.state(session)
        for who,base,text in [(self.admin,a,'Fictional text A'),(session,b,'Fictional text B')]:
            self.change(who,base,'note.save',{'id':self.note,'card_id':self.card,'text':text})
        rows=self.value('/api/profiles/conflicts',session=session)
        row=next(r for r in rows if r['module']=='notes' and r['field']=='text')
        self.assertNotIn('assignee_id',json.dumps(rows))
        self.value('/api/profiles/conflicts/resolve',{'id':row['id'],'choice':'saved','review_snapshot':row['review_snapshot']},session)
        note=self.store.require('notes',self.note)
        self.assertEqual(note['text'],'Fictional text A');self.assertEqual(note['assignee_id'],user)


    def test_redistribution_profiles_preserve_history_and_hide_new_membership_metadata(self):
        from test_geography import address
        area=self.store.mutate('area.save',{'name':'Fictional area'})['id']
        rows=[address('move'+str(i),str(i+1),lng=10+i*.001) for i in range(6)]
        self.store.mutate('geo.import',{'records':rows,'source':'Fictional','label':'Fictional local test'})
        self.store.mutate('geo.assign',{'card_id':self.card,'address_ids':[r['id'] for r in rows[:4]]})
        target=self.store.mutate('geo.assign',{'number':'F102','address_ids':[r['id'] for r in rows[4:]]})['id']
        for ident,day in [(self.card,'2026-03-02'),(target,'2026-01-02')]:
            self.store.mutate('card.save',{**self.store.require('cards',ident),'area_id':area})
            self.store.mutate('completion.record',{'card_id':ident,'date':day})
        data={'mode':'transfer','ids':[self.card,target],'address_ids':[rows[0]['id']],'number':'F102'}
        p=self.change(self.admin,self.state(self.admin),'card.restructure.preview',data)['result']
        self.change(self.admin,self.state(self.admin),'card.restructure.apply',{**data,'expected':p['expected'],'confirm':'ÆNDR KORT'})
        reader,role,user=self.reader(['cards.view'])
        state=self.state(reader);card=next(c for c in state['cards'] if c['id']==target)
        self.assertEqual(card['planning_date'],'2026-03-02');self.assertEqual(card['last_completed'],'2026-01-02')
        self.assertNotIn('membership',card['planning_reference']);self.assertEqual(state['completions'],[])
        before=self.store.revision
        with self.assertRaises(urllib.error.HTTPError) as error:self.change(reader,state,'card.restructure.preview',data)
        self.assertEqual(error.exception.code,403);self.assertEqual(self.store.revision,before)


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
                with urllib.request.urlopen(urllib.request.Request(server.origin+'/api/connections/drive',headers={'Origin':server.origin,'Cookie':cookie,'X-Distrikt-Token':server.token}),timeout=10) as response:
                    self.assertEqual(set(json.load(response)),{'connected','account'})
                with request('/api/profiles/activate',data,cookie) as response:self.assertTrue(json.load(response)['ok'])
                self.assertEqual(store.all('cards')[0]['number'],'F201')
                with self.assertRaises(urllib.error.HTTPError):request('/api/login',{'password':'Fiktiv-old-password'})
                # A run.json stop secret must not bypass profile login on LAN/HA.
                with self.assertRaises(urllib.error.HTTPError) as error:request('/api/shutdown',{})
                self.assertEqual(error.exception.code,401)
                with request('/api/login',{'name':'Fiktiv ejer','password':'Fiktiv-new-password'}) as response:self.assertTrue(json.load(response)['ok'])
            finally:server.shutdown();server.server_close();thread.join();store.close()



if __name__=='__main__':unittest.main()
