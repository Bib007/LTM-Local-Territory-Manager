"""Invented keys and upstream responses only; never access a real account."""
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from address_source import Datafordeler,NoRedirect,MAX_SCHEMA
from portable import snapshot,Restores
from store import Store

SCHEMA=b'type Query { DAR_Adresse: String DAR_Husnummer: String DAR_Postnummer: String }'
KEY='FICTIONAL_KEY_123456789'
PROBE=b'{"data":{"__typename":"Query"}}'

class AddressSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.client=Datafordeler(self.temp.name)

    def connect(self,key=KEY):
        with patch.object(self.client,'_request',side_effect=[SCHEMA,PROBE]):return self.client.connect(key)

    def test_check_persists_only_local_credential_and_public_schema(self):
        self.assertFalse(self.client.status()['configured'])
        result=self.connect();self.assertTrue(result['configured']);self.assertFalse(result['import_ready'])
        self.assertNotIn(KEY,json.dumps(result));self.assertEqual(self.client._auth()['api_key'],KEY)
        if os.name!='nt':self.assertEqual(os.stat(self.client.path).st_mode&0o777,0o600)
        schema=self.client.cache/('schema-'+result['schema_sha256']+'.graphql');self.assertEqual(schema.read_bytes(),SCHEMA)
        if os.name!='nt':self.assertEqual(os.stat(schema).st_mode&0o777,0o600)
        self.assertTrue(Datafordeler(self.temp.name).status()['configured'])
        with patch.object(self.client,'_request',side_effect=[SCHEMA,PROBE]):self.client.check()
        self.client.disconnect();self.assertFalse(self.client.path.exists());self.assertFalse(self.client.status()['configured'])

    def test_failed_replacement_or_probe_preserves_previous_key(self):
        self.connect();before=self.client.path.read_bytes()
        cases=[(b'<html>login</html>',),(SCHEMA,b'{"errors":[{"message":"'+KEY.encode()+b'"}]}'),(SCHEMA,b'not-json'),(SCHEMA,b'{"data":null}')]
        for replies in cases:
            with patch.object(self.client,'_request',side_effect=replies):
                with self.assertRaises(ValueError) as error:self.client.connect('FICTIONAL_REPLACEMENT')
            self.assertNotIn(KEY,str(error.exception));self.assertEqual(before,self.client.path.read_bytes())
        with patch('address_source.write_private',side_effect=OSError('Fictional disk full')):
            with self.assertRaises(OSError):self.connect('FICTIONAL_REPLACEMENT')
        self.assertEqual(before,self.client.path.read_bytes())

    def test_validation_does_not_contact_provider(self):
        with patch.object(self.client,'_request') as request:
            for value in (None,[],123,'short','x'*2001,'bad key'*4,'x\n'*20):
                with self.assertRaises(ValueError):self.client.connect(value)
            with self.assertRaises(ValueError):self.client.check()
            request.assert_not_called()

    def test_fixed_origin_encoded_key_no_redirect_and_no_request_body_data(self):
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        for suffix,query in [('/schema',None),('', 'query { __typename }')]:
            with patch('address_source.urllib.request.build_opener') as make:
                make.return_value.open.return_value=Response(SCHEMA)
                self.client._request('FAKE+KEY&not_a_parameter=secret',suffix,query)
                self.assertIsInstance(make.call_args.args[0],NoRedirect)
                req=make.return_value.open.call_args.args[0]
                self.assertTrue(req.full_url.startswith('https://graphql.datafordeler.dk/DAR/v3'+suffix+'?apiKey='))
                self.assertIn('%26',req.full_url);self.assertNotIn('&not_a_parameter',req.full_url)
                self.assertEqual(req.data,json.dumps({'query':query}).encode() if query else None)
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,None,None,'https://example.invalid'))

    def test_upstream_errors_never_echo_key_or_url(self):
        for status in (301,401,403,429,500):
            with patch('address_source.urllib.request.build_opener') as make:
                make.return_value.open.side_effect=urllib.error.HTTPError('https://fake.invalid/?apiKey='+KEY,status,KEY,{},None)
                with self.assertRaises(ValueError) as error:self.client._request(KEY)
                self.assertNotIn(KEY,str(error.exception));self.assertNotIn('fake.invalid',str(error.exception))
        with patch('address_source.urllib.request.build_opener') as make:
            make.return_value.open.side_effect=urllib.error.URLError(KEY)
            with self.assertRaises(ValueError) as error:self.client._request(KEY)
            self.assertNotIn(KEY,str(error.exception))

    def test_portable_backup_excludes_key_and_beta_reset_keeps_connection(self):
        store=Store(self.temp.name);self.addCleanup(store.close);self.connect()
        store.mutate('card.save',{'number':'FAKE','temporary':True})
        raw=snapshot(store,'FICTIONAL')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            self.assertFalse(any('datafordeler' in n for n in archive.namelist()))
            self.assertFalse(any(KEY.encode() in archive.read(n) for n in archive.namelist()))
        Restores(store,'FICTIONAL').reset_beta('NULSTIL BETA',store.revision)
        self.assertEqual(self.client._auth()['api_key'],KEY)
