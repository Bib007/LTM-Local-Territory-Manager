"""Provider failures are actionable without echoing query values or credentials."""
import io
import json
import re
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from address_source import Datafordeler, reject_graphql
from dar_query import DarQuery
from postcode import SourceLimit
from test_dar_adapter import Provider, tables, STAMP

class DarErrorTests(unittest.TestCase):
    def test_only_known_diagnostics_survive_unknown_private_messages_and_paths(self):
        payload={'errors':[{'message':'The field `status` does not exist. FICTIONAL_SECRET https://invalid.example/?apiKey=FICTIONAL_SECRET','path':['FICTIONAL_PRIVATE_LOOKUP'],'extensions':{'code':'HC0011','exception':'FICTIONAL_SECRET'}}]}
        with self.assertRaises(ValueError) as error:reject_graphql(payload,'query { DAR_Adressepunkt(first:1) { nodes { id_lokalId } } }')
        message=str(error.exception);self.assertIn('GQL-SCHEMA',message);self.assertIn('HC0011',message);self.assertIn('status',message)
        self.assertNotIn('FICTIONAL',message);self.assertNotIn('http',message)

    def test_cost_is_typed_and_mixed_errors_cannot_be_mistaken_for_cost_only(self):
        for error in ({'message':'Max GraphQL request size reached FICTIONAL_SECRET'},{'extensions':{'code':'HC0047'},'message':'FICTIONAL_SECRET'}):
            with self.assertRaises(SourceLimit) as caught:reject_graphql({'errors':[error]},'query { DAR_Adresse(first:1){nodes{id_lokalId}} }')
            self.assertNotIn('FICTIONAL',str(caught.exception))
        with self.assertRaises(ValueError) as caught:reject_graphql({'errors':[{'extensions':{'code':'HC0047'}},{'message':'Unknown field `status` FICTIONAL_SECRET'}]},'query { DAR_Adresse(first:1){nodes{id_lokalId}} }')
        self.assertNotIsInstance(caught.exception,SourceLimit);self.assertIn('GQL-SCHEMA',str(caught.exception))

    def test_http_400_cost_body_is_classified_without_disclosing_url_or_key(self):
        body=json.dumps({'errors':[{'message':'Max GraphQL request size reached FICTIONAL_SECRET'}]}).encode()
        error=urllib.error.HTTPError('https://invalid.example/?apiKey=FICTIONAL_SECRET',400,'FICTIONAL_SECRET',{},io.BytesIO(body))
        with tempfile.TemporaryDirectory() as root,patch('address_source.urllib.request.build_opener') as make:
            make.return_value.open.side_effect=error
            with self.assertRaises(SourceLimit) as caught:Datafordeler(root)._request('FICTIONAL_SECRET',query='query { DAR_Adressepunkt(first:1){nodes{id_lokalId}} }')
            self.assertNotIn('FICTIONAL',str(caught.exception))

    def test_page_size_reduction_preserves_snapshot_filters_cursor_and_complete_units(self):
        provider=Provider(tables());calls=[]
        def source(query):
            calls.append(query)
            if any(int(n)>1 for n in re.findall(r'first:\s*(\d+)',query)):raise SourceLimit('Fiktiv størrelsesgrænse')
            return provider(query)
        result=DarQuery(source,snapshot=STAMP).collect('DAR_Adresse',{'husnummer':'h1'})
        self.assertEqual([r['id_lokalId'] for r in result],['a1','a2'])
        self.assertEqual(len(calls),5)
        for query in calls:self.assertIn(STAMP,query);self.assertIn('husnummer: { eq: "h1" }',query)
        self.assertIn('after: "1"',calls[-1])

    def test_alias_cost_falls_back_to_bounded_single_scopes(self):
        provider=Provider(tables());calls=[]
        def source(query):
            calls.append(query)
            if query.count('scope_')>1 or any(int(n)>4 for n in re.findall(r'first:\s*(\d+)',query)):raise SourceLimit('Fiktiv størrelsesgrænse')
            return provider(query)
        result=DarQuery(source,snapshot=STAMP).collect_many('DAR_Adresse','husnummer',['h1','h2'])
        self.assertEqual({r['id_lokalId'] for r in result},{'a1','a2','a3'});self.assertLessEqual(len(calls),6)
        for query in calls:self.assertIn(STAMP,query)

    def test_persistent_cost_stops_at_one_and_other_errors_are_not_retried(self):
        calls=[]
        def limited(query):calls.append(query);raise SourceLimit('Fiktiv grænse')
        with self.assertRaises(SourceLimit):DarQuery(limited).collect_bbox([550000,6170000,550100,6170100])
        self.assertEqual(len(calls),4);self.assertIn('first: 1',calls[-1])
        calls.clear()
        def invalid(query):calls.append(query);raise ValueError('Fiktiv skemafejl')
        with self.assertRaises(ValueError):DarQuery(invalid).collect('DAR_Postnummer',{'postnr':'9999'})
        self.assertEqual(len(calls),1)

    def test_access_error_is_distinct_from_key_connection_and_does_not_echo_details(self):
        with self.assertRaises(ValueError) as caught:reject_graphql({'errors':[{'message':'not authorized FICTIONAL_SECRET','extensions':{'code':'AUTH_NOT_AUTHORIZED'}}]},'query { DAR_Postnummer(first:1){nodes{id_lokalId}} }')
        self.assertIn('GQL-ACCESS',str(caught.exception));self.assertIn('selve dataopslaget',str(caught.exception));self.assertNotIn('FICTIONAL',str(caught.exception))

if __name__=='__main__':unittest.main()
