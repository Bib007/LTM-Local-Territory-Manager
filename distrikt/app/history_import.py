"""Reviewed local completion imports. No allocation or existing record is rewritten."""
import base64
import binascii
import csv
import io
import json
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

MAX_BYTES=2000000
HEADERS=['kortnummer','dato']

def template_csv():return ('\ufeff'+';'.join(HEADERS)+'\r\n').encode('utf-8')
def norm(value):return str(value or '').strip().casefold()

def csv_text(rows):
    stream=io.StringIO();writer=csv.writer(stream,delimiter=';');writer.writerow(HEADERS);writer.writerows(rows)
    return stream.getvalue()

def source(data):
    name=str(data.get('name','historik.csv')).lower();content=data.get('content','')
    if not isinstance(content,str):raise ValueError('Importfilen kunne ikke læses.')
    if name.endswith('.pdf'):
        if len(content)>4*((MAX_BYTES+2)//3):raise ValueError('Filen må højst fylde 2 MB.')
        try:raw=base64.b64decode(content,validate=True)
        except (ValueError,binascii.Error):raise ValueError('PDF-filen kunne ikke læses.') from None
        if len(raw)>MAX_BYTES:raise ValueError('Filen må højst fylde 2 MB.')
        try:
            run=subprocess.run([sys.executable,'-I','-S',str(Path(__file__).with_name('s13_reader.py'))],input=raw,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=15,check=True)
            parsed=json.loads(run.stdout)
        except (subprocess.SubprocessError,ValueError,OSError):raise ValueError('PDF-filen kunne ikke aflæses lokalt. Brug CSV-skabelonen.') from None
        if parsed.get('error'):raise ValueError(parsed['error'])
        return csv_text(parsed['rows'])
    if not name.endswith('.csv'):raise ValueError('Vælg CSV eller en digital S-13 PDF. Scanninger og fotos kræver manuel indtastning i skabelonen.')
    if len(content.encode('utf-8'))>MAX_BYTES:raise ValueError('Filen må højst fylde 2 MB.')
    return content.lstrip('\ufeff')

def day(value):
    value=value.strip()
    if len(value)==10 and value[4:5]=='-' and value[7:8]=='-':return date.fromisoformat(value).isoformat()
    import re
    match=re.fullmatch(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4}|\d{2})',value)
    if not match:raise ValueError('Brug ÅÅÅÅ-MM-DD eller DD.MM.ÅÅÅÅ i dato.')
    d,m,y=map(int,match.groups());y=y+2000 if y<100 else y
    return date(y,m,d).isoformat()

def preview(store,data):
    text=source(data);first=text.split('\n',1)[0];delimiter=';' if first.count(';')>=first.count(',') else ','
    try:raw=list(csv.reader(io.StringIO(text),delimiter=delimiter,strict=True))
    except csv.Error:raise ValueError('CSV-filen kunne ikke læses. Brug kortnummer og dato som kolonner.') from None
    if not raw or [norm(v) for v in raw[0]] not in (HEADERS,['card','date']):raise ValueError('Brug kortnummer og dato som kolonner.')
    if len(raw)>10001:raise ValueError('Importér højst 10.000 gennemgange ad gangen.')
    cards={}
    for card in store.all('cards'):cards.setdefault(norm(card['number']),[]).append(card)
    entries=store.all('completions');known={(e['card_id'],e['date']) for e in entries}
    known.update((e['card_id'],e['previous_completed']) for e in entries if e.get('previous_completed'))
    known.update((c['id'],c['last_completed']) for group in cards.values() for c in group if c.get('last_completed'))
    recovery={(e['card_id'],e['date']) for e in store.all('completions',deleted=True)}
    today=date.today().isoformat();cutoff=store.history_cutoff();rows=[];seen=set();ready=[]
    for line,values in enumerate(raw[1:],2):
        if not any(v.strip() for v in values):continue
        row={'line':line,'number':values[0].strip()[:100],'date':values[1].strip()[:100] if len(values)>1 else '', 'status':'error','message':''}
        try:
            if len(values)!=2 or any(len(v)>100 for v in values):raise ValueError('Hver række skal have ét kortnummer og én dato.')
            matches=cards.get(norm(values[0]),[])
            if len(matches)!=1:raise ValueError('Kortnummeret mangler eller er ikke entydigt. Opret eller ret kortet først.')
            card=matches[0];stamp=day(values[1]);row.update(date=stamp,archived=bool(card.get('archived')))
            key=(card['id'],stamp)
            if key in recovery:raise ValueError('Gennemgangen findes i Gendan ved fejl. Gendan eller fjern den dér først.')
            if stamp>today:raise ValueError('Datoen ligger i fremtiden.')
            if stamp<cutoff:row.update(status='outside',message='Ældre end to år; medtages ikke.')
            elif key in known or key in seen:row.update(status='duplicate',message='Allerede kendt eller gentaget; medtages ikke.')
            else:
                row['status']='ready';ready.append({'card_id':card['id'],'date':stamp})
            seen.add(key)
        except (ValueError,TypeError) as error:
            message=str(error);row['message']=message if message.startswith(('Brug ','Hver ','Kort','Gennemgangen','Datoen')) else 'Datoen er ugyldig.'
        rows.append(row)
    if not rows:raise ValueError('Skabelonen indeholder ingen gennemgange endnu.')
    payload={'rows':rows,'entries':ready,'revision':store.revision,'cutoff':cutoff,'today':today}
    token=store.setup_remember('history-import',payload)
    return {'token':token,'rows':rows,'csv':text,'count':len(ready),'errors':sum(r['status']=='error' for r in rows),'cutoff':cutoff,'today':today}

def apply(store,data):
    if data.get('confirm')!='IMPORTÉR HISTORIK':raise ValueError('Skriv IMPORTÉR HISTORIK for at fortsætte.')
    plan=store.setup_require_preview(data,'history-import')
    if plan['revision']!=store.revision or plan['today']!=date.today().isoformat():raise ValueError('Historikken er ændret. Kontrollér importen igen.')
    if any(r['status']=='error' for r in plan['rows']):raise ValueError('Ret alle fejl, og kontrollér importen igen.')
    if not plan['entries']:raise ValueError('Der er ingen nye gennemgange at importere.')
    dates={}
    for e in store.all('completions'):
        dates.setdefault(e['card_id'],set()).update(d for d in (e.get('date'),e.get('previous_completed')) if d)
    for c in store.all('cards'):
        if c.get('last_completed'):dates.setdefault(c['id'],set()).add(c['last_completed'])
    for e in sorted(plan['entries'],key=lambda e:e['date']):
        card=dict(store.require('cards',e['card_id']));earlier=[d for d in dates.get(card['id'],set()) if d<e['date']]
        store.put('completions',{'id':uuid.uuid4().hex,'card_id':card['id'],'date':e['date'],'loan_id':None,'assigned':None,'previous_completed':max(earlier,default=None),'visits':0,'visits_unknown':True,'source':'history-import'})
        dates.setdefault(card['id'],set()).add(e['date'])
        if not card.get('last_completed') or e['date']>card['last_completed']:
            card['last_completed']=e['date'];store.put('cards',card)
    return {'count':len(plan['entries'])}
