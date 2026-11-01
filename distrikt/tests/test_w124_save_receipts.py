"""W124: real loopback HTTP, disposable SQLite and fictional accounts only."""
import unittest
import urllib.error
from unittest.mock import patch
import test_profiles_integration as fixture

class SaveReceiptTests(unittest.TestCase):
    setUp=fixture.ProfilesIntegrationTests.setUp
    tearDown=fixture.ProfilesIntegrationTests.tearDown
    request=fixture.ProfilesIntegrationTests.request
    value=fixture.ProfilesIntegrationTests.value
    login=fixture.ProfilesIntegrationTests.login
    state=fixture.ProfilesIntegrationTests.state
    change=fixture.ProfilesIntegrationTests.change

    def fork(self,base,session=None):
        session=session or self.admin
        return self.value('/api/profiles/edit-base',{'snapshot':base['profile']['snapshot']},session)['snapshot']

    def test_open_edit_base_survives_other_page_admin_and_review_reads(self):
        base=self.state(self.admin);base['profile']['snapshot']=self.fork(base)
        for _ in range(20):
            self.state(self.admin)
            self.value('/api/profiles/admin',session=self.admin)
            self.value('/api/profiles/conflicts',session=self.admin)
        result=self.change(self.admin,base,'card.save',{**base['cards'][0],'name':'Fiktiv bevaret kladde'})
        self.assertEqual(result['state']['cards'][0]['name'],'Fiktiv bevaret kladde')
        # Its successor must remain protected while this form is still open.
        base['profile']['snapshot']=result['profile_snapshot']
        for _ in range(20):self.state(self.admin)
        self.change(self.admin,base,'card.save',{**base['cards'][0],'name':'Fiktiv næste kladde'})
        self.assertEqual(self.store.require('cards',self.card)['name'],'Fiktiv næste kladde')

    def test_separate_dialog_bases_preserve_unseen_fields_and_conflicts(self):
        base=self.state(self.admin)
        a={**base,'profile':{**base['profile'],'snapshot':self.fork(base)}}
        b={**base,'profile':{**base['profile'],'snapshot':self.fork(base)}}
        self.change(self.admin,a,'card.save',{**base['cards'][0],'name':'Fiktiv A'})
        result=self.change(self.admin,b,'card.save',{**base['cards'][0],'number':'F102'})
        self.assertEqual(result['state']['cards'][0]['name'],'Fiktiv A')
        self.assertEqual(result['state']['profile']['conflicts'],0)
        b['profile']['snapshot']=result['profile_snapshot']
        result=self.change(self.admin,b,'card.save',{**base['cards'][0],'number':'F102','name':'Fiktiv B'})
        self.assertEqual(result['state']['cards'][0]['name'],'Fiktiv B')
        self.assertEqual(result['state']['profile']['conflicts'],1)

    def test_post_commit_read_failure_returns_known_saved_receipt(self):
        for failure in (ValueError('Fictional snapshot full'),OSError('Fictional read failure')):
            base=self.state(self.admin)
            with patch.object(self.server,'app_state',side_effect=failure):
                result=self.change(self.admin,base,'card.save',{**base['cards'][0],'name':str(failure)})
            self.assertTrue(result['ok']);self.assertTrue(result['state_unavailable'])
            self.assertNotIn('state',result);self.assertNotIn('error',result)
            self.assertEqual(result['revision'],self.store.revision)
            self.assertEqual(self.store.require('cards',self.card)['name'],str(failure))
            self.assertIn(result['profile_snapshot'],self.server.profiles.bases._items)

    def test_real_snapshot_byte_failure_after_commit_is_known_saved(self):
        base=self.state(self.admin)
        items=self.server.profiles.bases._items
        oldsize=items[base['profile']['snapshot']]['size']
        self.server.profiles.bases.max_bytes=2*oldsize+1000
        for n in range(40):self.store.mutate('card.save',{'number':'F'+str(200+n),'name':'Fiktiv ekstra '*6,'temporary':True})
        result=self.change(self.admin,base,'card.save',{**base['cards'][0],'name':'Fiktiv faktisk gemt'})
        self.assertTrue(result['state_unavailable'])
        self.assertEqual(self.store.require('cards',self.card)['name'],'Fiktiv faktisk gemt')

    def test_necessary_successor_capacity_failure_still_rolls_back(self):
        base=self.state(self.admin);base['profile']['snapshot']=self.fork(base)
        self.server.profiles.bases.capacity=len(self.server.profiles.bases._items)
        before=self.store.require('cards',self.card)
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.change(self.admin,base,'card.save',{**base['cards'][0],'name':'Fiktiv må ikke gemmes'})
        self.assertEqual(e.exception.code,400)
        self.assertEqual(self.store.require('cards',self.card),before)
        self.assertIn(base['profile']['snapshot'],self.server.profiles.bases._items)

    def test_fork_is_session_bound_expires_and_respects_limits(self):
        base=self.state(self.admin);token=base['profile']['snapshot']
        other=self.login('Fiktiv admin','Fiktiv-password-123')
        with self.assertRaises(urllib.error.HTTPError):self.fork(base,other)
        fork=self.fork(base);items=self.server.profiles.bases._items
        self.assertEqual(items[fork]['until'],items[token]['until'])
        items[fork]['until']=0
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.change(self.admin,{**base,'profile':{**base['profile'],'snapshot':fork}},'card.save',base['cards'][0])
        self.assertEqual(__import__('json').load(e.exception)['code'],'edit_base_unavailable')
        self.server.profiles.bases.max_bytes=sum(item['size'] for item in items.values())
        with self.assertRaises(urllib.error.HTTPError):self.fork(base)
        self.server.profiles.bases.max_bytes=64*1024*1024
        self.server.profiles.bases.capacity=len(items)
        with self.assertRaises(urllib.error.HTTPError):self.fork(base)

    def test_protected_base_cannot_bypass_current_rights(self):
        editor,role,user=fixture.ProfilesIntegrationTests.reader(self,['cards.view','cards.edit'])
        base=self.state(editor);base['profile']['snapshot']=self.fork(base,editor)
        self.value('/api/profiles/roles/save',{'id':role,'name':'Fiktiv rolle','permissions':['cards.view']},self.admin)
        before=self.store.require('cards',self.card)
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.change(editor,base,'card.save',{**base['cards'][0],'name':'Fiktiv uden ret'})
        self.assertEqual(e.exception.code,403)
        self.assertEqual(self.store.require('cards',self.card),before)

    def test_distinct_editor_bases_do_not_allow_double_issue(self):
        self.store.mutate('folder.set',{'ids':[self.card],'in_folder':True})
        base=self.state(self.admin)
        a={**base,'profile':{**base['profile'],'snapshot':self.fork(base)}}
        b={**base,'profile':{**base['profile'],'snapshot':self.fork(base)}}
        data={'card_id':self.card,'publisher_name':'Fiktiv låner','date':base['today']}
        self.change(self.admin,a,'loan.issue',data)
        with self.assertRaises(urllib.error.HTTPError) as e:self.change(self.admin,b,'loan.issue',data)
        self.assertEqual(e.exception.code,400)
        self.assertEqual(len([x for x in self.store.all('loans') if not x.get('returned')]),1)

    def test_release_cannot_discard_another_sessions_base(self):
        base=self.state(self.admin);fork=self.fork(base)
        other=self.login('Fiktiv admin','Fiktiv-password-123')
        self.value('/api/profiles/edit-base/release',{'snapshot':fork},other)
        self.assertIn(fork,self.server.profiles.bases._items)
        self.value('/api/profiles/edit-base/release',{'snapshot':fork},self.admin)
        self.assertNotIn(fork,self.server.profiles.bases._items)

if __name__=='__main__':unittest.main()
