"""Fictional road geometry; no network, private files or real locations."""
import copy
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from geography import point_in_polygon
from territory_partition import area, contained, overlaps, partition
from territory_paths import split_polygon_path, road_paths, MAX_POINTS, MAX_PATHS

POLY = [[10,55],[10.04,55],[10.04,55.04],[10,55.04]]
CONCAVE = [[10,55],[10.04,55],[10.04,55.01],[10.01,55.01],[10.01,55.03],[10.04,55.03],[10.04,55.04],[10,55.04]]
CURVE = [[9.99,55.01],[10.01,55.01],[10.01,55.025],[10.03,55.025],[10.03,55.02],[10.05,55.02]]

def canonical(parts):
    return sorted(sorted(map(tuple, p)) for p in parts)

class PathGeometryTests(unittest.TestCase):
    def assert_partition(self, poly, parts):
        self.assertEqual(len(parts),2)
        self.assertAlmostEqual(sum(abs(area(p)) for p in parts),abs(area(poly)),places=8)
        self.assertTrue(all(contained(p,poly) for p in parts))
        self.assertFalse(overlaps(*parts))
        rng = random.Random(33)
        for _ in range(400):
            p=[10+rng.random()*.04,55+rng.random()*.04]
            self.assertEqual(sum(point_in_polygon(p,part) for part in parts),int(point_in_polygon(p,poly)))
    def test_curve_preserves_every_actual_inside_bend_and_both_sides(self):
        original=copy.deepcopy(CURVE)
        parts=split_polygon_path(POLY,CURVE)
        self.assert_partition(POLY,parts)
        shared=set(map(tuple,parts[0]))&set(map(tuple,parts[1]))
        self.assertTrue(set(map(tuple,CURVE[1:-1])).issubset(shared))
        self.assertEqual({p for p in shared if p[0] in (10,10.04)},{(10,55.01),(10.04,55.02)})
        self.assertEqual(CURVE,original)
        for poly in (POLY,list(reversed(POLY))):
            self.assertEqual(canonical(parts),canonical(split_polygon_path(poly,list(reversed(CURVE)))))
    def test_curved_path_can_split_a_concave_parent(self):
        path=[[10.005,54.99],[10.007,55.005],[10.004,55.02],[10.006,55.035],[10.005,55.05]]
        self.assert_partition(CONCAVE,split_polygon_path(CONCAVE,path))
    def test_exact_boundary_endpoints_are_accepted_without_extrapolation(self):
        path=[[10,55.012],[10.02,55.018],[10.04,55.022]]
        self.assert_partition(POLY,split_polygon_path(POLY,path))
    def test_dead_ends_gaps_touches_loops_and_self_crossings_are_rejected(self):
        paths=[CURVE[1:-1],CURVE[:-1],[[9.99,54.99],[10,55],[10.05,55.02]],
               [[9.99,55.01],[10.02,55.03],[10.01,55.03],[10.02,55.01],[10.05,55.03]],
               [[9.99,55.01],[10.02,55.01],[10.01,55.01],[10.05,55.03]],
               [[9.99,55.01],[10.02,55.02],[10.03,55.01],[10.02,55.02],[10.05,55.03]],
               [[9.99,55],[10.05,55]],CURVE+[CURVE[0]]]
        for points in paths:
            with self.subTest(points=points),self.assertRaises(ValueError):split_polygon_path(POLY,points)
        with self.assertRaises(ValueError):
            split_polygon_path(CONCAVE,[[9.99,55.005],[10.03,55.005],[10.03,55.035],[10.05,55.035]])
    def test_seeded_monotone_curves_preserve_coverage_in_both_orientations(self):
        rng=random.Random(82)
        for _ in range(25):
            path=[[9.99,55.02]]+[[10+i*.004,55.012+rng.random()*.016] for i in range(1,10)]+[[10.05,55.02]]
            first=split_polygon_path(POLY,path)
            self.assert_partition(POLY,first)
            self.assertEqual(canonical(first),canonical(split_polygon_path(list(reversed(POLY)),list(reversed(path)))))

    def test_bounded_vertex_count_rejects_before_expensive_geometry(self):
        with self.assertRaises(ValueError):split_polygon_path(POLY,[[10+i*.000001,55.01] for i in range(MAX_POINTS+1)])

class RoadChainTests(unittest.TestCase):
    def roads(self):
        return [{'name':'Fiktiv Kurvevej','points':CURVE[:3]},
                {'name':'Fiktiv Kurvevej','points':list(reversed(CURVE[2:4]))},
                {'name':'Fiktiv Kurvevej','points':CURVE[3:]}]
    def test_exact_unbranched_same_name_parts_join_in_either_order(self):
        roads=self.roads();original=copy.deepcopy(roads)
        paths=road_paths(roads,POLY)
        self.assertEqual(len(paths),1)
        self.assertEqual(set(paths[0][0]),set(map(tuple,CURVE)))
        for sequence in (list(reversed(roads)),[dict(r,points=list(reversed(r['points']))) for r in roads],roads+[roads[0]]):
            self.assertEqual(paths,road_paths(sequence,POLY))
        self.assertEqual(roads,original)
    def test_gaps_names_and_unnamed_fragments_are_never_guessed(self):
        for kind in ('gap','different name','unnamed'):
            roads=self.roads()
            if kind=='gap':roads[1]['points'][0]=[10.0300001,55.025]
            elif kind=='different name':roads[1]['name']='En anden fiktiv vej'
            else:
                for r in roads:r['name']=''
            self.assertGreater(len(road_paths(roads,POLY)),1)
    def test_branch_at_endpoint_or_interior_vertex_stops_joining(self):
        for points in ([[10.01,55.025],[10.018,55.033]],[[10.005,55.03],[10.01,55.025],[10.015,55.033]]):
            paths=road_paths(self.roads()+[{'name':'Fiktiv Kurvevej','points':points}],POLY)
            self.assertGreater(len(paths),1)
            self.assertFalse(any(set(map(tuple,CURVE)).issubset(set(p)) for p,n in paths))
    def test_candidate_count_is_bounded(self):
        roads=[{'name':'Fiktiv '+str(i),'points':[[9.99,55.001+i*.00001],[10.05,55.002+i*.00001]]} for i in range(MAX_PATHS+20)]
        self.assertEqual(len(road_paths(roads,POLY)),MAX_PATHS)

class PartitionIntegrationTests(unittest.TestCase):
    def addresses(self):
        points=[(10.005,55.005),(10.02,55.006),(10.035,55.007),(10.005,55.035),(10.02,55.036),(10.035,55.037)]
        return [{'id':'fake'+str(i),'road':'Fiktiv Husvej','number':str(i+1),'postcode':'9999','lng':x,'lat':y,'count':1} for i,(x,y) in enumerate(points)]
    def test_partition_follows_the_curve_and_preserves_ids_and_visits(self):
        addresses=self.addresses()
        parts=partition(POLY,addresses,3,roads=RoadChainTests().roads())
        self.assertEqual(len(parts),2)
        self.assertEqual(sorted(p['visits'] for p in parts),[3,3])
        self.assertTrue(all('Fiktiv Kurvevej' in p['warning'] for p in parts))
        shared=set(map(tuple,parts[0]['polygon']))&set(map(tuple,parts[1]['polygon']))
        self.assertTrue(set(map(tuple,CURVE[1:-1])).issubset(shared))
        self.assertEqual({a['id'] for p in parts for a in p['members']},{a['id'] for a in addresses})
        self.assertEqual(parts,partition(POLY,list(reversed(addresses)),3,roads=list(reversed(RoadChainTests().roads()))))
    def test_a_house_straddling_the_curve_is_not_split_or_lost(self):
        addresses=self.addresses()
        addresses[0].update(number='42',lng=10.019,lat=55.024)
        addresses[3].update(number='42',lng=10.021,lat=55.026)
        parts=partition(POLY,addresses,3,roads=RoadChainTests().roads())
        self.assertFalse(any('Fiktiv Kurvevej' in p['warning'] for p in parts))
        owners=[p for p in parts if any(a['id']=='fake0' for a in p['members'])]
        self.assertEqual(len(owners),1)
        self.assertIn('fake3',[a['id'] for a in owners[0]['members']])
        self.assertEqual(sum(len(p['members']) for p in parts),6)

if __name__=='__main__':unittest.main()
