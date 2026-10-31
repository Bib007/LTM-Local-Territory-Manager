"""Incomplete fictional XLSX/CSV IB, confirmed imports and atomic effects."""
import base64
from copy import deepcopy
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from xml.sax.saxutils import escape
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from ib_import import HEADERS,template_xlsx
from card_import import xlsx_rows
from portable import snapshot,Restores
from store import Store

def workbook(headers,rows):
    template=template_xlsx();out=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(template)) as source,zipfile.ZipFile(out,'w') as result:
        for name in source.namelist():
            raw=source.read(name)
            if name=='xl/worksheets/sheet1.xml':
                table=''.join('<row r="'+str(n)+'">'+''.join('<c r="'+chr(65+i)+str(n)+'" t="inlineStr"><is><t>'+escape(str(value))+'</t></is></c>' for i,value in enumerate(values))+'</row>' for n,values in enumerate([headers]+rows,1))
                text=raw.decode();a=text.index('<sheetData>');b=text.index('</sheetData>')
                raw=(text[:a]+'<sheetData>'+table+text[b:]).encode()
            result.writestr(name,raw)
    return base64.b64encode(out.getvalue()).decode()

class IBImportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
        self.card=self.s.mutate('card.save',{'number':'F001','temporary':True})['id']
        for side in ('front','back'):self.s.mutate('revision.approve',{'card_id':self.card,'side':side})
    def tearDown(self):self.s.close();self.temp.cleanup()
    def preview(self,content,**kw):return self.s.mutate('setup.ib.preview',{'content':content,'date':'2026-10-01',**kw})
    def apply(self,p,**kw):return self.s.mutate('setup.ib.apply',{'token':p['token'],'confirm':'IMPORTÉR IB',**kw})

    def test_template_is_blank_text_format_and_no_private_data(self):
        raw=template_xlsx();self.assertEqual(raw,template_xlsx())
        self.assertEqual(xlsx_rows(raw,sheet_name='IB'),[(1,HEADERS)])
        with zipfile.ZipFile(io.BytesIO(raw)) as book:
            xml=book.read('xl/worksheets/sheet1.xml').decode()
            self.assertIn('style="1"',xml);self.assertIn('numFmtId="49"',book.read('xl/styles.xml').decode())
            self.assertNotIn('F001',xml);self.assertNotIn('<f>',xml)
    def test_missing_postcode_column_needs_card_and_explicit_review_then_preserves_manual_line(self):
        raw=workbook(['vejnavn','husnummer'],[['Fiktiv vej','01A']])
        p=self.preview(raw,name='fiktiv.xlsx');self.assertEqual(p['errors'],1)
        before=deepcopy(self.s.require('cards',self.card));revision=self.s.revision
        p=self.preview(raw,name='fiktiv.xlsx',card_id=self.card)
        self.assertEqual((p['new'],p['errors'],p['warnings']),(1,0,1));self.assertIn('postnummer',p['missing_columns'])
        self.assertTrue(any('Postnummer mangler' in w for w in p['rows'][0]['warnings']))
        self.assertEqual(self.s.revision,revision);self.assertEqual(self.s.all('ib'),[])
        with self.assertRaisesRegex(ValueError,'bekræft'):self.apply(p)
        self.apply(p,acknowledge=True);ib=self.s.all('ib')[0]
        self.assertEqual((ib['road'],ib['number'],ib['date']),('Fiktiv vej','01A','2026-10-01'))
        self.assertFalse(ib.get('address_id'));self.assertEqual(ib['missing_fields'],['postcode'])
        after=self.s.require('cards',self.card)
        self.assertEqual(before['addresses'],after['addresses']);self.assertEqual(before['front_revision'],after['front_revision']);self.assertTrue(after['back_revision'])
        self.assertEqual(self.s.all('geo'),[])
    def test_manual_duplicates_skip_and_postcode_can_be_completed_normally(self):
        text='kortnummer;vejnavn;husnummer\nF001;Fiktiv vej;2\nF001;Fiktiv vej;2\n'
        p=self.preview(text);self.assertEqual((p['new'],p['existing']),(1,1));self.apply(p,acknowledge=True)
        p=self.preview(text);self.assertEqual((p['new'],p['existing']),(0,2));self.apply(p)
        ib=self.s.all('ib')[0];self.s.mutate('ib.save',{**ib,'postcode':'9999'})
        self.assertEqual(self.s.all('ib')[0]['missing_fields'],[])
        self.assertEqual(self.s.all('ib')[0]['postcode'],'9999')
    def test_unmatched_known_postcode_is_explicit_manual_not_a_guessed_address(self):
        p=self.preview('kortnummer;vejnavn;husnummer;postnummer;etage;dør\nF001;Fiktiv ukendt;4;9999;1;tv')
        self.assertEqual(p['warnings'],1);self.apply(p,acknowledge=True)
        ib=self.s.all('ib')[0];self.assertEqual(ib['number'],'4, 1 tv');self.assertEqual(ib['postcode'],'9999');self.assertFalse(ib.get('address_id'))
    def test_unknown_card_and_invalid_values_block_whole_file(self):
        for line in ('Ukendt;Fiktiv vej;2;9999','F001;Fiktiv vej;2;99','F001;Fiktiv vej;;9999','F001;'+('x'*121)+';2;9999'):
            p=self.preview('kortnummer;vejnavn;husnummer;postnummer\n'+line,card_id=self.card)
            self.assertEqual(p['errors'],1)
            with self.assertRaises(ValueError):self.apply(p,acknowledge=True)
        self.assertEqual(self.s.all('ib'),[])
    def test_failure_during_normal_domain_write_rolls_back_all_rows_and_revisions(self):
        p=self.preview('kortnummer;vejnavn;husnummer\nF001;Fiktiv vej;2\nF001;Fiktiv vej;3')
        before=deepcopy(self.s.state());original=self.s._mutate
        def fail(action,data):
            if action=='ib.save' and data['number']=='3':raise OSError('Fictional storage failure')
            return original(action,data)
        with patch.object(self.s,'_mutate',side_effect=fail),self.assertRaises(OSError):self.apply(p,acknowledge=True)
        self.assertEqual(self.s.state(),before)
    def test_backup_retains_missing_marker_without_exporting_anything_else(self):
        p=self.preview('kortnummer;vejnavn;husnummer\nF001;Fiktiv vej;2');self.apply(p,acknowledge=True)
        raw=snapshot(self.s,'fictional')
        with tempfile.TemporaryDirectory() as other:
            target=Store(other);restores=Restores(target,'fictional');check=restores.preview(raw)
            restores.apply(check['token'])
            self.assertEqual(target.all('ib')[0]['missing_fields'],['postcode']);target.close()

if __name__=='__main__':unittest.main()
