"""W127 permissions, CSRF, state tokens and no writes over the normal local HTTP server."""
import unittest,urllib.error
from copy import deepcopy
import test_profiles_integration as profiles_fixture

class ColumnHTTPTests(unittest.TestCase):
    setUp=profiles_fixture.ProfilesIntegrationTests.setUp
    tearDown=profiles_fixture.ProfilesIntegrationTests.tearDown
    request=profiles_fixture.ProfilesIntegrationTests.request
    value=profiles_fixture.ProfilesIntegrationTests.value
    login=profiles_fixture.ProfilesIntegrationTests.login
    reader=profiles_fixture.ProfilesIntegrationTests.reader
    state=profiles_fixture.ProfilesIntegrationTests.state
    change=profiles_fixture.ProfilesIntegrationTests.change
    def data(self):return {'name':'fiktiv.csv','content':'Distrikt;Vej;Nr\n001;Fiktivvej;01-09\n','header_row':1,'column_map':['card','road','number']}
    def test_inspect_and_mapping_preview_have_no_domain_writes_or_implicit_apply(self):
        before=deepcopy(self.store.state());d=self.data();state=self.state(self.admin)
        inspect=self.change(self.admin,state,'setup.card-import.inspect',d)['result']
        self.assertEqual(inspect['sample'][0]['values'],['001','Fiktivvej','01-09']);self.assertNotIn('token',inspect)
        self.assertEqual(self.store.state(),before)
        p=self.change(self.admin,self.state(self.admin),'setup.card-import.preview',d)['result']
        self.assertEqual(self.store.state(),before);self.assertEqual(p['cards'][0]['number'],'001')
        with self.assertRaises(urllib.error.HTTPError) as error:self.change(self.admin,self.state(self.admin),'setup.card-import.apply',{'token':p['token'],'confirm':'yes'})
        self.assertEqual(error.exception.code,400);self.assertEqual(self.store.state(),before)
    def test_inspect_preview_and_apply_keep_each_existing_permission(self):
        reader,_,_=self.reader(['cards.view','ib.view'])
        for action in ['setup.card-import.inspect','setup.card-import.preview','setup.card-import.apply','setup.ib.inspect','setup.ib.preview','setup.ib.apply']:
            with self.subTest(action=action),self.assertRaises(urllib.error.HTTPError) as error:self.change(reader,self.state(reader),action,self.data())
            self.assertEqual(error.exception.code,403)
    def test_inspect_requires_same_origin_csrf_and_authenticated_session(self):
        for extra in [{'Origin':'http://untrusted.invalid'},{'X-Distrikt-Token':'wrong'}]:
            with self.subTest(extra=extra),self.assertRaises(urllib.error.HTTPError) as error:
                self.request('/api/mutate',{'action':'setup.card-import.inspect','data':self.data()},self.admin,extra=extra)
            self.assertEqual(error.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/mutate',{'action':'setup.card-import.inspect','data':self.data()})
        self.assertIn(error.exception.code,(401,403))
    def test_permission_revocation_stale_data_and_duplicate_card_block_apply(self):
        reader,role,_=self.reader(['cards.view','cards.edit','geo.view']);d=self.data()
        p=self.change(reader,self.state(reader),'setup.card-import.preview',d)['result']
        role_value=next(r for r in self.value('/api/profiles/admin',session=self.admin)['roles'] if r['id']==role)
        self.value('/api/profiles/roles/save',{**role_value,'permissions':['cards.view','geo.view']},self.admin)
        with self.assertRaises(urllib.error.HTTPError) as error:self.change(reader,self.state(reader),'setup.card-import.apply',{'token':p['token'],'confirm':'IMPORTÉR KORT'})
        self.assertEqual(error.exception.code,403)
        self.store.mutate('card.save',{'number':'001','temporary':True})
        with self.assertRaises(urllib.error.HTTPError) as error:self.change(self.admin,self.state(self.admin),'setup.card-import.apply',{'token':p['token'],'confirm':'IMPORTÉR KORT'})
        self.assertEqual(error.exception.code,400)
        p=self.change(self.admin,self.state(self.admin),'setup.card-import.preview',d)['result'];self.assertTrue(p['errors'])
if __name__=='__main__':unittest.main()
