"""Real authenticated HTTP boundaries; invented card/address, no image service."""
import base64
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from server import Server
from store import Store
from test_photo_ocr import png


class PhotoHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name);self.server=Server(('127.0.0.1',0),self.store,access_host='127.0.0.1',password='Fictional-pass-123');self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.cookie=None
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.store.close();self.temp.cleanup()
    def request(self,path,body=None,token=True):
        headers={'X-Distrikt-Token':self.server.token} if token else {}
        if self.cookie:headers['Cookie']=self.cookie
        if body is not None:headers['Content-Type']='application/json'
        return urllib.request.urlopen(urllib.request.Request(self.server.origin+path,data=json.dumps(body).encode() if body is not None else None,headers=headers),timeout=3)
    def login(self):
        with self.request('/api/login',{'password':'Fictional-pass-123'},token=False) as response:self.cookie=response.headers['Set-Cookie'].split(';')[0]
    def test_login_token_and_private_static_asset(self):
        for path in ('/photo-import-ui.js','/api/photo/status','/api/photo/job?id=fake'):
            with self.assertRaises(urllib.error.HTTPError) as error:self.request(path)
            self.assertEqual(error.exception.code,401)
        self.login()
        with self.request('/photo-import-ui.js') as response:self.assertIn(b'PhotoImportUI',response.read())
        for path in ('/api/photo/read','/api/photo/cancel'):
            with self.assertRaises(urllib.error.HTTPError) as error:self.request(path,{},token=False)
            self.assertEqual(error.exception.code,403)
    def test_reviewed_import_requires_exact_card_and_confirmation_and_marks_back(self):
        self.login()
        self.store.mutate('geo.import',{'records':[dict(id='fictional-a',entity='address',road='Fiktivvej',number='8',postcode='9999',floor='1',door='tv',lng=10,lat=55,count=1)],'source':'Invented test data'})
        card=self.store.mutate('geo.assign',{'address_ids':['fictional-a'],'number':'901'})['id']
        self.store.mutate('revision.approve',{'card_id':card,'side':'front'});self.store.mutate('revision.approve',{'card_id':card,'side':'back'})
        def post(action,data):
            with self.request('/api/mutate',{'action':action,'data':data,'include_state':True}) as response:return json.load(response)
        content='kortnummer;vejnavn;husnummer;postnummer;etage;dør;dato\n901;Fiktivvej;8;9999;1;tv;2026-10-24'
        preview=post('setup.ib.preview',{'content':content})['result'];self.assertEqual(preview['new'],1);self.assertEqual(self.store.all('ib'),[])
        with self.assertRaises(urllib.error.HTTPError):post('setup.ib.apply',{'token':preview['token'],'confirm':'wrong'})
        self.assertEqual(self.store.all('ib'),[])
        result=post('setup.ib.apply',{'token':preview['token'],'confirm':'IMPORTÉR IB'})
        self.assertEqual(result['result']['count'],1);self.assertEqual(len(result['state']['ib']),1);self.assertTrue(self.store.get('cards',card)['back_revision']);self.assertFalse(self.store.get('cards',card)['front_revision'])
        duplicate=post('setup.ib.preview',{'content':content})['result'];self.assertEqual(duplicate['new'],0);self.assertEqual(duplicate['existing'],1)
        wrong=post('setup.ib.preview',{'content':content.replace(';1;tv;',';1;th;')})['result'];self.assertEqual(wrong['errors'],1)

    def test_read_start_cancel_never_modify_database_or_expose_images(self):
        self.login();before=self.store.revision
        with patch.object(self.server.photo_ocr,'available',return_value={'available':False,'languages':[]}):
            with self.request('/api/photo/status') as response:self.assertFalse(json.load(response)['available'])
            with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/photo/read',{'png':base64.b64encode(png()).decode()})
            self.assertEqual(error.exception.code,400)
        with self.request('/api/photo/cancel',{'id':'unknown'}) as response:self.assertTrue(json.load(response)['ok'])
        self.assertEqual(self.store.revision,before);self.assertEqual(self.store.all('ib'),[])

if __name__=='__main__':unittest.main()
