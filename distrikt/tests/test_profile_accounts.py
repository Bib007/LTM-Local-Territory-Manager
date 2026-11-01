"""Only invented names/passwords in temporary isolated data directories."""
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from profile_accounts import ProfileAccounts,SESSION_LIFETIME,ONLINE_WINDOW,PERMISSIONS
from portable import snapshot
from store import Store


class ProfileAccountsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.t=1000
        self.a=ProfileAccounts(self.root,clock=lambda:self.t)
        self.admin=self.a.bootstrap('Fiktiv Admin','Fiktiv-Password-123')
        self.token=self.a.login('Fiktiv Admin','Fiktiv-Password-123','fictional-client-a')
        self.admin_role=self.a.overview(self.token)['users'][0]['roles'][0]
    def tearDown(self):self.tmp.cleanup()
    def user(self):
        role=self.a.save_role(self.token,'Fiktiv rolle',['cards.view','cards.edit','presence.view'])
        user=self.a.save_user(self.token,'Fiktiv bruger',[role],password='Fiktiv-Password-456')
        return role,user,self.a.login('Fiktiv bruger','Fiktiv-Password-456','fictional-client-b')

    def test_profiles_are_hashed_private_and_not_in_normal_backups(self):
        raw=self.a.path.read_text();self.assertNotIn('Fiktiv-Password-123',raw);self.assertNotIn(self.token,raw)
        self.assertNotIn('hash',str(self.a.overview(self.token)));self.assertNotIn('salt',str(self.a.overview(self.token)))
        if os.name!='nt':self.assertEqual(self.a.path.stat().st_mode&0o777,0o600)
        store=Store(self.root)
        try:
            with zipfile.ZipFile(io.BytesIO(snapshot(store,'fictional'))) as archive:
                self.assertNotIn('profiles.json',archive.namelist())
                for name in archive.namelist():self.assertNotIn(b'Fiktiv-Password-123',archive.read(name))
        finally:store.close()

    def test_roles_are_custom_and_server_permissions_update_for_existing_session(self):
        role,user,token=self.user();self.assertEqual(self.a.authorize(token,'cards.edit'),user)
        with self.assertRaises(PermissionError):self.a.authorize(token,'users.manage')
        with self.assertRaises(PermissionError):self.a.save_role(token,'Uautoriseret',['users.manage'])
        self.a.save_role(self.token,'Fiktiv ændret rolle',['cards.view'],role)
        self.assertEqual(self.a.authorize(token,'cards.view'),user)
        with self.assertRaises(PermissionError):self.a.authorize(token,'cards.edit')
        with self.assertRaises(PermissionError):self.a.online(token)

    def test_backup_notice_upgrade_is_once_and_respects_later_role_choice(self):
        role,_,_=self.user();legacy=self.a._copy();legacy.pop('permission_schema')
        legacy['roles'][self.admin_role]['permissions']=sorted(PERMISSIONS-{'backup.notify'})
        self.a.path.write_text(json.dumps(legacy))
        upgraded=ProfileAccounts(self.root)
        token=upgraded.login('Fiktiv Admin','Fiktiv-Password-123','fictional-client')
        self.assertEqual(upgraded.authorize(token,'backup.notify'),self.admin)
        self.assertNotIn('backup.notify',upgraded.data['roles'][role]['permissions'])
        upgraded.save_role(token,'Administrator',sorted(PERMISSIONS-{'backup.notify'}),self.admin_role)
        restarted=ProfileAccounts(self.root)
        token=restarted.login('Fiktiv Admin','Fiktiv-Password-123','fictional-client')
        with self.assertRaises(PermissionError):restarted.authorize(token,'backup.notify')

    def test_disabling_or_resetting_an_account_invalidates_all_sessions(self):
        role,user,token=self.user();second=self.a.login('Fiktiv bruger','Fiktiv-Password-456','fictional-client-c')
        self.a.save_user(self.token,'Fiktiv bruger',[role],user,password='Fiktiv-Ny-Password-456')
        for old in (token,second):
            with self.assertRaises(PermissionError):self.a.authorize(old,'cards.view')
        new=self.a.login('Fiktiv bruger','Fiktiv-Ny-Password-456','fictional-client-c')
        self.a.save_user(self.token,'Fiktiv bruger',[role],user,disabled=True)
        with self.assertRaises(PermissionError):self.a.authorize(new,'cards.view')
        with self.assertRaises(PermissionError):self.a.login('Fiktiv bruger','Fiktiv-Ny-Password-456','fictional-client-c')

    def test_last_administrator_cannot_be_removed_and_bad_edit_is_atomic(self):
        before=self.a.path.read_bytes()
        with self.assertRaises(ValueError):self.a.save_user(self.token,'Fiktiv Admin',[self.admin_role],self.admin,disabled=True)
        with self.assertRaises(ValueError):self.a.save_role(self.token,'Administrator',['cards.view'],self.admin_role)
        self.assertEqual(self.a.path.read_bytes(),before);self.assertEqual(self.a.authorize(self.token,'users.manage'),self.admin)
        with patch('profile_accounts.write_private',side_effect=OSError('fictional write failure')):
            with self.assertRaises(OSError):self.a.save_role(self.token,'Ny rolle',['cards.view'])
        self.assertEqual(self.a.path.read_bytes(),before);self.assertEqual(len(self.a.overview(self.token)['roles']),1)

    def test_returned_overview_cannot_modify_live_permissions(self):
        overview=self.a.overview(self.token)
        overview['users'][0]['roles'].clear();overview['roles'][0]['permissions'].clear()
        self.assertEqual(self.a.authorize(self.token,'users.manage'),self.admin)

    def test_rate_limit_capacity_does_not_evict_active_accounts(self):
        self.a.account_attempts={f'fictional-{i}':[self.t] for i in range(1000)}
        with self.assertRaisesRegex(PermissionError,'later'):
            self.a.login('Fiktiv Admin','Fiktiv-Password-123','fictional-new-client')
        self.assertIn('fictional-0',self.a.account_attempts)
        self.t+=301
        self.assertTrue(self.a.login('Fiktiv Admin','Fiktiv-Password-123','fictional-new-client'))

    def test_sign_in_rate_limit_expiry_and_unknown_user_are_safe(self):
        for _ in range(8):
            with self.assertRaisesRegex(PermissionError,'Incorrect login'):self.a.login('Ukendt','Fiktiv-Password-123','fictional-bad-client')
        with self.assertRaisesRegex(PermissionError,'later'):self.a.login('Fiktiv Admin','Fiktiv-Password-123','fictional-bad-client')
        self.t+=301;self.assertTrue(self.a.login('Fiktiv Admin','Fiktiv-Password-123','fictional-bad-client'))
        self.t+=SESSION_LIFETIME
        with self.assertRaises(PermissionError):self.a.authorize(self.token,'users.manage')

    def test_account_rate_limit_applies_across_different_clients(self):
        for i in range(8):
            with self.assertRaisesRegex(PermissionError,'Incorrect login'):
                self.a.login('Fiktiv Admin','Wrong fictional password',f'fictional-client-{i}')
        with self.assertRaisesRegex(PermissionError,'later'):
            self.a.login('Fiktiv Admin','Fiktiv-Password-123','fictional-client-new')
        self.t+=301;self.assertTrue(self.a.login('Fiktiv Admin','Fiktiv-Password-123','fictional-client-new'))

    def test_recent_presence_deduplicates_sessions_and_expires(self):
        role,user,first=self.user();second=self.a.login('Fiktiv bruger','Fiktiv-Password-456','fictional-client-c')
        self.assertEqual(len(self.a.online(self.token)),2)
        self.t+=ONLINE_WINDOW+1;self.a.heartbeat(second)
        visible=self.a.online(self.token);self.assertEqual({u['id'] for u in visible},{self.admin,user})
        self.a.logout(second);self.t+=ONLINE_WINDOW+1
        self.assertEqual([u['id'] for u in self.a.online(self.token)],[self.admin])
        self.a.logout(first)

    def test_unique_names_existing_role_and_short_password_validation(self):
        role,user,_=self.user()
        with self.assertRaises(ValueError):self.a.save_user(self.token,' fiktiv bruger ',[role],password='Fiktiv-Password-789')
        with self.assertRaises(ValueError):self.a.save_user(self.token,'Ny bruger',['unknown-role'],password='Fiktiv-Password-789')
        with self.assertRaises(ValueError):self.a.save_user(self.token,'Ny bruger',[role],password='short')
        with self.assertRaises(ValueError):self.a.bootstrap('Ny admin','Fiktiv-Password-789')


if __name__=='__main__':unittest.main()
