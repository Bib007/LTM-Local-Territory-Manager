"""End-to-end download/store integration with invented GraphQL data only."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from geodata import Downloads
from store import Store
from geography import utm32_to_wgs84
from postcode import Paused, SourceUnavailable, SourceTimeout
from dar_download import road_lines
from address_checkpoint import GRAPHQL_SOURCE, REST_SOURCE
from test_dar_adapter import Provider, tables


class Source:
    def __init__(self, provider):
        self.provider = provider
        self.configured = True
    def status(self):return {'configured': self.configured, 'schema_sha256': getattr(self, 'schema', None)}
    def query(self, query):return self.provider(query)


def two_roads():
    rows = tables()
    rows['DAR_NavngivenVej'].append({'id_lokalId': 'r2', 'status': '3', 'vejnavn': 'Z-Fiktivvej'})
    rows['DAR_Husnummer'][1].update(navngivenVej='r2', postnummer='p1')
    rows['DAR_Adresse'][2]['adressebetegnelse'] = 'Z-Fiktivvej 14, 9999 Prøveby'
    rows['DAR_NavngivenVej'][0]['vejnavnebeliggenhed_vejnavnelinje'] = {
        'crs': 25832, 'dimension': 'XYZ', 'wkt': 'LINESTRING Z (550000 6170000 0, 550100 6170000 0)'}
    return rows


class DarDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name);self.addCleanup(lambda: self.store.close())
        self.provider = Provider(two_roads());self.source = Source(self.provider)
        self.download = Downloads(self.store, self.source)
        self.download.request = Mock(side_effect=AssertionError('Unexpected legacy/OSM request'))

    def test_named_road_import_uses_graphql_and_preserves_units(self):
        self.download.suggest = Mock(side_effect=AssertionError('GraphQL must not depend on legacy suggestions'))
        result = self.download.road({'road': 'Fiktivvej', 'postcode': '9999'}, lambda **kw: None)
        self.assertEqual(result['count'], 2)
        addresses = self.store.geo_state()['addresses']
        self.assertEqual({row['id'] for row in addresses}, {'dar:a1', 'dar:a2'})
        self.assertTrue(all(row['source'] == 'DAR / Datafordeleren' for row in addresses))
        self.assertEqual(next(row for row in addresses if row['id'] == 'dar:a1')['door'], 'tv')
        self.download.request.assert_not_called()
        self.download.suggest.assert_not_called()

    def test_postcode_commits_roads_and_checkpoint_at_same_snapshot(self):
        result = self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertTrue(result['complete']);self.assertEqual(result['count'], 3)
        manifest = self.store.get('geo', 'postcode:9999')
        self.assertEqual(manifest['source_id'], GRAPHQL_SOURCE)
        self.assertTrue(all(row['status'] == 'done' for row in manifest['roads']))
        self.assertEqual(self.store.geo_info()['roads'], 1)
        for query in self.provider.calls:
            self.assertIn(manifest['snapshot'], query)
        self.download.request.assert_not_called()

    def test_area_road_addresses_do_not_need_legacy_suggestions(self):
        point = utm32_to_wgs84(550000, 6170000)
        self.download.request = Mock(return_value={'elements': [{'id': 'fixture-road',
            'tags': {'highway': 'residential', 'name': 'Fiktivvej'},
            'geometry': [{'lon': point[0], 'lat': point[1]},
                         {'lon': point[0]+.0001, 'lat': point[1]+.0001}]}]})
        self.download.suggest = Mock(side_effect=AssertionError('Legacy suggestions unavailable'))
        result = self.download.area({'postcode': '9999',
            'bbox': [point[0]-.001, point[1]-.001, point[0]+.001, point[1]+.001]}, True, lambda **kw: None)
        self.assertEqual(result['roads_downloaded'], 1)
        self.assertEqual(result['warnings'], [])
        self.assertEqual(len(self.store.geo_state()['addresses']), 2)
        self.download.suggest.assert_not_called()
        self.download.request.assert_called_once()
        self.assertEqual(self.download.request.call_args.args[0], 'overpass-api.de')

    def test_failed_graphql_road_preserves_existing_local_records(self):
        self.download.suggest = Mock(side_effect=AssertionError('Legacy suggestions unavailable'))
        self.download.road({'road': 'Fiktivvej', 'postcode': '9999'}, lambda **kw: None)
        before = copy.deepcopy(self.store.geo_state());revision = self.store.revision
        self.source.query = Mock(side_effect=ValueError('Fiktiv forbindelsesfejl'))
        with self.assertRaises(SourceUnavailable):
            self.download.road({'road': 'Fiktivvej', 'postcode': '9999'}, lambda **kw: None)
        self.assertEqual(self.store.geo_state(), before)
        self.assertEqual(self.store.revision, revision)
        self.download.suggest.assert_not_called()

    def test_same_name_with_multiple_official_ids_is_one_complete_retirement_scope(self):
        self.provider.tables['DAR_NavngivenVej'][1]['vejnavn'] = 'Fiktivvej'
        self.provider.tables['DAR_Adresse'][2]['adressebetegnelse'] = 'Fiktivvej 14, 9999 Prøveby'
        result = self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertTrue(result['complete']);self.assertEqual(result['count'], 3)
        manifest = self.store.get('geo', 'postcode:9999')
        self.assertEqual(len(manifest['roads']), 1);self.assertEqual(manifest['roads'][0]['ids'], ['r1', 'r2'])
        self.assertTrue(self.download.postcode({'postcode': '9999', 'refresh': True}, lambda **kw: None)['complete'])
        self.assertEqual(self.store.geo_state()['changes'], [])
        self.assertTrue(all(not row.get('retired') for row in self.store.geo_state()['addresses']))
        self.download.suggest = Mock(return_value={'suggestions': [{'road': 'Fiktivvej', 'postcode': '9999'}]})
        self.assertEqual(self.download.road({'road': 'Fiktivvej', 'postcode': '9999'}, lambda **kw: None)['count'], 3)

    def test_pause_and_restart_resume_only_unfinished_road_with_same_snapshot(self):
        def progress(**values):
            if values.get('completed') == 1:self.download.cancel_event.set()
        with self.assertRaises(Paused):self.download.postcode({'postcode': '9999'}, progress)
        manifest = self.store.get('geo', 'postcode:9999');snapshot = manifest['snapshot']
        self.assertEqual(manifest['status'], 'paused');self.assertEqual(self.store.geo_info()['addresses'], 2)
        self.store.close();self.store = Store(self.temp.name)
        self.provider.calls.clear();self.download = Downloads(self.store, self.source)
        result = self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertTrue(result['complete']);self.assertEqual(result['count'], 3)
        self.assertEqual(self.store.get('geo', 'postcode:9999')['snapshot'], snapshot)
        self.assertNotIn('eq: "r1"', ' '.join(self.provider.calls))

    def test_source_failure_stops_after_completed_road_and_resume_does_not_replay(self):
        original = self.source.query
        def progress(**values):
            if values.get('completed') == 1:self.source.query = Mock(side_effect=ValueError('Fiktiv afvist adgang'))
        result = self.download.postcode({'postcode': '9999'}, progress)
        self.assertFalse(result['complete']);self.assertEqual(self.store.geo_info()['addresses'], 2)
        self.assertEqual(self.source.query.call_count, 1)
        self.source.query = original;self.provider.calls.clear()
        result = self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertTrue(result['complete']);self.assertNotIn('eq: "r1"', ' '.join(self.provider.calls))

    def test_legacy_checkpoint_is_not_mixed_or_overwritten_without_refresh(self):
        manifest = {'id': 'postcode:9999', 'entity': 'postcode_download', 'postcode': '9999', 'name': 'Prøveby',
                    'snapshot': '2026-10-16T10:00:00Z', 'status': 'paused', 'roads': []}
        self.store.mutate('geo.postcode.save', {'manifest': manifest})
        before = copy.deepcopy(self.store.get('geo', 'postcode:9999'));revision = self.store.revision
        with self.assertRaisesRegex(ValueError, 'anden adressekilde'):
            self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertEqual(self.store.revision, revision)
        self.assertEqual(self.store.get('geo', 'postcode:9999'), before);self.assertEqual(self.provider.calls, [])
        self.assertTrue(self.download.postcode({'postcode': '9999', 'refresh': True}, lambda **kw: None)['complete'])
        self.assertEqual(self.store.get('geo', 'postcode:9999')['source_id'], GRAPHQL_SOURCE)
        self.source.configured = False;revision = self.store.revision
        with self.assertRaisesRegex(ValueError, 'anden adressekilde'):
            self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertEqual(self.store.revision, revision)

    def test_missing_join_or_failed_transaction_never_imports_partial_road(self):
        self.provider.tables['DAR_Adressepunkt'] = []
        result = self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertFalse(result['complete']);self.assertEqual(self.store.geo_info()['addresses'], 0)
        self.provider.tables = two_roads()
        mutate = self.store.mutate
        def failing(action, data):
            if action == 'geo.postcode.road':raise ValueError('Fiktiv transaktionsfejl')
            return mutate(action, data)
        with patch.object(self.store, 'mutate', side_effect=failing):
            result = self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertFalse(result['complete']);self.assertEqual(self.store.geo_info()['addresses'], 0)
        self.assertTrue(all(row['status'] == 'error' for row in self.store.get('geo', 'postcode:9999')['roads']))

    def test_schema_change_requires_new_checkpoint_and_rejects_changed_inflight_reply(self):
        self.source.schema = 'a' * 64
        self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertEqual(self.store.get('geo', 'postcode:9999')['schema_sha256'], 'a' * 64)
        self.source.schema = 'b' * 64;revision = self.store.revision
        with self.assertRaisesRegex(ValueError, 'ændret skema'):
            self.download.postcode({'postcode': '9999'}, lambda **kw: None)
        self.assertEqual(self.store.revision, revision)
        adapter = self.download.graph_adapter()
        def changed(query):
            result = self.provider(query);self.source.schema = 'c' * 64;return result
        self.source.query = changed
        with self.assertRaises(SourceUnavailable):adapter.discover_postcode('9999')
        self.assertEqual(self.store.revision, revision)

    def boundary(self):
        # A triangle includes h1 and excludes h2 despite sharing a rectangular tile.
        points = [utm32_to_wgs84(x, y) for x, y in [(549990, 6169990), (550110, 6169990), (549990, 6170040)]]
        self.store.mutate('geo.main.save', {'points': points})
        return points

    def test_boundary_filters_private_polygon_locally_and_preserves_other_records(self):
        points = self.boundary()
        card = self.store.mutate('card.save', {'number': 'TEST', 'temporary': True})['id']
        self.store.mutate('ib.save', {'card_id': card, 'road': 'FIKTIV PRIVAT IB', 'number': '1', 'date': '2026-10-01'})
        before = self.store.state()
        result = self.download.boundary({}, lambda **kw: None)
        self.assertTrue(result['complete']);self.assertEqual(result['count'], 2)
        manifest = self.store.get('geo', 'main-boundary-download')
        self.assertEqual(manifest['source_id'], GRAPHQL_SOURCE)
        self.assertEqual({row['id'] for row in self.store.geo_state()['addresses']}, {'dar:a1', 'dar:a2'})
        for module in ('cards', 'publishers', 'loans', 'completions', 'ib', 'ignored', 'visits'):
            self.assertEqual(before[module], self.store.state()[module])
        sent = ' '.join(self.provider.calls)
        self.assertNotIn('FIKTIV PRIVAT IB', sent);self.assertNotIn(json.dumps(points), sent)
        for query in self.provider.calls:self.assertIn(manifest['snapshot'].replace('+00:00', '.000000Z'), query)
        self.download.request.assert_not_called()

    def test_old_empty_graph_checkpoint_is_refetched_instead_of_replayed_as_success(self):
        self.boundary();self.provider.tables['DAR_Adressepunkt']=[];self.download.boundary({},lambda **kw:None)
        old=copy.deepcopy(self.store.get('geo','main-boundary-download'));old.pop('point_query_version')
        for tile in old['tiles']:tile.update(status='done',count=0,address_ids=[])
        self.store.mutate('geo.main.download.save',{'manifest':old});self.provider.tables=two_roads();self.provider.calls.clear()
        result=self.download.boundary({},lambda **kw:None)
        self.assertTrue(result['complete']);self.assertEqual(result['count'],2)
        self.assertTrue(any('within:' in query for query in self.provider.calls))
        self.assertEqual(self.store.get('geo','main-boundary-download')['point_query_version'],2)

    def test_verified_empty_boundary_has_explicit_warning_instead_of_checked_address_claim(self):
        self.boundary();self.provider.tables['DAR_Adressepunkt']=[]
        result=self.download.boundary({},lambda **kw:None)
        self.assertEqual(result['count'],0);self.assertTrue(result['warnings']);self.assertTrue(result['empty']);self.assertEqual(result['fetched_count'],0)
        self.assertNotIn('Alle udsnit er hentet og kontrolleret',result['note'])
        self.assertIn('Ingen adresser fundet',result['note'])

    def test_empty_graph_refresh_cannot_retire_existing_local_addresses(self):
        self.boundary();self.download.boundary({},lambda **kw:None)
        before=copy.deepcopy(self.store.geo_state()['addresses']);self.provider.tables['DAR_Adressepunkt']=[]
        with self.assertRaisesRegex(ValueError,'ingen adresser'):
            self.download.boundary({'refresh':True},lambda **kw:None)
        self.assertEqual(self.store.geo_state()['addresses'],before)

    def test_boundary_checkpoint_mismatch_and_source_failure_preserve_addresses(self):
        self.boundary();self.assertTrue(self.download.boundary({}, lambda **kw: None)['complete'])
        before = copy.deepcopy(self.store.geo_state()['addresses']);revision = self.store.revision
        self.source.configured = False
        with self.assertRaisesRegex(ValueError, 'anden adressekilde'):self.download.boundary({}, lambda **kw: None)
        self.assertEqual(self.store.revision, revision)
        self.source.configured = True;self.source.query = Mock(side_effect=ValueError('Fiktiv netfejl'))
        result = self.download.boundary({'refresh': True}, lambda **kw: None)
        self.assertFalse(result['complete']);self.assertEqual(self.store.geo_state()['addresses'], before)
        self.assertEqual(self.source.query.call_count, 1)

    def test_graph_boundary_pause_restart_skips_completed_tiles(self):
        points = [utm32_to_wgs84(x, y) for x, y in [(549900,6169900),(556300,6169900),(556300,6170200),(549900,6170200)]]
        self.store.mutate('geo.main.save', {'points': points})
        def pause(**values):
            if values.get('completed') == 1:self.download.cancel_event.set()
        with self.assertRaises(Paused):self.download.boundary({}, pause)
        manifest = copy.deepcopy(self.store.get('geo', 'main-boundary-download'))
        self.assertEqual(manifest['status'], 'paused');self.assertGreater(len(manifest['tiles']), 1)
        first_calls = [call for call in self.provider.calls if 'within:' in call]
        self.assertEqual(len(first_calls), 1)
        self.store.close();self.store = Store(self.temp.name);self.download = Downloads(self.store, self.source)
        self.provider.calls.clear()
        self.assertTrue(self.download.boundary({}, lambda **kw: None)['complete'])
        self.assertEqual(self.store.get('geo', 'main-boundary-download')['snapshot'], manifest['snapshot'])
        self.assertNotIn(first_calls[0], self.provider.calls)

    def test_graph_timeout_type_and_request_state_cleanup(self):
        self.download.active = 'job';self.download.jobs['job'] = {'status': 'running', 'message': 'Henter'}
        self.source.query = Mock(side_effect=SourceTimeout('Fiktiv timeout'))
        with self.assertRaises(SourceTimeout):self.download.graph_adapter().discover_postcode('9999')
        self.assertNotIn('request_started', self.download.jobs['job'])
        self.source.query = Mock(side_effect=ValueError('Fiktiv afvist adgang'))
        with self.assertRaises(SourceUnavailable):self.download.graph_adapter().discover_postcode('9999')
        self.assertNotIn('request_started', self.download.jobs['job'])

    def test_optional_road_geometry_and_xyz_lines(self):
        rows = two_roads()['DAR_NavngivenVej'];lines = road_lines(rows)
        self.assertEqual(len(lines), 1);self.assertEqual(lines[0]['id'], 'dar-road:r1:0')
        self.assertAlmostEqual(lines[0]['points'][0][0], utm32_to_wgs84(550000, 6170000)[0])
        for bad in ({'crs': 4326, 'dimension': 'XY', 'wkt': 'LINESTRING (9 55, 10 55)'},
                    {'crs': 25832, 'dimension': 'XYZ', 'wkt': 'LINESTRING Z (550000 NaN 0, 550100 6170000 0)'}):
            with self.assertRaises(ValueError):road_lines([dict(rows[0], vejnavnebeliggenhed_vejnavnelinje=bad)])


if __name__ == '__main__':unittest.main()
