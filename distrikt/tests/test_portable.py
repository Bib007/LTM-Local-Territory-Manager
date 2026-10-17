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
    def test_beta_reset_backups_roundtrip_and_preserves_credentials(self):
        resets=Restores(self.s,'1.12.0-beta.9');preview=resets.preview(self.backup)
        before=digest(self.s);old_revision=self.s.revision
        result=resets.reset_beta('NULSTIL BETA',old_revision)
        self.assertNotEqual(old_revision,self.s.revision)
        for module in MODULES:self.assertEqual(len(self.s.all(module)),1 if module=='settings' else 0)
        self.assertFalse(self.s.state()['undo_available']);self.assertEqual(self.s._setup_previews,{})
        self.assertEqual(resets.pending,{})
        self.assertEqual((self.s.root/'drive-auth.json').read_text(),'PRIVATE_FAKE_SECRET')
        self.assertEqual((self.s.root/'access.json').read_text(),'PRIVATE_FAKE_PASSWORD')
        backup=self.s.root/'backups'/result['safety_backup']
        data=resets.preview(backup.read_bytes());self.assertEqual(data['counts']['cards'],1)
        resets.apply(data['token']);self.assertEqual(digest(self.s),before)

    def test_beta_reset_refuses_invalid_confirmation_stale_data_or_shared_maps(self):
        resets=Restores(self.s,'1.12.0-beta.9');before=digest(self.s)
        for confirmation,revision in [('yes',self.s.revision),('NULSTIL BETA','old')]:
            with self.assertRaises(ValueError):resets.reset_beta(confirmation,revision)
            self.assertEqual(before,digest(self.s))
        for status in ('published','ready','withdraw_failed'):
            with self.s.transaction():self.s.put('maps',{'id':'p','entity':'publication','file_id':'FAKE','status':status})
            before=digest(self.s)
            with self.assertRaisesRegex(ValueError,'offentlig'):resets.reset_beta('NULSTIL BETA',self.s.revision)
            self.assertEqual(before,digest(self.s))
        with self.s.transaction():self.s.put('maps',{'id':'p','entity':'publication','file_id':'FAKE','status':'private'})
        resets.reset_beta('NULSTIL BETA',self.s.revision)

    def test_beta_reset_preserves_data_if_backup_or_transaction_fails(self):
        resets=Restores(self.s,'1.12.0-beta.9');before=digest(self.s)
        with patch('portable.snapshot',side_effect=OSError('fictional disk full')):
            with self.assertRaises(OSError):resets.reset_beta('NULSTIL BETA',self.s.revision)
        self.assertEqual(before,digest(self.s))
        with patch.object(self.s,'put',side_effect=RuntimeError('fictional transaction failure')):
            with self.assertRaises(RuntimeError):resets.reset_beta('NULSTIL BETA',self.s.revision)
        self.assertEqual(before,digest(self.s))

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
    def test_preview_visible_counts_match_restored_lists_and_preserve_history(self):
        self.s.mutate('note.save',{'card_id':self.card,'text':'Fiktiv kortnote'})
        self.s.mutate('note.save',{'text':'Fiktiv generel opgave','task':True})
        deleted=self.s.mutate('note.save',{'text':'Fiktiv slettet note'})['id']
        self.s.mutate('delete',{'module':'notes','id':deleted})
        with self.s.transaction():self.s.put('cards',{'id':'archived-fictional','number':'99','archived':True,'addresses':[]})
        before=digest(self.t);preview=self.restore.preview(snapshot(self.s,'1.12.0-beta.9'))
        self.assertEqual(digest(self.t),before,'A preview must not replace target data')
        self.assertEqual(preview['counts']['cards'],2)
        self.assertGreater(preview['counts']['notes'],2,'The original raw count still includes activity')
        source=self.s.state()
        for key in ('cards','publishers','loans','ib','completions','notes'):
            self.assertEqual(preview['visible_counts'][key],len(source[key]),key)
        self.assertEqual(preview['visible_counts']['cards'],1)
        self.assertEqual(preview['visible_counts']['notes'],2)
        self.restore.apply(preview['token']);restored=self.t.state()
        for key in ('cards','publishers','loans','ib','completions','notes'):
            self.assertEqual(preview['visible_counts'][key],len(restored[key]),key)
        self.assertEqual(restored['archived_cards'][0]['id'],'archived-fictional')
        self.assertTrue(any(n.get('entity')=='activity' for n in self.t.all('notes')))
        self.assertEqual(digest(self.s),digest(self.t),'Archived cards and activity must still be restored')
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
