"""Synthetic flat DAR sets: complete local joins and stable LTM address shape."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from dar_join import join_addresses
from dar_paging import IncompleteResult
from postcode import rest_addresses
from dar_query import DarQuery
from address_source import Datafordeler


def fixture():
    return [
        [{'id_lokalId': 'a1', 'status': '3', 'husnummer': 'h1', 'adressebetegnelse': 'Prøvevej 12B, 2. tv., 9999 Prøveby',
          'etagebetegnelse': '2', 'doerbetegnelse': 'tv'},
         {'id_lokalId': 'a2', 'status': '3', 'husnummer': 'h1', 'adressebetegnelse': 'Prøvevej 12B, 9999 Prøveby',
          'etagebetegnelse': None, 'doerbetegnelse': ''}],
        [{'id_lokalId': 'h1', 'status': '3', 'husnummertekst': '12B', 'navngivenVej': 'r1', 'postnummer': 'p1', 'adgangspunkt': 'g1'}],
        [{'id_lokalId': 'g1', 'status': '3', 'position': {'crs': 25832, 'dimension': 'XY', 'wkt': 'POINT (550000 6170000)'}}],
        [{'id_lokalId': 'r1', 'status': '3', 'vejnavn': 'Prøvevej'}],
        [{'id_lokalId': 'p1', 'status': '3', 'postnr': '9999'}],
    ]


class DarJoinTests(unittest.TestCase):
    def test_transport_pages_and_flat_joins_work_together(self):
        rows = fixture()
        entities = ['DAR_Adresse', 'DAR_Husnummer', 'DAR_Adressepunkt', 'DAR_NavngivenVej', 'DAR_Postnummer']
        scopes = [{'husnummer': 'h1'}, {'navngivenVej': 'r1'}, {'id_lokalId': 'g1'},
                  {'id_lokalId': 'r1'}, {'id_lokalId': 'p1'}]
        replies = []
        for entity, table in zip(entities, rows):
            for index, node in enumerate(table):
                replies.append(json.dumps({'data': {entity: {
                    'nodes': [node], 'pageInfo': {'hasNextPage': index + 1 < len(table), 'endCursor': str(index)},
                }}}).encode())
        with tempfile.TemporaryDirectory() as root:
            client = Datafordeler(root)
            with patch.object(client, '_auth', return_value={'api_key': 'FICTIONAL_KEY'}), \
                    patch.object(client, '_request', side_effect=replies) as request:
                source = DarQuery(client.query, snapshot='2026-10-16T21:30:00Z', page_size=1)
                collected = [source.collect(entity, scope) for entity, scope in zip(entities, scopes)]
                actual = join_addresses(*collected, postcode='9999', road='Prøvevej')
                self.assertEqual(actual, join_addresses(*rows))
                self.assertEqual(request.call_count, 6)
                for call in request.call_args_list:
                    query = call.kwargs['query']
                    self.assertEqual(query.count('2026-10-16T21:30:00.000000Z'), 2)
                    self.assertNotIn('FICTIONAL_KEY', query)

    def test_stable_ids_units_coordinates_and_no_mutation(self):
        rows = fixture();before = copy.deepcopy(rows)
        result = join_addresses(*rows, postcode='9999', road='Prøvevej')
        self.assertEqual(rows, before)
        self.assertEqual([r['id'] for r in result], ['dar:a1', 'dar:a2'])
        self.assertEqual(result[0]['house_id'], 'h1')
        self.assertEqual((result[0]['floor'], result[0]['door'], result[0]['number']), ('2', 'tv', '12B'))
        self.assertEqual([r['type'] for r in result], ['Lejlighed', 'Hus'])
        self.assertTrue(9 < result[0]['lng'] < 11 and 55 < result[0]['lat'] < 57)
        # Compare every normalized field with the established REST path.
        rest = []
        for a in rows[0]:
            rest.append(dict(a, **{'dørbetegnelse': a['doerbetegnelse'], 'husnummer': {
                'id_lokalId': 'h1', 'husnummertekst': '12B', 'postnummer': {'postnr': '9999'},
                'navngivenVej': {'vejnavn': 'Prøvevej'}, 'adgangspunkt': {'position': 'POINT (550000 6170000)'}}}))
        self.assertEqual(result, rest_addresses(rest, '9999', 'Prøvevej'))

    def test_cross_postcode_road_filters_before_requiring_outside_point(self):
        rows = fixture()
        rows[0].append(dict(rows[0][0], id_lokalId='a3', husnummer='h2'))
        rows[1].append(dict(rows[1][0], id_lokalId='h2', postnummer='p2', adgangspunkt='outside'))
        rows[4].append({'id_lokalId': 'p2', 'status': '3', 'postnr': '9998'})
        self.assertEqual(len(join_addresses(*rows, postcode='9999')), 2)
        with self.assertRaises(IncompleteResult):join_addresses(*rows)

    def test_missing_or_retired_relation_and_duplicate_ids_fail_whole_result(self):
        for table in (1, 2, 3, 4):
            for mode in ('missing', 'retired', 'duplicate'):
                rows = fixture()
                if mode == 'missing':rows[table] = []
                elif mode == 'retired':rows[table][0]['status'] = '4'
                else:rows[table].append(dict(rows[table][0]))
                with self.subTest(table=table, mode=mode), self.assertRaises(IncompleteResult):join_addresses(*rows)
        rows = fixture();rows[0].append(dict(rows[0][0], id_lokalId='last', husnummer='missing'))
        with self.assertRaises(IncompleteResult):join_addresses(*rows)

    def test_malformed_fields_and_wrong_road_cannot_silently_skip(self):
        for table, field, value in [(0, 'status', '4'), (0, 'doerbetegnelse', []),
                                     (0, 'adressebetegnelse', None), (1, 'husnummertekst', ''),
                                     (4, 'postnr', 'bad'), (3, 'vejnavn', None)]:
            rows = fixture();rows[table][0][field] = value
            with self.assertRaises(IncompleteResult):join_addresses(*rows)
        rows = fixture();del rows[0][0]['doerbetegnelse']
        with self.assertRaises(IncompleteResult):join_addresses(*rows)
        with self.assertRaises(IncompleteResult):join_addresses(*fixture(), road='Anden vej')

    def test_coordinate_dimension_crs_and_finite_bounds(self):
        for crs, dim, wkt in [(4326, 'XY', 'POINT (9 55)'), (25832, 'XY', 'POINT (9 55)'),
                              (25832, 'XY', 'POINT (NaN 6170000)'), (25832, 'XY', 'POINT (inf 6170000)'),
                              (25832, 'XY', 'POINT (550000 6170000 0)'), (25832, 'XYZ', 'POINT (550000 6170000)'),
                              (25832, 'XY', 'LINESTRING (550000 6170000)')]:
            rows = fixture();rows[2][0]['position'] = {'crs': crs, 'dimension': dim, 'wkt': wkt}
            with self.assertRaises(IncompleteResult):join_addresses(*rows)
        expected = join_addresses(*fixture())
        for wkt in ('POINT (550000 6170000 4)', 'POINT Z (550000 6170000 4)'):
            rows = fixture();rows[2][0]['position'].update(dimension='XYZ', wkt=wkt)
            self.assertEqual(join_addresses(*rows), expected)

    def test_empty_result_and_sanitized_errors(self):
        self.assertEqual(join_addresses([], [], [], [], []), [])
        rows = fixture();rows[0][0]['husnummer'] = 'FICTIONAL_SECRET'
        with self.assertRaises(IncompleteResult) as error:join_addresses(*rows)
        self.assertNotIn('FICTIONAL_SECRET', str(error.exception))


if __name__ == '__main__':unittest.main()
