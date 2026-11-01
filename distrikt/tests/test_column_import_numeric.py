"""Targeted W127 numeric XLSX regression cases. Only invented values."""
import base64,io,zipfile,unittest
from test_column_import import workbook
from column_import import describe,normalized_rows

def data(value,fmt=None,kind=None,formula=False):
    d=workbook([('Data',[['Kort','Vej','Nr','Ubrugt'],['001','Fiktivvej',value,'1']])],numeric=(1,2,3),formula=(1,2,4) if formula else None)
    out=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(d['content']))) as old,zipfile.ZipFile(out,'w') as new:
        for name in old.namelist():
            raw=old.read(name)
            if name.endswith('sheet1.xml'):
                raw=raw.replace(b'r="C2" s="1"',b'r="C2"'+(b' t="'+kind.encode()+b'"' if kind else b'')+(b' s="1"' if fmt is not None else b''))
            new.writestr(name,raw)
        if fmt is not None:
            if isinstance(fmt,int):formats='';ident=fmt
            else:formats='<numFmts><numFmt numFmtId="164" formatCode="'+fmt+'"/></numFmts>';ident=164
            new.writestr('xl/styles.xml','<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'+formats+'<cellXfs><xf numFmtId="0"/><xf numFmtId="'+str(ident)+'"/></cellXfs></styleSheet>')
    return {**d,'content':base64.b64encode(out.getvalue()).decode(),'kind':'card','sheet':'Data','header_row':1,'column_map':['card','road','number',None]}
class NumericColumnTests(unittest.TestCase):
    def test_general_integer_house_and_card_numbers_are_strings(self):
        for value in ['12','001','12.0','1.2E2','0','-1','999999999999999']:
            with self.subTest(value=value):
                d=data(value);row=normalized_rows(d,'card')[1][1];self.assertIsInstance(row[2],str)
                self.assertEqual(row[2],str(int(__import__('decimal').Decimal(value))))
                self.assertEqual(normalized_rows({**d,'column_map':[None,'road','card',None]},'card')[1][1][-1],row[2])
    def test_zero_padding_and_explicit_text_are_preserved(self):
        for fmt,want in [('00000','00012'),(1,'12'),(49,'12')]:
            with self.subTest(fmt=fmt):self.assertEqual(normalized_rows(data('12',fmt),'card')[1][1][2],want)
        d=workbook([('Data',[['K'],['001']])]);d.update(sheet='Data',header_row=1,column_map=['card'])
        self.assertEqual(normalized_rows(d,'card')[1][1],['001'])
    def test_column_and_row_zero_formats_are_not_lost(self):
        for inheritance in ('column','row'):
            d=data('12','00000');out=io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(base64.b64decode(d['content']))) as old,zipfile.ZipFile(out,'w') as new:
                for name in old.namelist():
                    raw=old.read(name)
                    if name.endswith('sheet1.xml'):
                        raw=raw.replace(b'r="C2" s="1"',b'r="C2"')
                        if inheritance=='column':raw=raw.replace(b'<sheetData>',b'<cols><col min="3" max="3" style="1"/></cols><sheetData>')
                        else:raw=raw.replace(b'<row r="2">',b'<row r="2" s="1" customFormat="1">')
                    new.writestr(name,raw)
            d['content']=base64.b64encode(out.getvalue()).decode()
            self.assertEqual(normalized_rows(d,'card')[1][1][2],'00012')
    def test_unsafe_values_preview_but_reject_only_selected_fields(self):
        for value,fmt,kind in [('1000000000000000',None,None),('1.5',None,None),('1e999999999',None,None),('12','0.00',None),('46000',14,None),('2026-01-01',None,'d'),('1',None,'b'),('NaN',None,None)]:
            with self.subTest(value=value,fmt=fmt,kind=kind):
                d=data(value,fmt,kind);p=describe(d);self.assertTrue(p['issues'])
                with self.assertRaisesRegex(ValueError,'kolonne 3'):normalized_rows(d,'card')
                self.assertEqual(normalized_rows({**d,'column_map':['card',None,None,None]},'card')[1][1],['001'])
    def test_conditional_number_format_is_not_guessed(self):
        d=data('12');out=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(d['content']))) as old,zipfile.ZipFile(out,'w') as new:
            for name in old.namelist():
                raw=old.read(name)
                if name.endswith('sheet1.xml'):raw=raw.replace(b'</worksheet>',b'<conditionalFormatting sqref="C2"><cfRule type="expression"><formula>1=1</formula></cfRule></conditionalFormatting></worksheet>')
                new.writestr(name,raw)
        d['content']=base64.b64encode(out.getvalue()).decode()
        with self.assertRaisesRegex(ValueError,'Talformat'):normalized_rows(d,'card')
        self.assertEqual(normalized_rows({**d,'column_map':['card',None,None,None]},'card')[1][1],['001'])
    def test_formula_cached_result_is_never_imported_and_ignored_formula_is_allowed(self):
        d=data('12',formula=True);self.assertEqual(normalized_rows(d,'card')[1][1][-1],'12')
        self.assertEqual(describe(d)['sample'][0]['values'][3],'[ƒ]')
        with self.assertRaisesRegex(ValueError,'Formler'):normalized_rows({**d,'column_map':['card','road','number','name']},'card')
    def test_long_ignored_csv_column_does_not_block_and_selected_column_rejects(self):
        d={'name':'opdigtet.csv','content':'Kort;Note\n001;'+('x'*251),'header_row':1,'column_map':['card',None]}
        self.assertEqual(normalized_rows(d,'card')[1][1],['001'])
        with self.assertRaisesRegex(ValueError,'250'):normalized_rows({**d,'column_map':['card','name']},'card')
if __name__=='__main__':unittest.main()
