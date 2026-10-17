import io
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store, MODULES
from server import Server

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.server=Server(('127.0.0.1',0),self.store);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.store.close();self.tmp.cleanup()
    def request(self,path,body=None,token=True,headers=None):
        h={'X-Distrikt-Token':self.server.token} if token else {}
        if body is not None:h['Content-Type']='application/json'
        h.update(headers or {})
        req=urllib.request.Request(self.server.origin+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
        return urllib.request.urlopen(req,timeout=3)
    def test_parameterized_validation_metadata_keeps_original_error_and_does_not_write(self):
        before=self.store.revision
        cases=[
            ({'action':'setup.preview','data':{'target':0}},'Besøg pr. kort skal være mellem 1 og 1000.','{label} skal være mellem {low} og {high}.',{'label':'Besøg pr. kort','low':1,'high':1000}),
            ({'action':'setup.ib.preview','data':{'content':'vejnavn;husnummer;postnummer\nFiktiv;1;9999','date':'not-a-date'}},'Dato skal være en gyldig dato.','{field} skal være en gyldig dato.',{'field':'Dato'}),
        ]
        for payload,original,key,params in cases:
            with self.assertRaises(urllib.error.HTTPError) as caught:self.request('/api/mutate',payload)
            self.assertEqual(caught.exception.code,400)
            body=json.load(caught.exception)
            self.assertEqual(body,{'error':original,'ui_error':{'key':key,'params':params}})
            self.assertEqual(self.store.revision,before)
    def test_address_source_api_keeps_key_private_and_requires_token(self):
        schema=b'type Query { DAR_Adresse: String DAR_Husnummer: String DAR_Postnummer: String }'
        fake_key='FICTIONAL_ADDRESS_KEY_123456'
        for path,body in [('/api/address-source/status',None),('/api/address-source/connect',{'api_key':fake_key}),('/api/address-source/check',{}),('/api/address-source/disconnect',{})]:
            with self.assertRaises(urllib.error.HTTPError) as error:self.request(path,body,token=False)
            self.assertEqual(error.exception.code,403)
        with patch.object(self.server.address_source,'_request',side_effect=[schema,b'{"data":{"__typename":"Query"}}']):
            with self.request('/api/address-source/connect',{'api_key':fake_key}) as response:self.assertTrue(json.load(response)['configured'])
        for path in ['/api/address-source/status','/api/state','/api/geo']:
            with self.request(path) as response:self.assertNotIn(fake_key,response.read().decode())
        with self.request('/api/address-source/disconnect',{}) as response:self.assertFalse(json.load(response)['configured'])
        with self.request('/address-source-ui.js') as response:self.assertIn(b'AddressSourceUI',response.read())

    def test_state_version_matches_running_server_in_both_channels(self):
        from server import VERSION
        for beta in (False,True):
            self.server.beta=beta
            with self.request('/api/state') as response:state=json.load(response)
            with self.request('/api/ping',token=False) as response:ping=json.load(response)
            self.assertEqual(state['version'],VERSION)
            self.assertEqual(state['version'],ping['version'])
            self.assertEqual(state['beta'],beta)

    def test_local_printing_code_is_available_with_app_security_policy(self):
        with self.request('/printing.js') as response:
            self.assertEqual(response.status,200)
            self.assertIn(b'function printOptions',response.read())
            self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])

    def test_navigation_language_asset_and_desktop_stop_control(self):
        with self.request('/i18n.js') as response:
            self.assertEqual(response.status,200)
            self.assertIn(b'const I18n=',response.read())
            self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
        with self.request('/') as response:
            html=response.read().decode()
            self.assertIn('data-action="stop" data-ui="Luk den lokale app"',html)
            self.assertIn('/i18n.js',html)
            self.assertNotIn('Lokalt på din Mac',html)
    def test_large_private_payload_is_gzipped_without_public_cache(self):
        import gzip
        with self.store.transaction():
            for i in range(500):self.store.put('geo',{'id':str(i),'entity':'address','road':'Fiktiv vej','number':str(i),'postcode':'9999','lat':55,'lng':10,'count':1,'label':'Fiktiv adresse '+str(i)})
        with self.request('/api/geo',headers={'Accept-Encoding':'gzip'}) as response:
            self.assertEqual(response.headers['Content-Encoding'],'gzip');self.assertEqual(response.headers['Cache-Control'],'no-store')
            self.assertEqual(len(json.loads(gzip.decompress(response.read()))['addresses']),500)
        for asset in ('/workspace.js','/workspace.css'):
            with self.request(asset) as response:self.assertEqual(response.status,200)
    def test_bootstrap_and_headers(self):
        with self.request('/',token=False) as r:
            html=r.read().decode();self.assertIn(self.server.token,html);self.assertIn('frame-ancestors',r.headers['Content-Security-Policy']);self.assertEqual(r.headers['Cache-Control'],'no-store')
    def test_removed_aerial_endpoints_and_unchanged_map_assets(self):
        for path in ('/navigation.js','/basemaps.js','/ib-ui.js','/report-map.js'):
            with self.request(path) as response:self.assertEqual(response.status,200)
        for path in ('/api/basemap/status','/api/basemap/tile/11/1079/642'):
            with self.assertRaises(urllib.error.HTTPError) as error:self.request(path)
            self.assertEqual(error.exception.code,404)
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/mutate',{'action':'geo.basemap.save','data':{'apikey':'TEST_FAKE_KEY'}})

    def test_admin_assets_and_storage_authentication(self):
        with self.request('/admin.js') as r:self.assertIn(b'AdminUI',r.read())
        with self.request('/district-map.js') as r:self.assertIn(b'DistrictMap',r.read())
        with self.request('/main-boundary.js') as r:self.assertIn(b'MainBoundaryUI',r.read())
        with self.request('/report-print.js') as r:self.assertIn(b'reportPrintDocument',r.read())
        with self.request('/s13-template.js') as r:self.assertIn(b'S13Template',r.read())
        with self.request('/s13-background.jpg') as r:self.assertEqual(r.headers['Content-Type'],'image/jpeg');self.assertGreater(len(r.read()),1000)
        with self.assertRaises(urllib.error.HTTPError) as cm:self.request('/boundary-proposal.geojson')
        self.assertEqual(cm.exception.code,404)
        with self.request('/api/storage') as r:self.assertEqual(len(json.load(r)['files']),11)
        with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/storage',token=False)
        self.assertEqual(e.exception.code,403)
    def test_main_boundary_write_preview_and_download_cleanup_guard(self):
        payload={'action':'geo.main.save','data':{'points':[[9.99,54.99],[10.01,54.99],[10.01,55.01],[9.99,55.01]]}}
        with self.request('/api/mutate',payload) as r:self.assertEqual(json.load(r)['result']['points'],4)
        with self.request('/api/mutate',{'action':'geo.main.prune.preview','data':{}}) as r:p=json.load(r)['result']
        with patch.object(self.server.downloads,'status',return_value={'status':'running'}):
            with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/mutate',{'action':'geo.main.prune','data':{'expected':p['expected']}})
            self.assertEqual(e.exception.code,400)
    def test_kml_preview_asset_token_and_no_implicit_save(self):
        xml='<kml xmlns="http://www.opengis.net/kml/2.2"><Placemark><name>Fiktiv grænse</name><Polygon><outerBoundaryIs><LinearRing><coordinates>10,55 10.02,55 10,55.02 10,55</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></kml>'
        payload={'action':'geo.main.import.preview','data':{'content':xml}}
        revision=self.store.revision
        with self.request('/api/mutate',payload) as response:
            result=json.load(response)
            self.assertEqual(result['result']['points'],[[10,55],[10.02,55],[10,55.02]])
            self.assertEqual(result['revision'],revision)
        self.assertIsNone(self.store.main_boundary())
        with self.request('/boundary-import.js') as response:
            self.assertIn(b'BoundaryImportUI',response.read())
            self.assertEqual(response.headers['Cache-Control'],'no-store')
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/mutate',payload,token=False)
        self.assertEqual(error.exception.code,403)
    def test_setup_assets_and_private_blank_ib_template(self):
        with self.request('/setup-ui.js') as response:
            self.assertIn(b'SetupUI',response.read())
        with self.request('/api/setup/ib-template.csv') as response:
            self.assertEqual(response.headers['Cache-Control'],'no-store')
            self.assertIn('IB-import-skabelon.csv',response.headers['Content-Disposition'])
            content=response.read().decode('utf-8-sig')
            self.assertEqual(len(content.splitlines()),1)
            self.assertEqual(content.split(';')[0],'kortnummer')
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/setup/ib-template.csv',token=False)
        self.assertEqual(error.exception.code,403)
    def test_no_foreign_origin_or_missing_token(self):
        for token,headers in [(False,{}),(True,{'Origin':'https://example.com'}),(True,{'Host':'evil.example'})]:
            with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/state',token=token,headers=headers)
            self.assertEqual(e.exception.code,403)
    def test_actual_write_read_backup_pdf(self):
        with self.request('/api/mutate',{'action':'card.save','data':{'number':'120','temporary':True}}) as r:self.assertTrue(json.load(r)['ok'])
        with self.request('/api/state') as r:self.assertEqual(json.load(r)['cards'][0]['number'],'120')
        with self.request('/api/export/backup') as r:
            z=zipfile.ZipFile(io.BytesIO(r.read()));self.assertEqual(len([n for n in z.namelist() if n.endswith('.sqlite3')]),len(MODULES))
        with self.request('/api/export/s13?year=2027') as r:self.assertEqual(r.headers['Content-Type'],'application/pdf');self.assertTrue(r.read().startswith(b'%PDF'))
    def test_removed_boundary_reference_is_unavailable(self):
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/boundary-reference.png')
        self.assertEqual(error.exception.code,404)

    def test_no_directory_exposure(self):
        for path in ['/../store.py','/store.py','/data/kort.sqlite3','/api/export/s13?year=-1']:
            with self.assertRaises(urllib.error.HTTPError):self.request(path)
    def test_invalid_mutation_preserves_state(self):
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/mutate',{'action':'loan.issue','data':{'card_id':'none'}})
        self.assertEqual(self.store.all('loans'),[])

    def test_geodata_and_local_map_assets(self):
        for path in ('/geo.js','/road-search.js','/map-export.js','/vendor/leaflet.js','/vendor/leaflet.css'):
            with self.request(path,token=False) as response:self.assertGreater(len(response.read()),1000)
        with self.request('/api/geo') as response:self.assertEqual(json.load(response)['addresses'],[])
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/geo',token=False)
        with self.request('/api/geo/job') as response:self.assertEqual(json.load(response)['status'],'idle')
        with self.request('/api/mutate',{'action':'geo.manual','data':{'road':'Eksempelvej','number':'1','postcode':'9999','lng':10,'lat':55}}) as response:self.assertTrue(json.load(response)['ok'])
        with self.request('/api/geo') as response:self.assertEqual(len(json.load(response)['addresses']),1)

    def test_official_suggestions_require_token_and_pass_only_public_fields(self):
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/geo/suggest?road=eksempel&postcode=9999',token=False)
        with patch.object(self.server.downloads,'suggest',return_value={'suggestions':[{'road':'Eksempelvej','postcode':'9999'}]}) as suggest:
            with self.request('/api/geo/suggest?road=eksempel&postcode=9999') as response:self.assertEqual(json.load(response)['suggestions'][0]['road'],'Eksempelvej')
            suggest.assert_called_once_with('eksempel','9999')
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/geo/pause',{'job_id':'none'})


    def test_front_qr_asset_and_public_metadata(self):
        from sharing import fingerprint
        ident=self.store.mutate('card.save',{'number':'120','temporary':True})['id']
        with self.store.transaction():
            c=self.store.get('cards',ident)
            self.store.put('maps',{'id':'publication:'+ident,'entity':'publication','card_id':ident,'status':'published','url':'https://drive.google.com/file/d/TEST_QR/view','fingerprint':fingerprint(self.store,c)})
        with self.request('/api/state') as response:
            state=json.load(response);self.assertEqual(state['public_maps'][0]['card_id'],ident)
        with self.request('/card-qr.svg?card_id='+ident,token=False) as response:
            self.assertEqual(response.headers['Content-Type'],'image/svg+xml');self.assertIn(b'<svg',response.read())
