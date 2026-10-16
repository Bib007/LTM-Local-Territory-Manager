"""KML fixtures are synthetic. Never load private boundaries or addresses."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'app'))
from boundary_import import preview_boundary
from store import Store

POINTS = [[10,55], [10.02,55], [10.02,55.02], [10,55.02]]


def polygon(points=POINTS, inner=''):
    coords = ' '.join(','.join(map(str,p))+',0' for p in points+points[:1])
    return '<Polygon><outerBoundaryIs><LinearRing><coordinates>'+coords+'</coordinates></LinearRing></outerBoundaryIs>'+inner+'</Polygon>'


def kml(body=None, namespace='http://www.opengis.net/kml/2.2'):
    return '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="'+namespace+'"><Document><Folder><name>Fiktivt område</name><Placemark><name>Fiktiv grænse ÆØÅ</name>'+(polygon() if body is None else body)+'</Placemark></Folder></Document></kml>'


class BoundaryImportTests(unittest.TestCase):
    def test_polygon_namespace_altitude_closed_ring_and_name(self):
        r = preview_boundary(kml())
        self.assertEqual(r['points'], POINTS)
        self.assertEqual(r['boundaries'][0]['name'], 'Fiktiv grænse ÆØÅ')
        self.assertEqual(r['format'], 'KML')
        self.assertEqual(r['limit'], 5000)

    def test_prefixed_and_legacy_namespace(self):
        for ns in ('', 'http://earth.google.com/kml/2.1', 'http://www.opengis.net/kml/2.3'):
            self.assertEqual(preview_boundary(kml(namespace=ns))['points'], POINTS)
        xml=kml().replace('<kml xmlns=', '<k:kml xmlns:k=').replace('</kml>','</k:kml>')
        self.assertEqual(preview_boundary(xml)['points'], POINTS)

    def test_multiple_polygons_are_returned_separately_never_merged(self):
        r=preview_boundary(kml('<MultiGeometry>'+polygon()+polygon([[11,56],[11.02,56],[11,56.02]])+'</MultiGeometry>'))
        self.assertEqual(len(r['boundaries']),2)
        self.assertNotIn('points',r)
        self.assertEqual(r['boundaries'][0]['points'],POINTS)
        self.assertEqual(r['boundaries'][1]['index'],1)

    def test_invalid_polygon_does_not_hide_another_valid_choice(self):
        r=preview_boundary(kml('<MultiGeometry>'+polygon(inner='<innerBoundaryIs/>')+polygon()+'</MultiGeometry>'))
        self.assertIn('huller',r['boundaries'][0]['error'])
        self.assertNotIn('points',r['boundaries'][0])
        self.assertEqual(r['boundaries'][1]['points'],POINTS)

    def test_closed_line_and_standalone_ring(self):
        for tag in ('LineString','LinearRing'):
            r=preview_boundary(kml('<'+tag+'><coordinates>10,55 10.02,55 10,55.02 10,55</coordinates></'+tag+'>'))
            self.assertEqual(len(r['points']),3)
        with self.assertRaisesRegex(ValueError,'ikke lukket'):
            preview_boundary(kml('<LineString><coordinates>10,55 10.02,55 10,55.02</coordinates></LineString>'))

    def test_marker_and_network_link_do_not_become_boundaries_or_fetch(self):
        from unittest.mock import patch
        xml=kml(polygon()+'<Point><coordinates>10,55</coordinates></Point><NetworkLink><Link><href>https://invalid.example/private.kml</href></Link></NetworkLink>')
        with patch('urllib.request.urlopen',side_effect=AssertionError('Network forbidden')):
            r=preview_boundary(xml)
        self.assertEqual(len(r['boundaries']),1)
        self.assertEqual(r['skipped'],2)
        with self.assertRaisesRegex(ValueError,'ingen polygoner'):preview_boundary(kml('<Point><coordinates>10,55</coordinates></Point>'))

    def test_holes_duplicate_corners_outside_denmark_crossings_and_bad_numbers_reject(self):
        for body in (polygon(inner='<innerBoundaryIs/>'),polygon(POINTS+POINTS[:1]),polygon([[1,1],[2,1],[1,2]]),polygon([[10,55],[10.03,55.02],[10.03,55],[10,55.03]]),polygon().replace('10,55,0','NaN,55,0'),polygon().replace('10,55,0','10,55,NaN'),polygon().replace('10,55,0','x,55,0')):
            with self.subTest(body=body[:100]),self.assertRaises(ValueError):preview_boundary(kml(body))

    def test_main_and_card_boundaries_accept_5000_corners(self):
        points=[[10+.01*math.cos(i*2*math.pi/5000),55+.01*math.sin(i*2*math.pi/5000)] for i in range(5000)]
        xml=kml(polygon(points))
        self.assertEqual(len(preview_boundary(xml)['points']),5000)
        self.assertEqual(len(preview_boundary(xml,'card')['points']),5000)
        with self.assertRaisesRegex(ValueError,'5000'):preview_boundary(kml(polygon(points+[[10.03,55.03]])))

    def test_xml_entities_dtd_wrong_namespace_and_malformed_files_reject(self):
        for xml in ('<!DOCTYPE kml [<!ENTITY x "test">]>'+kml(),kml(namespace='urn:foreign'),'<kml><Polygon>','not a boundary','',kml().replace('10,55,0','10,55,0,0')):
            with self.subTest(xml=xml[:50]),self.assertRaises(ValueError):preview_boundary(xml)

    def test_byte_size_and_candidate_limits(self):
        with self.assertRaisesRegex(ValueError,'2 MB'):preview_boundary('æ'*1000001)
        with self.assertRaisesRegex(ValueError,'100 grænser'):preview_boundary(kml('<MultiGeometry>'+polygon()*101+'</MultiGeometry>'))

    def test_geojson_compatibility_bom_closed_ring_and_invalid_crs(self):
        geo={'type':'Feature','properties':{'name':'Fiktiv GeoJSON'},'geometry':{'type':'Polygon','coordinates':[POINTS+POINTS[:1]]}}
        self.assertEqual(preview_boundary('\ufeff'+json.dumps(geo))['points'],POINTS)
        self.assertEqual(preview_boundary(kml().replace('<?xml version="1.0" encoding="UTF-8"?>',''))['points'],POINTS)
        geo['crs']={'properties':{'name':'EPSG:25832'}}
        with self.assertRaisesRegex(ValueError,'WGS84'):preview_boundary(json.dumps(geo))

    def test_preview_never_saves_and_explicit_save_preserves_existing_private_records(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(d)
            try:
                c=s.mutate('card.save',{'number':'120','temporary':True})['id']
                s.mutate('ib.save',{'card_id':c,'road':'Fiktiv vej','number':'1','date':'2026-01-01'})
                s.mutate('note.save',{'card_id':c,'text':'Fiktiv privat note'})
                s.mutate('geo.main.save',{'points':[[11,56],[11.02,56],[11,56.02]]})
                before=s.state();boundary=s.main_boundary();revision=s.revision
                r=s.mutate('geo.main.import.preview',{'content':kml()})
                self.assertEqual(s.main_boundary(),boundary)
                self.assertEqual(s.revision,revision)
                s.mutate('geo.main.save',{'points':r['points']})
                for key in ('cards','ib','notes','loans','publishers','completions','ignored'):
                    self.assertEqual(s.state()[key],before[key],key)
                r=s.mutate('geo.main.import.preview',{'content':kml(),'scope':'card'})
                s.mutate('geo.boundary',{'card_id':c,'polygon':r['points']})
                self.assertEqual(s.require('cards',c)['geo_polygon'],POINTS)
                self.assertEqual(s.require('cards',c)['temporary'],True)
                self.assertEqual(s.state()['ib'],before['ib'])
                s.close();s=Store(d)
                self.assertEqual(s.main_boundary()['points'],POINTS)
            finally:s.close()


if __name__=='__main__':unittest.main()
