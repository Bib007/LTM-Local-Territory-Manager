"""Original English assets, Danish compatibility and local print-language persistence."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from pdf_export import s13_pdf,allocation_rows
from store import Store
ROOT=Path(__file__).resolve().parents[1]
def fixture():
    return {'cards':[{'id':'c','number':'F001','last_completed':'2025-06-01'}],'publishers':[{'id':'p','name':'Fictional Publisher'}],'loans':[{'id':'l','card_id':'c','publisher_id':'p','assigned':'2026-09-15','cycle_start':'2026-09-15','returned':'2026-10-15'}],'completions':[{'id':'e','card_id':'c','loan_id':'l','date':'2026-10-15','assigned':'2026-09-15'}]}
class EnglishFormsTests(unittest.TestCase):
    def test_originals_are_unmodified_and_field_rectangles_are_inside_page(self):
        for name,expected in [('S-12-E.pdf','0f861205b5e71acd70e61b858bf0e9abe8fb783a5feb00c8ef0b6eade1752bf6'),('S-13-E.pdf','467de173fedf65713879fb1c1c69c60666975f1f2db09e1f8bca3d9791a0a36e')]:
            self.assertEqual(hashlib.sha256((ROOT/'templates'/name).read_bytes()).hexdigest(),expected)
        t=json.loads((ROOT/'templates/S-13-E-fields.json').read_text());self.assertEqual(len(t['fields']),281)
        for x,y,right,bottom in t['fields'].values():self.assertTrue(0<=x<right<=t['width'] and 0<=y<bottom<=t['height'])
    def test_danish_pdf_is_byte_identical_to_released_128(self):
        self.assertEqual(hashlib.sha256(s13_pdf(fixture(),2027)).hexdigest(),'c040bfeed56c3c7a2aa4f92ae3f9dce6b50668f761afd1026022ab45d0db47fd')
    def test_english_pdf_uses_its_own_background_and_preserves_values(self):
        raw=s13_pdf(fixture(),2027,'en');self.assertTrue(raw.startswith(b'%PDF'))
        for text in [b'F001',b'Fictional Publisher',b'15.09.26',b'15.10.26',b'2026/2027']:self.assertIn(text,raw)
        self.assertNotIn(b'Hus til hus',raw);self.assertIn(b'/Count 1',raw)
        with self.assertRaises(ValueError):s13_pdf(fixture(),2027,'invalid')
    def test_print_language_is_saved_and_invalid_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            s=Store(root)
            try:
                profile=dict(orientation='landscape',paper='cut',mode='full',width=146,height=94,x=0,y=0,form_language='en')
                s.mutate('print.profile.save',dict(side='front',profile=profile));self.assertEqual(s.get('settings','config')['print_profiles']['front']['form_language'],'en')
                with self.assertRaises(ValueError):s.mutate('print.profile.save',dict(side='front',profile=dict(profile,form_language='invalid')))
                self.assertEqual(s.get('settings','config')['print_profiles']['front']['form_language'],'en')
            finally:s.close()
if __name__=='__main__':unittest.main()
