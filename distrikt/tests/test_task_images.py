"""Only generated test pixels and temporary task databases."""
import base64
from contextlib import closing
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from portable import Restores, snapshot
from store import Store
from task_images import read_image


def test_png():
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\0\x64\x88\xac')) + chunk(b'IEND', b''))


class TaskImageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = Store(self.folder.name)
        self.addCleanup(self.store.close)

    def attach(self, name='Fiktivt billede.png'):
        return {'name': name, 'png': base64.b64encode(test_png()).decode()}

    def create(self):
        return self.store.mutate('note.save', {'text': 'Fiktiv opgave', 'attachments': {'add': [self.attach()]}})['id']

    def test_atomic_validation_state_and_reopen(self):
        task = self.create()
        note = self.store.get('notes', task)
        image = note['images'][0]['id']
        self.assertEqual(read_image(self.store, task, image), test_png())
        self.assertIsNone(read_image(self.store, 'other-task', image))
        self.assertNotIn(self.attach()['png'], json.dumps(self.store.state()))
        with self.assertRaises(ValueError):
            self.store.mutate('note.save', {'id': task, 'text': 'Should not save',
                'attachments': {'remove': [image], 'add': [{'name': 'bad.png', 'png': 'PHN2Zz4='}]}})
        self.assertEqual(self.store.get('notes', task), note)
        with closing(Store(self.folder.name)) as other:
            self.assertEqual(read_image(other, task, image), test_png())

    def test_concurrent_deltas_and_undo(self):
        task = self.create()
        before = self.store.get('notes', task)['images']
        for name in ('first.png', 'second.png'):
            self.store.mutate('note.save', {'text': 'Fiktiv opgave', 'id': task,
                                            'attachments': {'add': [self.attach(name)]}})
        self.store.mutate('note.save', {'text': 'Ny tekst', 'id': task})
        self.assertEqual(len(self.store.get('notes', task)['images']), 3)
        self.store.mutate('note.save', {'text': 'Ny tekst', 'id': task,
                                        'attachments': {'remove': [before[0]['id']]}})
        self.assertIsNone(self.store.get('task_images', before[0]['id']))
        self.store.mutate('workflow.undo', {})
        self.assertEqual(read_image(self.store, task, before[0]['id']), test_png())

    def test_backup_restore_old_backup_and_delete(self):
        empty = snapshot(self.store, 'test')
        task = self.create()
        ident = self.store.get('notes', task)['images'][0]['id']
        archive = snapshot(self.store, 'test')
        batch = self.store.mutate('delete', {'module': 'notes', 'id': task})['batch']
        self.assertIsNone(read_image(self.store, task, ident))
        self.store.mutate('restore', {'batch': batch})
        self.assertEqual(read_image(self.store, task, ident), test_png())
        batch = self.store.mutate('delete', {'module': 'notes', 'id': task})['batch']
        self.store.mutate('recovery.purge', {'batch': batch})
        self.assertIsNone(self.store.get('task_images', ident))
        restores = Restores(self.store, 'test')
        restores.apply(restores.preview(archive)['token'])
        self.assertEqual(read_image(self.store, task, ident), test_png())
        restores.apply(restores.preview(empty)['token'])
        self.assertIsNone(self.store.get('task_images', ident))
