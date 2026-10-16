import io
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store, MODULES
from portable import snapshot, Restores, digest

class PortableTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.s=Store(Path(self.temp.name)/'source');self.t=Store(Path(self.temp.name)/'target')
        self.card=self.s.mutate('card.save',{'number':'120','temporary':True})['id']
        self.publisher=self.s.mutate('publisher.save',{'name':'Fiktiv testperson'})['id']
        self.loan=self.s.mutate('loan.issue',{'card_id':self.card,'publisher_id':self.publisher,'date':'2026-01-01','initial':True})['id']
        self.s.mutate('ib.save',{'card_id':self.card,'road':'Testvej','number':'42','date':'2026-01-01'})
        (self.s.root/'drive-auth.json').write_text('PRIVATE_FAKE_SECRET')
        (self.s.root/'access.json').write_text('PRIVATE_FAKE_PASSWORD')
        self.backup=snapshot(self.s,'1.9.0');self.restore=Restores(self.t,'1.9.0')
    def tearDown(self):self.s.close();self.t.close();self.temp.cleanup()
    def test_roundtrip_all_modules_and_credentials_stay_out(self):
        with zipfile.ZipFile(io.BytesIO(self.backup)) as z:
            self.assertEqual(len([n for n in z.namelist() if n.endswith('.sqlite3')]),11)
            self.assertNotIn('drive-auth.json',z.namelist());self.assertNotIn('access.json',z.namelist())
            self.assertFalse(any(b'PRIVATE_FAKE' in z.read(n) for n in z.namelist()))
        old=self.t.mutate('card.save',{'number':'999','temporary':True})['id']
        preview=self.restore.preview(self.backup);self.assertEqual(preview['counts']['ib'],1)
        result=self.restore.apply(preview['token']);self.assertIsNone(self.t.get('cards',old));self.assertEqual(digest(self.s),digest(self.t))
        backup=self.t.root/'backups'/result['safety_backup'];self.assertTrue(backup.exists())
        before=Restores(self.s,'1.9.0').preview(backup.read_bytes());self.assertEqual(before['counts']['cards'],1)
    def test_changed_target_refuses_restore(self):
        result=self.restore.preview(self.backup);self.t.mutate('card.save',{'number':'7','temporary':True})
        before=digest(self.t)
        with self.assertRaisesRegex(ValueError,'ændret'):self.restore.apply(result['token'])
        self.assertEqual(digest(self.t),before)
    def test_expired_or_unknown_confirmation_rejected(self):
        with self.assertRaises(ValueError):self.restore.apply('wrong')
        p=self.restore.preview(self.backup);self.restore.pending[p['token']]['expires']=0
        with self.assertRaises(ValueError):self.restore.apply(p['token'])
    def modified(self,change):
        out=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(self.backup)) as source,zipfile.ZipFile(out,'w') as dest:
            values={n:source.read(n) for n in source.namelist()};change(values)
            for n,v in values.items():dest.writestr(n,v)
        return out.getvalue()
    def test_paths_and_unknown_database_are_rejected(self):
        for n in ('../evil','access.json','unknown.sqlite3'):
            with self.assertRaises(ValueError):self.restore.preview(self.modified(lambda f:f.update({n:b'x'})))
    def test_missing_core_database_is_rejected(self):
        with self.assertRaises(ValueError):self.restore.preview(self.modified(lambda f:f.pop('ib.sqlite3')))
    def test_older_backup_without_manifest_and_notes(self):
        old=self.modified(lambda f:(f.pop('manifest.json'),f.pop('kortnoter.sqlite3')))
        p=self.restore.preview(old);self.restore.apply(p['token']);self.assertEqual(len(self.t.all('cards')),1)
    def test_invalid_database_does_not_change_target(self):
        before=digest(self.t)
        with self.assertRaises(ValueError):self.restore.preview(self.modified(lambda f:f.update({'ib.sqlite3':b'bad database'})))
        self.assertEqual(digest(self.t),before)
    def test_import_rolls_back_every_module_on_failure(self):
        p=self.restore.preview(self.backup);before=digest(self.t)
        original=self.t.alias
        def fail(module):
            if module=='ib':raise RuntimeError('injected failure')
            return original(module)
        # Fail after some tables have been written, inside the attached-DB transaction.
        with patch.object(self.t,'alias',side_effect=fail),patch('portable.digest',return_value=self.restore.pending[p['token']]['digest']),patch('portable.snapshot',return_value=self.backup):
            with self.assertRaises(RuntimeError):self.restore.apply(p['token'])
        self.assertEqual(digest(self.t),before)
    def test_import_never_resumes_public_uploads(self):
        with self.s.transaction():self.s.put('maps',{'id':'publication:'+self.card,'entity':'publication','card_id':self.card,'status':'queued','queued_png':'PRIVATE_PENDING','url':'https://drive.google.com/file/d/fake/view'})
        p=self.restore.preview(snapshot(self.s,'1.9.0'));self.restore.apply(p['token'])
        row=self.t.get('maps','publication:'+self.card);self.assertEqual(row['status'],'review');self.assertNotIn('queued_png',row)

    def test_active_public_links_block_import_to_avoid_orphans(self):
        with self.t.transaction():self.t.put('maps',{'id':'publication:old','entity':'publication','card_id':'old','file_id':'OLD_FILE','status':'published','url':'https://drive.google.com/file/d/OLD_FILE/view'})
        p=self.restore.preview(self.backup)
        with self.assertRaisesRegex(ValueError,'offentlig adgang'):self.restore.apply(p['token'])
