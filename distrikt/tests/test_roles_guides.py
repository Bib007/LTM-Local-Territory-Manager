"""W121/W123/W126: fictional isolated accounts, aggregate projections and real HTTP."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from profile_accounts import ProfileAccounts,PERMISSIONS
from profile_features import summaries,DASHBOARD_LEGACY,REPORT_LEGACY,RELEASE
from profile_recovery import backup_value,parsed_backup,restore_value
from profile_policy import state_for
from server import Server
from store import Store

class RolesGuidesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.a=ProfileAccounts(self.temp.name)
        self.admin_id=self.a.bootstrap('Fiktiv admin','Fiktiv-password-123');self.admin=self.a.login('Fiktiv admin','Fiktiv-password-123','fictional-a')
    def tearDown(self):self.temp.cleanup()
    def user(self,rights=()):
        role=self.a.save_role(self.admin,'Fiktiv rolle',list(rights));ident=self.a.save_user(self.admin,'Fiktiv bruger',[role],password='Fiktiv-password-456');token=self.a.login('Fiktiv bruger','Fiktiv-password-456','fictional-b');return role,ident,token
    def finish(self,token):
        for _ in range(50):
            guide=self.a.guide_current(token)
            if not guide['steps']:return
            self.a.guide_progress(token,guide['run_id'],guide['request_id'],guide['steps'][0]['id'])
        self.fail('Guide did not terminate')
    def test_summaries_use_current_inventory_and_no_raw_values(self):
        raw={'today':'2026-11-01','revision':'fictional-r','cards':[{'id':'secret-card-a','last_completed':'2026-10-01'},{'id':'secret-card-b','last_completed':None},{'id':'secret-card-c'}], 'loans':[{'card_id':'secret-card-b','returned':None,'publisher_name':'Fiktiv privat'}], 'completions':[{'card_id':'secret-card-a','date':'2026-10-01'},{'card_id':'secret-card-a','date':'2026-10-02'},{'card_id':'secret-archived','date':'2026-09-01'}]}
        value=summaries(raw);s=value['periods']['service']
        self.assertEqual(s,{'start':'2026-09-01','end':'2026-11-01','completions':3,'territories':3,'completed_territories':1,'missing':2,'assigned':1,'home':2,'missing_assigned':1,'missing_home':1})
        self.assertNotIn('secret',json.dumps(value));self.assertNotIn('Fiktiv privat',json.dumps(value))
        raw['today']='2024-02-29';self.assertEqual(summaries(raw)['periods']['rolling']['start'],'2023-02-28')
    def test_union_migration_is_visible_once_and_no_raw_rights_added(self):
        role,user,token=self.user();data=self.a._copy();adminrole=data['users'][self.admin_id]['roles'][0]
        data['roles'][adminrole]['permissions']=sorted(PERMISSIONS-{'dashboard.view','reports.view'})
        data['roles'][role]['permissions']=sorted(DASHBOARD_LEGACY-{'geo.view'})
        import uuid
        second='role-'+uuid.uuid4().hex;data['roles'][second]={'id':second,'name':'Fiktiv geografisk læser','permissions':['geo.view']};data['users'][user]['roles'].append(second);data['permission_schema']=2
        Path(self.a.path).write_text(json.dumps(data));upgraded=ProfileAccounts(self.temp.name);u=upgraded.data['users'][user];rights=upgraded._permissions(upgraded.data,u)
        self.assertEqual(rights,set(DASHBOARD_LEGACY)|{'dashboard.view','reports.view'})
        self.assertGreater(len(u['roles']),2);self.assertTrue(any(r['name'].startswith('Bevaret oversigtsadgang') for r in upgraded.data['roles'].values()))
        admin=upgraded.login('Fiktiv admin','Fiktiv-password-123','fictional-c');compat=u['roles'][-1]
        upgraded.save_role(admin,'Fiktiv ændret bevaret rolle',[],compat)
        self.assertNotIn('dashboard.view',ProfileAccounts(self.temp.name)._permissions(upgraded.data,u))
    def test_personal_guide_is_filtered_and_does_not_write_shared_setup(self):
        role,user,token=self.user(['reports.view']);guide=self.a.guide_current(token)
        self.assertEqual([s['id'] for s in guide['steps']],['start','reports'])
        self.finish(token);self.assertTrue(self.a.data['users'][user]['onboarded']);self.assertNotIn('settings',self.a.data)
        self.assertEqual(self.a.data['users'][self.admin_id].get('intro'),None)
    def test_assignment_waits_for_new_login_and_does_not_reset_intro(self):
        role,user,old=self.user(['dashboard.view']);self.finish(old);before=list(self.a.data['users'][user]['intro']['completed_steps'])
        self.a.guide_assign(self.admin,user,'intro','');self.assertEqual(self.a.guide_current(old)['steps'],[])
        new=self.a.login('Fiktiv bruger','Fiktiv-password-456','fictional-c');guide=self.a.guide_current(new)
        self.assertEqual(guide['kind'],'intro');self.assertNotEqual(guide['request_id'],'first');self.finish(new)
        self.assertEqual(self.a.data['users'][user]['intro']['completed_steps'],before)
    def test_assign_requires_admin_and_stale_assignment_is_rejected(self):
        role,user,token=self.user();self.finish(token)
        with self.assertRaises(PermissionError):self.a.guide_assign(token,user,'intro','')
        self.a.guide_assign(self.admin,user,'news','')
        with self.assertRaises(ValueError):self.a.guide_assign(self.admin,user,'intro','')
    def test_new_assignment_cannot_be_acknowledged_by_old_run(self):
        role,user,token=self.user();self.finish(token);self.a.guide_assign(self.admin,user,'intro','');old_id=self.a.data['users'][user]['intro']['assigned']['id'];new=self.a.login('Fiktiv bruger','Fiktiv-password-456','fictional-c');guide=self.a.guide_current(new)
        self.a.guide_assign(self.admin,user,'intro',old_id)
        with self.assertRaises(ValueError):self.a.guide_progress(new,guide['run_id'],guide['request_id'],'start')
        self.assertNotEqual(self.a.data['users'][user]['intro'].get('completed_assignment'),self.a.data['users'][user]['intro']['assigned']['id'])
    def test_revocation_and_forged_step_are_checked_at_each_ack(self):
        role,user,token=self.user(['cards.view']);guide=self.a.guide_current(token)
        self.a.save_role(self.admin,'Fiktiv rolle',[],role)
        with self.assertRaises(PermissionError):self.a.guide_progress(token,guide['run_id'],guide['request_id'],'cards')
        with self.assertRaises(ValueError):self.a.guide_progress(self.admin,guide['run_id'],guide['request_id'],'start')
    def test_replay_is_read_only_and_completion_is_idempotent(self):
        role,user,token=self.user();self.finish(token);before=self.a._copy();guide=self.a.guide_replay(token);self.a.guide_progress(token,guide['run_id'],guide['request_id'],'start');self.a.guide_progress(token,guide['run_id'],guide['request_id'],'start');self.assertEqual(before,self.a._copy())
    def test_new_features_are_per_feature_and_later_grants_remain_unseen(self):
        role,user,token=self.user();self.finish(token)
        self.a.save_role(self.admin,'Fiktiv rolle',['reports.view'],role);new=self.a.login('Fiktiv bruger','Fiktiv-password-456','fictional-c');self.assertEqual([s['id'] for s in self.a.guide_current(new)['steps']],['reports']);self.finish(new)
        again=self.a.login('Fiktiv bruger','Fiktiv-password-456','fictional-d');self.assertEqual(self.a.guide_current(again)['steps'],[])
        self.assertEqual(self.a.data['users'][user]['intro']['seen_features'],['summary-reports'])
    def test_user_edit_and_backup_restore_preserve_individual_progress(self):
        role,user,token=self.user(['reports.view']);self.finish(token);self.a.guide_assign(self.admin,user,'intro','');before=self.a._copy()['users'][user]['intro']
        self.a.save_user(self.admin,'Fiktiv bruger omdøbt',[role],user);self.assertEqual(before,self.a.data['users'][user]['intro'])
        value=backup_value(self.a);restore_value(self.a,parsed_backup(value));self.assertEqual(before,self.a.data['users'][user]['intro']);self.assertEqual(self.a.sessions,{})
        value['accounts']['users'][user]['intro']['assigned']['kind']='grant-admin'
        with self.assertRaises(ValueError):parsed_backup(value)

class RolesGuidesHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name);self.server=Server(('127.0.0.1',0),self.store);self.a=self.server.accounts
        self.a.bootstrap('Fiktiv admin','Fiktiv-password-123');self.admin=self.a.login('Fiktiv admin','Fiktiv-password-123','fictional-admin');role=self.a.save_role(self.admin,'Fiktiv oversigt',['dashboard.view','reports.view']);self.user=self.a.save_user(self.admin,'Fiktiv læser',[role],password='Fiktiv-password-456');self.reader=self.a.login('Fiktiv læser','Fiktiv-password-456','fictional-reader')
        self.store.mutate('publisher.save',{'name':'Fiktiv hemmelig person'});self.store.mutate('note.save',{'text':'Fiktiv hemmelig note'})
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.store.close();self.temp.cleanup()
    def request(self,path,token,data=None):
        req=urllib.request.Request(self.server.origin+path,headers={'Origin':self.server.origin,'Cookie':self.server.profiles.cookie+'='+token,'X-Distrikt-Token':self.server.profiles.csrf(token),'Content-Type':'application/json'},data=json.dumps(data).encode() if data is not None else None)
        with urllib.request.urlopen(req,timeout=5) as r:return json.load(r)
    def test_summary_only_state_and_denied_raw_routes(self):
        state=self.request('/api/state',self.reader);self.assertIsNotNone(state['dashboard_summary']);self.assertIsNotNone(state['report_summary'])
        for module in ('cards','publishers','loans','notes','ib','completions','visits','maps'):self.assertEqual(state[module],[])
        self.assertNotIn('Fiktiv hemmelig',json.dumps(state))
        for path in ('/api/geo','/api/export/s13','/api/export/backup','/api/profiles/admin'):
            with self.assertRaises(urllib.error.HTTPError) as caught:self.request(path,self.reader)
            self.assertEqual(caught.exception.code,403)
    def test_assignment_uses_users_manage_and_old_session_does_not_capture_it(self):
        self.request('/api/profiles/guide/assign',self.admin,{'user_id':self.user,'kind':'intro','expected_assignment':''})
        with self.assertRaises(urllib.error.HTTPError) as caught:self.request('/api/profiles/guide/assign',self.reader,{'user_id':self.user,'kind':'intro','expected_assignment':''})
        self.assertEqual(caught.exception.code,403)
        guide=self.request('/api/profiles/guide',self.reader)
        for step in list(guide['steps']):guide=self.request('/api/profiles/guide/progress',self.reader,{'run_id':guide['run_id'],'request_id':guide['request_id'],'step_id':step['id']})
        self.assertEqual(guide['steps'],[])
        newer=self.a.login('Fiktiv læser','Fiktiv-password-456','fictional-new');self.assertNotEqual(self.request('/api/profiles/guide',newer)['request_id'],'first')
