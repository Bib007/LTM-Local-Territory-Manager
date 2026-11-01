"""Local XLSX/CSV card imports. Preview has no database writes or network calls."""
import base64
import binascii
import csv
import io
import posixpath
import re
import uuid
import zipfile
from decimal import Decimal,InvalidOperation
from ui_errors import UIError,error_payload
from xml.etree import ElementTree as ET

HEADERS=['kortnummer','område','kortnavn','distriktstype','vejnavn','husnummer','etage','dør','postnummer','adressetype','besøg']
ALIASES=dict(zip(HEADERS,['card','area','name','kind','road','number','floor','door','postcode','type','count']))
ALIASES.update(dict(zip(['card','area','name','kind','road','number','floor','door','postcode','type','count'],['card','area','name','kind','road','number','floor','door','postcode','type','count'])))
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
MAX_BYTES=2000000

def norm(value):return re.sub(r'\s+',' ',str(value or '').strip()).casefold()
def template_csv():return ('\ufeff'+';'.join(HEADERS)+'\r\n').encode('utf-8')

class NoDTD(ET.TreeBuilder):
    def doctype(self,name,pubid,system):
        # Parser-level rejection also covers UTF-16 XML inside XLSX files.
        raise ValueError('Regnearket indeholder ikke-understøttede XML-deklarationer.')

class ImportCell(str):
    """Inert preview text plus a deferred selected-field error; never a formula value."""
    def __new__(cls,value,issue=''):
        obj=str.__new__(cls,str(value)[:250]);obj.issue=issue;return obj

def import_number(value,format_code):
    try:
        n=Decimal(value)
        if not n.is_finite() or n!=n.to_integral_value():raise ValueError()
        # Excel only guarantees 15 significant decimal digits. Never invent rounded identifiers.
        if n.copy_abs()>999999999999999:raise ValueError()
    except (InvalidOperation,ValueError):return ImportCell(value,'Tallet er ikke et sikkert heltal. Gem feltet som tekst, eller ignorér kolonnen.')
    if format_code not in ('General','@','0') and not re.fullmatch(r'0{1,30}',format_code or ''):
        return ImportCell(value,'Talformat eller dato kan ikke bevares sikkert. Gem feltet som tekst, eller ignorér kolonnen.')
    text=str(int(n))
    if format_code not in ('General','@'):text=('-' if n<0 else '')+str(abs(int(n))).zfill(len(format_code))
    return ImportCell(text)

def xlsx_rows(raw,sheet_name='Distriktskort',*,list_sheets=False,strict_sheet=False,column_cells=False):
    """Read values from the named input sheet; never evaluate formulas or links."""
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos=archive.infolist();names=[i.filename for i in infos]
            if len(infos)>500 or len(set(names))!=len(names) or sum(i.file_size for i in infos)>20000000:
                raise ValueError('Regnearket er for stort. Brug højst 10.000 adresser.')
            if any(i.flag_bits&1 for i in infos):raise ValueError('Fjern adgangskoden fra regnearket før import.')
            if any('vbaproject' in n.lower() for n in names):raise ValueError('Gem filen som almindelig .xlsx uden makroer.')
            def xml(name):
                content=archive.read(name)
                if b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():raise ValueError('Regnearket indeholder ikke-understøttede XML-deklarationer.')
                return ET.fromstring(content,parser=ET.XMLParser(target=NoDTD()))
            book=xml('xl/workbook.xml');sheets=book.findall('s:sheets/s:sheet',NS)
            sheet_names=[s.get('name') for s in sheets]
            if not sheet_names or any(not n for n in sheet_names) or len(set(sheet_names))!=len(sheet_names):raise ValueError('Fanenavne mangler eller er gentaget.')
            if list_sheets:return sheet_names
            chosen=next((s for s in sheets if s.get('name')==sheet_name),None)
            if chosen is None:
                if strict_sheet:raise ValueError('Vælg en eksisterende fane eksplicit.')
                if len(sheets)!=1:raise UIError('Brug skabelonens fane {sheet}, eller gem som CSV.',sheet=sheet_name)
                chosen=sheets[0]
            rels={r.get('Id'):r for r in xml('xl/_rels/workbook.xml.rels')}
            rel=rels.get(chosen.get('{'+NS['r']+'}id'))
            if rel is None or rel.get('TargetMode')=='External':raise ValueError('Vælg et lokalt regneark uden eksternt datalink.')
            target=rel.get('Target','');sheetpath=posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/'+target)
            if not sheetpath.startswith('xl/worksheets/'):raise ValueError('Regnearkets fane kunne ikke læses.')
            strings=[]
            if 'xl/sharedStrings.xml' in names:
                strings=[''.join(t.text or '' for t in item.iter('{'+NS['s']+'}t')) for item in xml('xl/sharedStrings.xml')]
                if len(strings)>150000:raise ValueError('Regnearket indeholder for meget tekst.')
            formats={0:'General',1:'0',49:'@'};styles=[]
            if column_cells and 'xl/styles.xml' in names:
                style_xml=xml('xl/styles.xml')
                base_styles=style_xml.findall('s:cellStyleXfs/s:xf',NS)
                plain_base=not base_styles or base_styles[0].get('numFmtId','0')=='0'
                for fmt in style_xml.findall('s:numFmts/s:numFmt',NS):
                    try:formats[int(fmt.get('numFmtId',''))]=fmt.get('formatCode','')
                    except ValueError:raise ValueError('Regnearkets fane kunne ikke læses.') from None
                for xf in style_xml.findall('s:cellXfs/s:xf',NS):
                    try:styles.append(formats.get(int(xf.get('numFmtId','0')),'') if xf.get('applyNumberFormat')!='0' and xf.get('xfId','0')=='0' and (plain_base or xf.get('applyNumberFormat')=='1') else '')
                    except ValueError:styles.append('')
            sheet_xml=xml(sheetpath);column_styles=[]
            if column_cells:
                for col_style in sheet_xml.findall('s:cols/s:col',NS):
                    if col_style.get('style') is not None:
                        try:column_styles.append((int(col_style.get('min','0')),int(col_style.get('max','0')),col_style.get('style')))
                        except ValueError:raise ValueError('Regnearkets fane kunne ikke læses.') from None
            rows=[]
            for row in sheet_xml.findall('s:sheetData/s:row',NS):
                cells={}
                for cell in row.findall('s:c',NS):
                    ref=cell.get('r','');match=re.fullmatch(r'([A-Z]{1,3})([1-9]\d*)',ref)
                    if not match:raise ValueError('En cellereference er ugyldig.')
                    col=0
                    for letter in match[1]:col=col*26+ord(letter)-64
                    formula=cell.find('s:f',NS) is not None
                    if formula and not column_cells:raise ValueError('Formler understøttes ikke. Indsæt som værdier, og prøv igen.')
                    value=cell.findtext('s:v','',NS);kind=cell.get('t')
                    if formula and column_cells:kind='str';value='[ƒ]'
                    if kind=='inlineStr':value=''.join(t.text or '' for t in cell.findall('.//s:t',NS))
                    elif kind=='s':
                        try:
                            index=int(value)
                            if index<0 or index>=len(strings):raise IndexError()
                            value=strings[index]
                        except (ValueError,IndexError):raise ValueError('En tekstcelle kunne ikke læses.') from None
                    elif kind in ('e','b','d') and not column_cells:raise ValueError('Brug almindelig tekst eller tal i importfelterne.')
                    if column_cells:
                        if formula:value=ImportCell('[ƒ]','Formler understøttes ikke. Indsæt som værdier, eller ignorér kolonnen.')
                        elif kind in ('e','b','d'):value=ImportCell('[Dato / celleværdi]' if kind=='d' else '[Celleværdi]','Dato, fejl eller sand/falsk skal gemmes som tekst, eller kolonnen skal ignoreres.')
                        elif len(value)>250:value=ImportCell(value,'Et felt er for langt (højst 250 tegn).')
                        elif value and kind not in ('inlineStr','s','str'):
                            try:
                                default_style=next((style for low,high,style in reversed(column_styles) if low<=col<=high),'0')
                                if row.get('customFormat')=='1':default_style=row.get('s','0')
                                style=int(cell.get('s',default_style))
                                fmt=styles[style] if 0<=style<len(styles) else ('General' if style==0 and not styles else '')
                            except ValueError:fmt=''
                            if sheet_xml.find('s:conditionalFormatting',NS) is not None:fmt=''
                            value=import_number(value,fmt)
                    elif len(value)>250:raise ValueError('Et felt er for langt (højst 250 tegn).')
                    if value:
                        if col>40:raise ValueError('Filen indeholder for mange kolonner. Brug skabelonen.')
                        if col in cells:raise ValueError('En celle er gentaget i regnearket.')
                        cells[col]=value
                if cells:rows.append((int(row.get('r') or match[2]),[cells.get(i,'') for i in range(1,max(cells)+1)]))
                if len(rows)>10001:raise ValueError('Importfilen må højst indeholde 10.000 adresser.')
            return rows
    except (zipfile.BadZipFile,KeyError,ET.ParseError,RuntimeError,OverflowError) as error:
        raise ValueError('XLSX-filen kunne ikke læses. Gem som .xlsx eller CSV fra skabelonen.') from error

def read_rows(data,sheet_name='Distriktskort',*,list_sheets=False,strict_sheet=False,column_cells=False):
    filename=str(data.get('name','')).lower()
    if filename.endswith('.xlsx'):
        encoded=data.get('content','')
        if not isinstance(encoded,str) or len(encoded)>4*((MAX_BYTES+2)//3):raise ValueError('Filen må højst fylde 2 MB.')
        try:raw=base64.b64decode(encoded,validate=True)
        except (ValueError,binascii.Error):raise ValueError('Regnearket kunne ikke afkodes.') from None
        if len(raw)>MAX_BYTES:raise ValueError('Filen må højst fylde 2 MB.')
        return xlsx_rows(raw,sheet_name,list_sheets=list_sheets,strict_sheet=strict_sheet,column_cells=column_cells)
    if not filename.endswith('.csv'):raise ValueError('Vælg en .xlsx- eller .csv-fil. Gem gamle .xls-filer som .xlsx først.')
    raw=data.get('content','')
    if not isinstance(raw,str) or len(raw.encode('utf-8'))>MAX_BYTES:raise ValueError('Filen må højst fylde 2 MB.')
    first=raw.lstrip('\ufeff').split('\n',1)[0];delimiter=';' if first.count(';')>=first.count(',') else ','
    try:
        rows=[]
        for line,row in enumerate(csv.reader(io.StringIO(raw.lstrip('\ufeff')),delimiter=delimiter,strict=True),1):
            if any(v.strip() for v in row):rows.append((line,row))
            if len(rows)>10001 or line>20001:raise ValueError('Importfilen må højst indeholde 10.000 adresser.')
        return rows
    except csv.Error:raise ValueError('CSV-filen kunne ikke læses. Brug skabelonens kolonner.') from None

def preview(store,data):
    from store import ADDRESS_TYPES,clean_text
    if 'column_map' in data:
        from column_import import normalized_rows
        rows=normalized_rows(data,'card')
    else:rows=read_rows(data)
    if not rows:raise ValueError('Filen er tom. Udfyld skabelonen først.')
    fields=[ALIASES.get(norm(x)) for x in rows[0][1]]
    if any(not x for x in fields) or len(set(fields))!=len(fields) or 'card' not in fields:
        raise ValueError('Brug skabelonens kolonneoverskrifter. Kortnummer er påkrævet; vejliste kan tilføjes senere.')
    cards={};errors=[];addresses={};duplicates=0
    reserved={norm(c['number']) for c in store.all('cards')+store.all('cards',deleted=True)}
    old_areas={norm(a['name']):a for a in store.all('settings') if a.get('id')!='config' and not a.get('entity')}
    removed_areas={norm(a.get('name')) for a in store.all('settings',deleted=True) if not a.get('entity')}
    occupied=set()
    for c in store.all('cards')+store.all('cards',deleted=True):
        for a in c.get('geo_addresses') or c.get('imported_addresses') or []:
            occupied.add(tuple(norm(a.get(k)) for k in ('postcode','road','number','floor','door')))
    for line,values in rows[1:]:
        try:
            if len(values)>len(fields) and any(values[len(fields):]):raise ValueError('Linjen har for mange kolonner.')
            v={key:str(value).strip() for key,value in zip(fields,values+['']*(len(fields)-len(values)))}
            if any(len(x)>250 for x in v.values()):raise ValueError('Et felt er for langt.')
            number=clean_text(v.get('card'),30,True);key=norm(number)
            if key in reserved:raise ValueError('Kortnummeret findes allerede eller er reserveret i Gendan ved fejl.')
            meta={'area':clean_text(v.get('area'),80),'name':clean_text(v.get('name'),100),'kind':v.get('kind') or ''}
            if meta['kind'] and meta['kind'] not in ('By','Land','Ukendt'):raise ValueError('Distriktstype skal være By, Land eller Ukendt.')
            if key not in cards:
                if len(cards)>=500:raise ValueError('Importér højst 500 kort ad gangen.')
                cards[key]={'number':number,'area':'','name':'','kind':'','addresses':[],'lines':[]}
            c=cards[key]
            for field,val in meta.items():
                if not val:continue
                if c[field] and norm(c[field])!=norm(val):raise UIError('Samme kort har forskellige oplysninger i kolonnen {field}.',field={'area':'område','name':'kortnavn','kind':'distriktstype'}[field])
                c[field]=val
            if norm(c['area']) in removed_areas and norm(c['area']) not in old_areas:raise ValueError('Området findes i Gendan ved fejl. Gendan eller omdøb det først.')
            road=clean_text(v.get('road'),120);house=clean_text(v.get('number'),100)
            if not road and not house:
                if any(v.get(k) for k in ('postcode','floor','door','type','count')):raise ValueError('Angiv både vej og nummer, eller lad alle adressefelter stå tomme til et registerkort.')
                c['lines'].append(line);continue
            if not road or not house:raise ValueError('Angiv både vejnavn og husnummer eller interval.')
            postcode=v.get('postcode','')
            if postcode and not re.fullmatch(r'\d{4}',postcode):raise ValueError('Postnummeret skal have fire cifre eller stå tomt for en manuel vejlinje.')
            line_only=not(postcode and re.fullmatch(r'\d+[A-Za-zÆØÅæøå]?',house))
            if not line_only and len(house)>30:raise ValueError('Et præcist husnummer må højst være 30 tegn.')
            floor=clean_text(v.get('floor'),20);door=clean_text(v.get('door'),30)
            typ=v.get('type') or 'Hus'
            if typ not in ADDRESS_TYPES:raise ValueError('Vælg en adressetype fra skabelonen.')
            unknown=line_only and not v.get('count')
            count='0' if unknown else v.get('count') or '1'
            if not unknown and (not re.fullmatch(r'\d+',count) or not 1<=int(count)<=10000):raise ValueError('Besøg skal være et helt tal fra 1 til 10.000 eller stå tomt for en manuel vejlinje.')
            address_key=tuple(norm(x) for x in (postcode,road,house,floor,door))
            if not line_only and address_key in occupied:raise ValueError('Adressen findes allerede på et eksisterende kort eller i gendannelse.')
            if address_key in addresses:
                duplicates+=1
                raise UIError('Adressen er gentaget i filen (først på linje {line}).',line=addresses[address_key])
            if len(c['addresses'])>=300:raise ValueError('Kortet har over 300 adresser. Fordel dem på flere kort.')
            unit=house+(', '+' '.join(x for x in (floor,door) if x) if floor or door else '')
            unit=clean_text(unit,100,True)
            a={'id':'import-'+uuid.uuid4().hex,'road':road,'number':house,'postcode':postcode,'floor':floor,'door':door,'count':int(count),'type':typ,'label':road+' '+unit,'numbers':unit}
            if line_only:a['line_only']=True
            if unknown:a['count_unknown']=True
            c['addresses'].append(a);c['lines'].append(line);addresses[address_key]=line
        except (ValueError,TypeError) as error:errors.append({'line':line,**error_payload(error)})
    if not rows[1:]:raise ValueError('Skabelonen indeholder ingen kort endnu.')
    proposed=list(cards.values())
    for c in proposed:
        c['kind']=c['kind'] or 'Ukendt';c['visits']=sum(a['count'] for a in c['addresses'])
        c['visits_unknown']=not c['addresses'] or any(a.get('count_unknown') for a in c['addresses'])
    areas=sorted({norm(c['area']):c['area'] for c in proposed if c['area']}.values(),key=str.casefold)
    payload={'cards':proposed,'errors':errors,'duplicates':duplicates,'addresses':sum(not a.get('line_only') for c in proposed for a in c['addresses']),
        'manual_lines':sum(bool(a.get('line_only')) for c in proposed for a in c['addresses']),
        'register_cards':sum(not c['addresses'] for c in proposed),'unknown_cards':sum(c['visits_unknown'] for c in proposed),
        'visits':sum(c['visits'] for c in proposed),'areas':[{'name':name,'existing':norm(name) in old_areas} for name in areas]}
    return dict(payload,token=store.setup_remember('card-import',payload))

def apply(store,data):
    if data.get('confirm')!='IMPORTÉR KORT':raise ValueError('Skriv IMPORTÉR KORT for at bekræfte oprettelsen.')
    plan=store.setup_require_preview(data,'card-import')
    if plan['errors']:raise ValueError('Ret alle fejl i filen, og lav en ny forhåndsvisning.')
    ids=[];areas={norm(a['name']):a['id'] for a in store.all('settings') if a.get('id')!='config' and not a.get('entity')}
    for c in plan['cards']:
        area=norm(c['area'])
        if area and area not in areas:areas[area]=store._mutate('area.save',{'name':c['area']})['id']
        rows=[dict({k:a[k] for k in ('road','numbers','count','type')},**({'count_unknown':True} if a.get('count_unknown') else {})) for a in c['addresses']]
        ident=store._mutate('card.save',{'number':c['number'],'name':c['name'],'area_id':areas.get(area,''),'kind':c['kind'],'temporary':not rows,'addresses':rows})['id']
        item=dict(store.require('cards',ident),imported_addresses=[a for a in c['addresses'] if not a.get('line_only')],front_revision=bool(rows),back_revision=bool(rows))
        store.put('cards',item);ids.append(ident)
    return {'ids':ids,'count':len(ids),'addresses':plan['addresses'],'visits':plan['visits']}
