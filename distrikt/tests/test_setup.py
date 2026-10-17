"""Synthetic first-use setup, partitioning and private IB-import tests."""
import copy,csv,io,json,math,random,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store,MODULES
from territory_partition import partition,split_polygon,split_polygon_line,area,overlaps,contained
from geography import point_in_polygon
from setup_store import ib_template

POLY=[[10,55],[10.04,55],[10.04,55.04],[10,55.04]]
C_POLY=[[10,55],[10.04,55],[10.04,55.01],[10.01,55.01],[10.01,55.03],[10.04,55.03],[10.04,55.04],[10,55.04]]

def records(n=80):return [{'id':'fake'+str(i),'entity':'address','road':'Fiktiv vej '+str(i//40+1),'number':str(i+1),'postcode':'9999','lng':10.002+(i%10)*.003,'lat':55.002+(i//10)*.003,'count':1} for i in range(n)]

class PartitionTests(unittest.TestCase):
    def test_concave_cut_preserves_three_components_and_area(self):
        for p in (C_POLY,list(reversed(C_POLY))):
            parts=split_polygon(p,0,10.02)
            self.assertEqual(len(parts),3)
            self.assertAlmostEqual(sum(abs(area(x)) for x in parts),abs(area(p)),places=10)
            for i,a in enumerate(parts):
                self.assertTrue(contained(a,p))
                self.assertFalse(any(overlaps(a,b) for b in parts[i+1:]))
    def test_oblique_cut_is_not_axis_aligned_and_preserves_concave_components(self):
        # An affine map inclines the actual cut; no invented addresses or road data.
        transform=lambda p:[round(p[0]+.3*(p[1]-55),7),round(p[1]+.2*(p[0]-10),7)]
        outer=[transform(p) for p in C_POLY]
        # Inverse x coordinate: x - .3*y = 10.02 - .3*55.
        for poly in (outer,list(reversed(outer))):
            parts=split_polygon_line(poly,(1,-.3),10.02-.3*55)
            self.assertEqual(len(parts),3)
            self.assertAlmostEqual(sum(abs(area(p)) for p in parts),abs(area(poly)),places=8)
            for i,p in enumerate(parts):
                self.assertTrue(contained(p,poly))
                self.assertFalse(any(overlaps(p,q) for q in parts[i+1:]))
            # Sample both sides and every arm, including points close to the cut.
            for x in (10.005,10.015,10.019,10.021,10.035):
                for y in (55.005,55.02,55.035):
                    point=transform([x,y])
                    self.assertEqual(sum(point_in_polygon(point,p) for p in parts),int(point_in_polygon(point,poly)))
    def test_oblique_line_scaling_direction_and_invalid_cuts(self):
        normal=(1,-.7);cut=10.019-.7*55.021
        first=split_polygon_line(POLY,normal,cut)
        scaled=split_polygon_line(POLY,(2,-1.4),2*cut)
        reverse=split_polygon_line(POLY,(-1,.7),-cut)
        canonical=lambda parts:sorted(sorted(map(tuple,p)) for p in parts)
        self.assertEqual(canonical(first),canonical(scaled));self.assertEqual(canonical(first),canonical(reverse))
        for normal,cut in (((0,0),0),((float('nan'),1),0),((1,1),float('inf')),((1,1),65),((1,1),80)):
            with self.assertRaises(ValueError):split_polygon_line(POLY,normal,cut)

    def test_generated_polygons_cover_parent_without_overlap_and_keep_all_visits(self):
        rng=random.Random(7)
        for poly in (POLY,C_POLY,[[10,55],[10.04,55.005],[10.03,55.04],[10,55.03]]):
            addresses=[]
            for i in range(150):
                while True:
                    p=[10+rng.random()*.04,55+rng.random()*.04]
                    if point_in_polygon(p,poly):break
                addresses.append({'id':str(i),'road':'Fiktiv vej','number':str(i),'postcode':'9999','lng':p[0],'lat':p[1],'count':1})
            parts=partition(poly,addresses,25)
            self.assertGreater(len(parts),2)
            ids=[a['id'] for p in parts for a in p['members']]
            self.assertEqual(len(ids),150);self.assertEqual(len(set(ids)),150)
            self.assertAlmostEqual(sum(abs(area(p['polygon'])) for p in parts),abs(area(poly)),places=8)
            for i,p in enumerate(parts):
                self.assertTrue(contained(p['polygon'],poly))
                self.assertTrue(all(point_in_polygon([a['lng'],a['lat']],p['polygon']) for a in p['members']))
                self.assertFalse(any(overlaps(p['polygon'],q['polygon']) for q in parts[i+1:]))
    def test_actual_oblique_road_is_preferred_and_not_extrapolated(self):
        road={'name':'Fiktivt skråt skel','points':[[9.99,54.999],[10.05,55.029]]}
        addresses=[{'id':str(i),'road':'Testvej','number':str(i),'postcode':'9999','lng':x,'lat':y,'count':1} for i,(x,y) in enumerate(((10.005,55.003),(10.015,55.006),(10.025,55.009),(10.005,55.022),(10.015,55.026),(10.025,55.032)))]
        parts=partition(POLY,addresses,3,roads=[road])
        self.assertEqual(len(parts),2)
        self.assertEqual(sorted(p['visits'] for p in parts),[3,3])
        self.assertTrue(all('Fiktivt skråt skel' in p['warning'] for p in parts))
        shared=set(map(tuple,parts[0]['polygon']))&set(map(tuple,parts[1]['polygon']))
        self.assertEqual(len(shared),2);a,b=sorted(shared)
        self.assertNotEqual(a[0],b[0]);self.assertNotEqual(a[1],b[1])
        self.assertEqual({a['id'] for p in parts for a in p['members']},{str(i) for i in range(6)})
        self.assertAlmostEqual(sum(abs(area(p['polygon'])) for p in parts),abs(area(POLY)),places=8)
        self.assertFalse(overlaps(parts[0]['polygon'],parts[1]['polygon']))
        self.assertTrue(all(contained(p['polygon'],POLY) for p in parts))
        reversed_road=dict(road,points=list(reversed(road['points'])))
        self.assertEqual(parts,partition(POLY,list(reversed(addresses)),3,roads=[reversed_road]))
        # A short middle fragment cannot be extended into an invented boundary.
        short=dict(road,points=[[10.015,55.0115],[10.025,55.0165]])
        fallback=partition(POLY,addresses,3,roads=[short])
        self.assertTrue(all('Geometrisk deling' in p['warning'] for p in fallback))
        self.assertFalse(any('Fiktivt skråt skel' in p['warning'] for p in fallback))
    def test_road_cut_never_splits_units_at_a_house(self):
        addresses=[dict(a,road='Husvej',number='1' if i<2 else str(i)) for i,a in enumerate(records(8))]
        addresses[0].update(lng=10.014,lat=55.015);addresses[1].update(lng=10.016,lat=55.015)
        road={'name':'Fiktivt skel','points':[[10.015,54.99],[10.015,55.05]]}
        parts=partition(POLY,addresses,4,roads=[road])
        owners=[p for p in parts if any(a['id']=='fake0' for a in p['members'])]
        self.assertEqual(len(owners),1);self.assertIn('fake1',[a['id'] for a in owners[0]['members']])

    def test_house_units_stay_together_even_above_target(self):
        a=[dict(r,id='unit'+str(i),road='Fiktiv bolig',number='1',floor=str(i),lng=10.02,lat=55.02) for i,r in enumerate(records(30))]
        p=partition(POLY,a,10);self.assertEqual(len(p),1);self.assertEqual(p[0]['visits'],30);self.assertTrue(p[0]['warning'])
    def test_containment_and_overlap_with_shared_edges(self):
        left=[[10,55],[10.02,55],[10.02,55.04],[10,55.04]];right=[[10.02,55],[10.04,55],[10.04,55.04],[10.02,55.04]]
        self.assertFalse(overlaps(left,right));self.assertTrue(overlaps(POLY,POLY));self.assertTrue(overlaps(POLY,left))
        self.assertFalse(contained(POLY,C_POLY))

class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        self.s.mutate('geo.main.save',{'points':POLY})
        self.s.mutate('geo.import',{'records':records(),'source':'Fiktiv test','label':'Fiktive adresser'})
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def preview(self,**kw):
        return self.s.mutate('setup.preview',dict({'target':20,'numbering':'hundreds','start':100,'block':100,'areas':[{'name':'Fiktiv by','kind':'By'}]},**kw))
    def apply(self,p,edits=None,**kw):return self.s.mutate('setup.apply',{'token':p['token'],'cards':edits or [{'key':c['key'],'name':c['name'],'number':c['number']} for c in p['cards']],'confirm':'OPRET KORT',**kw})
    def make_cards(self):p=self.preview();self.apply(p);return self.s.all('cards')
    def csv(self,rows):
        out=io.StringIO();w=csv.writer(out,delimiter=';');w.writerow(['kortnummer','vejnavn','husnummer','postnummer','etage','dør','dato']);w.writerows(rows);return out.getvalue()
    def ib_preview(self,rows):return self.s.mutate('setup.ib.preview',{'content':self.csv(rows),'date':'2026-10-15'})
    def ib_apply(self,p):return self.s.mutate('setup.ib.apply',{'token':p['token'],'confirm':'IMPORTÉR IB'})
    def test_preview_is_read_only_apply_names_counts_and_schema_preserved(self):
        before=self.s.state();files={p.name for p in Path(self.tmp.name).glob('*.sqlite3')};revision=self.s.revision
        p=self.preview();self.assertEqual(self.s.state()['cards'],before['cards']);self.assertEqual(self.s.revision,revision)
        self.assertEqual(p['visits'],80);self.assertEqual(len(p['cards']),4)
        self.assertTrue(all(c['name'].startswith('Fiktiv by – ') for c in p['cards']))
        self.apply(p)
        self.assertEqual({c['number'] for c in self.s.all('cards')},{'100','101','102','103'})
        self.assertEqual(sum(sum(a['count'] for a in c['addresses']) for c in self.s.all('cards')),80)
        self.assertTrue(all(not c['temporary'] and not c['in_folder'] for c in self.s.all('cards')))
        self.assertEqual(files,{p.name for p in Path(self.tmp.name).glob('*.sqlite3')});self.assertEqual(len(files),11)
    def test_two_areas_prefixes_and_100_series(self):
        left=[[10,55],[10.016,55],[10.016,55.04],[10,55.04]];right=[[10.016,55],[10.04,55],[10.04,55.04],[10.016,55.04]]
        areas=[{'name':'Fiktiv vest','prefix':'F','polygon':left,'kind':'By'},{'name':'Fiktiv øst','prefix':'B','polygon':right,'kind':'Land'}]
        p=self.preview(areas=areas,numbering='prefix',start=101);self.assertEqual({c['number'][0] for c in p['cards']},{'F','B'});self.apply(p)
        self.assertEqual({a.get('setup_prefix') for a in self.s.state()['areas']},{'F','B'})
    def test_100_series_reserve_space_for_next_area(self):
        left=[[10,55],[10.016,55],[10.016,55.04],[10,55.04]];right=[[10.016,55],[10.04,55],[10.04,55.04],[10.016,55.04]]
        p=self.preview(areas=[{'name':'Vest','polygon':left},{'name':'Øst','polygon':right}]);self.assertEqual({int(c['number'])//100 for c in p['cards']},{1,2})
    def test_continuous_edited_names_and_numbers(self):
        p=self.preview(numbering='continuous',start=450)
        edits=[{'key':c['key'],'number':'X'+str(i),'name':'Fiktivt navn '+str(i)} for i,c in enumerate(p['cards'])]
        self.apply(p,edits);self.assertTrue(all(c['number'].startswith('X') for c in self.s.all('cards')))
    def test_existing_and_deleted_cards_ignore_retired_and_outside_never_reassigned(self):
        c=self.s.mutate('geo.assign',{'number':'900','address_ids':['fake0']})['id'];self.s.mutate('delete',{'module':'cards','id':c})
        c2=self.s.mutate('geo.assign',{'number':'901','address_ids':['fake1']})['id']
        self.s.mutate('ignore.save',{'address_id':'fake2','reason':'Fiktivt teknisk anlæg'})
        with self.s.transaction():
            a=self.s.require('geo','fake3');a['retired']=True;self.s.put('geo',a)
            a=self.s.require('geo','fake4');a['lng']=11;self.s.put('geo',a)
        old=self.s.require('cards',c2);p=self.preview();ids={i for c in p['cards'] for i in c['address_ids']}
        self.assertFalse(ids&{'fake0','fake1','fake2','fake3','fake4'});self.apply(p);self.assertEqual(self.s.require('cards',c2),old)
    def test_overlapping_and_outside_area_boundaries_reject(self):
        for areas in ([{'name':'A','polygon':POLY},{'name':'B','polygon':POLY}],[{'name':'A','polygon':[[9.99,55],[10.02,55],[10,55.02]]}]):
            with self.assertRaises(ValueError):self.preview(areas=areas)
        self.assertEqual(self.s.all('cards'),[])
    def test_duplicate_existing_deleted_numbers_and_stale_plan_reject(self):
        p=self.preview();self.s.mutate('card.save',{'number':'100','temporary':True})
        with self.assertRaises(ValueError):self.apply(p)
        with self.assertRaisesRegex(ValueError,'100'):self.preview()
    def test_preview_uses_local_road_and_apply_keeps_all_addresses(self):
        self.s.mutate('geo.import',{'records':[{'id':'test-through-road','entity':'road','name':'Fiktiv gennemgående vej','points':[[9.99,55.0125],[10.05,55.0125]]}],'source':'Fiktiv test','label':'Lokal vej'})
        p=self.preview(target=40)
        self.assertEqual(len(p['cards']),2)
        self.assertTrue(all('Fiktiv gennemgående vej' in c['warning'] for c in p['cards']))
        shared=set(map(tuple,p['cards'][0]['polygon']))&set(map(tuple,p['cards'][1]['polygon']))
        self.assertEqual({y for x,y in shared},{55.0125})
        self.assertEqual(self.s.all('cards'),[])
        self.apply(p)
        self.assertEqual({a for c in self.s.all('cards') for a in c['address_ids']},{a['id'] for a in records()})

    def test_curved_preview_can_be_edited_and_applied_without_losing_addresses(self):
        curve=[[9.99,55.0125],[10.014,55.0125],[10.014,55.0135],[10.023,55.0135],[10.023,55.0125],[10.05,55.0125]]
        self.s.mutate('geo.import',{'records':[{'id':'test-curved-road','entity':'road','name':'Fiktiv Kurvevej','points':curve}],'source':'Fiktiv test','label':'Kurvet vej'})
        p=self.preview(target=40)
        self.assertEqual(len(p['cards']),2)
        self.assertTrue(all('Fiktiv Kurvevej' in c['warning'] for c in p['cards']))
        shared=set(map(tuple,p['cards'][0]['polygon']))&set(map(tuple,p['cards'][1]['polygon']))
        self.assertTrue(set(map(tuple,curve[1:-1])).issubset(shared))
        edits=[dict(key=c['key'],number=c['number'],name=c['name'],polygon=[[x,y+.0002 if [x,y]==curve[2] else y] for x,y in c['polygon']]) for c in p['cards']]
        adjusted=self.s.mutate('setup.adjust.preview',{'token':p['token'],'cards':edits})
        self.assertEqual(sum(c['visits'] for c in adjusted['cards']),80)
        self.assertEqual(self.s.all('cards'),[])
        self.apply(adjusted)
        ids=[a for c in self.s.all('cards') for a in c['address_ids']]
        self.assertEqual(len(ids),80);self.assertEqual(len(set(ids)),80)

    def test_local_road_change_invalidates_a_preview_without_writing_cards(self):
        p=self.preview()
        self.s.mutate('geo.import',{'records':[{'id':'fake-road','entity':'road','name':'Fiktiv vej','points':[[10,55.015],[10.04,55.02]]}],'source':'Fiktiv test','label':'Vejstykke'})
        with self.assertRaisesRegex(ValueError,'ændret'):self.apply(p)
        self.assertEqual(self.s.all('cards'),[])
        self.assertTrue(self.preview())

    def test_confirmation_and_atomic_rollback(self):
        p=self.preview()
        with self.assertRaises(ValueError):self.apply(p,confirm='yes')
        original=self.s._mutate;counter=[0]
        def fail(action,data):
            if action=='card.save':
                counter[0]+=1
                if counter[0]==2:raise ValueError('Fiktiv fejl')
            return original(action,data)
        with patch.object(self.s,'_mutate',side_effect=fail):
            with self.assertRaisesRegex(ValueError,'Fiktiv fejl'):self.apply(p)
        self.assertEqual(self.s.all('cards'),[]);self.assertEqual(self.s.state()['areas'],[])
        self.apply(p);self.assertEqual(len(self.s.all('cards')),4)
    def test_duplicate_edited_numbers_and_expired_preview(self):
        p=self.preview();edits=[{'key':c['key'],'number':'same','name':c['name']} for c in p['cards']]
        with self.assertRaises(ValueError):self.apply(p,edits)
        self.s._setup_previews[p['token']]['until']=0
        with self.assertRaisesRegex(ValueError,'udløbet'):self.apply(p)
    def test_areas_outside_scope_are_counted_uncovered(self):
        p=self.preview(areas=[{'name':'Halvt område','polygon':[[10,55],[10.016,55],[10.016,55.04],[10,55.04]]}])
        self.assertGreater(p['uncovered'],0);self.assertLess(p['visits'],80)
    def test_adjusted_shared_boundary_is_previewed_and_recounts_before_apply(self):
        p=self.preview(target=40);self.assertEqual(len(p['cards']),2)
        polygons=[c['polygon'] for c in p['cards']]
        shared=set(map(tuple,polygons[0]))&set(map(tuple,polygons[1]))
        coordinate=next(v for point in shared for v in [point[1]] if 55<v<55.04)
        edits=[{'key':c['key'],'number':c['number'],'name':c['name'],'polygon':[[x,y+.003 if y==coordinate else y] for x,y in c['polygon']]} for c in p['cards']]
        r=self.s.mutate('setup.adjust.preview',{'token':p['token'],'cards':edits})
        self.assertEqual(sorted(c['visits'] for c in r['cards']),[30,50]);self.assertEqual(self.s.all('cards'),[])
        self.apply(r);self.assertEqual(sum(sum(a['count'] for a in c['addresses']) for c in self.s.all('cards')),80)
    def test_adjusted_boundary_holes_or_overlap_reject_without_writes(self):
        p=self.preview(target=40);edits=[{'key':c['key'],'number':c['number'],'name':c['name'],'polygon':copy.deepcopy(c['polygon'])} for c in p['cards']]
        edits[0]['polygon']=[[x+.0001 if x==10 else x,y] for x,y in edits[0]['polygon']]
        with self.assertRaises(ValueError):self.s.mutate('setup.adjust.preview',{'token':p['token'],'cards':edits})
        self.assertEqual(self.s.all('cards'),[])
    def test_template_is_bom_csv_and_has_no_private_values(self):
        text=ib_template().decode('utf-8-sig');self.assertEqual(len(text.splitlines()),1);self.assertIn('dør',text);self.assertNotIn('Fiktiv',text)
    def test_ib_matching_duplicate_skip_date_and_back_revision_only(self):
        cards=self.make_cards();c=next(c for c in cards if 'fake0' in c['address_ids']);before=self.s.require('cards',c['id'])
        p=self.ib_preview([['', 'Fiktiv vej 1','1','9999','','',''],['', 'Fiktiv vej 1','1','9999','','','']]);self.assertEqual((p['new'],p['existing'],p['errors']),(1,1,0));self.assertEqual(self.s.all('ib'),[])
        r=self.ib_apply(p);self.assertEqual(r['count'],1);ib=self.s.all('ib')[0];self.assertEqual(ib['date'],'2026-10-15');self.assertEqual(ib['address_id'],'fake0')
        after=self.s.require('cards',c['id']);self.assertEqual(after['addresses'],before['addresses']);self.assertEqual(after['front_revision'],before['front_revision']);self.assertTrue(after['back_revision'])
        p=self.ib_preview([[c['number'],'Fiktiv vej 1','1','9999','','','2026-10-01']]);self.assertEqual(p['existing'],1);self.ib_apply(p);self.assertEqual(self.s.all('ib')[0]['date'],'2026-10-15')
    def test_ib_errors_block_entire_file_and_unknown_number_is_not_guessed(self):
        self.make_cards();p=self.ib_preview([['','Fiktiv vej 1','1','9999','','',''],['9000','Fiktiv vej 1','2','9999','','','']]);self.assertEqual(p['errors'],1)
        with self.assertRaises(ValueError):self.ib_apply(p)
        self.assertEqual(self.s.all('ib'),[])
    def test_ib_floor_door_required_and_ambiguous_units_reject(self):
        original=self.s.require('geo','fake0')
        with self.s.transaction():
            self.s.mark_deleted('geo','fake0','test','2026-10-15T00:00:00+00:00')
        for i in (1,2):self.s.mutate('geo.import',{'records':[dict(original,id='apt'+str(i),floor=str(i),door='th')],'source':'Fiktiv test','label':'Test'})
        self.make_cards();p=self.ib_preview([['','Fiktiv vej 1','1','9999','','','']]);self.assertEqual(p['errors'],1)
        p=self.ib_preview([['','Fiktiv vej 1','1','9999','1','th','2026-10-01']]);self.assertEqual(p['new'],1);self.ib_apply(p);self.assertEqual(self.s.all('ib')[0]['number'],'1, 1 th')
    def test_ib_plan_stale_after_address_or_ib_change(self):
        self.make_cards();p=self.ib_preview([['','Fiktiv vej 1','1','9999','','','']]);self.s.mutate('geo.type',{'id':'fake0','type':'Butik'})
        with self.assertRaisesRegex(ValueError,'ændret'):self.ib_apply(p)
        self.assertEqual(self.s.all('ib'),[])
    def test_ib_invalid_date_fields_and_file_size(self):
        self.make_cards()
        p=self.ib_preview([['','Fiktiv vej 1','1','9999','','','15.10.2026']]);self.assertEqual(p['errors'],1)
        for content in ('wrong;header\nx;y','æ'*1000001):
            with self.assertRaises(ValueError):self.s.mutate('setup.ib.preview',{'content':content})
    def test_backup_roundtrip_accepts_setup_metadata_and_imported_ib(self):
        from portable import snapshot,Restores
        self.make_cards();self.ib_apply(self.ib_preview([['','Fiktiv vej 1','1','9999','','','']]))
        payload=snapshot(self.s,'1.11.0');preview=Restores(self.s,'1.11.0').preview(payload)
        self.assertTrue(preview)

if __name__=='__main__':unittest.main()
