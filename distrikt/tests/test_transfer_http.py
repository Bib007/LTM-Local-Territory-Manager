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
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from server import Server
from store import Store

class TransferHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name);self.server=Server(('127.0.0.1',0),self.store)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.store.close();self.temp.cleanup()
    def req(self,path,data=None,kind='application/json',token=True):
        headers={'X-Distrikt-Token':self.server.token} if token else {}
        if data is not None:
            headers['Content-Type']=kind
            if kind=='application/json':data=json.dumps(data).encode()
        return urllib.request.urlopen(urllib.request.Request(self.server.origin+path,data,headers),timeout=5)
    def test_full_export_preview_confirm_and_safety_download(self):
        c=self.store.mutate('card.save',{'number':'120','temporary':True})['id']
        with self.req('/api/export/backup') as r:backup=r.read()
        self.store.mutate('card.save',{'number':'999','temporary':True})
        with self.req('/api/restore/preview',backup,'application/zip') as r:preview=json.load(r)
        self.assertEqual(preview['counts']['cards'],1);self.assertEqual(len(self.store.all('cards')),2)
        with self.req('/api/restore/apply',{'token':preview['token']}) as r:result=json.load(r)
        self.assertEqual([x['id'] for x in self.store.all('cards')],[c])
        with self.req('/api/restore/safety?name='+result['safety_backup']) as r:
            with zipfile.ZipFile(io.BytesIO(r.read())) as z:self.assertIn('kort.sqlite3',z.namelist())
    def test_private_endpoints_require_token(self):
        for path in ('/api/share/status','/api/share/qr?card_id=foo','/api/export/backup','/api/restore/safety?name=../access.json'):
            with self.assertRaises(urllib.error.HTTPError) as error:self.req(path,token=False)
            self.assertEqual(error.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/restore/preview',b'fake','application/zip',token=False)
    def test_loan_driven_sharing_endpoints_keep_printable_qr_while_private(self):
        import base64
        from test_sharing import FakeDrive,png
        sharing=self.server.sharing;sharing.drive=FakeDrive()
        c=self.store.mutate('card.save',{'number':'120','temporary':True})['id']
        with self.store.transaction():
            card=self.store.get('cards',c);card['geo_polygon']=[[10,55],[10.02,55],[10.02,55.02]];self.store.put('cards',card)
        with self.req('/api/share/prepare',{'card_id':c}) as r:prepared=json.load(r)
        with self.req('/api/share/publish',{'card_id':c,'fingerprint':prepared['fingerprint'],'png':'data:image/png;base64,'+base64.b64encode(png()).decode()}) as r:self.assertTrue(json.load(r)['ok'])
        sharing.process_one()
        with self.req('/api/state') as r:state=json.load(r)
        self.assertEqual(len(state['public_maps']),1);link=state['public_maps'][0]['url']
        with self.req('/api/share/qr?card_id='+c) as r:qr=r.read()
        with self.req('/api/mutate',{'action':'loan.issue','data':{'card_id':c,'publisher_name':'Fiktiv person','date':'2026-01-01','initial':True}}) as r:loan=json.load(r)['result']['id']
        sharing.process_one()
        with self.req('/api/share/status') as r:self.assertEqual(json.load(r)['cards'][0]['status'],'published')
        with self.req('/api/mutate',{'action':'loan.finish','data':{'id':loan,'date':'2026-01-02','complete':False,'retain':False}}) as r:self.assertTrue(json.load(r)['ok'])
        sharing.process_one()
        with self.req('/api/share/status') as r:self.assertEqual(json.load(r)['cards'][0]['status'],'ready')
        with self.req('/api/state') as r:self.assertEqual(json.load(r)['public_maps'],[{'card_id':c,'url':link}])
        with self.req('/api/share/qr?card_id='+c) as r:self.assertEqual(r.read(),qr)
    def test_static_credentials_and_traversal_inaccessible(self):
        (Path(self.temp.name)/'drive-auth.json').write_text('FAKE_PRIVATE_SECRET')
        for path in ('/drive-auth.json','/access.json','/portable.py','/api/restore/safety?name=../drive-auth.json'):
            with self.assertRaises(urllib.error.HTTPError):self.req(path)
        for path in ('/share-ui.js','/transfer-ui.js','/login.js'):
            with self.req(path) as r:self.assertEqual(r.status,200)
    def test_ha_package_is_private_and_has_no_api_privileges(self):
        root=Path(__file__).resolve().parents[1];cfg=(root/'config.yaml').read_text()
        for text in ('ingress: false','host_network: false','hassio_api: false','homeassistant_api: false','backup_exclude:\n  - "*"'):self.assertIn(text,cfg)
        self.assertNotIn('privileged:',cfg);self.assertNotIn('full_access:',cfg)
        self.assertIn('--lan', (root/'run.sh').read_text())
