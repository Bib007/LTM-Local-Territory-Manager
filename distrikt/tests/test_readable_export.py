"""Invented private records in a temporary store; no network or real account."""
import base64,hashlib,io,json,struct,sys,tempfile,unittest,zipfile,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from readable_export import ReadableExport,csv_file,png_image,image_pdf

def png():
    def chunk(kind,raw):return struct.pack('>I',len(raw))+kind+raw+struct.pack('>I',zlib.crc32(kind+raw)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2200,1560,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\xff\xff\xff'*2200)*1560))+chunk(b'IEND',b'')

class ReadableExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        with self.store.transaction():
            cfg=self.store.get('settings','config');cfg.update(congregation='Fiktiv',api_key='DO_NOT_EXPORT_KEY',password='DO_NOT_EXPORT_PASSWORD');self.store.put('settings',cfg)
            self.store.put('cards',{'id':'c','number':'001','name':'Kort (fiktivt)','area_id':'a','addresses':[{'road':'Eksempelvej','numbers':'1; 9','count':2}],'geo_polygon':[[10,55],[10.01,55],[10.01,55.01]],'address_ids':['one','ib']})
            self.store.put('cards',{'id':'arch','number':'002','archived':True,'addresses':[],'last_completed':'2023-08-01'})
            self.store.put('settings',{'id':'a','name':'Område (fiktivt)'})
            self.store.put('publishers',{'id':'p','name':'Fiktiv Forkynder'})
            self.store.put('loans',{'id':'l','card_id':'c','publisher_id':'p','assigned':'2024-09-03','cycle_start':'2024-09-03','returned':None})
            self.store.put('completions',{'id':'e','card_id':'c','loan_id':'l','date':'2024-10-02','previous_completed':'2023-10-01','visits':2})
            self.store.put('notes',{'id':'n','task':True,'text':'=Fiktiv opgave\nAnden linje 😀','created':'2024-10-01','resolved':False})
            self.store.put('visits',{'id':'v','date':'2024-10-01','note':'Fiktiv bemærkning'})
            for ident,number in [('one','1'),('ib','9')]:self.store.put('geo',{'id':ident,'entity':'address','road':'Eksempelvej','number':number,'floor':'2','door':'tv','postcode':'9999','count':1,'lng':10,'lat':55})
            self.store.put('geo',{'id':'config','token':'DO_NOT_EXPORT_TOKEN'})
            self.store.put('ib',{'id':'i','card_id':'c','address_id':'ib','road':'Eksempelvej','number':'9 2 tv','date':'2024-01-01'})
        self.export=ReadableExport(self.store)
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def test_complete_private_zip_allowlists_and_exact_addresses(self):
        revision=self.store.revision;job=self.export.prepare();self.assertEqual(len(job['cards']),1)
        self.assertEqual([a['id'] for a in job['cards'][0]['members']],['one'])
        self.assertNotIn('ib',job['cards'][0]['card']);self.assertNotIn('notes',job)
        self.export.image({'token':job['token'],'card_id':'c','png':'data:image/png;base64,'+base64.b64encode(png()).decode()})
        raw=self.export.finish(job['token']);self.assertEqual(self.store.revision,revision)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=z.namelist();self.assertEqual(len([n for n in names if n.startswith('PDF/')]),4)
            self.assertIn('S-13/S-13-2022-2023.pdf',names);self.assertIn('CSV/omraader.csv',names)
            addresses=z.read('CSV/adresser.csv').decode('utf-8-sig');self.assertIn(';1;2;tv;9999;',addresses);self.assertIn(';9;2;tv;9999;',addresses);self.assertNotIn('1–9',addresses)
            self.assertIn("'=Fiktiv opgave",z.read('CSV/opgaver.csv').decode('utf-8-sig'))
            self.assertIn('😀',z.read('CSV/opgaver.csv').decode());self.assertIn(b'U+1F600',z.read('PDF/04-alle-opgaver.pdf'))
            self.assertIn(b'9 2 tv',z.read('PDF/02-alle-IB-bagsider.pdf'))
            for n in names:
                value=z.read(n)
                for secret in (b'DO_NOT_EXPORT_KEY',b'DO_NOT_EXPORT_PASSWORD',b'DO_NOT_EXPORT_TOKEN'):self.assertNotIn(secret,value)
            for row in z.read('SHA256SUMS.txt').decode().splitlines():
                digest,n=row.split('  ',1);self.assertEqual(hashlib.sha256(z.read(n)).hexdigest(),digest)
    def test_token_revision_completeness_and_replacement(self):
        first=self.export.prepare();second=self.export.prepare()
        with self.assertRaises(ValueError):self.export.finish(first['token'])
        with self.assertRaisesRegex(ValueError,'Ikke alle'):self.export.finish(second['token'])
        with self.assertRaises(ValueError):self.export.image({'token':second['token'],'card_id':'foreign','png':''})
        with self.store.transaction():self.store.put('notes',{'id':'new','task':True,'text':'Fiktiv'})
        with self.assertRaisesRegex(ValueError,'Data er ændret'):self.export.finish(second['token'])
    def test_csv_formulas_and_multiline_values(self):
        import csv
        rows=list(csv.reader(io.StringIO(csv_file(['tekst'],[['=1+1'],['+Fiktiv'],['@SUM(1)'],['Linje\n"to";æøå']]).decode('utf-8-sig')),delimiter=';'))
        self.assertEqual(rows[1],["'=1+1"]);self.assertEqual(rows[4],['Linje\n"to";æøå'])
    def test_rgba_predictors_and_white_alpha_compositing(self):
        previous=bytes([10,20,30,255,100,120,140,128]);current=bytes([40,50,60,255,180,190,200,0])
        for f in range(5):
            packed=bytearray()
            for row,above in [(previous,bytes(8)),(current,previous)]:
                packed.append(f)
                for x,value in enumerate(row):
                    a=row[x-4] if x>=4 else 0;b=above[x];c=above[x-4] if x>=4 else 0;p=a+b-c
                    da,db,dc=abs(p-a),abs(p-b),abs(p-c);paeth=a if da<=db and da<=dc else b if db<=dc else c
                    predictor=[0,a,b,(a+b)//2,paeth][f];packed.append((value-predictor)&255)
            def chunk(kind,raw):return struct.pack('>I',len(raw))+kind+raw+struct.pack('>I',zlib.crc32(kind+raw)&0xffffffff)
            raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,2,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(packed))+chunk(b'IEND',b'')
            result,w,h=png_image(raw);pixels=zlib.decompress(result)
            self.assertEqual((w,h),(2,2));self.assertEqual(pixels[:4],bytes([0,10,20,30]));self.assertEqual(pixels[-3:],b'\xff\xff\xff')

    def test_rgb_pdf_has_embedded_image_and_valid_page(self):
        raw=png();packed,w,h=png_image(raw);self.assertEqual((w,h),(2200,1560));self.assertEqual(len(zlib.decompress(packed)),1560*(1+2200*3))
        value=image_pdf([raw]);self.assertIn(b'/Count 1',value);self.assertIn(b'/Predictor 15',value);self.assertTrue(value.startswith(b'%PDF-'))

if __name__=='__main__':unittest.main()
