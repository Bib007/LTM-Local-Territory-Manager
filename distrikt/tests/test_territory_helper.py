import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from server import Server
from store import Store
from territory_helper import TerritoryHelperImport, read_polygon


POLYGON = [[10, 55], [10.02, 55], [10.02, 55.02]]
ROW = {'CongregationId': 42, 'Number': '007A', 'Label': 'Fiktivt kort',
       'Boundary': json.dumps(POLYGON + [POLYGON[0]]), 'ShapeType': 'polygon',
       'Notes': 'Fiktiv intern note', 'Address': 'Fiktiv privat testadresse'}


class TerritoryHelperTests(unittest.TestCase):
    def test_polygon_representation_and_unsupported_boundaries(self):
        self.assertEqual(read_polygon(ROW['Boundary']), POLYGON)
        self.assertEqual(read_polygon(json.dumps([[y, x] for x, y in POLYGON])), POLYGON)
        self.assertEqual(read_polygon(json.dumps([{'Lat': y, 'Lng': x} for x, y in POLYGON])), POLYGON)
        for value in (None, '"invalid"', '[[10,55],[10,55],[10,55]]',
                      '[[10,60],[11,60],[11,61]]', '[[10,55],[11,55],[11,true]]'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                read_polygon(value)

    def test_preview_rejects_ambiguous_or_wrong_congregation(self):
        pilot = TerritoryHelperImport('fictional-client', 'http://127.0.0.1:8787/territory-helper-return')
        for rows in ([ROW, ROW], [dict(ROW, CongregationId=43)], [dict(ROW, ShapeType='marker')]):
            with self.subTest(rows=rows), patch('territory_helper.request_json',
                    side_effect=[{'access_token': 'fictional'}, rows]), self.assertRaises(ValueError):
                pilot.preview(('fictional-code', 'fictional-verifier', '007A', '42'))

    def test_claim_is_session_bound_one_time_and_expires(self):
        pilot = TerritoryHelperImport('fictional-client', 'http://127.0.0.1:8787/territory-helper-return')
        with patch('territory_helper.time.monotonic', return_value=100):
            state = pilot.begin('session-a', '007A', '42')['state']
        with patch('territory_helper.time.monotonic', return_value=101):
            with self.assertRaises(ValueError):
                pilot.claim('session-b', state, 'fictional-code')
            work = pilot.claim('session-a', state, 'fictional-code')
            self.assertEqual(work[2:], ('007A', '42'))
            with self.assertRaises(ValueError):
                pilot.claim('session-a', state, 'fictional-code')
            expired = pilot.begin('session-a', '007A', '42')['state']
        with patch('territory_helper.time.monotonic', return_value=402), self.assertRaises(ValueError):
            pilot.claim('session-a', expired, 'fictional-code')

    def test_beta_http_preview_and_confirm_use_existing_local_storage(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {
                'LTM_CHANNEL': 'beta', 'LTM_TERRITORY_HELPER_CLIENT_ID': 'fictional-client'}):
            store = Store(directory)
            server = Server(('127.0.0.1', 0), store)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            def post(path, data, token=None):
                headers = {'Content-Type': 'application/json',
                           'X-Distrikt-Token': server.token if token is None else token}
                with urlopen(Request(server.origin + path, json.dumps(data).encode(), headers), timeout=5) as response:
                    return json.load(response)

            try:
                before = store.revision
                begin_path = '/api/territory-helper/begin'
                fields = {'number': '007A', 'congregation': '42'}
                with self.assertRaises(HTTPError) as missing_csrf:
                    post(begin_path, fields, token='')
                self.assertEqual(missing_csrf.exception.code, 403)
                server.beta = False
                with self.assertRaises(HTTPError) as not_beta:
                    post(begin_path, fields)
                self.assertEqual(not_beta.exception.code, 403)
                server.beta = True
                begin = post(begin_path, fields)
                query = parse_qs(urlsplit(begin['authorize_url']).query)
                self.assertEqual(query['redirect_uri'], [server.origin + '/territory-helper-return'])
                self.assertEqual(query['code_challenge_method'], ['S256'])

                with patch('territory_helper.request_json', side_effect=[
                        {'access_token': 'fictional-access', 'refresh_token': 'fictional-refresh'}, [ROW]]) as request:
                    preview = post('/api/territory-helper/preview', {'state': begin['state'], 'code': 'fictional-code'})
                self.assertEqual(preview, {'number': '007A', 'name': 'Fiktivt kort', 'polygon': POLYGON})
                self.assertEqual(store.revision, before)
                self.assertEqual(store.all('cards'), [])
                token_call, territory_call = request.call_args_list
                self.assertEqual((token_call.args[0], token_call.kwargs['method']), ('/oauth/token', 'POST'))
                digest = hashlib.sha256(token_call.args[1]['code_verifier'].encode()).digest()
                import base64
                self.assertEqual(query['code_challenge'], [base64.urlsafe_b64encode(digest).decode().rstrip('=')])
                self.assertEqual(territory_call.args, ('/territories', {'access_token': 'fictional-access',
                                 'territory_number': '007A', 'congregation_id': '42'}))

                save = {'action': 'geo.assign', 'data': {**preview, 'address_ids': [], 'planned': True}}
                post('/api/mutate', save)
                with self.assertRaises(HTTPError) as duplicate:
                    post('/api/mutate', save)
                self.assertEqual(duplicate.exception.code, 400)
                card, = store.all('cards')
                self.assertEqual((card['number'], card['planned'], card['geo_polygon']), ('007A', True, POLYGON))
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                store.close()
