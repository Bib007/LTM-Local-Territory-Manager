"""Local XLSX/CSV card imports. Preview has no database writes or network calls."""
import base64
import binascii
import csv
import io
import posixpath
import re
import uuid
import zipfile
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

def xlsx_rows(raw,sheet_name='Distriktskort'):
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
            chosen=next((s for s in sheets if s.get('name')==sheet_name),None)
            if chosen is None:
                if len(sheets)!=1:raise ValueError('Brug skabelonens fane '+sheet_name+', eller gem som CSV.')
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
            rows=[]
            for row in xml(sheetpath).findall('s:sheetData/s:row',NS):
                cells={}
                for cell in row.findall('s:c',NS):
                    ref=cell.get('r','');match=re.fullmatch(r'([A-Z]{1,3})([1-9]\d*)',ref)
                    if not match:raise ValueError('En cellereference er ugyldig.')
                    col=0
                    for letter in match[1]:col=col*26+ord(letter)-64
                    if cell.find('s:f',NS) is not None:raise ValueError('Formler understøttes ikke. Indsæt som værdier, og prøv igen.')
                    value=cell.findtext('s:v','',NS);kind=cell.get('t')
                    if kind=='inlineStr':value=''.join(t.text or '' for t in cell.findall('.//s:t',NS))
                    elif kind=='s':
                        try:
                            index=int(value)
                            if index<0 or index>=len(strings):raise IndexError()
                            value=strings[index]
                        except (ValueError,IndexError):raise ValueError('En tekstcelle kunne ikke læses.') from None
                    elif kind in ('e','b','d'):raise ValueError('Brug almindelig tekst eller tal i importfelterne.')
                    if len(value)>250:raise ValueError('Et felt er for langt (højst 250 tegn).')
                    if value:
                        if col>40:raise ValueError('Filen indeholder for mange kolonner. Brug skabelonen.')
                        if col in cells:raise ValueError('En celle er gentaget i regnearket.')
                        cells[col]=value
                if cells:rows.append((int(row.get('r') or match[2]),[cells.get(i,'') for i in range(1,max(cells)+1)]))
                if len(rows)>10001:raise ValueError('Importfilen må højst indeholde 10.000 adresser.')
            return rows
    except (zipfile.BadZipFile,KeyError,ET.ParseError,RuntimeError,OverflowError) as error:
        raise ValueError('XLSX-filen kunne ikke læses. Gem som .xlsx eller CSV fra skabelonen.') from error

def read_rows(data,sheet_name='Distriktskort'):
    filename=str(data.get('name','')).lower()
    if filename.endswith('.xlsx'):
        encoded=data.get('content','')
        if not isinstance(encoded,str) or len(encoded)>4*((MAX_BYTES+2)//3):raise ValueError('Filen må højst fylde 2 MB.')
        try:raw=base64.b64decode(encoded,validate=True)
        except (ValueError,binascii.Error):raise ValueError('Regnearket kunne ikke afkodes.') from None
        if len(raw)>MAX_BYTES:raise ValueError('Filen må højst fylde 2 MB.')
        return xlsx_rows(raw,sheet_name)
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
    rows=read_rows(data)
    if not rows:raise ValueError('Filen er tom. Udfyld skabelonen først.')
    fields=[ALIASES.get(norm(x)) for x in rows[0][1]]
    if any(not x for x in fields) or len(set(fields))!=len(fields) or not {'card','road','number','postcode'}.issubset(fields):
        raise ValueError('Brug skabelonens kolonneoverskrifter. Kortnummer, vejnavn, husnummer og postnummer er påkrævet.')
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
                if c[field] and norm(c[field])!=norm(val):raise ValueError('Samme kort har forskellige oplysninger i kolonnen '+{'area':'område','name':'kortnavn','kind':'distriktstype'}[field]+'.')
                c[field]=val
            if norm(c['area']) in removed_areas and norm(c['area']) not in old_areas:raise ValueError('Området findes i Gendan ved fejl. Gendan eller omdøb det først.')
            road=clean_text(v.get('road'),120,True);house=clean_text(v.get('number'),30,True)
            if not re.fullmatch(r'\d+[A-Za-zÆØÅæøå]?',house):raise ValueError('Angiv ét husnummer, fx 12A. Brug én række pr. adresse, uden intervaller.')
            postcode=v.get('postcode','')
            if not re.fullmatch(r'\d{4}',postcode):raise ValueError('Postnummeret skal have fire cifre.')
            floor=clean_text(v.get('floor'),20);door=clean_text(v.get('door'),30)
            typ=v.get('type') or 'Hus'
            if typ not in ADDRESS_TYPES:raise ValueError('Vælg en adressetype fra skabelonen.')
            count=v.get('count') or '1'
            if not re.fullmatch(r'\d+',count) or not 1<=int(count)<=10000:raise ValueError('Besøg skal være et helt tal fra 1 til 10.000.')
            address_key=tuple(norm(x) for x in (postcode,road,house,floor,door))
            if address_key in occupied:raise ValueError('Adressen findes allerede på et eksisterende kort eller i gendannelse.')
            if address_key in addresses:
                duplicates+=1
                raise ValueError('Adressen er gentaget i filen (først på linje '+str(addresses[address_key])+').')
            if len(c['addresses'])>=300:raise ValueError('Kortet har over 300 adresser. Fordel dem på flere kort.')
            unit=house+(', '+' '.join(x for x in (floor,door) if x) if floor or door else '')
            a={'id':'import-'+uuid.uuid4().hex,'road':road,'number':house,'postcode':postcode,'floor':floor,'door':door,'count':int(count),'type':typ,'label':road+' '+unit,'numbers':unit}
            c['addresses'].append(a);c['lines'].append(line);addresses[address_key]=line
        except (ValueError,TypeError) as error:errors.append({'line':line,'error':str(error)})
    if not rows[1:]:raise ValueError('Skabelonen indeholder ingen adresser endnu.')
    proposed=list(cards.values())
    for c in proposed:c['kind']=c['kind'] or 'Ukendt';c['visits']=sum(a['count'] for a in c['addresses'])
    areas=sorted({norm(c['area']):c['area'] for c in proposed if c['area']}.values(),key=str.casefold)
    payload={'cards':proposed,'errors':errors,'duplicates':duplicates,'addresses':sum(len(c['addresses']) for c in proposed),'visits':sum(c['visits'] for c in proposed),'areas':[{'name':name,'existing':norm(name) in old_areas} for name in areas]}
    return dict(payload,token=store.setup_remember('card-import',payload))

def apply(store,data):
    if data.get('confirm')!='IMPORTÉR KORT':raise ValueError('Skriv IMPORTÉR KORT for at bekræfte oprettelsen.')
    plan=store.setup_require_preview(data,'card-import')
    if plan['errors']:raise ValueError('Ret alle fejl i filen, og lav en ny forhåndsvisning.')
    ids=[];areas={norm(a['name']):a['id'] for a in store.all('settings') if a.get('id')!='config' and not a.get('entity')}
    for c in plan['cards']:
        area=norm(c['area'])
        if area and area not in areas:areas[area]=store._mutate('area.save',{'name':c['area']})['id']
        rows=[{k:a[k] for k in ('road','numbers','count','type')} for a in c['addresses']]
        ident=store._mutate('card.save',{'number':c['number'],'name':c['name'],'area_id':areas.get(area,''),'kind':c['kind'],'temporary':False,'addresses':rows})['id']
        item=dict(store.require('cards',ident),imported_addresses=c['addresses'],front_revision=True,back_revision=True)
        store.put('cards',item);ids.append(ident)
    return {'ids':ids,'count':len(ids),'addresses':plan['addresses'],'visits':plan['visits']}
