"""Regression for local DAR outline clearance using fictional coordinates only."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))

from geography import point_in_polygon
from territory_outline import (
    edges, improve_address_clearance, meets, point_segment_distance,
    simple_ring, suggest_outline,
)


class LocalClearanceTests(unittest.TestCase):
    scale = 111320 * math.cos(math.radians(55))

    @classmethod
    def point(cls, x, y):
        return [round(10 + x / cls.scale, 7), round(55 + y / 111320, 7)]

    @classmethod
    def address(cls, number, x, y):
        lng, lat = cls.point(x, y)
        return {'number': str(number), 'postcode': '9999',
                'road': 'Fictional road', 'lng': lng, 'lat': lat}

    @classmethod
    def rectangle(cls, x0, y0, x1, y1):
        return [cls.point(x0, y0), cls.point(x1, y0),
                cls.point(x1, y1), cls.point(x0, y1)]

    @classmethod
    def clearance(cls, outline, address):
        lng, lat = address['lng'], address['lat']
        ring = [((p[0] - 10) * cls.scale, (p[1] - 55) * 111320)
                for p in outline]
        dot = ((lng - 10) * cls.scale, (lat - 55) * 111320)
        return min(point_segment_distance(dot, a, b) for a, b in edges(ring))

    def test_short_edge_tapers_near_excluded_house_instead_of_losing_selected_house(self):
        # The 20-metre top edge has one selected entrance pinned at its
        # left-hand end. Translating both vertices inward loses that house;
        # tapering the right-hand vertex creates room around the blue dot.
        ring = [(0., 0.), (20., 0.), (20., 20.), (0., 20.)]
        chosen = (1., 19.)
        outsider = (15., 21.)
        neighboring = [(23., -5.), (35., -5.), (35., 35.), (23., 35.)]
        def validate(candidate):
            if not simple_ring(candidate):
                return []
            if not point_in_polygon(chosen, candidate):
                return []
            if meets(candidate, neighboring, 0):
                return []
            area = abs(sum(a[0]*b[1] - b[0]*a[1]
                           for a, b in edges(candidate)))
            return candidate if area >= 400 * 2 * .65 else []

        original = min(point_segment_distance(outsider, a, b)
                       for a, b in edges(ring))
        improved = improve_address_clearance(ring, ring, [(outsider, 6.)], validate)
        clearance = min(point_segment_distance(outsider, a, b)
                        for a, b in edges(improved))
        self.assertAlmostEqual(original, 1.)
        self.assertGreater(clearance, 3.8)
        self.assertTrue(point_in_polygon(chosen, improved))
        self.assertFalse(meets(improved, neighboring, 0))
        self.assertTrue(simple_ring(improved))

    def test_short_and_tight_corridors_keep_selected_and_avoid_other_cards(self):
        selected = [self.address(1, -40, 0), self.address(3, 40, 0)]
        for length in (21, 100):
            with self.subTest(neighbor_length_m=length):
                neighbor = self.rectangle(-10, -length, 10, length)
                others = [self.address(2, -25, 8),
                          self.address(4, 25, -8)]
                outline, status = suggest_outline(selected, selected + others,
                                                  [neighbor])
                self.assertEqual(status, 'clear')
                self.assertTrue(simple_ring([tuple(p) for p in outline]))
                for address in selected:
                    self.assertTrue(point_in_polygon(
                        (address['lng'], address['lat']), outline))
                for address in others:
                    self.assertFalse(point_in_polygon(
                        (address['lng'], address['lat']), outline))
                    self.assertGreater(self.clearance(outline, address), .75)
                self.assertFalse(meets(outline, neighbor, 0))

    def test_close_unselected_entrance_does_not_remove_selected_entrance(self):
        selected = [self.address(1, -12, 0), self.address(3, 12, 0)]
        outsider = self.address(2, 0, 4)
        outline, status = suggest_outline(selected, selected + [outsider], [])
        self.assertEqual(status, 'clear')
        self.assertTrue(all(point_in_polygon(
            (a['lng'], a['lat']), outline) for a in selected))
        self.assertFalse(point_in_polygon(
            (outsider['lng'], outsider['lat']), outline))
        self.assertGreater(self.clearance(outline, outsider), .75)


if __name__ == '__main__':
    unittest.main()
