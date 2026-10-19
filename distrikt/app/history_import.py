"""Reviewed local history imports. Existing loans are never overwritten."""
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
FULL_HEADERS=HEADERS+['forkynder','udleveret','afleveret']

def template_csv():return ('\ufeff'+';'.join(HEADERS)+'\r\n').encode('utf-8')
def norm(value):return str(value or '').strip().casefold()

def csv_text(rows,headers=HEADERS):
    stream=io.StringIO();writer=csv.writer(stream,delimiter=';');writer.writerow(headers);writer.writerows(rows)
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
        records=parsed.get('records',[])
        return csv_text(records,FULL_HEADERS) if any(any(r[2:]) for r in records) else csv_text(parsed['rows'])
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
    if not raw or [norm(v) for v in raw[0]] not in (HEADERS,['card','date'],FULL_HEADERS,['card','date','publisher','assigned','returned']):raise ValueError('Brug kortnummer og dato, eventuelt med forkynder, udleveret og afleveret som kolonner.')
    if len(raw)>10001:raise ValueError('Importér højst 10.000 gennemgange ad gangen.')
    cards={}
    for card in store.all('cards'):cards.setdefault(norm(card['number']),[]).append(card)
    entries=store.all('completions');known={(e['card_id'],e['date']) for e in entries}
    known.update((e['card_id'],e['previous_completed']) for e in entries if e.get('previous_completed'))
    known.update((c['id'],c['last_completed']) for group in cards.values() for c in group if c.get('last_completed'))
    recovery={(e['card_id'],e['date']) for e in store.all('completions',deleted=True)}
    from history_loans import LoanPreview
    today=date.today().isoformat();cutoff=store.history_cutoff();rows=[];seen=set();ready={};plain_rows={};allocations=LoanPreview(store,today,cutoff)
    def parsed_day(value):
        try:return day(value)
        except (ValueError,TypeError):raise ValueError('Datoen er ugyldig.') from None
    for line,values in enumerate(raw[1:],2):
        if not any(v.strip() for v in values):continue
        row={'line':line,'number':values[0].strip()[:100],'date':values[1].strip()[:100] if len(values)>1 else '', 'status':'error','message':''}
        try:
            if len(values)!=len(raw[0]) or any(len(v)>100 for v in values):raise ValueError('Rækkens felter skal følge skabelonen og være højst 100 tegn.')
            values=[v.strip() for v in values]+(['','',''] if len(values)==2 else [])
            matches=cards.get(norm(values[0]),[])
            if len(matches)!=1:raise ValueError('Kortnummeret mangler eller er ikke entydigt. Opret eller ret kortet først.')
            card=matches[0];row['archived']=bool(card.get('archived'))
            if any(values[2:]):
                if values[1]:raise ValueError('Brug enten dato for en løs gennemgang eller felterne forkynder, udleveret og afleveret.')
                row.update(kind='loan',publisher=values[2],assigned=values[3],returned=values[4])
                allocations.add(row,card,values[2],parsed_day(values[3]) if values[3] else None,parsed_day(values[4]) if values[4] else None)
                rows.append(row);continue
            stamp=parsed_day(values[1]);row.update(date=stamp,kind='completion')
            key=(card['id'],stamp)
            if key in recovery:raise ValueError('Gennemgangen findes i Gendan ved fejl. Gendan eller fjern den dér først.')
            if stamp>today:raise ValueError('Datoen ligger i fremtiden.')
            if stamp<cutoff:row.update(status='outside',message='Ældre end to år; medtages ikke.')
            elif key in known or key in seen:row.update(status='duplicate',message='Allerede kendt eller gentaget; medtages ikke.')
            else:
                row['status']='ready';ready[key]={'card_id':card['id'],'date':stamp};plain_rows[key]=row
            seen.add(key)
        except (ValueError,TypeError) as error:
            row['message']=str(error)
        rows.append(row)
    if not rows:raise ValueError('Skabelonen indeholder ingen gennemgange endnu.')
    for key,event in allocations.events.items():
        if key in plain_rows:plain_rows[key].update(status='duplicate',message='Gennemgangen medtages sammen med udleveringen.')
        ready[key]=event
    allocation_plan=allocations.payload()
    payload={'rows':rows,'entries':list(ready.values()),'allocation_plan':allocation_plan,'revision':store.revision,'cutoff':cutoff,'today':today}
    token=store.setup_remember('history-import',payload)
    return {'token':token,'rows':rows,'csv':text,'count':len(ready),'loan_count':len(allocation_plan['loans']),'publisher_count':len(allocation_plan['publishers']),'linked_count':len(allocation_plan['links']),'errors':sum(r['status']=='error' for r in rows),'cutoff':cutoff,'today':today}

def apply(store,data):
    if data.get('confirm')!='IMPORTÉR HISTORIK':raise ValueError('Skriv IMPORTÉR HISTORIK for at fortsætte.')
    plan=store.setup_require_preview(data,'history-import')
    if plan['revision']!=store.revision or plan['today']!=date.today().isoformat():raise ValueError('Historikken er ændret. Kontrollér importen igen.')
    if any(r['status']=='error' for r in plan['rows']):raise ValueError('Ret alle fejl, og kontrollér importen igen.')
    allocation_plan=plan['allocation_plan']
    if not plan['entries'] and not allocation_plan['loans'] and not allocation_plan['links']:raise ValueError('Der er ingen nye gennemgange eller udlån at importere.')
    from history_loans import apply_loans
    apply_loans(store,allocation_plan)
    dates={}
    for e in store.all('completions'):
        dates.setdefault(e['card_id'],set()).update(d for d in (e.get('date'),e.get('previous_completed')) if d)
    for c in store.all('cards'):
        if c.get('last_completed'):dates.setdefault(c['id'],set()).add(c['last_completed'])
    for e in sorted(plan['entries'],key=lambda e:e['date']):
        card=dict(store.require('cards',e['card_id']));earlier=[d for d in dates.get(card['id'],set()) if d<e['date']]
        store.put('completions',{'id':uuid.uuid4().hex,'card_id':card['id'],'date':e['date'],'loan_id':e.get('loan_id'),'assigned':e.get('assigned'),'previous_completed':max(earlier,default=None),'visits':0,'visits_unknown':True,'source':'history-import'})
        dates.setdefault(card['id'],set()).add(e['date'])
        if not card.get('last_completed') or e['date']>card['last_completed']:
            card['last_completed']=e['date'];store.put('cards',card)
    return {'count':len(plan['entries']),'loans':len(allocation_plan['loans']),'publishers':len(allocation_plan['publishers']),'linked':len(allocation_plan['links'])}
