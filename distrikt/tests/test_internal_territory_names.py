"""Fictional regression fixtures for private, optional territory names."""
import csv
import io
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from profile_policy import mutation, CARD_FIELDS
from profile_edits import SAVE, REVIEW_FIELDS
from portable import snapshot, Restores
from readable_export import tables
from sharing import Publications, fingerprint


class InternalTerritoryNameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def create(self, **extra):
        data = {'number': '25', 'internal_number': 'B07', 'name': 'Fiktiv syd',
                'temporary': True, 'addresses': []}
        data.update(extra)
        return self.store.mutate('card.save', data)['id']

    def test_legacy_defaults_and_old_client_save_preserve_new_label(self):
        ident = self.create()
        card = self.store.require('cards', ident)
        with self.store.transaction():
            card.pop('internal_name', None)
            self.store.put('cards', card)
        self.assertEqual(self.store.state()['cards'][0]['internal_name'], '')
        self.store.mutate('card.save', dict(self.store.require('cards', ident),
                                            internal_name='Ved den fiktive skole'))
        before = self.store.require('cards', ident)
        self.store.mutate('card.save', {'id': ident, 'number': '25', 'name': 'Fiktiv syd',
                                       'internal_number': 'B07',
                                       'temporary': True, 'addresses': []})
        after = self.store.require('cards', ident)
        self.assertEqual(after['internal_name'], 'Ved den fiktive skole')
        self.assertEqual((after['id'], after['number'], after['internal_number'], after['name']),
                         (ident, '25', 'B07', 'Fiktiv syd'))
        self.assertEqual((after['front_revision'], after['back_revision']),
                         (before['front_revision'], before['back_revision']))

    def test_unicode_long_name_update_clear_restart_and_relationships(self):
        ident = self.create(internal_name='Fiktiv skole – område øst')
        publisher = self.store.mutate('publisher.save', {'name': 'Fiktiv person'})['id']
        loan = self.store.mutate('loan.issue', {
            'card_id': ident, 'publisher_id': publisher, 'initial': True, 'date': '2026-10-01'
        })['id']
        ib = self.store.mutate('ib.save', {
            'card_id': ident, 'road': 'Fiktiv vej', 'number': '7', 'date': '2026-10-01'
        })['id']
        self.store.close()
        self.store = Store(self.tmp.name)
        card = self.store.require('cards', ident)
        self.assertEqual(card['internal_name'], 'Fiktiv skole – område øst')
        self.store.mutate('card.save', dict(card, internal_name=''))
        self.assertEqual(self.store.require('cards', ident)['internal_name'], '')
        self.assertEqual(self.store.require('loans', loan)['card_id'], ident)
        self.assertEqual(self.store.require('ib', ib)['card_id'], ident)

    def test_length_validation_and_shared_names_do_not_collide(self):
        ident = self.create(internal_name='Samme område')
        self.store.mutate('card.save', {'number':'26', 'name':'Andet officielt navn',
                                        'internal_name':'Samme område', 'temporary':True, 'addresses':[]})
        before = self.store.require('cards', ident)
        with self.assertRaisesRegex(ValueError, 'for lang'):
            self.store.mutate('card.save', dict(before, internal_name='x'*161))
        self.assertEqual(self.store.require('cards', ident), before)

    def test_csv_import_optional_column_and_readable_export(self):
        text = 'kortnummer;kortnavn;internt_nummer;internt_navn\n25;Fiktiv syd;B07;Ved den fiktive skole\n'
        plan = self.store.mutate('setup.card-import.preview', {'name':'fiktivt.csv','content':text})
        self.assertFalse(plan['errors'])
        ident = self.store.mutate('setup.card-import.apply', {
            'token':plan['token'], 'confirm':'IMPORTÉR KORT'
        })['ids'][0]
        card = self.store.require('cards', ident)
        self.assertEqual((card['number'],card['name'],card['internal_number'],card['internal_name']),
                         ('25','Fiktiv syd','B07','Ved den fiktive skole'))
        rows = list(csv.DictReader(io.StringIO(
            tables(self.store.state(), [])['CSV/kort.csv'].decode('utf-8-sig')
        ), delimiter=';'))
        self.assertEqual(rows[0]['kort_id'], ident)
        self.assertEqual(rows[0]['internt_nummer'], 'B07')
        self.assertEqual(rows[0]['internt_navn'], 'Ved den fiktive skole')

    def test_legacy_csv_import_and_column_map_support(self):
        old = self.store.mutate('setup.card-import.preview', {
            'name':'fiktivt.csv', 'content':'kortnummer;kortnavn\n25;Fiktiv syd\n'})
        self.assertFalse(old['errors'])
        self.store.mutate('setup.card-import.apply', {
            'token':old['token'], 'confirm':'IMPORTÉR KORT'})
        self.assertEqual(self.store.state()['cards'][0]['internal_name'],'')
        from column_import import schema
        self.assertIn('internal_name', [key for key, _, _ in schema('card')])
        self.assertIn('internal_number', [key for key, _, _ in schema('card')])

    def test_profile_access_edit_review_and_public_share_field_allowlist(self):
        ident = self.create(internal_name='Privat genkendelsesnavn')
        self.assertIn('internal_name', CARD_FIELDS)
        self.assertIn('internal_name', SAVE['card.save'][1])
        self.assertIn('internal_name', REVIEW_FIELDS['cards'])
        with self.assertRaises(PermissionError):
            mutation({'id':'readonly','permissions':{'cards.view'}}, 'card.save',
                     {'id':ident, 'number':'25', 'internal_name':'Uautoriseret'}, self.store)
        mutation({'id':'editor','permissions':{'cards.view','cards.edit'}}, 'card.save',
                 {'id':ident, 'number':'25', 'internal_name':'Tilladt'}, self.store)
        c = self.store.require('cards', ident)
        before = fingerprint(self.store, c)
        self.store.mutate('card.save', dict(c, internal_name='Ændret privat navn'))
        after = self.store.require('cards', ident)
        self.assertEqual(fingerprint(self.store, after), before)
        publication = Publications(self.store)
        # A fictional manual-front card produces a public payload with an explicit allowlist.
        card = dict(after, temporary=False,
                    addresses=[{'road':'Fiktiv vej','numbers':'1','count':1,'type':'Hus'}])
        self.store.mutate('card.save', card)
        public = publication.prepare(ident)['card']
        self.assertEqual(public['name'], 'Fiktiv syd')
        self.assertNotIn('internal_name', public)
        self.assertNotIn('internal_number', public)

    def test_full_backup_roundtrip_retains_internal_name(self):
        ident = self.create(internal_name='Privat felt i backup')
        with tempfile.TemporaryDirectory() as directory:
            target = Store(directory)
            try:
                restore = Restores(target, 'fictional')
                preview = restore.preview(snapshot(self.store, 'fictional'))
                restore.apply(preview['token'])
                self.assertEqual(target.require('cards', ident)['internal_name'],
                                 'Privat felt i backup')
            finally:
                target.close()


if __name__ == '__main__':
    unittest.main()
