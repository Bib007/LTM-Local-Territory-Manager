"""Local IB values only. Incomplete rows never invent geographic addresses."""
from collections import defaultdict
from datetime import date
import io
import re
import zipfile
from xml.sax.saxutils import escape
from card_import import read_rows,norm
from ui_errors import error_payload

HEADERS=['kortnummer','vejnavn','husnummer','postnummer','etage','dør','dato']
FIELDS=['card','road','number','postcode','floor','door','date']
ALIASES=dict(zip(HEADERS,FIELDS));ALIASES.update({key:key for key in FIELDS})
ALIASES.update(husnr='number',postnr='postcode',doer='door')


def template_xlsx():
    """Blank text cells preserve leading zeroes; no formulas, links or data."""
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    rows=['<row r="1">'+''.join('<c r="'+chr(65+i)+'1" t="inlineStr"><is><t>'+escape(h)+'</t></is></c>' for i,h in enumerate(HEADERS))+'</row>']
    parts={
      '[Content_Types].xml':'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
      '_rels/.rels':'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
      'xl/workbook.xml':'<workbook xmlns="'+ns+'" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="IB" sheetId="1" r:id="rId1"/></sheets></workbook>',
      'xl/_rels/workbook.xml.rels':'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>',
      'xl/styles.xml':'<styleSheet xmlns="'+ns+'"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="49" applyNumberFormat="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>',
      'xl/worksheets/sheet1.xml':'<worksheet xmlns="'+ns+'"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols><col min="1" max="7" width="22" customWidth="1" style="1"/></cols><sheetData>'+''.join(rows)+'</sheetData><autoFilter ref="A1:G1"/></worksheet>'}
    target=io.BytesIO()
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for path,text in sorted(parts.items()):
            entry=zipfile.ZipInfo(path,date_time=(2026,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(entry,'<?xml version="1.0" encoding="UTF-8"?>'+text)
    return target.getvalue()


def unit(row):return row['number']+(', '+' '.join(row.get(k,'') for k in ('floor','door') if row.get(k)) if row.get('floor') or row.get('door') else '')


def preview(store,data):
    from store import valid_day,clean_text
    source=read_rows({**data,'name':data.get('name') or 'ib.csv'},sheet_name='IB')
    if not source:raise ValueError('Importfilen mangler kolonneoverskrifter.')
    fields=[ALIASES.get(norm(header)) for header in source[0][1]]
    known=[key for key in fields if key]
    if len(known)!=len(set(known)) or not {'road','number'}<=set(known):
        raise ValueError('Brug én kolonne til vejnavn og én til husnummer. Kolonner må ikke gentages.')
    missing_columns=[name for name,key in zip(HEADERS,FIELDS) if key not in known]
    ignored_columns=[str(header)[:250] for header,key in zip(source[0][1],fields) if not key and str(header).strip()]
    default_day=valid_day(data.get('date') or date.today().isoformat())
    cards=[c for c in store.all('cards') if not c.get('archived')]
    by_number={norm(c['number']):c for c in cards};by_id={c['id']:c for c in cards}
    fallback=data.get('card_id') or ''
    if fallback and fallback not in by_id:raise ValueError('Vælg et eksisterende standardkort.')
    lookup=defaultdict(list)
    for c in cards:
        for a in c.get('geo_addresses') or c.get('imported_addresses') or [store.get('geo',i) for i in c.get('address_ids',[])]:
            if a:lookup[(norm(a['road']),norm(a['number']),str(a['postcode']),norm(a.get('floor')),norm(a.get('door')))].append((c,a))
    existing=store.all('ib');seen=set();rows=[]
    for line,values in source[1:]:
        if len(rows)>=5000:raise ValueError('Importfilen må højst indeholde 5.000 linjer.')
        row={'line':line,'status':'error','warnings':[]}
        try:
            if len(values)>len(fields) and any(str(v).strip() for v in values[len(fields):]):raise ValueError('Linjen har flere værdier end kolonneoverskrifter.')
            values=list(values)+['']*max(0,len(fields)-len(values))
            v={key:str(value).strip() for key,value in zip(fields,values) if key}
            if any(len(value)>250 for value in v.values()):raise ValueError('Et felt er for langt.')
            road=clean_text(v.get('road'),120,True);number=clean_text(unit({'number':v.get('number',''),'floor':v.get('floor',''),'door':v.get('door','')}),80,True)
            if not v.get('number'):raise ValueError('Husnummer mangler. Ret linjen før import.')
            postcode=v.get('postcode','')
            if postcode and not re.fullmatch(r'\d{4}',postcode):raise ValueError('Postnummer skal være fire cifre eller stå tomt med en synlig advarsel.')
            requested=norm(v.get('card'))
            if requested and requested not in by_number:raise ValueError('Kortnummeret findes ikke.')
            chosen=by_number[requested] if requested else by_id.get(fallback)
            candidates=lookup.get((norm(road),norm(v['number']),postcode,norm(v.get('floor')),norm(v.get('door'))),[]) if postcode else []
            if chosen:candidates=[(c,a) for c,a in candidates if c['id']==chosen['id']]
            if len(candidates)==1:
                c,a=candidates[0];record={'card_id':c['id'],'address_id':a['id'],'road':a['road'],'number':unit(a),'postcode':postcode}
            else:
                if not chosen:raise ValueError('Intet entydigt adressematch. Angiv kortnummer i filen, eller vælg et standardkort til manuelle linjer.')
                c=chosen;record={'card_id':c['id'],'road':road,'number':number,'postcode':postcode}
                row['warnings'].append('Manuel IB-linje på det valgte kort. Adressen er ikke knyttet til en geografisk adresse; kontrollér vej, husnummer og lejlighed.')
            if not postcode:row['warnings'].append('Postnummer mangler. Der gættes ikke et postnummer.');record['missing_fields']=['postcode']
            record['date']=valid_day(v.get('date') or default_day)
            key=(c['id'],norm(record['road']),norm(record['number']))
            duplicate=key in seen or any(i['card_id']==c['id'] and (record.get('address_id') and i.get('address_id')==record['address_id'] or norm(i['road'])==key[1] and norm(i['number'])==key[2]) for i in existing)
            row.update(status='existing' if duplicate else 'new',card_number=c['number'],label=record['road']+' '+record['number'],date=record['date'],record=record)
            seen.add(key)
        except (ValueError,TypeError,KeyError) as error:row.update(error_payload(error))
        rows.append(row)
    if not rows:raise ValueError('Importfilen indeholder ingen IB-linjer. Udfyld skabelonen først.')
    return {'rows':rows,'new':sum(r['status']=='new' for r in rows),'existing':sum(r['status']=='existing' for r in rows),
        'errors':sum(r['status']=='error' for r in rows),'warnings':sum(bool(r['warnings']) and r['status']=='new' for r in rows),
        'missing_columns':missing_columns,'ignored_columns':ignored_columns}
