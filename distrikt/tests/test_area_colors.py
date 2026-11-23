import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store


class AreaColors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def area(self, name='Fiktivt område', **values):
        return self.store.mutate('area.save', {'name': name, **values})['id']

    def card(self, number, area_id=''):
        return self.store.mutate('card.save', {
            'number': number, 'area_id': area_id, 'temporary': True,
        })['id']

    def test_new_and_moved_cards_inherit_area_colour(self):
        a = self.area(map_color='#AB22CD')
        b = self.area('Andet fiktivt område', map_color='#337799')
        first = self.card('A-1', a)
        self.assertEqual(self.store.get('cards', first)['map_color'], '#ab22cd')
        unassigned = self.card('B-1')
        self.store.mutate('card.save', {
            'id': unassigned, 'number': 'B-1', 'area_id': b, 'temporary': True,
        })
        self.assertEqual(self.store.get('cards', unassigned)['map_color'], '#337799')
        self.store.mutate('card.color', {'card_id': first, 'map_color': '#ff8800'})
        self.store.mutate('card.save', {'id': first, 'number': 'A-1', 'area_id': a, 'temporary': True})
        self.assertEqual(self.store.get('cards', first)['map_color'], '#ff8800')

    def test_area_recolour_overwrites_previous_card_colours_only_after_confirmation(self):
        a = self.area(map_color='#113355')
        other = self.area('Andet', map_color='#001122')
        first, second = self.card('A-1', a), self.card('A-2', a)
        outside = self.card('B-1', other)
        self.store.mutate('card.color', {'card_id': first, 'map_color': '#ffee00'})
        before = {x['id']: x for x in self.store.all('cards')}
        with self.assertRaises(ValueError):
            self.store.mutate('area.save', {'id': a, 'name': 'Fiktivt område', 'map_color': '#bb8899'})
        self.assertEqual({x['id']: x for x in self.store.all('cards')}, before)
        self.assertEqual(self.store.get('settings', a)['map_color'], '#113355')
        self.store.mutate('area.save', {
            'id': a, 'name': 'Fiktivt område', 'map_color': '#BB8899',
            'reset_card_colors': True,
        })
        self.assertEqual(self.store.get('cards', first)['map_color'], '#bb8899')
        self.assertEqual(self.store.get('cards', second)['map_color'], '#bb8899')
        self.assertEqual(self.store.get('cards', outside)['map_color'], '#001122')
        self.store.mutate('card.color', {'card_id': second, 'map_color': '#66aa33'})
        self.assertEqual(self.store.get('cards', second)['map_color'], '#66aa33')
        self.store.close()
        self.store = Store(self.tmp.name)
        self.assertEqual(self.store.get('settings', a)['map_color'], '#bb8899')
        self.assertEqual(self.store.get('cards', second)['map_color'], '#66aa33')

    def test_rename_and_legacy_area_colour_do_not_recolour_cards(self):
        a = self.area()
        c = self.card('F-1', a)
        self.store.mutate('card.color', {'card_id': c, 'map_color': '#ccaa44'})
        self.store.mutate('area.save', {'id': a, 'name': 'Omdøbt'})
        self.assertEqual(self.store.get('cards', c)['map_color'], '#ccaa44')
        self.store.mutate('area.save', {'id': a, 'name': 'Omdøbt', 'map_color': '#477596'})
        self.assertEqual(self.store.get('cards', c)['map_color'], '#ccaa44')

    def test_bad_colour_or_missing_confirmation_changes_nothing(self):
        a = self.area(map_color='#123456')
        c = self.card('F-1', a)
        before_area = self.store.get('settings', a)
        before_card = self.store.get('cards', c)
        for value in ('red', '#abc', None, '#112233" onload="bad'):
            with self.assertRaises(ValueError):
                self.store.mutate('area.save', {
                    'id': a, 'name': 'Fiktivt område', 'map_color': value,
                    'reset_card_colors': True,
                })
            self.assertEqual(self.store.get('settings', a), before_area)
            self.assertEqual(self.store.get('cards', c), before_card)


if __name__ == '__main__':
    unittest.main()
