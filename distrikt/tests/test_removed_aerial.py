import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
class RemovedAerialTests(unittest.TestCase):
 def test_old_key_removed_on_upgrade_other_data_unchanged(self):
  with tempfile.TemporaryDirectory() as directory:
   s=Store(directory)
   s.mutate('card.save',{'number':'120','temporary':True})
   with s.transaction():s.put('geo',{'id':'basemap-config','entity':'basemap_config','apikey':'FAKE_TEST_KEY'})
   before=s.state();s.close();s=Store(directory)
   try:
    self.assertIsNone(s.get('geo','basemap-config'))
    after=s.state();before['revision']=after['revision'];before['undo_available']=after['undo_available'];self.assertEqual(after,before)
    with self.assertRaises(ValueError):s.mutate('geo.basemap.save',{'apikey':'FAKE_TEST_KEY'})
   finally:s.close()
