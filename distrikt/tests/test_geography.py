import io
import json
import math
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store, MODULES
from geography import point_in_polygon, valid_polygon, in_number_range, format_numbers, enclosing_outline, utm32_to_wgs84, decode_dar
from geodata import Downloads

POLYGON=[[9.99,54.99],[10.02,54.99],[10.02,55.02],[9.99,55.02]]
def address(id='a',number='1',floor='',door='',lng=10,lat=55,**extra):
    return dict(id=id,entity='address',road='Eksempelvej',number=number,postcode='9999',floor=floor,door=door,lng=lng,lat=lat,**extra)
def dar_unit(id='unit',number='42',floor=None,door=None):
    return {'id_lokalid':id,'status':'3','etagebetegnelse':floor,'doerbetegnelse':door,'adressebetegnelse':'Fiktiv testadresse',
        'husnummer':{'id_lokalid':'house','husnummertekst':number,'vejnavn':'Eksempelvej','postnummer':{'postnr':'9999'},
            'adgangspunkt':{'geometri':{'crs':{'properties':{'name':'EPSG:25832'}},'coordinates':[500000,6094791.420874]}}}}

class GeometryTests(unittest.TestCase):
    def test_polygon_includes_edges_and_handles_concave_shape(self):
        self.assertTrue(point_in_polygon([10,55],POLYGON));self.assertTrue(point_in_polygon([9.99,55],POLYGON));self.assertFalse(point_in_polygon([10.5,55],POLYGON))
        shape=[[10,55],[10.02,55],[10.02,55.02],[10.01,55.01],[10,55.02]]
        self.assertFalse(point_in_polygon([10.01,55.018],shape));self.assertTrue(point_in_polygon([10.001,55.001],shape))
    def test_invalid_boundaries(self):
        for poly in [[[10,55],[10,55],[10,55]],[[10,55],[10.01,55.01],[10.02,55.02]],[[10,55],[10.02,55.02],[10,55.02],[10.02,55]],[[math.nan,55],[10,55],[10,55.1]]]:
            with self.assertRaises(ValueError):valid_polygon(poly)
    def test_letters_parity_and_exact_ranges(self):
        self.assertTrue(in_number_range('12B','1','12B'));self.assertFalse(in_number_range('12C','1','12B'))
        self.assertTrue(in_number_range('12C','1','12'));self.assertFalse(in_number_range('43','42','58','even'))
        self.assertTrue(in_number_range('42A','42','58','even'))
        with self.assertRaises(ValueError):in_number_range('42','58','42')
    def test_compact_first_last_number_format(self):
        self.assertEqual(format_numbers(['5','1','3']),'1–5 (ulige)');self.assertEqual(format_numbers(['2','4','6']),'2–6 (lige)')
        self.assertEqual(format_numbers(['1','3','7']),'1–7 (ulige)');self.assertEqual(format_numbers(['1A','1C']),'1A–1C (ulige)')
        self.assertEqual(format_numbers(['1','2','3']),'1–3')
    def test_utm_and_outline(self):
        lng,lat=utm32_to_wgs84(500000,6094791.420874)
        self.assertAlmostEqual(lng,9,places=6);self.assertAlmostEqual(lat,55,places=6)
        for points in [[[10,55]],[[10,55],[10.001,55.001]],[[10,55],[10.001,55],[10,55.001]]]:
            shape=enclosing_outline(points)
            for p in points:self.assertTrue(point_in_polygon(p,shape))
    def test_dar_apartments_are_independent_units(self):
        units=decode_dar([dar_unit('u1'),dar_unit('u2',floor='1',door='tv')])
        self.assertEqual(len(units),2);self.assertEqual(units[1]['count'],1);self.assertEqual(units[1]['type'],'Lejlighed')
        closed=dar_unit('closed');closed['status']='4';self.assertEqual(decode_dar([closed]),[])

class GeoStorageTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def add(self,records):return self.s.mutate('geo.import',{'records':records,'source':'Test','label':'Fiktive adresser'})
    def test_auto_boundary_counts_all_units_and_skips_outside(self):
        self.add([address('a1','1'),address('a2','1',floor='1',door='tv'),address('a3','3'),address('out','5',lng=10.5)])
        preview=self.s.mutate('geo.preview',{'mode':'polygon','polygon':POLYGON});self.assertEqual(len(preview['addresses']),3);self.assertEqual(preview['visits'],3)
    def test_assign_keeps_loans_and_ib_and_enables_front_print(self):
        c=self.s.mutate('card.save',{'number':'120','temporary':True})['id'];p=self.s.mutate('publisher.save',{'name':'Testperson'})['id']
        l=self.s.mutate('loan.issue',{'card_id':c,'publisher_id':p,'date':'2026-01-01','initial':True})['id']
        ib=self.s.mutate('ib.save',{'card_id':c,'road':'Eksempelvej','number':'1','date':'2026-01-01'})['id']
        self.add([address('a1','1'),address('a3','3'),address('a5','5')]);self.s.mutate('geo.assign',{'card_id':c,'address_ids':['a1','a3','a5']})
        card=self.s.get('cards',c);self.assertFalse(card['temporary']);self.assertEqual(card['addresses'][0]['numbers'],'1–5 (ulige)');self.assertEqual(card['addresses'][0]['count'],3)
        self.assertEqual(self.s.active_loan(c)['id'],l);self.assertIsNotNone(self.s.get('ib',ib));self.assertTrue(card['front_revision']);self.assertTrue(card['geo_polygon'])
    def test_range_new_card_and_conflict_reservation(self):
        self.add([address('a42','42'),address('a42b','42B'),address('a43','43'),address('a58','58')])
        p=self.s.mutate('geo.preview',{'mode':'range','road':'Eksempelvej','postcode':'9999','from':'42','to':'58','parity':'even'})
        self.assertEqual(len(p['addresses']),3)
        c=self.s.mutate('geo.assign',{'number':'120','address_ids':['a42','a42b']})['id']
        with self.assertRaises(ValueError):self.s.mutate('geo.assign',{'number':'121','address_ids':['a42']})
        self.assertEqual(len(self.s.all('cards')),1)
        self.s.mutate('delete',{'module':'cards','id':c})
        self.assertNotIn('card_id',self.s.geo_state()['status']['a42'])
        self.s.mutate('geo.assign',{'number':'121','address_ids':['a42']})
    def test_duplicate_import_ids_do_not_inflate_units(self):
        self.add([address('a','1'),address('same-physical-unit','1')]);self.assertEqual(self.s.geo_info()['addresses'],1);result=self.s.mutate('geo.assign',{'number':'120','address_ids':['a','a']})
        self.assertEqual(result['visits'],1)
    def test_ignore_and_recovery_are_local(self):
        self.add([address()]);self.s.mutate('ignore.save',{'address_id':'a','reason':'Transformerstation'})
        preview=self.s.mutate('geo.preview',{'address_ids':['a']});self.assertEqual(preview['ignored'],['a'])
        with self.assertRaises(ValueError):self.s.mutate('geo.assign',{'number':'120','address_ids':['a']})
        item=self.s.all('ignored')[0];deletion=self.s.mutate('delete',{'module':'ignored','id':item['id']});self.assertEqual(self.s.all('ignored'),[])
        self.s.mutate('restore',deletion);self.assertEqual(len(self.s.all('ignored')),1)
    def test_csv_geojson_validation_is_atomic(self):
        self.s.mutate('geo.import_file',{'content':'road;number;postcode;lng;lat;floor;door\nEksempelvej;1;9999;10;55;st;tv\n','name':'Test.csv'})
        self.assertEqual(self.s.geo_info()['addresses'],1)
        with self.assertRaises(ValueError):self.add([address('good','3'),address('bad','5',lng=math.nan)])
        self.assertIsNone(self.s.get('geo','good'))
        geo={'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[10.002,55.002]},'properties':{'road':'Eksempelvej','number':'7','postcode':'9999'}}]}
        self.s.mutate('geo.import_file',{'content':json.dumps(geo),'name':'Test.geojson'});self.assertEqual(self.s.geo_info()['addresses'],2)
    def test_refresh_marks_retired_units_without_changing_cards(self):
        def load(records):return self.s.mutate('geo.import',{'records':records,'source':'DAR / Adressevælger','label':'Test','complete_road':{'road':'Eksempelvej','postcode':'9999'}})
        load([address('a'),address('b','3')]);c=self.s.mutate('geo.assign',{'number':'120','address_ids':['a','b']})['id'];before=self.s.get('cards',c)['addresses']
        load([address('a')]);self.assertTrue(self.s.get('geo','b')['retired']);self.assertEqual(self.s.get('cards',c)['addresses'],before)
        p=self.s.mutate('geo.preview',{'mode':'polygon','polygon':POLYGON,'card_id':c});self.assertEqual(len(p['addresses']),1)
    def test_v1_files_survive_new_modules(self):
        c=self.s.mutate('card.save',{'number':'120','temporary':True})['id'];self.s.close()
        for file in ('geodata.sqlite3','se_bort_fra.sqlite3'):(Path(self.tmp.name)/file).unlink()
        self.s=Store(self.tmp.name);self.assertEqual(self.s.get('cards',c)['number'],'120');self.assertEqual(len(list(Path(self.tmp.name).glob('*.sqlite3'))),11)
    def test_token_never_appears_in_state_or_geo_response(self):
        self.s.mutate('geo.token',{'token':'SECRETTESTVALUE'})
        self.assertNotIn('SECRETTESTVALUE',json.dumps(self.s.state()));self.assertNotIn('SECRETTESTVALUE',json.dumps(self.s.geo_state()))

class DownloadTests(unittest.TestCase):
    def test_public_road_download_decodes_all_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(tmp);d=Downloads(s);requests=[]
            def request(host,path,params=None,query=None):
                requests.append((host,path,params))
                if path=='/soeg':return {'status':'ok','fund':[{'type':'navngivenvejpostnummer','vejnavn':'Eksempelvej','postnr':'9999'}]}
                if path.endswith('/soeg'):return {'status':'ok','fund':[{'type':'adresse','id':'u1'},{'type':'adresse','id':'u2'}]}
                return {'status':'ok','adresser':[dar_unit('u1'),dar_unit('u2',floor='1',door='tv')]}
            d.request=request
            result=d.road({'road':'Eksempelvej','postcode':'9999'},lambda **kwargs:None)
            self.assertEqual(result['count'],2);self.assertEqual(s.geo_info()['addresses'],2)
            self.assertTrue(all(host=='adressevaelger.dk' for host,path,params in requests));self.assertNotIn('card_id',str(requests));s.close()
    def test_truncated_or_missing_data_never_marked_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(tmp);d=Downloads(s)
            def request(host,path,params=None,query=None):
                if path=='/soeg':return {'status':'ok','fund':[{'type':'navngivenvejpostnummer','vejnavn':'Eksempelvej','postnr':'9999'}]}
                if path.endswith('/soeg'):return {'status':'ok','fund':[{'type':'adresse','id':'u1'},{'type':'adresse','id':'u2'}]}
                return {'status':'ok','adresser':[dar_unit('u1')]}
            d.request=request
            with self.assertRaises(ValueError):d.road({'road':'Eksempelvej','postcode':'9999'},lambda **kwargs:None)
            self.assertEqual(s.geo_info()['addresses'],0);s.close()

if __name__=='__main__':unittest.main()
