import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'app'))
from store import Store

class CardColors(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        self.c=self.s.mutate('card.save',{'number':'120','temporary':True})['id']
    def tearDown(self):
        self.s.close();self.tmp.cleanup()
    def test_color_only_preserves_card_and_revisions(self):
        before=self.s.get('cards',self.c)
        self.s.mutate('card.color',{'card_id':self.c,'map_color':'#AB22CD'})
        after=self.s.get('cards',self.c)
        self.assertEqual(after,dict(before,map_color='#ab22cd'))
        self.s.close();self.s=Store(self.tmp.name)
        self.assertEqual(self.s.get('cards',self.c),after)
    def test_card_save_preserves_omitted_color(self):
        self.s.mutate('card.color',{'card_id':self.c,'map_color':'#123abc'})
        self.s.mutate('card.save',{'id':self.c,'number':'120','temporary':True})
        self.assertEqual(self.s.get('cards',self.c)['map_color'],'#123abc')
    def test_invalid_color_is_atomic_for_both_actions(self):
        before=self.s.get('cards',self.c)
        for value in ['red','#abc',None,'#000000" onload="x','javascript:x']:
            for action in ['card.color','card.save']:
                with self.assertRaises(ValueError):
                    self.s.mutate(action,{'card_id':self.c,'id':self.c,'number':'120','temporary':True,'map_color':value})
                self.assertEqual(self.s.get('cards',self.c),before)
