"""Fictional in-process provider errors, never live credentials or data."""
import json
import re
import sys
import tempfile
import unittest
import io
import urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from address_source import Datafordeler
from dar_diagnostic import diagnose, probes, WORDS


class DarDiagnosticTests(unittest.TestCase):
    def test_http_rejection_body_is_kept_in_process_only_for_diagnostic(self):
        raw = b'{"errors":[{"message":"invalid filter FICTIONAL_SECRET"}]}'
        with tempfile.TemporaryDirectory() as root, patch('address_source.urllib.request.build_opener') as make:
            make.return_value.open.side_effect = urllib.error.HTTPError('https://invalid.example/?apiKey=FICTIONAL_SECRET', 400, 'private', {}, io.BytesIO(raw))
            source = Datafordeler(root)
            with patch.object(source, '_auth', return_value={'api_key': 'FICTIONAL_KEY'}):
                report = diagnose(source)
            self.assertNotIn('FICTIONAL', json.dumps(report))
            self.assertEqual(report['probes'][0]['terms'], ['filter', 'invalid'])

    def test_plain_alias_and_batch_differ_only_in_root_aliases(self):
        queries = list(probes('2026-10-18T12:00:00Z'))
        self.assertEqual(len(queries), 15)
        for i in range(0, len(queries), 3):
            plain, alias, batch = [item[2] for item in queries[i:i+3]]
            self.assertEqual(plain, alias.replace('scope_0: ', ''))
            self.assertEqual(batch.count('scope_'), 10)
            for query in (plain, alias, batch):
                self.assertIn('first: 1', query)
                self.assertIn('virkningstid:', query)
                self.assertIn('registreringstid:', query)
                self.assertNotIn('mutation', query)

    def test_provider_messages_rows_paths_extensions_never_leave_report(self):
        secret = 'FICTIONAL_PRIVATE_SECRET'
        def request(key, *, query, return_graphql_errors):
            self.assertTrue(return_graphql_errors)
            return json.dumps({'errors': [{'message': 'Multiple aliases not supported ' + secret,
                 'path': [secret], 'extensions': {'code': secret, 'exception': secret}},
                 {'message': 'invalid filter ' + secret, 'extensions': {'code': 'HC0011'}}],
                 'data': {secret: [{'address': secret}]}}).encode()
        with tempfile.TemporaryDirectory() as root:
            source = Datafordeler(root)
            with patch.object(source, '_auth', return_value={'api_key': secret}), patch.object(source, '_request', side_effect=request):
                report = diagnose(source)
            self.assertEqual(list(Path(root).iterdir()), [])
        self.assertNotIn(secret, json.dumps(report))
        self.assertEqual(report['probes'][0]['codes'], ['HC0011'])
        self.assertEqual(set(report['probes'][0]['terms']), {'multiple', 'aliases', 'supported', 'invalid', 'filter'})

    def test_success_never_returns_provider_data_and_checks_alias_connections(self):
        def request(key, *, query, return_graphql_errors):
            names = re.findall(r'(scope_\d+):', query) or [re.search(r'\b(DAR_\w+)\(', query)[1]]
            return json.dumps({'data': {name: {'nodes': [{'id_lokalId': 'fictional-id', 'private': 'FICTIONAL_PRIVATE'}],
                'pageInfo': {'hasNextPage': False, 'endCursor': 'fictional-cursor'}} for name in names}}).encode()
        with tempfile.TemporaryDirectory() as root:
            source = Datafordeler(root)
            with patch.object(source, '_auth', return_value={'api_key': 'FICTIONAL_KEY'}), patch.object(source, '_request', side_effect=request):
                report = diagnose(source)
        self.assertTrue(all(row['status'] == 'ACCEPTED' for row in report['probes']))
        self.assertNotIn('FICTIONAL', json.dumps(report))

    def test_no_auth_no_network_and_transport_failure_stops_remaining_probes(self):
        with tempfile.TemporaryDirectory() as root:
            source = Datafordeler(root)
            with patch.object(source, '_request') as request:
                self.assertEqual(diagnose(source)['status'], 'NOT-CONFIGURED')
                request.assert_not_called()
            with patch.object(source, '_auth', return_value={'api_key': 'FICTIONAL_KEY'}), patch.object(source, '_request', side_effect=RuntimeError('FICTIONAL_SECRET')) as request:
                report = diagnose(source)
                self.assertEqual(request.call_count, 1)
                self.assertEqual(report['probes'][0]['status'], 'TRANSPORT-FAILED')
                self.assertTrue(all(row['status'] == 'NOT-TESTED' for row in report['probes'][1:]))
                self.assertNotIn('FICTIONAL', json.dumps(report))

    def test_malformed_and_missing_alias_results_are_not_accepted(self):
        for raw in (b'not json', b'[]', b'{"data":{}}', b'{"errors":[null]}'):
            with tempfile.TemporaryDirectory() as root:
                source = Datafordeler(root)
                with patch.object(source, '_auth', return_value={'api_key': 'FICTIONAL_KEY'}), patch.object(source, '_request', return_value=raw):
                    report = diagnose(source)
                self.assertTrue(all(row['status'] != 'ACCEPTED' for row in report['probes']))

    def test_invalid_page_info_is_not_accepted(self):
        for info in ({}, {'hasNextPage': 'broken'}, {'hasNextPage': True, 'endCursor': 'fictional'}):
            raw = json.dumps({'data': {'DAR_Postnummer': {'nodes': [], 'pageInfo': info}}}).encode()
            with tempfile.TemporaryDirectory() as root:
                source = Datafordeler(root)
                with patch.object(source, '_auth', return_value={'api_key': 'FICTIONAL_KEY'}), patch.object(source, '_request', return_value=raw):
                    report = diagnose(source)
                self.assertEqual(report['probes'][0]['status'], 'GQL-RESULT')
