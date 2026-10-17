"""Fictional GraphQL envelopes only; no live key, network or local database."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from dar_adapter import DarAdapter, SOURCE
from dar_query import DarQuery
from dar_paging import IncompleteResult
from dar_join import point_coordinates

STAMP = '2026-10-17T07:00:00.000000Z'


class Provider:
    """Tiny synthetic provider, interprets the public equality/page contract."""
    def __init__(self, tables):
        self.tables = tables
        self.calls = []

    def __call__(self, query):
        self.calls.append(query)
        data = {}
        for alias, entity, arguments in re.findall(r'(?:(scope_\d+):\s*)?(DAR_\w+)\((.*?)\)\s*\{', query):
            filters = {field: json.loads(value) for field, value in
                       re.findall(r'(\w+):\s*\{\s*eq:\s*("(?:[^"\\]|\\.)*")\s*\}', arguments)}
            selected = [copy.deepcopy(row) for row in self.tables.get(entity, [])
                        if all(row.get(field) == value for field, value in filters.items())]
            spatial = re.search(r'position:\s*\{\s*within:\s*\{\s*wkt:\s*("(?:[^"\\]|\\.)*")', arguments)
            if spatial:
                numbers = [float(value) for value in re.findall(r'-?\d+(?:\.\d+)?', json.loads(spatial[1]))]
                xs, ys = numbers[::2], numbers[1::2]
                selected = [row for row in selected if min(xs) < point_coordinates(row)[0] < max(xs)
                            and min(ys) < point_coordinates(row)[1] < max(ys)]
            size = int(re.search(r'first:\s*(\d+)', arguments)[1])
            cursor = re.search(r'after:\s*("(?:[^"\\]|\\.)*")', arguments)
            offset = int(json.loads(cursor[1])) if cursor else 0
            rows = selected[offset:offset + size]
            data[alias or entity] = {'nodes': rows, 'pageInfo': {
                'hasNextPage': offset + size < len(selected),
                'endCursor': str(offset + len(rows)) if rows else None,
            }}
        return {'data': data}


def tables():
    return {
        'DAR_NavngivenVej': [{'id_lokalId': 'r1', 'status': '3', 'vejnavn': 'Fiktivvej'}],
        'DAR_Postnummer': [{'id_lokalId': 'p1', 'status': '3', 'postnr': '9999', 'navn': 'Prøveby'},
                          {'id_lokalId': 'p2', 'status': '3', 'postnr': '9998', 'navn': 'Prøveby 2'}],
        'DAR_Husnummer': [{'id_lokalId': 'h1', 'status': '3', 'navngivenVej': 'r1', 'postnummer': 'p1', 'adgangspunkt': 'g1', 'husnummertekst': '12B'},
                         {'id_lokalId': 'h2', 'status': '3', 'navngivenVej': 'r1', 'postnummer': 'p2', 'adgangspunkt': 'g2', 'husnummertekst': '14'}],
        'DAR_Adressepunkt': [{'id_lokalId': 'g1', 'status': '3', 'position': {'crs': 25832, 'dimension': 'XY', 'wkt': 'POINT (550000 6170000)'}},
                            {'id_lokalId': 'g2', 'status': '3', 'position': {'crs': 25832, 'dimension': 'XY', 'wkt': 'POINT (550100 6170000)'}}],
        'DAR_Adresse': [{'id_lokalId': 'a1', 'status': '3', 'husnummer': 'h1', 'adressebetegnelse': 'Fiktivvej 12B, 2. tv., 9999 Prøveby', 'etagebetegnelse': '2', 'doerbetegnelse': 'tv'},
                        {'id_lokalId': 'a2', 'status': '3', 'husnummer': 'h1', 'adressebetegnelse': 'Fiktivvej 12B, 9999 Prøveby', 'etagebetegnelse': None, 'doerbetegnelse': ''},
                        {'id_lokalId': 'a3', 'status': '3', 'husnummer': 'h2', 'adressebetegnelse': 'Fiktivvej 14, 9998 Prøveby 2', 'etagebetegnelse': None, 'doerbetegnelse': None}],
    }


class BatchTests(unittest.TestCase):
    def test_twenty_five_ids_need_three_requests_with_one_fixed_snapshot(self):
        provider = Provider({'DAR_Postnummer': [{'id_lokalId': 'p' + str(i), 'status': '3'} for i in range(25)]})
        values = ['p' + str(i) for i in range(25)]
        query = DarQuery(provider, snapshot=STAMP)
        result = query.collect_many('DAR_Postnummer', 'id_lokalId', values + ['p0'], require_all=True)
        self.assertEqual([row['id_lokalId'] for row in result], values)
        self.assertEqual(len(provider.calls), 3)
        for call in provider.calls:
            self.assertEqual(call.count('registreringstid: "' + STAMP + '"'), call.count('DAR_Postnummer('))
            self.assertEqual(call.count('virkningstid: "' + STAMP + '"'), call.count('DAR_Postnummer('))
            self.assertNotIn(' in:', call)

    def test_each_alias_has_complete_independent_pagination(self):
        provider = Provider(tables())
        query = DarQuery(provider, page_size=1, snapshot=STAMP)
        result = query.collect_many('DAR_Adresse', 'husnummer', ['h1', 'h2'])
        self.assertEqual([row['id_lokalId'] for row in result], ['a1', 'a2', 'a3'])
        self.assertEqual(len(provider.calls), 2)
        self.assertIn('scope_0:', provider.calls[0]);self.assertIn('scope_1:', provider.calls[0])
        self.assertIn('after: "1"', provider.calls[1]);self.assertNotIn('scope_1:', provider.calls[1])

    def test_missing_alias_partial_error_null_and_wrong_scope_fail(self):
        good = Provider(tables())('query { scope_0: DAR_Postnummer(where: {id_lokalId: {eq: "p1"}}, first: 100) { nodes { id_lokalId } } }')
        bad_scope = copy.deepcopy(good);bad_scope['data']['scope_0']['nodes'][0]['id_lokalId'] = 'other'
        for response in ({'data': {}}, {'data': {'scope_0': None}}, dict(good, errors=[{'message': 'FICTIONAL_KEY'}]), bad_scope):
            with self.assertRaises(IncompleteResult) as error:
                DarQuery(Mock(return_value=response)).collect_many('DAR_Postnummer', 'id_lokalId', ['p1'], require_all=True)
            self.assertNotIn('FICTIONAL_KEY', str(error.exception))

    def test_missing_required_id_duplicate_across_scopes_and_late_page_failure(self):
        with self.assertRaises(IncompleteResult):
            DarQuery(Provider(tables())).collect_many('DAR_Postnummer', 'id_lokalId', ['absent'], require_all=True)
        rows = tables();rows['DAR_Adresse'][2]['id_lokalId'] = 'a1'
        with self.assertRaises(IncompleteResult):
            DarQuery(Provider(rows)).collect_many('DAR_Adresse', 'husnummer', ['h1', 'h2'])
        provider = Provider(tables())
        first = provider('query { scope_0: DAR_Adresse(where: {husnummer: {eq: "h1"}}, first: 1) { nodes { id_lokalId } } }')
        with self.assertRaisesRegex(ValueError, 'transport'):
            DarQuery(Mock(side_effect=[first, ValueError('clean transport error')]), page_size=1).collect_many('DAR_Adresse', 'husnummer', ['h1'])

    def test_bounds_empty_input_validation_and_cancellation(self):
        provider = Mock()
        query = DarQuery(provider)
        self.assertEqual(query.collect_many('DAR_Adresse', 'husnummer', []), [])
        for kw in ({'batch_size': 0}, {'batch_size': 11}, {'max_requests': 0}, {'max_nodes': 0}, {'require_all': True}):
            with self.assertRaises(ValueError):query.collect_many('DAR_Adresse', 'husnummer', ['h1'], **kw)
        with self.assertRaises(ValueError):query.collect_many('DAR_Adresse', 'husnummer', ['h1', None])
        provider.assert_not_called()
        with self.assertRaises(IncompleteResult):
            DarQuery(Provider(tables()), page_size=1).collect_many('DAR_Adresse', 'husnummer', ['h1'], max_requests=1)
        with self.assertRaises(IncompleteResult):
            DarQuery(Provider(tables())).collect_many('DAR_Adresse', 'husnummer', ['h1', 'h2'], max_nodes=2)
        cancel = Mock(side_effect=RuntimeError('pause'))
        with self.assertRaisesRegex(RuntimeError, 'pause'):
            DarQuery(provider, check_cancel=cancel).collect_many('DAR_Adresse', 'husnummer', ['h1'])
        provider.assert_not_called()


class AdapterTests(unittest.TestCase):
    def adapter(self, rows=None, **kwargs):
        provider = Provider(rows if rows is not None else tables())
        return DarAdapter(DarQuery(provider, snapshot=STAMP, **kwargs)), provider

    def test_postcode_discovery_uses_houses_and_complete_road_id_lookups(self):
        adapter, provider = self.adapter(page_size=1)
        result = adapter.discover_postcode('9999')
        self.assertEqual(result['source'], SOURCE);self.assertEqual(result['snapshot'], STAMP)
        self.assertEqual(result['name'], 'Prøveby')
        self.assertEqual([r['id_lokalId'] for r in result['roads']], ['r1'])
        self.assertNotIn('DAR_Adresse(', ' '.join(provider.calls))

    def test_road_across_two_postcodes_retains_all_units_and_source(self):
        adapter, _ = self.adapter(page_size=1)
        result = adapter.road('r1')
        self.assertEqual(result['source'], SOURCE);self.assertEqual(result['snapshot'], STAMP)
        self.assertEqual([r['id'] for r in result['addresses']], ['dar:a1', 'dar:a2', 'dar:a3'])
        self.assertEqual(result['addresses'][0]['door'], 'tv')
        self.assertEqual(result['addresses'][2]['postcode'], '9998')
        self.assertTrue(all(row['source'] == 'DAR / Datafordeleren' for row in result['addresses']))

    def test_postcode_scope_does_not_fetch_other_postcode_house_or_point(self):
        adapter, provider = self.adapter(page_size=1)
        result = adapter.road('r1', postcode='9999')
        self.assertEqual(len(result['addresses']), 2)
        self.assertNotIn('"h2"', ' '.join(provider.calls));self.assertNotIn('"g2"', ' '.join(provider.calls))

    def test_missing_active_relations_prevent_any_returned_import(self):
        for entity in ('DAR_NavngivenVej', 'DAR_Postnummer', 'DAR_Adressepunkt'):
            rows = tables();rows[entity][0]['status'] = '4'
            adapter, _ = self.adapter(rows)
            with self.subTest(entity=entity), self.assertRaises(IncompleteResult):adapter.road('r1')
        rows = tables();rows['DAR_Husnummer'][0].pop('adgangspunkt')
        with self.assertRaises(IncompleteResult):self.adapter(rows)[0].road('r1')

    def test_empty_road_no_artificial_addresses_and_ambiguous_postcode_fails(self):
        rows = tables();rows['DAR_Adresse'] = []
        result = self.adapter(rows)[0].road('r1')
        self.assertEqual(result['addresses'], [])
        rows = tables();rows['DAR_Postnummer'].append(dict(rows['DAR_Postnummer'][0], id_lokalId='duplicate-post'))
        with self.assertRaises(IncompleteResult):self.adapter(rows)[0].discover_postcode('9999')
        with self.assertRaises(ValueError):self.adapter()[0].discover_postcode('bad')


class TileTests(unittest.TestCase):
    def test_complete_multisided_tile_keeps_edge_points_and_apartments(self):
        provider = Provider(tables());query = DarQuery(provider, snapshot=STAMP, page_size=1)
        result = DarAdapter(query).tile([550000, 6170000, 550100, 6170100])
        self.assertEqual([row['id'] for row in result['addresses']], ['dar:a1', 'dar:a2', 'dar:a3'])
        self.assertEqual({row['postcode'] for row in result['addresses']}, {'9999', '9998'})
        self.assertEqual(result['source'], SOURCE);self.assertEqual(result['snapshot'], STAMP)
        self.assertIn('within:', provider.calls[0]);self.assertIn('549999.990000000', provider.calls[0])
        self.assertTrue(all('POLYGON' not in call for call in provider.calls[2:]))

    def test_padding_removed_locally_and_adjacent_tiles_share_stable_edge_id(self):
        rows = tables();rows['DAR_Adressepunkt'].append({'id_lokalId': 'padding', 'status': '3',
            'position': {'crs': 25832, 'dimension': 'XY', 'wkt': 'POINT (549999.995 6170000)'}})
        query = DarQuery(Provider(rows), snapshot=STAMP)
        result = query.collect_bbox([550000, 6170000, 550100, 6170100])
        self.assertEqual({row['id_lokalId'] for row in result}, {'g1', 'g2'})
        adapter = DarAdapter(query)
        left = adapter.tile([549900, 6169990, 550000, 6170100])
        right = adapter.tile([550000, 6169990, 550100, 6170100])
        shared = {row['id'] for row in left['addresses']} & {row['id'] for row in right['addresses']}
        self.assertEqual(shared, {'dar:a1', 'dar:a2'})

    def test_broken_scope_status_geometry_and_partial_envelope_fail(self):
        row = tables()['DAR_Adressepunkt'][0]
        variants = [dict(row, status='4'), dict(row, position=dict(row['position'], wkt='POINT (560000 6170000)')),
                    dict(row, position=dict(row['position'], crs=4326))]
        for node in variants:
            response = {'data': {'DAR_Adressepunkt': {'nodes': [node], 'pageInfo': {'hasNextPage': False, 'endCursor': 'last'}}}}
            with self.assertRaises(IncompleteResult):
                DarQuery(Mock(return_value=response)).collect_bbox([550000, 6170000, 550100, 6170100])
        with self.assertRaises(IncompleteResult):
            DarQuery(Mock(return_value={'data': {}, 'errors': [{'message': 'FICTIONAL_KEY'}]})).collect_bbox([550000, 6170000, 550100, 6170100])

    def test_invalid_large_or_nonfinite_tile_never_contacts_provider(self):
        provider = Mock();query = DarQuery(provider)
        for bounds in (None, [1, 2], [550000, 6170000, float('nan'), 6170100],
                       [550000, 6170000, 554000, 6174000], [550100, 6170000, 550000, 6170100],
                       [9, 55, 10, 56], [True, 6170000, 550100, 6170100]):
            with self.assertRaises(ValueError):query.collect_bbox(bounds)
        provider.assert_not_called()

    def test_empty_tile_or_streetpoint_produces_no_artificial_address(self):
        rows = tables();rows['DAR_Husnummer'] = []
        result = DarAdapter(DarQuery(Provider(rows))).tile([550000, 6170000, 550100, 6170100])
        self.assertEqual(result['addresses'], []);self.assertEqual(result['roads'], [])
        result = DarAdapter(DarQuery(Provider(tables()))).tile([551000, 6170000, 551100, 6170100])
        self.assertEqual(result['addresses'], [])

    def test_missing_tile_join_and_transport_failure_preserve_complete_result_rule(self):
        rows = tables();rows['DAR_NavngivenVej'] = []
        with self.assertRaises(IncompleteResult):
            DarAdapter(DarQuery(Provider(rows))).tile([550000, 6170000, 550100, 6170100])
        provider = Provider(tables())
        response = provider('query { DAR_Adressepunkt(where: {status: {eq: "3"}}, first: 1) { nodes { id_lokalId } } }')
        with self.assertRaisesRegex(ValueError, 'network'):
            DarAdapter(DarQuery(Mock(side_effect=[response, ValueError('clean network error')]), page_size=1)).tile([550000, 6170000, 550100, 6170100])


if __name__ == '__main__':unittest.main()
