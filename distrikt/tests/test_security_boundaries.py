"""Regression cases use only temporary databases and fictional connection values."""
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from portable import snapshot,Restores
from profile_policy import mutation
from sharing import Publications


class SecurityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.source=Store(Path(self.temp.name)/'source')
        self.target=Store(Path(self.temp.name)/'target')

    def tearDown(self):
        self.source.close();self.target.close();self.temp.cleanup()

    def test_composite_actions_require_each_affected_module(self):
        user={'id':'fictional','permissions':{'cards.view','cards.edit'}}
        mutation(user,'card.save',{'number':'F1'},self.source)
        with self.assertRaises(PermissionError):mutation(user,'card.save',{'number':'F1','initial_completed':'2025-01-01'},self.source)
        user['permissions']={'history.view','history.edit'}
        with self.assertRaises(PermissionError):mutation(user,'history.cleanup',{},self.source)
        user['permissions'].update(('loans.view','loans.manage','history.cleanup'))
        mutation(user,'history.cleanup',{},self.source)
        with self.source.transaction():
            self.source.put('loans',{'id':'fictional-loan','assigned':'2025-01-01'})
            self.source.put('completions',{'id':'fictional-completion','loan_id':'fictional-loan'})
        user['permissions']={'loans.view','loans.manage','publishers.view','publishers.manage'}
        mutation(user,'loan.correct',{'id':'fictional-loan','assigned':'2025-01-01'},self.source)
        with self.assertRaises(PermissionError):mutation(user,'loan.correct',{'id':'fictional-loan','assigned':'2025-01-02'},self.source)

    def test_card_import_requires_settings_only_for_new_areas(self):
        user={'id':'fictional','permissions':{'cards.view','cards.edit','geo.view'}}
        for existing in (True,False):
            token=self.source.setup_remember('card-import',{'areas':[{'name':'Fictional','existing':existing}]})
            if existing:mutation(user,'setup.card-import.apply',{'token':token},self.source)
            else:
                with self.assertRaises(PermissionError):mutation(user,'setup.card-import.apply',{'token':token},self.source)

    def test_record_backup_excludes_custom_token_and_preserves_destination_connection(self):
        self.source.mutate('geo.token',{'token':'PRIVATE_FAKE_SOURCE_VALUE'})
        self.target.mutate('geo.token',{'token':'PRIVATE_FAKE_DESTINATION_VALUE'})
        backup=snapshot(self.source,'fictional')
        with zipfile.ZipFile(io.BytesIO(backup)) as archive:
            raw=archive.read('geodata.sqlite3')
        self.assertNotIn(b'PRIVATE_FAKE_SOURCE_VALUE',raw)
        dbpath=Path(self.temp.name)/'export.sqlite3';dbpath.write_bytes(raw)
        with sqlite3.connect(dbpath) as db:
            cfg=json.loads(db.execute('SELECT payload FROM records WHERE id=?',('config',)).fetchone()[0])
        self.assertNotIn('token',cfg)
        restores=Restores(self.target,'fictional');preview=restores.preview(backup);restores.apply(preview['token'])
        self.assertEqual(self.target.get('geo','config')['token'],'PRIVATE_FAKE_DESTINATION_VALUE')

    def test_imported_publication_cannot_trigger_external_operations(self):
        with self.source.transaction():
            self.source.put('maps',{'id':'publication:fictional','entity':'publication','card_id':'absent-fictional-card',
                'file_id':'FICTIONAL_FILE_ID','possibly_public':True,'url':'https://drive.google.com/file/d/FICTIONAL_FILE_ID/view',
                'manual_withdraw':True,'next_try':0,'status':'published'})
        restores=Restores(self.target,'fictional');preview=restores.preview(snapshot(self.source,'fictional'));restores.apply(preview['token'])
        row=self.target.get('maps','publication:fictional')
        self.assertNotIn('file_id',row);self.assertNotIn('possibly_public',row)
        publications=Publications(self.target);drive=Mock();drive.connected.return_value=True;publications.drive=drive
        publications.process_one()
        for name in ('unshare','upload','share','link'):getattr(drive,name).assert_not_called()
