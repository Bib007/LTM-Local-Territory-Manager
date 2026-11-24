"""Synthetic offline boundary format tests. No live congregation or outside services."""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from territory_boundary_adapter import nws_to_geojson, geojson_to_nws, th_to_geojson, geojson_to_th, main
from boundary_import import preview_boundary

RING = [[10, 55], [10.01, 55], [10.01, 55.01], [10, 55.01], [10, 55]]


def nw(*, boundary=None, number='17', extra=None):
    out = io.StringIO(newline='')
    fields = ['Number', 'CategoryCode', 'Suffix', 'Boundary'] + (['Notes'] if extra is not None else [])
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    row = {'Number': number, 'CategoryCode': 'C', 'Suffix': 'A',
           'Boundary': boundary if boundary is not None else ','.join(json.dumps(p) for p in RING)}
    if extra is not None:
        row['Notes'] = extra
    writer.writerow(row)
    return out.getvalue()


class TerritoryBoundaryAdapterTests(unittest.TestCase):
    def test_roundtrip_preserves_numbers_category_and_coordinates(self):
        with patch('urllib.request.urlopen', side_effect=AssertionError('No external requests')):
            geo, preview = nws_to_geojson(nw())
            self.assertEqual(preview['hjørner'], 4)
            csv_text, back = geojson_to_nws(geo)
            self.assertEqual(back['distrikt'], '17')
            regenerated, _ = nws_to_geojson(csv_text)
        self.assertEqual(json.loads(regenerated), json.loads(geo))
        self.assertEqual(json.loads(geo)['properties']['nws']['CategoryCode'], 'C')

    def test_no_lossy_notes_or_private_columns(self):
        with self.assertRaisesRegex(ValueError, 'Kun Number'):
            nws_to_geojson(nw(extra='Private person'))
        geo, _ = nws_to_geojson(nw())
        obj = json.loads(geo)
        obj['properties']['Notes'] = 'Private person'
        with self.assertRaisesRegex(ValueError, 'private felter'):
            geojson_to_nws(json.dumps(obj))

    def test_malformed_csv_multiple_territories_and_invalid_boundary(self):
        cases = (nw() + nw().split('\n', 1)[1], nw(boundary='[10,55],[10.01,55]'),
                 nw(boundary='[10,55],[10.01,55],[10,55.01],[10,55.02]'),
                 nw(boundary='[10,55],[10.01,55],[10,55.01],[10,55]') + 'unexpected,extra\n',
                 nw(number='0017'))
        for content in cases:
            with self.subTest(case=content[-50:]), self.assertRaises(ValueError):
                nws_to_geojson(content)

    def test_out_of_denmark_and_bad_metadata_rejected(self):
        foreign = [[13, 52], [13.01, 52], [13, 52.01], [13, 52]]
        with self.assertRaises(ValueError):
            nws_to_geojson(nw(boundary=','.join(json.dumps(x) for x in foreign)))
        geo, _ = nws_to_geojson(nw())
        with self.assertRaisesRegex(ValueError, 'afviger'):
            geojson_to_nws(geo, number='18')

    def test_territory_helper_kml_local_roundtrip_and_reject_lossy_inputs(self):
        geo, _ = nws_to_geojson(nw())
        kml, summary = geojson_to_th(geo)
        self.assertEqual(summary['grænser'], 1)
        self.assertEqual(preview_boundary(kml)['points'], RING[:-1])
        result, preview = th_to_geojson(kml)
        self.assertEqual(preview['hjørner'], 4)
        self.assertEqual(json.loads(result)['geometry']['coordinates'][0], RING)
        unsafe = kml.replace('</Document>', '<NetworkLink><Link><href>https://invalid.example/private.kml</href></Link></NetworkLink></Document>')
        with self.assertRaisesRegex(ValueError, 'præcis én polygon'):
            th_to_geojson(unsafe)
        altered = json.loads(geo)
        altered['properties']['Publisher'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'private felter'):
            geojson_to_th(json.dumps(altered))

    def test_preview_approval_and_no_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / 'fictional.csv', Path(temp) / 'fictional.geojson'
            source.write_text(nw(), encoding='utf-8')
            with patch('builtins.print'):
                self.assertEqual(main(['nws-to-ltm', str(source), str(target)]), 0)
                self.assertFalse(target.exists())
                self.assertEqual(main(['nws-to-ltm', str(source), str(target), '--approve', 'no']), 1)
                self.assertFalse(target.exists())
                code = hashlib.sha256(('nws-to-ltm\n' + nws_to_geojson(nw())[0]).encode()).hexdigest()[:16]
                self.assertEqual(main(['nws-to-ltm', str(source), str(target), '--approve', code]), 0)
                first = target.read_bytes()
                self.assertEqual(main(['nws-to-ltm', str(source), str(target), '--approve', code]), 1)
            self.assertEqual(target.read_bytes(), first)
            self.assertEqual(json.loads(first)['geometry']['coordinates'][0], RING)
            self.assertEqual(main(['nws-to-ltm', str(source), str(source), '--approve', code]), 1)
            self.assertEqual(source.read_text(encoding='utf-8'), nw())

    def test_file_size_and_csv_formula_injection_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'Number'):
            nws_to_geojson(nw(number='=1+1'))
        with self.assertRaisesRegex(ValueError, '2 MB'):
            nws_to_geojson('X' * 2000001)


if __name__ == '__main__':
    unittest.main()
