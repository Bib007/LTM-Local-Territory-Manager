import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from geodata import Downloads
from postcode import rest_addresses,rest_road_lines,Paused,BASE,HOST
from test_geography import address,POLYGON

def unit(id,number='1',road='Eksempelvej',post='9999',floor='',door=''):
    return {'id_lokalId':id,'status':'3','etagebetegnelse':floor,'dørbetegnelse':door,
        'husnummer':{'id_lokalId':'house:'+number,'husnummertekst':number,'postnummer':{'postnr':post},
            'navngivenVej':{'vejnavn':road},'adgangspunkt':{'position':'POINT(500000 6094791.420874)'}}}

class PostcodeTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name);self.d=Downloads(self.s)
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def request(self,roads,records,fail=None):
        calls=[]
        def request(host,path,params=None,query=None):
            calls.append((host,path,dict(params or {})))
            self.assertEqual(host,HOST);self.assertNotIn('card_id',params);self.assertNotIn('publisher_id',params)
            if path==BASE+'postnummer':return [{'id_lokalId':'post','postnr':'9999','navn':'Eksempelby'}]
            if path==BASE+'navngivenvej':items=roads
            else:
                if params['NavngivenVej']==fail:raise ValueError('Fiktiv netværksfejl')
                items=records.get(params['NavngivenVej'],[])
            size=params['pagesize'];start=(params['page']-1)*size;return copy.deepcopy(items[start:start+size])
        self.d.request=request;return calls
    def test_rest_decoder_preserves_apartments_and_filters_other_postcode(self):
        rows=rest_addresses([unit('u1'),unit('u2',floor='1',door='tv'),unit('outside',post='8888')],'9999','Eksempelvej')
        self.assertEqual(len(rows),2);self.assertEqual(rows[1]['door'],'tv');self.assertEqual(rows[1]['count'],1)
        bad=unit('bad');bad['husnummer']['adgangspunkt']['position']='POINT EMPTY'
        with self.assertRaises(ValueError):rest_addresses([bad],'9999','Eksempelvej')
    def test_complete_postcode_over_multiple_pages_and_independent_units(self):
        roads=[{'id_lokalId':f'r{i}','vejnavn':f'Eksempelvej {i}'} for i in range(5)]
        records={r['id_lokalId']:[unit(r['id_lokalId']+'u'+str(j),str(j+1),r['vejnavn']) for j in range(7)] for r in roads}
        calls=self.request(roads,records)
        with patch('postcode.PAGE_SIZE',3):result=self.d.postcode({'postcode':'9999'},lambda **kw:None)
        self.assertTrue(result['complete']);self.assertEqual(result['count'],35);self.assertEqual(self.s.geo_info()['addresses'],35)
        self.assertTrue(any(c[2].get('page',0)>1 for c in calls));self.assertEqual(self.s.get('geo','postcode:9999')['status'],'complete')
    def test_partial_failure_resumes_only_missing_road_across_restart(self):
        roads=[{'id_lokalId':'r1','vejnavn':'Eksempelvej'},{'id_lokalId':'r2','vejnavn':'Anden vej'}]
        records={'r1':[unit('a')],'r2':[unit('b',road='Anden vej')]};self.request(roads,records,fail='r2')
        result=self.d.postcode({'postcode':'9999'},lambda **kw:None);self.assertFalse(result['complete']);self.assertEqual(len(result['warnings']),1)
        self.s.close();self.s=Store(self.tmp.name);self.d=Downloads(self.s);calls=self.request(roads,records)
        result=self.d.postcode({'postcode':'9999'},lambda **kw:None);self.assertTrue(result['complete'])
        self.assertEqual([p['NavngivenVej'] for h,e,p in calls if e==BASE+'adresse'],['r2'])
    def test_pause_retains_finished_road_and_all_private_card_records(self):
        c=self.s.mutate('card.save',{'number':'120','temporary':True})['id'];p=self.s.mutate('publisher.save',{'name':'Fiktiv person'})['id']
        l=self.s.mutate('loan.issue',{'card_id':c,'publisher_id':p,'date':'2026-01-01','initial':True})['id']
        roads=[{'id_lokalId':'r1','vejnavn':'Eksempelvej'},{'id_lokalId':'r2','vejnavn':'Anden vej'}];self.request(roads,{'r1':[unit('a')],'r2':[unit('b',road='Anden vej')]})
        def progress(**kw):
            if kw.get('completed')==1 and kw.get('total')==2:self.d.cancel_event.set()
        with self.assertRaises(Paused):self.d.postcode({'postcode':'9999'},progress)
        self.assertEqual(self.s.get('geo','postcode:9999')['status'],'paused');self.assertEqual(self.s.geo_info()['addresses'],1);self.assertEqual(self.s.active_loan(c)['id'],l)
    def test_duplicate_pages_are_rejected_and_import_is_not_marked_complete(self):
        self.d.request=lambda *args,**kwargs:[{'id_lokalId':'same'}]
        with patch('postcode.PAGE_SIZE',1),self.assertRaises(ValueError):self.d.rest_pages('adresse',{},lambda n:None)
    def test_long_road_exceeds_old_search_cap_and_still_saves_card(self):
        roads=[{'id_lokalId':'r','vejnavn':'Eksempelvej'}];records={'r':[unit('u'+str(i),str(i+1)) for i in range(205)]}
        self.request(roads,records);request=self.d.request
        def combined(host,path,params=None,query=None):
            if host==HOST:return request(host,path,params,query)
            return {'status':'ok','fund':[{'type':'navngivenvejpostnummer','vejnavn':'Eksempelvej','postnr':'9999'}]}
        self.d.request=combined;result=self.d.road({'road':'Eksempelvej','postcode':'9999'},lambda **kw:None)
        self.assertEqual(result['count'],205)
        card=self.s.mutate('geo.assign',{'number':'004','address_ids':[a['id'] for a in self.s.geo_state()['addresses']]})['id']
        self.assertEqual(self.s.get('cards',card)['addresses'][0]['numbers'],'1–205');self.assertEqual(self.s.get('cards',card)['addresses'][0]['count'],205)
    def test_suggestions_use_official_names_and_reject_ambiguous_download(self):
        calls=[]
        def request(host,path,params=None,query=None):
            calls.append(params);return {'status':'ok','fund':[{'type':'navngivenvejpostnummer','vejnavn':'Eksempel Allé','postnr':'9999'},{'type':'navngivenvejpostnummer','vejnavn':'Eksempelvej','postnr':'9999'},{'type':'navngivenvejpostnummer','vejnavn':'Anden post','postnr':'8888'}]}
        self.d.request=request
        result=self.d.suggest('eksempel','9999');self.assertEqual(len(result['suggestions']),2);self.assertEqual(calls[0]['maal'],'navngivenvejpostnummer')
        self.d.suggest('eksempel','9999');self.assertEqual(len(calls),1)
        with self.assertRaises(ValueError):self.d.road({'road':'eksempel','postcode':'9999'},lambda **kw:None)
    def test_compact_label_fixes_36_lettered_house_numbers_without_inflating_count(self):
        values=[address('a'+str(i),str(2*i+2)+'B') for i in range(36)]
        self.s.mutate('geo.import',{'records':values,'label':'Fiktive husnumre','source':'Test'})
        c=self.s.mutate('geo.assign',{'number':'004','address_ids':[a['id'] for a in values]})['id'];row=self.s.get('cards',c)['addresses'][0]
        self.assertEqual(row['numbers'],'2B–72B (lige)');self.assertEqual(row['count'],36)
    def test_missing_inside_boundary_ignore_assignment_and_recovery(self):
        self.s.mutate('geo.import',{'records':[address('on'),address('missing','3'),address('outside','5',lng=10.5)],'label':'Test','source':'Test'})
        c=self.s.mutate('geo.assign',{'number':'120','address_ids':['on'],'polygon':POLYGON})['id']
        statuses=self.s.geo_state()['status'];self.assertEqual(statuses['on']['card_id'],c);self.assertEqual(statuses['missing']['within'][0]['card_id'],c);self.assertEqual(statuses['outside']['within'],[])
        ignored=self.s.mutate('ignore.save',{'address_id':'missing','reason':'Transformerstation'});item=self.s.all('ignored')[0]
        self.assertTrue(self.s.geo_state()['status']['missing']['ignored_id'])
        deletion=self.s.mutate('delete',{'module':'ignored','id':item['id']});self.s.mutate('geo.assign',{'card_id':c,'address_ids':['on','missing']})
        with self.assertRaises(ValueError):self.s.mutate('restore',deletion)
    def test_official_road_lines_convert_to_local_geometry(self):
        roads=[{'id_lokalId':'r','vejnavn':'Eksempelvej','vejnavnebeliggenhed_vejnavnelinje':'MULTILINESTRING((500000 6094791.42,500020 6094791.42),(500020 6094791.42,500030 6094800))'}]
        lines=rest_road_lines(roads);self.assertEqual(len(lines),2);self.assertAlmostEqual(lines[0]['points'][0][0],9,places=6)

if __name__=='__main__':unittest.main()
