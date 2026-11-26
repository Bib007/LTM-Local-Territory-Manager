"""Fictional provider only. No account, schema download or live DAR calls."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from address_source import Datafordeler, MAX_SCHEMA
from dar_paging import IncompleteResult
from dar_query import DarQuery, snapshot_time, FIELDS

STAMP = '2026-10-16T21:30:00.000000Z'


def page(rows, more=False, cursor='last', entity='DAR_Postnummer'):
    return {'data': {entity: {'nodes': rows, 'pageInfo': {'hasNextPage': more, 'endCursor': cursor}}}}


class DarQueryTests(unittest.TestCase):
    def test_paging_pins_filters_and_both_times_and_escapes_cursor(self):
        filters = {'postnr': '9999'}
        calls = []
        cursor = 'fictional"cursor\\\n'
        def request(query):
            calls.append(query)
            filters['postnr'] = '0000'
            rows = [{'id_lokalId': str(len(calls)), 'status': '3', 'postnr': '9999'}]
            return page(rows, len(calls) == 1, cursor if len(calls) == 1 else 'end')
        result = DarQuery(request, snapshot=STAMP).collect('DAR_Postnummer', filters)
        self.assertEqual(len(result), 2)
        for query in calls:
            self.assertIn('virkningstid: ' + json.dumps(STAMP), query)
            self.assertIn('registreringstid: ' + json.dumps(STAMP), query)
            self.assertIn('postnr: { eq: "9999" }', query)
            self.assertIn('status: { eq: "3" }', query)
            self.assertIn('first: 100', query)
        self.assertNotIn('after:', calls[0])
        self.assertIn('after: ' + json.dumps(cursor), calls[1])

    def test_all_flat_projections_and_filter_values_are_literal(self):
        for entity in FIELDS:
            request = Mock(return_value=page([], cursor=None, entity=entity))
            self.assertEqual(DarQuery(request, snapshot=STAMP).collect(entity, {'id_lokalId': 'fake"} mutation { x\\\n'}), [])
            query = request.call_args.args[0]
            self.assertIn(json.dumps('fake"} mutation { x\\\n'), query)
            self.assertIn(FIELDS[entity], query)
            self.assertIn('pageInfo { hasNextPage endCursor }', query)

    def test_invalid_or_unbounded_queries_never_contact_provider(self):
        request = Mock()
        for entity, filters in [('DAR_Adresse', {}), ('Unknown', {'id_lokalId': 'a'}),
                                ('DAR_Adresse', {'private_note': 'x'}), ('DAR_Adresse', {'husnummer': None})]:
            with self.assertRaises(ValueError):DarQuery(request).collect(entity, filters)
        for size in (True, 0, -1, 1001, '100'):
            with self.assertRaises(ValueError):DarQuery(request, page_size=size)
        for stamp in ('bad', '2026-10-16T12:00:00', 123):
            with self.assertRaises(ValueError):DarQuery(request, snapshot=stamp)
        request.assert_not_called()
        self.assertEqual(snapshot_time('2026-10-16T23:30:00+02:00'), STAMP)

    def test_scope_status_malformed_and_partial_errors_cannot_return_rows(self):
        valid = {'id_lokalId': 'p', 'status': '3', 'postnr': '9999'}
        cases = [page([dict(valid, postnr='0000')]), page([dict(valid, status='4')]),
                 page([{'id_lokalId': 'p'}]), {'data': []}, {'data': None},
                 dict(page([valid]), errors=[{'message': 'FICTIONAL_SECRET'}])]
        for response in cases:
            with self.assertRaises(ValueError) as error:
                DarQuery(Mock(return_value=response)).collect('DAR_Postnummer', {'postnr': '9999'})
            self.assertNotIn('FICTIONAL_SECRET', str(error.exception))

    def test_cancellation_and_late_failure_do_not_return_first_page(self):
        request = Mock(side_effect=[page([{'id_lokalId': 'p', 'status': '3', 'postnr': '9999'}], True), ValueError('clean transport error')])
        with self.assertRaisesRegex(ValueError, 'clean transport'):
            DarQuery(request).collect('DAR_Postnummer', {'postnr': '9999'})
        cancel = Mock(side_effect=RuntimeError('fictional pause'))
        request.reset_mock()
        with self.assertRaisesRegex(RuntimeError, 'pause'):
            DarQuery(request, check_cancel=cancel).collect('DAR_Postnummer', {'postnr': '9999'})
        request.assert_not_called()

    def test_authenticated_transport_decodes_and_sanitizes_provider_errors(self):
        with tempfile.TemporaryDirectory() as root:
            client = Datafordeler(root)
            with patch.object(client, '_request') as request:
                with self.assertRaises(ValueError):client.query('query { __typename }')
                request.assert_not_called()
            with patch.object(client, '_auth', return_value={'api_key': 'FICTIONAL_KEY'}):
                for raw in (b'not json', b'[]', b'{"data":null}', b'{"data":[],"errors":[]}',
                            b'{"data":{},"errors":[{"message":"FICTIONAL_KEY"}]}'):
                    with patch.object(client, '_request', return_value=raw):
                        with self.assertRaises(ValueError) as error:client.query('query { __typename }')
                        self.assertNotIn('FICTIONAL_KEY', str(error.exception))
                with patch.object(client, '_request', return_value=b'{"data":{"x":{}}}') as request:
                    self.assertEqual(client.query('query { x }'), {'data': {'x': {}}})
                    request.assert_called_once_with('FICTIONAL_KEY', query='query { x }')

    def test_transport_enforces_response_size_and_timeout(self):
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self, *args):self.close()
        with tempfile.TemporaryDirectory() as root, patch('address_source.urllib.request.build_opener') as make:
            make.return_value.open.return_value = Response(b'x' * (MAX_SCHEMA + 1))
            with self.assertRaisesRegex(ValueError, 'stort svar'):
                Datafordeler(root)._request('FICTIONAL_KEY', query='query { x }')
            self.assertEqual(make.return_value.open.call_args.kwargs['timeout'], 20)


if __name__ == '__main__':unittest.main()
