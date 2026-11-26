import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import base64,csv,io,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape
from copy import deepcopy
from column_import import describe,normalized_rows,load
from store import Store
from profile_policy import ACTIONS
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
def workbook(tables,formula=None,numeric=None,external=False,macro=False,dtd=False):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('xl/workbook.xml',('<!DOCTYPE workbook [<!ENTITY x "fiktiv">]>' if dtd else '')+'<workbook xmlns="'+NS+'" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join('<sheet name="'+escape(name)+'" sheetId="'+str(i)+'" r:id="r'+str(i)+'"/>' for i,(name,rows) in enumerate(tables,1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships>'+''.join('<Relationship Id="r'+str(i)+'" Target="'+('https://example.invalid/sheet.xml' if external else 'worksheets/sheet'+str(i)+'.xml')+'"'+(' TargetMode="External"' if external else '')+'/>' for i in range(1,len(tables)+1))+'</Relationships>')
        for i,(name,rows) in enumerate(tables,1):
            body=[]
            for line,values in enumerate(rows,1):
                cells=[]
                for col,value in enumerate(values,1):
                    ref=chr(64+col)+str(line)
                    content=('<v>'+escape(str(value))+'</v>') if numeric==(i,line,col) else '<is><t>'+escape(str(value))+'</t></is>'
                    cells.append('<c r="'+ref+'"'+(' s="1"' if numeric==(i,line,col) else ' t="inlineStr"')+'>'+content+('<f>1+1</f>' if formula==(i,line,col) else '')+'</c>')
                body.append('<row r="'+str(line)+'">'+''.join(cells)+'</row>')
            z.writestr('xl/worksheets/sheet'+str(i)+'.xml','<worksheet xmlns="'+NS+'"><sheetData>'+''.join(body)+'</sheetData></worksheet>')
        if macro:z.writestr('xl/vbaProject.bin',b'FICTIONAL')
    return {'name':'opdigtet.xlsx','content':base64.b64encode(out.getvalue()).decode()}
def source(rows,**kw):
    out=io.StringIO();w=csv.writer(out,delimiter=';');w.writerows(rows)
    return {'name':'opdigtet.csv','content':out.getvalue(),'header_row':1,**kw}
def fixture():return source([['Vej','Nr','Dør','Distrikt','Område','Etage','Postnr','Note'],['Fiktivvej','01-09','tv','001','Prøveø','st','0999','ignoreret'],['Opdigtetvej','02','th','002','Prøveø','1','0999','=1+1']],column_map=['road','number','door','card','area','floor','postcode',None])
class ColumnImportTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='ltm-column-test-');self.s=Store(self.tmp.name)
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def preview(self,d,kind='card'):return self.s.mutate('setup.card-import.preview' if kind=='card' else 'setup.ib.preview',{**d,'date':'2026-10-01'})
    def apply(self,p,kind='card',**kw):return self.s.mutate('setup.card-import.apply' if kind=='card' else 'setup.ib.apply',{'token':p['token'],'confirm':'IMPORTÉR KORT' if kind=='card' else 'IMPORTÉR IB',**kw})
    def test_full_card_mapping_preserves_text_and_existing_preview_is_read_only(self):
        d=fixture();before=deepcopy(self.s.state())
        with patch('urllib.request.urlopen',side_effect=AssertionError('no network')):p=self.preview(d)
        self.assertEqual(self.s.state(),before);self.assertEqual(p['errors'],[])
        self.assertEqual(p['cards'][0]['number'],'001');a=p['cards'][0]['addresses'][0]
        self.assertEqual((a['number'],a['floor'],a['door'],a['postcode']),('01-09','st','tv','0999'))
        self.assertTrue(a['line_only']);self.assertEqual(normalized_rows(d,'card')[1][0],2)
    def test_no_header_keeps_first_row(self):
        d=source([['001'],['002']],header_row=None,column_map=['card']);p=self.preview(d)
        self.assertEqual([c['number'] for c in p['cards']],['001','002']);self.assertEqual(p['cards'][0]['lines'],[1])
    def test_explicit_header_after_preamble(self):
        d=source([['Fiktiv forklaring'],['Kort'],['001']],header_row=2,column_map=['card'])
        self.assertEqual(self.preview(d)['cards'][0]['lines'],[3])
    def test_duplicate_empty_and_extra_columns_are_positional(self):
        d=source([['Nr','','Nr','Ubrugt'],['001','','09','bogstavelig tekst']],column_map=['card',None,'number',None],kind='card')
        desc=describe(d);self.assertEqual(desc['width'],4);self.assertNotEqual(desc['columns'][0]['index'],desc['columns'][2]['index'])
        self.assertEqual(normalized_rows(d,'card'),[(0,['card','number']),(2,['001','09'])])
    def test_ambiguous_names_never_assign_fields(self):
        d=source([['Nummer','Nummer'],['001','02']],kind='card');self.assertNotIn('column_map',describe(d))
        with self.assertRaisesRegex(ValueError,'hver kildekolonne'):normalized_rows(d,'card')
    def test_missing_required_and_duplicates_block(self):
        for kind,mapping,error in [('card',[None],'Kortnummer'),('ib',['road'],'Husnummer'),('card',['card','card'],'flere gange')]:
            d=source([['a']*len(mapping),['x']*len(mapping)],column_map=mapping)
            with self.subTest(kind=kind,mapping=mapping),self.assertRaisesRegex(ValueError,error):normalized_rows(d,kind)
    def test_invalid_map_types_unknown_fields_and_cross_domain_rejected(self):
        for mapping in [[],[True],[{}],['date'],['card',None]]:
            with self.subTest(mapping=mapping),self.assertRaises(ValueError):normalized_rows(source([['a'],['001']],column_map=mapping),'card')
    def test_missing_row_and_bad_header_type_rejected(self):
        for h in [True,0,-1,'1',7]:
            with self.subTest(h=h),self.assertRaises(ValueError):normalized_rows(source([['Kort'],['001']],header_row=h,column_map=['card']),'card')
    def test_row_errors_reference_original_lines(self):
        d=source([['Bemærkning'],['Kort','Vej','Nr','Postnr'],['001','Fiktivvej','1','99']],header_row=2,column_map=['card','road','number','postcode'])
        p=self.preview(d);self.assertEqual(p['errors'][0]['line'],3)
        with self.assertRaises(ValueError):self.apply(p)
        self.assertEqual(self.s.all('cards'),[])
    def test_card_domain_requires_road_and_number_together(self):
        p=self.preview(source([['Kort','Vej'],['001','Fiktivvej']],column_map=['card','road']));self.assertEqual(len(p['errors']),1)
    def test_card_register_only_is_valid(self):
        p=self.preview(source([['Kort'],['001']],column_map=['card']));self.assertEqual((p['register_cards'],p['errors']),(1,[]))
    def test_csv_quotes_commas_crlf_and_multiline_are_text(self):
        d={'name':'f.csv','content':'"a","b"\r\n"001","Fiktiv, vej\nlinje"\r\n','header_row':1,'column_map':['card','name']}
        r=normalized_rows(d,'card');self.assertEqual(r[1][1],['001','Fiktiv, vej\nlinje'])
    def test_csv_formula_like_text_is_not_executed(self):
        d=source([['Kort','Navn'],['001','=HYPERLINK("https://example.invalid")']],column_map=['card','name'])
        self.assertEqual(self.preview(d)['cards'][0]['name'],'=HYPERLINK("https://example.invalid")')
    def test_sheet_discovery_selection_and_strict_missing(self):
        d={**workbook([('Fane A',[['Kort'],['001']]),('Fane B',[['Kort'],['002']])]),'header_row':1,'column_map':['card'],'kind':'card'}
        self.assertEqual(describe(d)['sheets'],['Fane A','Fane B'])
        with self.assertRaisesRegex(ValueError,'fane'):normalized_rows(d,'card')
        self.assertEqual(self.preview({**d,'sheet':'Fane B'})['cards'][0]['number'],'002')
        with self.assertRaisesRegex(ValueError,'fane'):normalized_rows({**d,'sheet':'Forkert'},'card')
        single={**workbook([('Eneste',[['Kort'],['001']])]),'header_row':1,'column_map':['card'],'sheet':'Forkert'}
        with self.assertRaises(ValueError):normalized_rows(single,'card')
    def test_xlsx_text_preserves_zeroes_and_units(self):
        d={**workbook([('Data',[['K','Nr','Etage','Dør'],['001','01-09','st','0tv']])]),'sheet':'Data','header_row':1,'column_map':['card','number','floor','door']}
        self.assertEqual(normalized_rows(d,'card')[1][1],['001','01-09','st','0tv'])
    def test_formatted_numeric_cells_block_instead_of_losing_zeroes(self):
        d={**workbook([('Data',[['K'],['1']])],numeric=(1,2,1)),'sheet':'Data','header_row':1,'column_map':['card']}
        with self.assertRaisesRegex(ValueError,'Talformat'):normalized_rows(d,'card')
    def test_formulas_are_inert_when_ignored_and_block_when_selected(self):
        d={**workbook([('Data',[['K','Note'],['001','2']])],formula=(1,2,2)),'sheet':'Data','header_row':1,'column_map':['card',None]}
        self.assertEqual(normalized_rows(d,'card')[1][1],['001'])
        with self.assertRaisesRegex(ValueError,'Formler'):normalized_rows({**d,'column_map':['card','name']},'card')
    def test_external_sheet_macros_dtd_and_bad_base64_block(self):
        for options in [{'external':True},{'macro':True},{'dtd':True}]:
            d={**workbook([('Data',[['K'],['001']])],**options),'sheet':'Data','header_row':1,'column_map':['card']}
            with self.subTest(options=options),self.assertRaises(ValueError):normalized_rows(d,'card')
        with self.assertRaises(ValueError):load({'name':'bad.xlsx','content':'!!!','sheet':'A'})
    def test_limits_bytes_columns_fields_rows(self):
        cases=[{'name':'big.csv','content':'x'*2000001},source([['x']*41,['y']*41]),source([['a']]+[['001']]*10001)]
        for d in cases:
            with self.subTest(size=len(d['content'])),self.assertRaises(ValueError):load(d)
        d=source([['a']]+[['Fiktivvej','1']]*5001,column_map=['road','number'])
        with self.assertRaisesRegex(ValueError,'datarækker'):normalized_rows(d,'ib')
    def test_duplicate_card_address_and_reserved_number_block(self):
        d=source([['K','Vej','Nr','Postnr'],['001','Fiktivvej','01','0999'],['001','Fiktivvej','01','0999']],column_map=['card','road','number','postcode'])
        p=self.preview(d);self.assertEqual((p['duplicates'],p['errors'][0]['line']),(1,3))
        self.s.mutate('card.save',{'number':'001','temporary':True});p=self.preview(d);self.assertEqual(len(p['errors']),2)
    def test_confirmation_and_stale_preview_still_required(self):
        p=self.preview(fixture())
        with self.assertRaises(ValueError):self.s.mutate('setup.card-import.apply',{'token':p['token'],'confirm':'ja'})
        self.s.mutate('card.save',{'number':'999','temporary':True})
        with self.assertRaisesRegex(ValueError,'ændret'):self.apply(p)
    def test_card_failure_rolls_back_entire_file(self):
        p=self.preview(fixture());before=deepcopy(self.s.state());original=self.s._mutate
        def fail(action,data,**kw):
            if action=='card.save' and data.get('number')=='002':raise OSError('Fiktiv fejl')
            return original(action,data,**kw)
        with patch.object(self.s,'_mutate',side_effect=fail),self.assertRaises(OSError):self.apply(p)
        self.assertEqual(self.s.state(),before)
    def ib_data(self):
        self.s.mutate('card.save',{'number':'F001','temporary':True})
        return source([['Vej','Nr','Kort','Etage','Dør'],['Fiktivvej','01-09','F001','st','tv']],column_map=['road','number','card','floor','door'])
    def test_ib_manual_warning_ack_duplicate_and_text_preserved(self):
        d=self.ib_data();before=deepcopy(self.s.state());p=self.preview(d,'ib');self.assertEqual(self.s.state(),before)
        self.assertEqual((p['new'],p['warnings'],p['errors']),(1,1,0));self.assertEqual(p['rows'][0]['record']['number'],'01-09, st tv')
        with self.assertRaisesRegex(ValueError,'bekræft'):self.apply(p,'ib')
        self.apply(p,'ib',acknowledge=True);self.assertEqual(self.preview(d,'ib')['existing'],1)
        self.assertEqual(self.s.all('geo'),[])
    def test_ib_no_card_no_match_is_an_error_and_date_not_guessed(self):
        d=source([['Vej','Nr','Dato'],['Fiktivvej','01','31/10/2026']],column_map=['road','number','date']);p=self.preview(d,'ib');self.assertEqual(p['errors'],1)
        d=self.ib_data();d['column_map'].append('date');d['content']='Vej;Nr;Kort;Etage;Dør;Dato\nFiktivvej;01;F001;st;tv;31/10/2026\n';self.assertEqual(self.preview(d,'ib')['errors'],1)
    def test_ib_fallback_card_explicit_and_row_duplicates(self):
        d=self.ib_data();ident=self.s.all('cards')[0]['id'];d=source([['Vej','Nr'],['Fiktivvej','01'],['Fiktivvej','01']],column_map=['road','number'],card_id=ident)
        p=self.preview(d,'ib');self.assertEqual((p['new'],p['existing']),(1,1));self.assertEqual(p['rows'][0]['line'],2)
    def test_ib_failure_rolls_back_all_rows(self):
        d=self.ib_data();d['content']+='Fiktivvej;02;F001;st;tv\n';p=self.preview(d,'ib');before=deepcopy(self.s.state());original=self.s._mutate
        def fail(action,data,**kw):
            if action=='ib.save' and data['number'].startswith('02'):raise OSError('Fiktiv fejl')
            return original(action,data,**kw)
        with patch.object(self.s,'_mutate',side_effect=fail),self.assertRaises(OSError):self.apply(p,'ib',acknowledge=True)
        self.assertEqual(self.s.state(),before)
    def test_policy_requires_current_permissions(self):
        self.assertEqual(ACTIONS['setup.card-import.preview'],frozenset(['cards.view','cards.edit','geo.view']))
        self.assertEqual(ACTIONS['setup.ib.preview'],frozenset(['cards.view','ib.view','ib.edit']))
        self.assertEqual(ACTIONS['setup.card-import.preview'],ACTIONS['setup.card-import.apply'])
        self.assertEqual(ACTIONS['setup.ib.preview'],ACTIONS['setup.ib.apply'])
if __name__=='__main__':unittest.main(verbosity=2)
