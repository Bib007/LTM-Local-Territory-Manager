import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from pdf_export import s13_pdf

class RecoveryChangesTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def card(self,number='120'):
        self.s.mutate('geo.manual',{'road':'Fiktiv vej','number':'1','postcode':'9999','lng':10,'lat':55})
        ident=self.s.geo_state()['addresses'][0]['id']
        return self.s.mutate('geo.assign',{'number':number,'address_ids':[ident]})['id'],ident
    def test_deleted_card_releases_addresses_and_restore_rejects_reassignment(self):
        c,a=self.card();batch=self.s.mutate('delete',{'module':'cards','id':c})
        self.assertNotIn('card_id',self.s.geo_state()['status'][a])
        other=self.s.mutate('geo.assign',{'number':'121','address_ids':[a]})['id']
        with self.assertRaises(ValueError):self.s.mutate('restore',batch)
        self.assertIsNone(self.s.get('cards',c));self.assertEqual(self.s.geo_state()['status'][a]['card_id'],other)
    def test_purge_whole_card_batch_keeps_live_records_and_public_addresses(self):
        c,a=self.card();p=self.s.mutate('publisher.save',{'name':'Fiktiv person'})['id']
        self.s.mutate('loan.issue',{'card_id':c,'publisher_id':p,'date':'2026-01-01','initial':True})
        self.s.mutate('ib.save',{'card_id':c,'road':'Fiktiv vej','number':'1','date':'2026-01-01'})
        other=self.s.mutate('card.save',{'number':'121','temporary':True})['id'];batch=self.s.mutate('delete',{'module':'cards','id':c})
        self.assertEqual(self.s.mutate('recovery.purge',batch)['count'],3);self.assertFalse(self.s.recovery())
        self.assertIsNotNone(self.s.get('geo',a));self.assertIsNotNone(self.s.get('cards',other));self.assertIsNotNone(self.s.get('publishers',p))
        self.assertEqual(self.s.all('loans',deleted=True),[])
        with self.assertRaises(ValueError):self.s.mutate('restore',batch)
        with self.assertRaises(ValueError):self.s.mutate('recovery.purge',{'batch':'nonexistent'})
        self.s.mutate('card.save',{'number':'120','temporary':True})
    def test_original_s13_background_is_embedded_and_margin_transform_used(self):
        c,a=self.card();pdf=s13_pdf(self.s.state(),2027)
        self.assertIn(b'/DCTDecode',pdf);self.assertIn(b'/Im1 Do',pdf);self.assertIn(b'q .88 0 0 .88',pdf)
        self.assertIn((Path(__file__).resolve().parents[1]/'templates'/'S-13-background.jpg').read_bytes(),pdf)
        self.assertIn(b'2026/2027',pdf);self.assertIn(b'(120)',pdf)

if __name__=='__main__':unittest.main()
