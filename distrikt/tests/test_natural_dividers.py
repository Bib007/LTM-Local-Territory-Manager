"""Fictional waterways/railways: bounded geometry, local data and explicit setup."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from geodata import Downloads
from store import Store
from territory_partition import partition, area, contained, overlaps
from territory_paths import divider_paths
from test_territory_paths import POLY, CURVE
import test_territory_paths as paths_fixture


def divider(kind='river', points=None, **extra):
    return dict(id='fiction-divider',entity='divider',divider_type=kind,name='Fiktivt skel',points=copy.deepcopy(points or CURVE),**extra)


class NaturalGeometryTests(unittest.TestCase):
    def addresses(self):
        return paths_fixture.PartitionIntegrationTests().addresses()
    def assert_partition(self, parts, addresses):
        self.assertEqual(sorted(a['id'] for p in parts for a in p['members']),sorted(a['id'] for a in addresses))
        self.assertEqual(sum(p['visits'] for p in parts),sum(a['count'] for a in addresses))
        self.assertAlmostEqual(sum(abs(area(p['polygon'])) for p in parts),abs(area(POLY)),places=8)
        self.assertTrue(all(contained(p['polygon'],POLY) for p in parts))
        self.assertFalse(any(overlaps(p['polygon'],q['polygon']) for i,p in enumerate(parts) for q in parts[i+1:]))
    def test_actual_waterway_and_rail_curves_are_preferred_to_competing_roads(self):
        addresses=self.addresses();road={'name':'Fiktiv vej','points':[[9.99,55.02],[10.05,55.02]]}
        for kind in ('river','stream','canal','rail'):
            with self.subTest(kind=kind):
                feature=divider(kind);before=copy.deepcopy(feature)
                parts=partition(POLY,addresses,3,roads=[road],dividers=[feature])
                self.assert_partition(parts,addresses)
                self.assertEqual(sorted(p['visits'] for p in parts),[3,3])
                self.assertTrue(all(('Jernbane' if kind=='rail' else 'Vandløb') in p['warning'] for p in parts))
                self.assertTrue(all('vejforløbet' not in p['warning'] for p in parts))
                shared=set(map(tuple,parts[0]['polygon']))&set(map(tuple,parts[1]['polygon']))
                self.assertTrue(set(map(tuple,CURVE[1:-1])).issubset(shared))
                self.assertEqual(feature,before)
    def test_named_exact_same_kind_fragments_join_deterministically(self):
        rows=[divider(points=CURVE[:3]),divider(points=CURVE[2:])]
        paths=divider_paths(rows,POLY)
        self.assertEqual(len(paths),1)
        self.assertEqual(paths,divider_paths([dict(r,points=list(reversed(r['points']))) for r in reversed(rows)],POLY))
        self.assertEqual(set(paths[0][0]),set(map(tuple,CURVE)))
    def test_names_kinds_gaps_and_unnamed_fragments_are_not_invented(self):
        for mode in ('name','kind','gap','unnamed'):
            rows=[divider(points=CURVE[:3]),divider(points=CURVE[2:])]
            if mode=='name':rows[1]['name']='Fiktivt andet skel'
            if mode=='kind':rows[1]['divider_type']='rail'
            if mode=='gap':rows[1]['points'][0]=[10.0100001,55.025]
            if mode=='unnamed':
                for row in rows:row['name']=''
            with self.subTest(mode=mode):
                parts=partition(POLY,self.addresses(),3,dividers=rows)
                self.assertTrue(all('Geometrisk deling' in p['warning'] for p in parts))
                self.assert_partition(parts,self.addresses())
    def test_bridge_tunnel_other_layers_retired_and_unknown_types_are_not_surface_boundaries(self):
        for extra in ({'bridge':'yes'},{'tunnel':'culvert'},{'layer':'-1'},{'layer':'1'},{'layer':'unclear'},{'retired':True}):
            with self.subTest(extra=extra):self.assertEqual(divider_paths([divider(**extra)],POLY),[])
        self.assertEqual(divider_paths([dict(divider(),divider_type='ditch')],POLY),[])
        self.assertTrue(divider_paths([divider(layer='0',bridge='no',tunnel='no')],POLY))
    def test_closed_large_and_short_features_do_not_become_through_boundaries(self):
        for points in (CURVE[1:-1],CURVE+[CURVE[0]],[[9.99+i*.00001,55.02] for i in range(600)]):
            with self.subTest(length=len(points)):
                parts=partition(POLY,self.addresses(),3,dividers=[divider(points=points)])
                self.assertTrue(all('Geometrisk deling' in p['warning'] for p in parts))
                self.assert_partition(parts,self.addresses())
    def test_apartments_straddling_a_waterway_stay_in_one_house(self):
        addresses=self.addresses();addresses[0].update(number='42',lng=10.019,lat=55.024);addresses[3].update(number='42',lng=10.021,lat=55.026)
        parts=partition(POLY,addresses,3,dividers=[divider()])
        owners=[p for p in parts if any(a['id']=='fake0' for a in p['members'])]
        self.assertEqual(len(owners),1);self.assertIn('fake3',[a['id'] for a in owners[0]['members']])
        self.assertFalse(any('Vandløb' in p['warning'] for p in parts));self.assert_partition(parts,addresses)


class NaturalStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        self.s.mutate('geo.main.save',{'points':POLY})
        addresses=[dict(a,entity='address') for a in paths_fixture.PartitionIntegrationTests().addresses()]
        self.add(addresses+[divider()])
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def add(self,rows):return self.s.mutate('geo.import',{'records':rows,'source':'Fiktiv test','label':'Fiktive skel'})
    def preview(self):return self.s.mutate('setup.preview',{'target':3,'numbering':'hundreds','start':100,'block':100,'areas':[{'name':'Fiktiv by','kind':'By'}]})
    def apply(self,p,confirm='OPRET KORT'):return self.s.mutate('setup.apply',{'token':p['token'],'cards':[dict(key=c['key'],number=c['number'],name=c['name']) for c in p['cards']],'confirm':confirm})
    def test_real_preview_can_be_adjusted_and_requires_confirmation_before_apply(self):
        p=self.preview();self.assertEqual(len(p['cards']),2);self.assertEqual(self.s.all('cards'),[])
        self.assertTrue(all('Vandløb' in c['warning'] for c in p['cards']))
        edits=[dict(key=c['key'],number=c['number'],name=c['name'],polygon=[[x,y+.0001 if [x,y]==CURVE[2] else y] for x,y in c['polygon']]) for c in p['cards']]
        adjusted=self.s.mutate('setup.adjust.preview',{'token':p['token'],'cards':edits})
        self.assertTrue(all(c['warning_ui']==[] for c in adjusted['cards']),'Manual changes must not retain a claim about following the source waterway')
        with self.assertRaises(ValueError):self.apply(adjusted,'yes')
        self.assertEqual(self.s.all('cards'),[]);self.apply(adjusted)
        ids=[a for c in self.s.all('cards') for a in c['address_ids']]
        self.assertEqual(len(ids),6);self.assertEqual(len(set(ids)),6)
    def test_changed_divider_invalidates_old_proposal_and_refreshes_cached_context(self):
        p=self.preview();old=self.s.geo_state();self.assertEqual(old['info']['dividers'],1)
        self.add([divider(points=[[9.99,55.02],[10.05,55.02]])])
        self.assertNotEqual(old['dividers'],self.s.geo_state()['dividers'])
        with self.assertRaisesRegex(ValueError,'ændret'):self.apply(p)
        self.assertEqual(self.s.all('cards'),[])
    def test_metadata_survives_reopening_existing_database(self):
        self.add([divider('rail',layer='1',bridge='yes',tunnel='no')]);before=copy.deepcopy(self.s.geo_state()['dividers'])
        self.s.close();self.s=Store(self.tmp.name)
        self.assertEqual(self.s.geo_state()['dividers'],before)
        self.assertEqual(self.s.geo_info()['dividers'],1)
        self.assertEqual(divider_paths(before,POLY),[])
    def test_invalid_feature_type_rolls_back_whole_import(self):
        before=copy.deepcopy(self.s.geo_state());revision=self.s.revision
        with self.assertRaises(ValueError):self.add([dict(divider(),id='new-feature'),dict(divider(),id='invalid-feature',divider_type='pipeline')])
        self.assertEqual(self.s.geo_state(),before);self.assertEqual(self.s.revision,revision)


class NaturalDownloadTests(unittest.TestCase):
    def test_one_existing_area_request_imports_only_supported_features_and_never_addresses_for_waterways(self):
        with tempfile.TemporaryDirectory() as folder:
            s=Store(folder)
            try:
                d=Downloads(s)
                tags=[{'waterway':'river','name':'Fiktiv Å'},{'waterway':'stream'},{'waterway':'canal','tunnel':'culvert','layer':'-1'},
                      {'railway':'rail','name':'Fiktiv bane','bridge':'yes','layer':'1'},{'waterway':'ditch'},{'railway':'tram'},
                      {'highway':'residential','name':'Fiktiv vej'},{'building':'yes'}]
                payload={'elements':[{'id':i,'type':'way','tags':t,'geometry':[{'lon':x,'lat':y} for x,y in (POLY if 'building' in t else CURVE)]} for i,t in enumerate(tags)]}
                d.request=Mock(return_value=payload);d.road=Mock(return_value={'count':0})
                d.area({'bbox':[10,55,10.04,55.04],'postcode':'9999'},True,lambda **kw:None)
                self.assertEqual(d.request.call_count,1);self.assertEqual(d.request.call_args.args[0],'overpass-api.de')
                query=d.request.call_args.kwargs['query'];self.assertIn('"waterway"~"^(river|stream|canal)$"',query);self.assertIn('"railway"="rail"',query)
                self.assertEqual(s.geo_info()['dividers'],4);self.assertEqual(s.geo_info()['roads'],1);self.assertEqual(s.geo_info()['buildings'],1)
                self.assertEqual(d.road.call_count,1);self.assertEqual(d.road.call_args.args[0]['road'],'Fiktiv vej')
                self.assertTrue(any(x.get('tunnel')=='culvert' and x.get('layer')=='-1' for x in s.geo_state()['dividers']))
            finally:s.close()
    def test_partial_provider_response_does_not_store_divider_fragments(self):
        with tempfile.TemporaryDirectory() as folder:
            s=Store(folder)
            try:
                d=Downloads(s);d.request=Mock(return_value={'remark':'Fictional incomplete response','elements':[]})
                with self.assertRaises(ValueError):d.area({'bbox':[10,55,10.04,55.04]},False,lambda **kw:None)
                self.assertEqual(s.geo_info()['dividers'],0)
            finally:s.close()


if __name__=='__main__':unittest.main()
