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

        self.assertEqual(self.store.mutate(self.apply_action, payload)['id'], card['id'])
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

    def test_kml_preview_accepts_500_boundaries_and_rejects_501(self):
        def kml(count):
            placemarks = ''.join(
                f'<Placemark><name>{index}</name><Polygon><outerBoundaryIs><LinearRing>'
                '<coordinates>10,55 10.01,55 10.01,55.01 10,55</coordinates>'
                '</LinearRing></outerBoundaryIs></Polygon></Placemark>'
                for index in range(1, count + 1)
            )
            return '<kml><Document>' + placemarks + '</Document></kml>'

        cards = 'TerritoryId,Number\n' + '\n'.join(f'test-{number},{number}' for number in range(1, 501))
        result = self.store.mutate(self.preview_action, {'files': {'cards': cards, 'kml': kml(500)}})
        self.assertEqual(len(result['cards']), 500)
        self.assertTrue(all(card['polygon'] == self.polygon[:-1] for card in result['cards']))
        self.assertEqual(result['unmatched'], {})
        with self.assertRaisesRegex(ValueError, '500 grænser'):
            self.store.mutate(self.preview_action, {'files': {'cards': cards, 'kml': kml(501)}})

    def test_danish_exports_are_sorted_and_joined_by_type_and_number(self):
        def upload(name, content):
            return {'name': 'Test - ' + name + '.csv', 'content': content}

        address_header = 'Distriktstype,Distriktsnummer,Lokationstype,Status,Breddegrad,Længdegrad,Adresse,Nummer,Vej,Enhed,Etage,By,Kommune,Postnummer,Stat,Landekode,Sidst besøgt,Sidst opdateret,Dato oprettet'
        uploads = [
            upload('IB (1)', address_header + '\nLand,01,Adresse,IB,55.01,10.01,Testvej 4,4,Testvej,th,1,,,1234,,DK,,,' + str(self.today)),
            upload('Tildelinger', 'Distriktstype,Distriktsnummer,Distriktsmærke,Navn,E-mail,Telefon,Tildelt,Indleveret,Ikke gennemgået,Notater\n'
                   + f'By,01,Fiktivt kort,Eksempel Bruger,,,{self.earlier:%d-%m-%Y} 12:30,{self.yesterday},Nej,'),
            upload('Distrikter', 'TerritoryId,Distriktstype,Nummer,Mærke,Inkluder i statistikken,URL-ID,Vis URL,Udskriv URL,Billedets URL,Grænse,Mærkater,Notater,Dato oprettet\n'
                   'abc,By,01,Fiktivt kort,true,,,,,,,<b>Byens kort</b>,\nxyz,Land,01,Landkort,true,,,,,,,,'),
            upload('Forkyndere', 'Fornavn,Efternavn,E-mail,Telefon,Rolle,Aktiv,Sidst opdateret,Dato oprettet\n'
                   'Eksempel,Bruger,,,Test,true,,'),
            upload('Lokationer', address_header + '\nBy,01,Adresse,Aktiv,55.01,10.01,Testvej 3,3,Testvej,,,,,1234,,DK,,,')
        ]
        result = self.store.mutate(self.preview_action, {'uploads': uploads})
        self.assertEqual(set(result['sources']), {'cards', 'locations', 'ib', 'publishers', 'assignments'})
        self.assertEqual(result['unmatched'], {})
        urban, rural = result['cards']
        self.assertEqual((urban['number'], rural['number']), ('By-01', 'Land-01'))
        self.assertEqual(urban['note'], 'Byens kort')
        self.assertEqual(urban['locations'][0]['number'], '3')
        self.assertTrue(urban['assignments'][0]['completed'])
        self.assertEqual((rural['ib'][0]['number'], rural['ib'][0]['floor'], rural['ib'][0]['door']), ('4', '1', 'th'))
        self.assertEqual(rural['assignments'], [])

    def test_number_collision_keeps_existing_card_and_imports_under_temporary_number(self):
        existing = self.store.mutate('card.save', {'number': '01', 'name': 'Før import'})
        result = self.store.mutate(self.preview_action, {'files': self.example()})
        self.assertTrue(result['cards'][0]['errors'])
        saved = self.store.mutate(self.apply_action, {'token': result['token'], 'index': 0})
        self.assertEqual(self.store.require('cards', existing['id'])['name'], 'Før import')
        self.assertEqual(saved['number'], 'TH-1')
        self.assertEqual(self.store.all('ib')[0]['card_id'], saved['id'])
        task, = [row for row in self.store.all('notes') if row.get('card_id') == saved['id'] and row.get('task')]
        issue, = task['territory_helper_issues']
        self.assertEqual(issue['fields'], {'number': '01'})
        self.store.mutate('setup.territory-helper.repair',
                          {'id': task['id'], 'issue_id': issue['id'], 'fields': {'number': '99'}})
        self.assertEqual(self.store.require('cards', saved['id'])['number'], '99')

    def test_bulk_keeps_warnings_and_groups_locations_without_print_tasks(self):
        files = {
            'cards': 'TerritoryId,Number,Notes\na,01,Testnotat\nb,02,',
            'locations': ('TerritoryId,Street,HouseNumber,PostalCode,Latitude,Longitude\n'
                          'a,Testvej,1,1234,55.0,10.0\na,Testvej,3,1234,55.0,10.001\na,Testvej,,1234,55.0,10.002'),
            'ib': 'TerritoryId,Street,HouseNumber,PostalCode\na,Testvej,3,1234',
        }
        occupied = self.store.mutate('card.save', {'number': '02', 'name': 'Eksisterende'})
        preview = self.store.mutate(self.preview_action, {'files': files})
        result = self.store.mutate(self.apply_action, {'token': preview['token'], 'all': True})
        saved, collision = result['saved']
        self.assertEqual(result['skipped'], [])
        self.assertEqual(collision['number'], 'TH-2')
        card = self.store.require('cards', saved['id'])
        self.assertEqual(self.store.require('cards', occupied['id'])['name'], 'Eksisterende')
        self.assertEqual(len(card['addresses']), 1)
        self.assertEqual(card['addresses'][0]['count'], 2)
        self.assertEqual(len(card['imported_addresses']), 2)
        self.assertFalse(card['front_revision'])
        self.assertFalse(card['back_revision'])
        warning, = [note for note in self.store.all('notes') if note.get('task') and note['card_id'] == saved['id']]
        self.assertEqual(json.loads(warning['followup_key']), ['checks', card['id'], 'territory-helper'])
        self.assertTrue(warning['text'])
        self.assertEqual(len(self.store.all('ib')), 1)

    def test_bulk_continues_after_invalid_card_number_and_ib_rows(self):
        future = self.today + timedelta(days=1)
        files = {
            'cards': 'TerritoryId,Number\na,01\nb,\nc,03\nd,04',
            'ib': ('TerritoryId,Street,HouseNumber,Floor,Date\n'
                   f'a,Testvej,1,,{future}\na,Testvej,{"1" * 80},1,\na,Testvej,2,,{self.today}'),
        }
        preview = self.store.mutate(self.preview_action, {'files': files})
        result = self.store.mutate(self.apply_action, {'token': preview['token'], 'all': True})
        self.assertEqual([row['number'] for row in result['saved']], ['01', 'TH-2', '03', '04'])
        self.assertFalse(result['skipped'])
        self.assertEqual([row['number'] for row in self.store.all('ib')], ['2'])
        warning, = [note for note in self.store.all('notes') if note.get('task') and note['card_id'] == result['saved'][0]['id']]
        self.assertIn('IB-dato ligger i fremtiden', warning['text'])
        self.assertIn('for langt husnummer', warning['text'])

    def test_invalid_locations_and_ib_can_be_repaired_after_bulk_approval(self):
        files = {
            'cards': 'TerritoryId,Number\na,57\nb,70',
            'locations': 'TerritoryId,Street,HouseNumber,PostalCode\na,Testvej,,1234\nb,Testvej,2-6,1234\nb,Testvej,8,1234',
            'ib': 'TerritoryId,Street,HouseNumber,PostalCode\nb,Testvej,3/5,1234',
        }
        preview = self.store.mutate(self.preview_action, {'files': files})
        self.assertIn('tomt husnummerfelt', preview['cards'][0]['errors'][0])
        saved = self.store.mutate(self.apply_action, {'token': preview['token'], 'all': True})['saved']
        first, second = saved
        self.assertEqual(self.store.require('cards', second['id'])['addresses'][0]['numbers'], '8')
        self.assertFalse(self.store.all('ib'))
        tasks = {note['card_id']: note for note in self.store.all('notes') if note.get('task')}
        for card in (first, second):
            task = tasks[card['id']]
            data = {'id': task['id']}
            entries = self.store.mutate('setup.territory-helper.review', data)['issues']
            self.assertEqual(entries[0]['fields']['house'], '' if card is first else '2-6')
            self.assertIn('housenumber', entries[0]['source'])
            for entry, number in zip(entries, ('4', '5')):
                self.store.mutate('setup.territory-helper.repair', {
                    **data, 'issue_id': entry['id'], 'fields': {**entry['fields'], 'house': number},
                })
            self.assertTrue(self.store.require('notes', task['id'])['resolved'])
        self.assertEqual(self.store.all('ib')[0]['number'], '5')
        self.assertEqual(len(self.store.require('cards', second['id'])['imported_addresses']), 2)
        again = self.store.mutate(self.preview_action, {'files': files})
        result = self.store.mutate(self.apply_action, {'token': again['token'], 'all': True})
        self.assertEqual([row['id'] for row in result['saved']], [first['id'], second['id']])
        self.assertEqual(len(self.store.all('cards')), 2)
        self.assertEqual(len(self.store.all('ib')), 1)

    def test_reimport_reuses_legacy_card_and_preserves_existing_history(self):
        files = self.example()
        preview = self.store.mutate(self.preview_action, {'files': files})
        ident = self.store.mutate(self.apply_action, {'token': preview['token'], 'index': 0})['id']
        legacy = dict(self.store.require('cards', ident))
        legacy.pop('territory_helper_import_id')
        with self.store.transaction():
            self.store.put('cards', legacy)
        files['locations'] += '\na,Testvej,4-10,1234,,'
        preview = self.store.mutate(self.preview_action, {'files': files})
        saved = self.store.mutate(self.apply_action, {'token': preview['token'], 'all': True})['saved']
        self.assertEqual(saved[0]['id'], ident)
        self.assertEqual(len(self.store.all('cards')), 2)
        self.assertEqual(len(self.store.all('loans')), 2)
        self.assertEqual(len(self.store.all('ib')), 1)
        note, = [row for row in self.store.all('notes') if row.get('card_id') == ident and row.get('task')]
        self.assertEqual(note['territory_helper_issues'][0]['fields']['house'], '4-10')

    def test_dar_suggestions_use_imported_coordinates_and_keep_kml_boundary(self):
        files = self.example()
        preview = self.store.mutate(self.preview_action, {'files': files})
        ident = self.store.mutate(self.apply_action, {'token': preview['token'], 'index': 0})['id']
        boundary = self.store.require('cards', ident)['geo_polygon']
        dar = {'entity': 'address', 'type': 'Hus', 'count': 1, 'postcode': '1234', 'road': 'Nyt vejnavn',
               'number': '4A', 'lat': 55.00101, 'lng': 10.003, 'source': 'DAR / Adressevælger'}
        with self.store.transaction():
            self.store.put('geo', dict(dar, id='near'))
            self.store.put('geo', dict(dar, id='far', lat=55.01))
            self.store.put('geo', dict(dar, id='wrong-number', number='4B'))
        data = {'mode': 'imported_points', 'card_id': ident}
        result = self.store.geo_preview_snapshot()[0].geo_preview(data)
        self.assertEqual([a['id'] for a in result['addresses']], ['near'])
        self.assertEqual(result['unmatched_points'], 0)
        self.assertEqual(self.store.require('cards', ident)['geo_polygon'], boundary)
        with self.store.transaction():
            self.store.put('geo', dict(dar, id='apartment', floor='1', door='th'))
        result = self.store.geo_preview_snapshot()[0].geo_preview(data)
        self.assertFalse(result['addresses'])
        self.assertEqual(result['unmatched_points'], 1)

    def test_kml_matches_extended_id_folder_labels_and_known_geometry(self):
        def mark(name, x, *, data='', folder=''):
            polygon = f'<Polygon><outerBoundaryIs><LinearRing><coordinates>{x},55 {x + 0.01},55 {x + 0.01},55.01 {x},55</coordinates></LinearRing></outerBoundaryIs></Polygon>'
            return f'<Folder><name>{folder}</name><Placemark><name>{name}</name>{data}{polygon}</Placemark></Folder>'

        marks = [
            mark('01', 10, folder='By'),
            mark('01', 11, folder='Land'),
            mark('Kort 02 — Midtbyen', 12),
            mark('', 13, data='<ExtendedData><Data name="TerritoryId"><value>d</value></Data></ExtendedData>'),
            mark('', 14),
            mark('Ukendt navn', 15),
        ]
        cards = 'TerritoryId,Number,TerritoryType,Label\na,01,By,A\nb,01,Land,B\nc,02,By,Midtbyen\nd,03,By,D\ne,04,By,E'
        boundary = [[14, 55], [14.01, 55], [14.01, 55.01], [14, 55]]
        geometry = json.dumps([{'Id': 'e', 'Number':'04', 'Boundary': json.dumps(boundary)}])
        preview = self.store.mutate(self.preview_action, {'files': {
            'cards': cards, 'geometry': geometry, 'kml': '<kml>' + ''.join(marks) + '</kml>',
        }})
        self.assertEqual([c['polygon'][0][0] for c in preview['cards']], [10, 11, 12, 13, 14])
        self.assertEqual(preview['unmatched'], {'kml': 1})
        warning, = preview['unmatched_details']
        self.assertEqual(warning['context']['kml_name'], 'Ukendt navn')
        self.assertEqual(warning['context']['kml_index'], '6')

    def test_invalid_kml_and_address_show_source_and_exact_reason(self):
        cards = 'TerritoryId,Number\na,57'
        locations = 'TerritoryId,Street,HouseNumber,PostalCode,Address\na,Testvej,,1234,Testvej ved stien\nx,Andenvej,42,1234,'
        kml = '<kml><Placemark><name>57</name><LineString><coordinates>10,55 10.01,55 10.01,55.01</coordinates></LineString></Placemark></kml>'
        preview = self.store.mutate(self.preview_action, {'files': {'cards': cards, 'locations': locations, 'kml': kml}})
        boundary, location = preview['cards'][0]['diagnostics']
        self.assertIn('ikke lukket', boundary['detail'])
        self.assertEqual(boundary['context']['kml_name'], '57')
        self.assertEqual(location['context']['row'], '2')
        self.assertEqual(location['context']['road'], 'Testvej')
        self.assertEqual(location['context']['house'], '')
        self.assertEqual(location['context']['address'], 'Testvej ved stien')
        unmatched, = preview['unmatched_details']
        self.assertEqual(unmatched['context']['card_id'], 'x')
        self.assertEqual(unmatched['params']['id'], 'x')
        self.assertEqual(unmatched['context']['road'], 'Andenvej')

    def test_reimport_recovers_newly_matched_boundary_and_closes_old_followup(self):
        kml = '<kml><Placemark><name>Kort 57</name><Polygon><outerBoundaryIs><LinearRing><coordinates>10,55 10.01,55 10.01,55.01 10,55</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></kml>'
        files = {'cards': 'TerritoryId,Number\na,57', 'kml': kml}
        preview = self.store.mutate(self.preview_action, {'files': files})
        plan = self.store.setup_require_preview({'token': preview['token']}, 'territory-helper')
        source = plan['cards'][0]
        source['polygon'] = []
        plan['kml_matches'].clear()
        plan['unlinked'].append({'id':'old', 'kind':'boundary', 'fields':{'boundary':'[]'},
                                  'message':'Rækker uden entydigt kort', 'source':{'index':0, 'name':'Kort 57'}})
        old = self.store.mutate(self.apply_action, {'token': preview['token'], 'all': True})['saved'][0]
        self.assertFalse(self.store.require('cards', old['id']).get('geo_polygon'))
        preview = self.store.mutate(self.preview_action, {'files': files})
        saved = self.store.mutate(self.apply_action, {'token': preview['token'], 'all': True})['saved'][0]
        self.assertEqual(saved['id'], old['id'])
        self.assertEqual(self.store.require('cards', saved['id'])['geo_polygon'], self.polygon[:-1])
        note, = [note for note in self.store.all('notes') if note.get('task')]
        self.assertTrue(note['resolved'])

    def test_outer_boundary_preview_encloses_district_corners_without_saving(self):
        from geography import point_in_polygon

        source = self.store.mutate(self.preview_action, {'files': self.example()})
        self.store.mutate(self.apply_action, {'token': source['token'], 'all': True})
        result = self.store.mutate('geo.main.suggest.preview', {})
        self.assertIsNone(self.store.main_boundary())
        self.assertTrue(all(point_in_polygon(point, result['points']) for point in self.polygon))

    def test_note_suggestions_use_only_locally_downloaded_dar_road_names(self):
        from territory_helper_import import note_roads

        self.store.put('geo', {'id': 'test-dar', 'entity': 'address', 'road': 'Testvej',
                              'postcode': '1234', 'number': '1', 'lat': 55.0, 'lng': 10.0, 'source': 'DAR / Adressevælger'})
        self.assertEqual(note_roads(self.store, 'Testvej 1–5\nAnden vej 1–2\nTestvej 3 er lukket'), [
            {'road': 'Testvej', 'postcode': '1234', 'numbers': '1–5'}
        ])
        self.store.put('geo', {'id': 'test-dar-2', 'entity': 'address', 'road': 'Testvej', 'postcode': '5678',
                              'number': '1', 'lat': 55.0, 'lng': 10.0, 'source': 'DAR / Adressevælger'})
        self.assertEqual(note_roads(self.store, 'Testvej 1–5'), [])
