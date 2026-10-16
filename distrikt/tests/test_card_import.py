"""Invented local imports: reviewed creation, rollback, identifiers and exact IB units."""
import base64,csv,io,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from portable import digest,snapshot,Restores
from card_import import HEADERS,read_rows

def csv_file(rows):
    f=io.StringIO();w=csv.writer(f,delimiter=';');w.writerow(HEADERS);w.writerows(rows);return {'name':'opdigtet.csv','content':f.getvalue()}

ROWS=[['001','Eksempelby','Vest','By','Fiktivvej','12','1','tv','0999','Lejlighed',1],['001','','','','Fiktivvej','12','1','th','0999','Lejlighed',1],['B02','eksempelby','Landkort','Land','Opdigtetvej','9A','','','9999','Hus',3]]

def xlsx_file(rows,formula=False):
    body=[]
    for i,values in enumerate([HEADERS]+rows,1):
        cells=[]
        for j,value in enumerate(values):
            ref=chr(65+j)+str(i)
            cells.append('<c r="'+ref+'" t="inlineStr"><is><t>'+escape(str(value))+'</t></is>'+('<f>1+1</f>' if formula and i==2 and j==0 else '')+'</c>')
        body.append('<row r="'+str(i)+'">'+''.join(cells)+'</row>')
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Distriktskort" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join(body)+'</sheetData></worksheet>')
    return {'name':'opdigtet.xlsx','content':base64.b64encode(stream.getvalue()).decode()}

class CardImportTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def preview(self,rows=ROWS):return self.s.mutate('setup.card-import.preview',csv_file(rows))
    def apply(self,p,**kw):return self.s.mutate('setup.card-import.apply',{'token':p['token'],'confirm':'IMPORTÉR KORT',**kw})
    def test_preview_is_read_only_and_apply_preserves_metadata_and_exact_units(self):
        area=self.s.mutate('area.save',{'name':'Eksempelby'})['id'];before=digest(self.s);revision=self.s.revision
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network')):p=self.preview()
        self.assertEqual(digest(self.s),before);self.assertEqual(self.s.revision,revision)
        self.assertEqual((len(p['cards']),p['addresses'],p['visits'],p['errors']),(2,3,5,[]));self.assertEqual(len(p['areas']),1)
        result=self.apply(p);self.assertEqual(result['count'],2)
        first=next(c for c in self.s.all('cards') if c['number']=='001');self.assertEqual(first['area_id'],area);self.assertEqual(first['name'],'Vest');self.assertEqual(first['kind'],'By')
        self.assertEqual(first['addresses'][0]['numbers'],'12, 1 tv');self.assertEqual(first['imported_addresses'][0]['postcode'],'0999');self.assertFalse(first['temporary']);self.assertFalse(first['in_folder']);self.assertTrue(first['front_revision']);self.assertTrue(first['back_revision'])
        self.assertNotIn('geo_addresses',first);self.assertFalse(self.s.all('geo'));self.assertFalse(self.s.all('loans'))
    def test_any_row_error_blocks_entire_import_and_creates_no_area(self):
        broken=[r[:] for r in ROWS];broken[-1][8]='invalid';p=self.preview(broken);before=digest(self.s)
        self.assertEqual(len(p['errors']),1)
        with self.assertRaisesRegex(ValueError,'Ret alle fejl'):self.apply(p)
        self.assertEqual(digest(self.s),before);self.assertFalse(self.s.state()['areas'])
    def test_duplicate_addresses_and_card_metadata_conflicts_have_row_numbers(self):
        p=self.preview([ROWS[0],ROWS[0]]);self.assertEqual(p['duplicates'],1);self.assertEqual(p['errors'][0]['line'],3)
        altered=ROWS[1][:];altered[2]='Et andet kortnavn';p=self.preview([ROWS[0],altered]);self.assertIn('kortnavn',p['errors'][0]['error'])
    def test_reserved_numbers_stale_preview_confirmation_and_replay(self):
        p=self.preview()
        with self.assertRaisesRegex(ValueError,'IMPORTÉR KORT'):self.apply(p,confirm='yes')
        self.s.mutate('card.save',{'number':'900'})
        with self.assertRaisesRegex(ValueError,'ændret'):self.apply(p)
        p=self.preview();self.apply(p)
        with self.assertRaisesRegex(ValueError,'ændret'):self.apply(p)
        p=self.preview();self.assertTrue(p['errors']);self.assertIn('Kortnummeret',p['errors'][0]['error'])
        existing=next(c for c in self.s.all('cards') if c['number']=='001');self.s.mutate('delete',{'module':'cards','id':existing['id']})
        self.assertTrue(self.preview()['errors'])
    def test_exact_ib_matching_after_excel_import_does_not_change_visit_counts(self):
        p=self.s.mutate('setup.card-import.preview',xlsx_file(ROWS));self.assertFalse(p['errors']);self.apply(p)
        f=io.StringIO();w=csv.writer(f,delimiter=';');w.writerow(['kortnummer','vejnavn','husnummer','postnummer','etage','dør','dato']);w.writerow(['001','Fiktivvej','12','0999','1','tv','2026-10-15'])
        p=self.s.mutate('setup.ib.preview',{'content':f.getvalue()});self.assertEqual((p['new'],p['errors']),(1,0));self.s.mutate('setup.ib.apply',{'token':p['token'],'confirm':'IMPORTÉR IB'})
        c=next(c for c in self.s.all('cards') if c['number']=='001');self.assertEqual(sum(a['count'] for a in c['addresses']),2)
        self.assertEqual(self.s.all('ib')[0]['number'],'12, 1 tv')
        other=c['imported_addresses'][1];self.s.mutate('ib.save',{'card_id':c['id'],'address_id':other['id'],'date':'2026-10-15'});self.assertEqual(len(self.s.all('ib')),2)
    def test_precise_addresses_follow_manual_road_list_edits(self):
        self.apply(self.preview());c=next(c for c in self.s.all('cards') if c['number']=='001')
        self.s.mutate('card.save',{**c,'addresses':c['addresses'][1:]})
        saved=self.s.get('cards',c['id']);self.assertEqual(len(saved['imported_addresses']),1);self.assertEqual(saved['imported_addresses'][0]['door'],'th')
    def test_known_address_cannot_be_assigned_to_a_second_imported_card(self):
        self.apply(self.preview());row=ROWS[0][:];row[0]='999';p=self.preview([row]);self.assertIn('Adressen findes allerede',p['errors'][0]['error'])
    def test_xlsx_parsing_and_shipped_template_are_blank_and_have_correct_headers(self):
        rows=read_rows(xlsx_file(ROWS));self.assertEqual(rows[1][1][0],'001');self.assertEqual(rows[1][1][8],'0999')
        template=Path(__file__).resolve().parents[1]/'app/kort-import-skabelon.xlsx';rows=read_rows({'name':'skabelon.xlsx','content':base64.b64encode(template.read_bytes()).decode()})
        self.assertEqual(len(rows),1);self.assertEqual([x.casefold() for x in rows[0][1]],HEADERS)
    def test_xlsx_formulas_corruption_and_unknown_extensions_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'Formler'):read_rows(xlsx_file(ROWS,formula=True))
        with self.assertRaises(ValueError):read_rows({'name':'test.xlsx','content':'not base64'})
        with self.assertRaises(ValueError):read_rows({'name':'test.xlsx','content':base64.b64encode(b'not a zip').decode()})
        with self.assertRaises(ValueError):read_rows({'name':'test.xls','content':'anything'})
    def test_manual_house_intervals_and_invalid_types_or_counts_are_not_silently_expanded(self):
        for column,value in [(5,'1-19'),(9,'invented type'),(10,'1.5'),(10,'0')]:
            row=ROWS[0][:];row[column]=value;p=self.preview([row]);self.assertEqual(len(p['errors']),1)
    def test_onboarding_preferences_are_validated_and_create_no_records(self):
        answers={'mode':'desk','boundary':'later','cards':'excel','ib':'yes'}
        self.s.mutate('setup.onboarding.save',{'answers':answers});self.assertEqual(self.s.state()['settings']['onboarding']['answers'],answers);self.assertFalse(self.s.all('cards'));self.assertFalse(self.s.all('ib'));self.assertFalse(self.s.all('geo'))
        before=digest(self.s)
        with self.assertRaises(ValueError):self.s.mutate('setup.onboarding.save',{'answers':{**answers,'cards':'auto'}})
        self.assertEqual(digest(self.s),before)
    def test_private_backup_round_trip_keeps_precise_addresses_and_setup_choices(self):
        self.apply(self.preview());answers={'mode':'desk','boundary':'later','cards':'excel','ib':'yes'};self.s.mutate('setup.onboarding.save',{'answers':answers})
        payload=snapshot(self.s,'1.12.0-beta.3')
        with tempfile.TemporaryDirectory() as directory:
            target=Store(directory)
            try:
                restores=Restores(target,'1.12.0-beta.3');p=restores.preview(payload);restores.apply(p['token'])
                self.assertEqual(target.all('cards'),self.s.all('cards'));self.assertEqual(target.state()['settings']['onboarding']['answers'],answers)
            finally:target.close()

if __name__=='__main__':unittest.main()
