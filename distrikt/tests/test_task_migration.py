"""Lossless task promotion, using invented local records and legacy backups only."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store, now
from portable import Restores, snapshot


class TaskMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.addCleanup(lambda:self.store.close())
        self.card=self.store.mutate('card.save',{'number':'FIKTIV','temporary':True})['id']

    def legacy(self,ident,**extra):
        item={'id':ident,'text':'Fiktiv opfølgning <bevar>\nanden linje',
              'card_id':self.card,'date':'2026-10-01','created':'2026-10-01T10:00:00Z',
              'resolved':False,'task':False}
        item.update(extra)
        return item

    def raw_insert(self,item,deleted_at=None,batch=None):
        self.store.db.execute('INSERT INTO notes.records(id,payload,deleted_at,batch) VALUES(?,?,?,?)',
                              (item['id'],json.dumps(item),deleted_at,batch))

    def test_startup_promotes_active_and_recoverable_rows_without_touching_activity(self):
        original=[self.legacy('old'),self.legacy('done',resolved=True,resolved_at='2026-10-02T12:00:00Z'),
                  self.legacy('deleted',task=None),{'id':'activity','entity':'activity','action':'note.save','count':1}]
        stamp=now()
        with self.store.transaction():
            for item in original:self.raw_insert(item,stamp if item['id']=='deleted' else None,'invented-batch' if item['id']=='deleted' else None)
        self.store.close();self.store=Store(self.temp.name)
        for item in original:
            expected=dict(item,task=True) if item.get('entity')!='activity' else item
            self.assertEqual(self.store.get('notes',item['id'],deleted=True),expected)
        deleted=self.store.all('notes',deleted=True)[0]
        self.assertEqual((deleted['_deleted_at'],deleted['_batch']),(stamp,'invented-batch'))
        rows=[tuple(r) for r in self.store.db.execute('SELECT * FROM notes.records ORDER BY id')]
        self.store.close();self.store=Store(self.temp.name)
        self.assertEqual([tuple(r) for r in self.store.db.execute('SELECT * FROM notes.records ORDER BY id')],rows)

    def test_legacy_backup_is_promoted_only_after_explicit_restore(self):
        item=self.legacy('restored',resolved=True,resolved_at='2026-10-02T12:00:00Z')
        with self.store.transaction():self.raw_insert(item)
        raw=snapshot(self.store,'FICTIONAL-OLD')
        restores=Restores(self.store,'FICTIONAL-NEW');preview=restores.preview(raw)
        self.assertFalse(self.store.get('notes','restored')['task'],'Preview must not migrate live records')
        restores.apply(preview['token'])
        self.assertEqual(self.store.get('notes','restored'),dict(item,task=True))
        self.assertTrue(self.store.state()['notes'][0]['resolved'])

    def test_migration_uses_callers_transaction_and_preserves_rollback(self):
        item=self.legacy('rollback')
        with self.store.transaction():self.raw_insert(item)
        before=copy.deepcopy(self.store.get('notes','rollback'));revision=self.store.revision
        with self.assertRaises(RuntimeError):
            with self.store.transaction():
                self.store.migrate_tasks()
                raise RuntimeError('Fictional failure before commit')
        self.assertEqual(self.store.get('notes','rollback'),before)
        self.assertEqual(self.store.revision,revision)

    def test_old_clients_cannot_create_non_tasks_and_edit_preserves_completion(self):
        ident=self.store.mutate('note.save',{'card_id':self.card,'text':'Fiktiv opgave','task':False})['id']
        self.assertTrue(self.store.get('notes',ident)['task'])
        self.store.mutate('note.resolve',{'id':ident,'resolved':True})
        completed=self.store.get('notes',ident)['resolved_at']
        self.store.mutate('note.save',{'id':ident,'card_id':self.card,'text':'Rettet fiktiv opgave','task':False})
        item=self.store.get('notes',ident)
        self.assertTrue(item['task']);self.assertTrue(item['resolved'])
        self.assertEqual(item['resolved_at'],completed);self.assertEqual(item['card_id'],self.card)
        self.store.mutate('note.resolve',{'id':ident,'resolved':False})
        self.assertFalse(self.store.get('notes',ident)['resolved'])


if __name__=='__main__':unittest.main()
