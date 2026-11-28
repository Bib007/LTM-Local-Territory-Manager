from datetime import date, timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store


class TerritoryHelperImportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = Store(self.directory.name)
        self.addCleanup(self.store.close)
        self.preview_action = 'setup.territory-helper.preview'
        self.apply_action = 'setup.territory-helper.apply'
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        self.earlier = self.today - timedelta(days=2)
        self.polygon = [[10, 55], [10.01, 55], [10.01, 55.01], [10, 55]]

    def example(self):
        return {
            'cards': 'TerritoryId;TerritoryNumber;Label;TerritoryType;Notes\na;01;Testkort A;City;<h3>Overskrift</h3><p>Ved havnen</p><script>skjult()</script>\nb;02;Testkort B;Rural;',
            'locations': 'TerritoryId,Street,HouseNumber,PostalCode,Latitude,Longitude\na,Testvej,4A,1234,55.001,10.003\nb,Eksempelvej,17,4321,55.002,10.003\nunknown,Uden tilknytning,01,1234,,',
            'ib': 'TerritoryId,Street,HouseNumber,PostalCode,Date,Notes\na,Testvej,4A,1234,,Testbemærkning',
            'publishers': 'PublisherId;First Name;Last Name\np;Fiktiv;Forsøg',
            'assignments': ('TerritoryId,PublisherId,DateAssigned,DateReturned,Completed\n'
                            f'a,p,{self.earlier},{self.yesterday},true\n'
                            f'b,p,{self.yesterday},{self.today},false'),
            'geometry': json.dumps([{'Id': 'a', 'Number': '01', 'Boundary': json.dumps(self.polygon)}]),
            'kml': '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>02</name><Polygon><outerBoundaryIs><LinearRing><coordinates>10,55 10.01,55 10.01,55.01 10,55</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>',
        }

    def test_upload_all_files_approval_is_per_card(self):
        present = self.store.revision
        result = self.store.mutate(self.preview_action, {'files': self.example(), '_owner': 'test'})
        self.assertEqual(result['unmatched'], {'locations': 1})
        self.assertEqual(result['cards'][0]['polygon'], self.polygon[:-1])
        self.assertEqual(result['cards'][1]['polygon'], self.polygon[:-1])
        self.assertEqual(result['cards'][0]['assignments'][0]['publisher'], 'Fiktiv Forsøg')
        self.assertEqual(self.store.revision, present)
        self.assertFalse(self.store.all('cards'))
        payload = {'token': result['token'], '_owner': 'test', 'index': 0}
        with self.assertRaises(PermissionError):
            self.store.mutate(self.apply_action, {**payload, '_owner': 'other'})
        saved = self.store.mutate(self.apply_action, payload)
        card, = self.store.all('cards')
        self.assertEqual(card['number'], '01')
        self.assertEqual(card['import_note'], 'Overskrift\nVed havnen')
        self.assertEqual(card['geo_polygon'], self.polygon[:-1])
        self.assertEqual(card['imported_addresses'][0]['lng'], 10.003)
        self.assertEqual(self.store.all('ib')[0]['import_note'], 'Testbemærkning')
        event, = self.store.all('completions')
        self.assertEqual(event['card_id'], saved['id'])
        self.assertTrue(event['visits_unknown'])
        self.assertEqual(len(self.store.all('loans')), 1)

        with self.assertRaises(ValueError):
            self.store.mutate(self.apply_action, payload)
        self.store.mutate(self.apply_action, {**payload, 'index': 1})
        self.assertEqual({card['number'] for card in self.store.all('cards')}, {'01', '02'})
        self.assertEqual(len(self.store.all('loans')), 2)
        self.assertEqual(len(self.store.all('completions')), 1)
        self.assertEqual(len(self.store.all('publishers')), 1)

    def test_unknown_reference_does_not_match_house_number(self):
        result = self.store.mutate(self.preview_action, {'files': {
            'cards': 'TerritoryId,Number\na,01',
            'locations': 'Street,Number\nTestvej,01',
        }})
        self.assertEqual(result['unmatched'], {'locations': 1})
        self.assertFalse(result['cards'][0]['locations'])

    def test_existing_or_invalid_card_is_not_written(self):
        existing = self.store.mutate('card.save', {'number': '01', 'name': 'Før import'})
        result = self.store.mutate(self.preview_action, {'files': self.example()})
        self.assertTrue(result['cards'][0]['errors'])
        with self.assertRaises(ValueError):
            self.store.mutate(self.apply_action, {'token': result['token'], 'index': 0})
        self.assertEqual(self.store.require('cards', existing['id'])['name'], 'Før import')
        self.assertFalse(self.store.all('ib'))
