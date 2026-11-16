"""Fictional street-line/DAR suggestions with normal atomic card saving."""
import sys
import tempfile
import unittest
from copy import deepcopy
from math import cos, radians
from random import Random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from street_suggestions import ranges, includes
from geography import point_in_polygon, valid_polygon
from territory_outline import meets, simple_ring, suggest_outline
from geography import enclosing_outline


class StreetSuggestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        self.card=self.s.mutate('card.save',{'number':'F001','addresses':[{'road':'Fictional road','numbers':'1–5 (ulige)','count':4,'type':'Hus'}]})['id']
        self.records=[dict(id='a'+str(i),entity='address',road='Fictional road',number=n,floor=f,door='',postcode='9999',lng=10+i*.001,lat=55,count=1,type='Hus') for i,(n,f) in enumerate([('1',''),('3',''),('3','1'),('5',''),('2',''),('7','')])]
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def fetch(self,complete=True):
        self.s.mutate('geo.import',dict(records=self.records,source='DAR / Datafordeleren',label='Fictional complete road',**({'complete_road':{'road':'Fictional road','postcode':'9999'}} if complete else {})))
    def preview(self,**extra):return self.s.mutate('geo.preview',dict(mode='street_lines',card_id=self.card,postcodes=['9999'],**extra))
    def save(self,preview,**extra):return self.s.mutate('geo.assign',dict(card_id=self.card,address_ids=[a['id'] for a in preview['addresses']],street_expected=preview['street_expected'],source_expected=preview['source_expected'],postcodes=['9999'],**extra))
    def test_plan_and_preview_are_read_only_and_select_every_apartment(self):
        before=deepcopy(self.s.state());plan=self.preview(planning_only=True)
        self.assertEqual(plan['roads'],[{'road':'Fictional road','postcode':'9999'}]);self.assertEqual(self.s.state(),before)
        self.fetch();before=deepcopy(self.s.state());preview=self.preview(source_expected=plan['source_expected'])
        self.assertEqual([a['id'] for a in preview['addresses']],['a0','a1','a2','a3']);self.assertEqual(preview['visits'],4)
        self.assertGreaterEqual(len(preview['outline']),3);self.assertEqual(self.s.state(),before)
    def test_save_preserves_history_and_imprecise_ib_date(self):
        self.fetch();loan=self.s.mutate('loan.issue',{'card_id':self.card,'publisher_name':'Fictional person','date':'2025-01-01','initial':True})['id']
        ib=self.s.mutate('ib.save',{'card_id':self.card,'road':'Fictional road','number':'1','date_text':'marts 2024'})['id']
        before=deepcopy(self.s.all('loans'));self.save(self.preview())
        c=self.s.require('cards',self.card);self.assertEqual(c['address_ids'],['a0','a1','a2','a3']);self.assertTrue(c['front_revision'])
        self.assertEqual(self.s.all('loans'),before);self.assertEqual(self.s.active_loan(self.card)['id'],loan)
        self.assertEqual(self.s.require('ib',ib)['date_text'],'marts 2024');self.assertEqual(self.s.require('ib',ib)['date'],'')
    def test_postcodes_and_precise_ranges_are_required(self):
        for posts in ([],[''],['999'],['9999','9999']):
            with self.assertRaises(ValueError):self.s.mutate('geo.preview',{'mode':'street_lines','card_id':self.card,'postcodes':posts,'planning_only':True})
        for value in ('1–5 og resten','5-1','1-5 (unknown)',''):
            with self.assertRaises(ValueError):ranges(value)
        self.assertEqual(ranges('1A-3B (odd); 8'),[('1A','3B','odd'),('8','8','all')])
    def test_whole_street_and_only_odd_note_keep_every_apartment(self):
        self.fetch();c=self.s.require('cards',self.card)
        for wording,expected in [('hele vejen',list('012345')),('hele vejen (kun ulige)',['0','1','2','3','5']),('1-5 (kun lige numre)',['4'])]:
            self.s.mutate('card.save',{**c,'addresses':[{**c['addresses'][0],'numbers':wording}]})
            preview=self.preview();self.assertEqual([a['id'] for a in preview['addresses']],['a'+i for i in expected])
    def test_ampersand_street_sides_do_not_fill_excluded_even_numbers(self):
        parts=ranges('23-29 & 24-26')
        self.assertEqual([n for n in range(23,31) if any(includes(str(n),part) for part in parts)],[23,24,25,26,27,29])
        self.assertEqual([n for n in range(23,28) if any(includes(str(n),part) for part in ranges('23-25 & 24-26'))],[23,24,25,26])
        self.assertEqual(ranges('2-8 (kun lige) og 1-9 (kun ulige)'),[('2','8','even'),('1','9','odd')])
    def test_partial_data_and_empty_matching_range_are_rejected(self):
        self.fetch(False)
        with self.assertRaisesRegex(ValueError,'Hent hver'):self.preview()
        self.fetch();c=self.s.require('cards',self.card);self.s.mutate('card.save',{**c,'addresses':[{**c['addresses'][0],'numbers':'90-99'}]})
        with self.assertRaisesRegex(ValueError,'ingen aktive'):self.preview()
    def test_failed_interval_identifies_street_postcode_and_number_range(self):
        self.fetch();c=self.s.require('cards',self.card)
        self.s.mutate('card.save',{**c,'addresses':[{**c['addresses'][0],'numbers':'90-99'}]})
        with self.assertRaisesRegex(ValueError,'Fictional road.*9999.*90-99.*ingen aktive'):
            self.preview()
        self.s.mutate('card.save',{**c,'addresses':[{**c['addresses'][0],'numbers':'bad interval'}]})
        with self.assertRaisesRegex(ValueError,'Fictional road.*9999.*bad interval.*nummerinterval'):
            self.preview(planning_only=True)

    def test_changed_street_lines_and_changed_geo_invalidate_approval(self):
        self.fetch();p=self.preview();c=self.s.require('cards',self.card)
        self.s.mutate('card.save',{**c,'addresses':[{**c['addresses'][0],'numbers':'1-3'}]})
        before=deepcopy(self.s.state())
        with self.assertRaisesRegex(ValueError,'vejlinjer er ændret'):self.save(p)
        self.assertEqual(self.s.state(),before)
        p=self.preview();a=self.s.require('geo','a0')
        with self.s.lock,self.s.transaction():self.s.put('geo',{**a,'lat':55.001})
        before=deepcopy(self.s.state())
        with self.assertRaisesRegex(ValueError,'Adressegrundlaget'):self.save(p)
        self.assertEqual(self.s.state(),before)
    def test_existing_ownership_is_visible_and_blocks_assignment(self):
        self.fetch();self.s.mutate('geo.assign',{'number':'F002','address_ids':['a0']});p=self.preview()
        self.assertEqual(p['conflicts'][0]['card_number'],'F002');before=deepcopy(self.s.state())
        with self.assertRaises(ValueError):self.save(p)
        self.assertEqual(self.s.state(),before)
    def test_saving_a_dar_suggestion_rechecks_a_new_neighbor(self):
        self.fetch()
        preview=self.preview()
        original=preview['outline']
        self.assertEqual(preview['outline_status'],'clear')
        neighbor=self.s.mutate('card.save',{'number':'F099','temporary':True})['id']
        x,y=self.records[0]['lng'],self.records[0]['lat']
        self.s.mutate('geo.boundary',{'card_id':neighbor,
            'polygon':[[x-.0003,y+.00004],[x+.0003,y+.00004],[x+.0003,y+.001],[x-.0003,y+.001]]})
        before=deepcopy(self.s.state())
        with self.assertRaisesRegex(ValueError,'Grænseforslaget er ændret'):
            self.save(preview,polygon=original,outline_expected=preview['outline_expected'])
        self.assertEqual(self.s.state(),before)
        fresh=self.preview()
        self.assertEqual(fresh['outline_status'],'clear')
        self.save(fresh,polygon=fresh['outline'],outline_expected=fresh['outline_expected'])
        self.assertEqual(self.s.require('cards',self.card)['geo_outline_source'],'suggestion')

    def test_manual_year_only_date_never_invents_month_or_day(self):
        for value in ('2024','marts 2024'):
            ident=self.s.mutate('ib.save',{'card_id':self.card,'road':'Fictional road','number':value,'date':'2026-01-01','date_text':value})['id']
            item=self.s.require('ib',ident);self.assertEqual((item['date'],item['date_text']),('',value))


class OutlineTests(unittest.TestCase):
    scale=111320*cos(radians(55))

    def point(self,x,y):
        return [round(10+x/self.scale,7),round(55+y/111320,7)]

    def rectangle(self,x0,y0,x1,y1):
        return [self.point(x0,y0),self.point(x1,y0),self.point(x1,y1),self.point(x0,y1)]

    def address(self,number,x,y,**extra):
        lng,lat=self.point(x,y)
        return dict(number=str(number),road='Fictional road',postcode='9999',lng=lng,lat=lat,**extra)

    def setUp(self):
        self.selected=[self.address(1,-40,0),self.address(3,40,0)]

    def trace(self,others=(),neighbors=(),expected='clear'):
        outline,status=suggest_outline(self.selected,[*self.selected,*others],neighbors)
        self.assertEqual(status,expected)
        if expected=='unavailable':
            self.assertEqual(outline,[])
        else:
            self.assertEqual(valid_polygon(outline,limit=5000),outline)
            self.assertTrue(simple_ring([tuple(p) for p in outline]))
            self.assertTrue(all(point_in_polygon((a['lng'],a['lat']),outline) for a in self.selected))
        return outline

    def test_wraps_a_house_between_selected_addresses(self):
        other=self.address(2,0,0)
        outline=self.trace(others=[other])
        self.assertFalse(point_in_polygon(self.point(0,0),outline))
        self.assertLessEqual(len(outline),28)
        self.assertTrue(any(a[0]!=b[0] and a[1]!=b[1] for a,b in zip(outline,outline[1:]+outline[:1])))
        outline=self.trace()
        self.assertTrue(meets(outline,self.rectangle(-7,-9,7,9),0),
                        'A footprint without another address must not pinch the territory')

    def test_open_rural_space_is_a_generous_simple_polygon(self):
        # Fictional sparse group, like a hand-drawn rural boundary.
        self.selected=[self.address(1,-110,0),self.address(3,-30,50),
                       self.address(5,60,15),self.address(7,115,-30)]
        harmless=[self.rectangle(-80,-12,-65,12),
                  self.rectangle(2,0,15,10),
                  self.rectangle(70,20,85,32)]
        outline=self.trace()
        width=(max(p[1] for p in outline)-min(p[1] for p in outline))*111320
        self.assertGreater(width,95,'Classic 12-metre hull must still be broader than the old corridor')
        self.assertLessEqual(len(outline),16,'The proposed boundary should have long simple edges')
        self.assertTrue(any(meets(outline,shape,0) for shape in harmless),
                        'Empty buildings are not arbitrary hard obstacles')

    def test_dense_street_is_safe_but_not_just_five_metres_wide(self):
        self.selected=[self.address(n,x,0) for n,x in ((1,-45),(3,-15),(5,15),(7,45))]
        # Houses on the other side of the street protect that side only.
        outsiders=[self.address(n,x,28) for n,x in ((2,-45),(4,-15),(6,15),(8,45))]
        outline=self.trace(others=outsiders)
        low=min(p[1] for p in outline)
        self.assertLess(low,self.point(0,-10)[1])
        self.assertFalse(any(point_in_polygon((a['lng'],a['lat']),outline) for a in outsiders))
        self.assertLessEqual(len(outline),24)

    def test_original_hull_is_unchanged_when_there_are_no_conflicts(self):
        expected=enclosing_outline([self.point(-40,0),self.point(40,0)])
        actual=self.trace()
        self.assertEqual(len(actual),len(expected))
        for found,original in zip(actual,expected):
            self.assertAlmostEqual(found[0],original[0],places=10)
            self.assertAlmostEqual(found[1],original[1],places=10)

    def test_other_dar_dot_inside_old_hull_creates_notch_not_a_thin_route(self):
        # Four selected corners enclose one separate DAR house. A five-metre
        # connection around the corners is not an acceptable automatic result.
        self.selected=[self.address(n,x,y) for n,x,y in (
            (1,-60,-35),(3,60,-35),(5,60,35),(7,-60,35))]
        other=self.address(9,0,0)
        outline=self.trace(others=[other])
        self.assertFalse(point_in_polygon((other['lng'],other['lat']),outline))
        self.assertTrue(point_in_polygon(self.point(-45,0),outline))
        self.assertTrue(point_in_polygon(self.point(45,0),outline))
        # A broad old-style territory must keep most of the original area.
        projected=[((x-10)*self.scale,(y-55)*111320) for x,y in outline]
        area=abs(sum(a[0]*b[1]-b[0]*a[1]
                     for a,b in zip(projected,projected[1:]+projected[:1]))/2)
        self.assertGreater(area,6500)
        self.assertLessEqual(len(outline),40)

    def test_loaded_outside_dar_dots_and_neighbour_boundaries_both_excluded(self):
        self.selected=[self.address(n,x,y) for n,x,y in (
            (1,-50,-30),(3,50,-30),(5,50,30),(7,-50,30))]
        outsiders=[self.address(8,0,0),self.address(10,0,-51)]
        neighbor=self.rectangle(-70,40,70,65)
        outline=self.trace(others=outsiders,neighbors=[neighbor])
        self.assertFalse(any(point_in_polygon((p['lng'],p['lat']),outline) for p in outsiders))
        self.assertFalse(meets(outline,neighbor,0))
        self.assertTrue(point_in_polygon(self.point(30,-10),outline))

    def test_parallel_territory_keeps_three_metre_gap(self):
        neighbor=self.rectangle(-60,8,60,50)
        outline=self.trace(neighbors=[neighbor])
        self.assertLessEqual(max(p[1] for p in outline),self.point(0,5)[1])
        self.assertFalse(meets(outline,neighbor,0))

    def test_envelope_stays_clear_of_the_neighbor(self):
        selected=[self.address(1,-40,7),self.address(3,40,7)]
        addresses=[*selected,self.address(2,0,10)]
        neighbor=self.rectangle(-55,25,55,45)
        outline,status=suggest_outline(selected,addresses,[neighbor])
        self.assertEqual(status,'clear')
        self.assertFalse(point_in_polygon(self.point(0,10),outline),
                         'The unselected DAR entrance must remain outside')
        self.assertFalse(point_in_polygon(self.point(0,10),outline))
        self.assertLessEqual(max(p[1] for p in outline),self.point(0,22)[1])
        for address in selected:
            self.assertTrue(point_in_polygon((address['lng'],address['lat']),outline))

    def test_short_detour_keeps_neighbor_outside(self):
        for length in (21,100):
            with self.subTest(length=length):
                neighbor=self.rectangle(-10,-length,10,length)
                outline=self.trace(neighbors=[neighbor])
                self.assertFalse(meets(outline,neighbor,0))

    def test_bounded_search_cannot_prove_crossing_is_necessary(self):
        self.trace(neighbors=[self.rectangle(-10,-500,10,500)],expected='unavailable')

    def test_selected_entrance_inside_neighbor_requires_a_warning(self):
        neighbor=self.rectangle(-50,-15,-30,15)
        outline=self.trace(neighbors=[neighbor],expected='crossing')
        self.assertTrue(meets(outline,neighbor,0))

    def test_distinct_addresses_at_same_point_make_a_proposal_impossible(self):
        self.trace(others=[self.address(2,-40,0)],expected='unavailable')

    def test_other_entrance_of_same_house_remains_outside(self):
        other=self.address(1,-34,0)
        outline=self.trace(others=[other])
        self.assertFalse(point_in_polygon((other['lng'],other['lat']),outline))

    def test_dense_unselected_fringe_is_cut_off_as_a_group(self):
        # Fictional streets based on the drawn correction. Selected entrances
        # on both sides of the frame keep the original hull over the fringe.
        selected = [
            (35, 345), (135, 337), (118, 415), (95, 505), (70, 570), (55, 645),
            (88, 723), (196, 732), (553, 516), (668, 444), (634, 602), (742, 602),
            (980, 508), (1525, 550), (1680, 445),
        ]
        unselected = [
            (100, 100), (220, 215), (222, 290), (192, 350), (194, 426), (188, 494),
            (154, 568), (130, 638), (290, 302), (294, 414), (278, 514), (244, 598),
            (380, 530), (432, 494), (420, 412), (482, 434), (498, 358), (506, 264),
            (555, 268), (607, 366), (658, 332), (794, 224), (790, 310), (780, 392),
            (782, 474), (876, 256), (890, 352), (866, 454), (1022, 198), (1026, 308),
            (1052, 384), (1080, 446), (1090, 208), (1143, 358), (1140, 442), (1164, 268),
            (1164, 210), (1336, 240), (1372, 246), (1402, 240), (1316, 352), (1306, 396),
            (1298, 430), (1370, 410), (1404, 404), (1444, 398), (1476, 390), (1506, 390),
            (1538, 384), (1436, 292), (1444, 326), (1456, 208), (1458, 244), (1530, 236),
            (1524, 266), (1520, 302), (1592, 336), (1608, 298), (1620, 228), (1624, 184),
        ]
        def places(points, offset):
            return [self.address(i+offset, x*.3, -y*.3) for i,(x,y) in enumerate(points)]

        self.selected = places(selected, 0)
        others = places(unselected, 100)
        outline = self.trace(others=others)
        self.assertFalse(any(point_in_polygon((a['lng'],a['lat']), outline) for a in others))
        # Several empty gaps between the blue dots belonged to the old fringe.
        for x,y in ((1250,440), (960,470)):
            self.assertFalse(point_in_polygon(self.point(x*.3,-y*.3),outline))
        self.assertTrue(point_in_polygon(self.point(850*.3,-580*.3),outline))
        self.assertLess(len(outline), 35)

        # Extend the fictional streets below the visible portion. These
        # variants made beta.24 trace a separate indentation at many dots.
        for seed in (1, 2, 8):
            with self.subTest(seed=seed):
                rng = Random(seed)
                continued_street = [(x,rng.randint(595,745)) for x in range(140,1680,65)]
                shifted = [(x+rng.randint(-15,15),y+rng.randint(-16,16)) for x,y in unselected]
                self.selected = places(selected+continued_street,0)
                others = places(shifted,100)
                outline = self.trace(others=others)
                for address in others:
                    self.assertFalse(point_in_polygon((address['lng'],address['lat']),outline))
                self.assertFalse(point_in_polygon(self.point(375,-132),outline))
                if seed == 2:
                    self.assertFalse(point_in_polygon(self.point(288,-141),outline))
                self.assertTrue(point_in_polygon(self.point(255,-174),outline))
                self.assertLess(len(outline),35)

    def test_multicluster_regression_keeps_a_filled_area(self):
        selected, others = multicluster_addresses()
        self.selected = selected
        outline = self.trace(others=others)
        self.assertFalse(any(point_in_polygon((a['lng'], a['lat']), outline) for a in others))
        projected = [((x-10)*self.scale, (y-55)*111320) for x,y in outline]
        area = abs(sum(x*v-u*y for (x,y),(u,v) in zip(projected,projected[1:]+projected[:1]))/2)
        # Beta .22 returns its skinny fallback (~22,000 m²) for this arrangement.
        self.assertGreater(area, 50_000)
        self.assertLess(len(outline), 130)
        self.selected.reverse()
        self.assertEqual(self.trace(others=list(reversed(others))), outline)


def multicluster_addresses():
    """Fictional house groups patterned on the screenshot, with a synthetic origin and scale."""
    selected_pixels = [
        (30, 510), (45, 494), (66, 499), (88, 500), (298, 472), (358, 450),
        (406, 347), (420, 335), (425, 310), (426, 291), (415, 260), (433, 243),
        (435, 220), (436, 201), (430, 161), (448, 110), (483, 104), (530, 102),
        (576, 108), (565, 151), (555, 193), (504, 160), (501, 194), (492, 224),
        (480, 258), (548, 234), (494, 298), (564, 334), (583, 346), (634, 312),
        (466, 440), (813, 204), (853, 248), (870, 168), (906, 247), (1026, 199),
    ]
    other_pixels = [
        (168, 454), (220, 521), (277, 445), (299, 396), (346, 389), (354, 352),
        (394, 474), (382, 515), (438, 519), (498, 387), (511, 402), (543, 365),
        (506, 472), (556, 450), (562, 489), (613, 462), (647, 517), (542, 277),
        (600, 266), (612, 230), (629, 194), (631, 158), (632, 120), (645, 92),
        (657, 246), (675, 203), (707, 151), (725, 209), (751, 192), (766, 164),
        (783, 124), (840, 130), (866, 110), (928, 180), (933, 143), (374, 200),
        (370, 171), (372, 145), (376, 120), (378, 95), (394, 63), (410, 31),
        (456, 30), (486, 46), (520, 40), (554, 44), (588, 43), (646, 54),
        (686, 57), (680, 95), (736, 468), (862, 428), (1033, 342), (316, 332),
        (288, 285), (332, 205), (298, 205), (330, 149), (302, 147), (341, 92),
    ]

    rng = Random(3)

    def addresses(points, offset):
        return [dict(number=str(n+offset), road='Fictional road', postcode='9999',
                     lng=round(round(10+x*.55/64000,7)+rng.uniform(-.00012,.00012),7),
                     lat=round(round(55-y*.55/111320,7)+rng.uniform(-.00006,.00006),7))
                for n,(x,y) in enumerate(points)]

    return addresses(selected_pixels, 0), addresses(other_pixels, 100)


if __name__=='__main__':unittest.main()
