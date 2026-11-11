"""Explicit local export. Fixed allowlists; no credential/config-file discovery."""
import base64
import csv
import hashlib
import io
import json
import secrets
import struct
import textwrap
import threading
import time
import zipfile
import zlib
from datetime import date
from pathlib import Path
from resource_paths import templates_dir
from pdf_export import pdf_document, text, s13_pdf, allocation_rows
from sharing import public_members, public_name, png_bytes, fingerprint, qrcode

MAX_IMAGES=100*1024*1024

def safe(value):
    # Keep unsupported characters identifiable; CSV always retains exact UTF-8 text.
    return ''.join(c if c.encode('cp1252','replace')!=b'?' or c=='?' else '[U+%04X]'%ord(c) for c in str(value or ''))

def line(x,y,value,size=9,**options):return text(x,y,safe(value),size,**options)

def csv_file(headers,rows):
    out=io.StringIO(newline='');writer=csv.writer(out,delimiter=';');writer.writerow(headers)
    for row in rows:
        # Excel must not execute user text as formulas. IDs/numbers remain text.
        writer.writerow([("'"+str(v)) if str(v).lstrip().startswith(('=','+','-','@')) else v for v in row])
    return ('\ufeff'+out.getvalue()).encode('utf-8')

def text_pdf(title,groups):
    pages=[]
    for heading,lines in groups:
        commands=[];y=0
        def new_page():
            nonlocal commands,y
            if commands:pages.append(commands)
            commands=[line(40,800,title,15),line(40,776,heading,11)];y=750
        new_page()
        for value in lines or ['Ingen registreringer.']:
            for part in str(value).splitlines() or ['']:
                for wrapped in textwrap.wrap(safe(part),88,replace_whitespace=False) or ['']:
                    if y<45:new_page()
                    commands.append(line(40,y,wrapped));y-=14
        pages.append(commands)
    return pdf_document(pages or [[line(40,800,title,15),line(40,770,'Ingen registreringer.')]])

def png_image(raw):
    """8-bit RGB/RGBA PNG to bounded RGB PDF image, with alpha on white."""
    width,height,depth,kind,_,_,interlace=struct.unpack('>IIBBBBB',raw[16:29])
    if depth!=8 or kind not in (2,6) or interlace:raise ValueError('Ukendt PNG-format.')
    chunks=[];pos=8
    while pos<len(raw):
        n=struct.unpack('>I',raw[pos:pos+4])[0]
        if raw[pos+4:pos+8]==b'IDAT':chunks.append(raw[pos+8:pos+8+n])
        pos+=12+n
    packed=b''.join(chunks)
    if kind==2:return packed,width,height
    channels=4;stride=width*channels
    dec=zlib.decompressobj();pixels=dec.decompress(packed,height*(stride+1)+1)
    if len(pixels)!=height*(stride+1) or not dec.eof or dec.unused_data or dec.unconsumed_tail:raise ValueError('Ugyldige PNG-pixels.')
    previous=bytearray(stride);result=bytearray()
    for y in range(height):
        start=y*(stride+1);f=pixels[start];row=bytearray(pixels[start+1:start+stride+1])
        for x in range(stride):
            a=row[x-channels] if x>=channels else 0;b=previous[x];c=previous[x-channels] if x>=channels else 0
            if f==1:predict=a
            elif f==2:predict=b
            elif f==3:predict=(a+b)//2
            elif f==4:
                p=a+b-c;da,db,dc=abs(p-a),abs(p-b),abs(p-c);predict=a if da<=db and da<=dc else b if db<=dc else c
            elif f==0:predict=0
            else:raise ValueError('Ukendt PNG-filter.')
            row[x]=(row[x]+predict)&255
        result.append(0)
        for x in range(0,stride,4):
            alpha=row[x+3];result.extend((row[x+j]*alpha+255*(255-alpha)+127)//255 for j in range(3))
        previous=row
    return zlib.compress(result),width,height

def image_pdf(images):
    """One self-contained landscape A4 page per rendered public card."""
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b''];kids=[]
    for raw in images:
        packed,w,h=png_image(raw);image_id=len(objects)+1
        objects.append(('<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /DecodeParms << /Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns %d >> /Length %d >>\nstream\n'%(w,h,w,len(packed))).encode()+packed+b'\nendstream')
        page_id=len(objects)+1;content_id=page_id+1;kids.append('%d 0 R'%page_id)
        objects.append(('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 841.89 595.28] /Resources << /XObject << /Im1 %d 0 R >> >> /Contents %d 0 R >>'%(image_id,content_id)).encode())
        commands=b'q 780 0 0 553.091 30 21 cm /Im1 Do Q'
        objects.append(('<< /Length %d >>\nstream\n'%len(commands)).encode()+commands+b'\nendstream')
    objects[1]=('<< /Type /Pages /Kids [%s] /Count %d >>'%(' '.join(kids),len(kids))).encode()
    result=bytearray(b'%PDF-1.4\n');offsets=[0]
    for i,obj in enumerate(objects,1):offsets.append(len(result));result.extend(('%d 0 obj\n'%i).encode()+obj+b'\nendobj\n')
    xref=len(result);result.extend(('xref\n0 %d\n0000000000 65535 f \n'%len(offsets)).encode())
    for n in offsets[1:]:result.extend(('%010d 00000 n \n'%n).encode())
    result.extend(('trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n'%(len(offsets),xref)).encode());return bytes(result)


def tables(state,geo):
    cards=state['cards']+state.get('archived_cards',[]);refs={c['id']:c['number'] for c in cards};people={p['id']:p['name'] for p in state['publishers']};addresses={a['id']:a for a in geo if a.get('entity')=='address'}
    def ref(ident):return refs.get(ident,'')
    result={}
    def add(name,headers,rows):result['CSV/'+name+'.csv']=csv_file(headers,rows)
    add('kort',['kort_id','kortnummer','navn','omraade_id','arkiveret','seneste_gennemgang','type','midlertidig','i_mappen','internt_nummer'],[(c['id'],c['number'],c.get('name',''),c.get('area_id',''),bool(c.get('archived')),c.get('last_completed',''),c.get('kind',''),bool(c.get('temporary')),bool(c.get('in_folder')),c.get('internal_number','')) for c in cards])
    address_rows=[]
    for c in cards:
        members=c.get('geo_addresses') or [addresses[i] for i in c.get('address_ids',[]) if i in addresses]
        for a in members:address_rows.append((c['id'],c['number'],'præcis',a.get('id',''),*[a.get(k,'') for k in ('road','number','floor','door','postcode','count','lng','lat')]))
        if not members:
            for a in c.get('addresses',[]):address_rows.append((c['id'],c['number'],'gemt vejlinje · besøg ukendt' if a.get('count_unknown') else 'gemt vejlinje','',a.get('road',''),a.get('numbers',a.get('from','')),'','','','' if a.get('count_unknown') else a.get('count',''),'',''))
    assigned={a.get('id') for c in cards for a in c.get('geo_addresses',[])}|{i for c in cards for i in c.get('address_ids',[])}
    for a in addresses.values():
        if a['id'] not in assigned:address_rows.append(('','','præcis · uden kort',a['id'],*[a.get(k,'') for k in ('road','number','floor','door','postcode','count','lng','lat')]))
    statuses={a['id']:a for a in addresses.values()};ignored={i.get('address_id') for i in state.get('ignored',[])}
    address_rows=[(*row,statuses.get(row[3],{}).get('type',''),bool(statuses.get(row[3],{}).get('retired')),row[3] in ignored) for row in address_rows]
    add('adresser',['kort_id','kortnummer','grundlag','adresse_id','vej','husnummer_eller_gemt_vejlinje','etage','doer','postnummer','besoegstal','laengdegrad','breddegrad','type','nedlagt','se_bort_fra'],address_rows)
    add('ib',['ib_id','kort_id','kortnummer','adresse_id','vej','nummer','dato'],[(r['id'],r.get('card_id',''),ref(r.get('card_id')),r.get('address_id',''),r.get('road',''),r.get('number',''),r.get('date_text') or r.get('date','')) for r in state['ib']])
    add('udleveringer',['udlaans_id','kort_id','kortnummer','forkynder_id','forkynder','udleveret','aktuel_gennemgang_fra','afleveret'],[(r['id'],r['card_id'],ref(r['card_id']),r['publisher_id'],people.get(r['publisher_id'],''),r['assigned'],r.get('cycle_start',''),r.get('returned','')) for r in state['loans']])
    add('gennemgange',['id','kort_id','kortnummer','dato','forrige_gennemgang','udlaans_id','besoeg','besoeg_ukendt','kilde'],[(r['id'],r['card_id'],ref(r['card_id']),r['date'],r.get('previous_completed',''),r.get('loan_id',''),'' if r.get('visits_unknown') else r.get('visits',''),bool(r.get('visits_unknown')),r.get('source','')) for r in state['completions']])
    add('forkyndere',['id','navn','tjenestegruppe','gruppefunktion','pioner'],[(r['id'],r['name'],r.get('group',''),r.get('group_role',''),bool(r.get('pioneer'))) for r in state['publishers']])
    add('omraader',['id','navn'],[(r['id'],r['name']) for r in state['areas']])
    add('opgaver',['id','kort_id','kortnummer','tekst','oprettet','udfoert','gentagelse','naeste_gang','afslutningshistorik'],[(r['id'],r.get('card_id',''),ref(r.get('card_id')),r.get('text',''),r.get('created',''),bool(r.get('resolved')),json.dumps(r.get('recurrence'),ensure_ascii=False),r.get('recurrence',{}).get('next_due','') if r.get('recurrence') else '',json.dumps(r.get('task_history',[]),ensure_ascii=False)) for r in state['notes']])
    add('ktm_besoeg',['id','dato','bemaerkning'],[(r['id'],r['date'],r.get('note','')) for r in state['visits']])
    add('stamdata',['menighed','opgoerelsesdato'],[(state['settings'].get('congregation',''),state['today'])])
    return result

class SnapshotView:
    """Reuse the public filter against one frozen read, without per-card SQL scans."""
    def __init__(self,state,geo):self.data={**state,'geo':geo,'settings':[state['settings'],*state['areas']]}
    def all(self,module):return self.data.get(module,[])
    def get(self,module,ident):return next((r for r in self.all(module) if r.get('id')==ident),None)

class ReadableExport:
    def __init__(self,store):self.store=store;self.lock=threading.RLock();self.job=None
    def prepare(self):
        with self.lock,self.store.lock:
            state=self.store.state();geo=self.store.all('geo');view=SnapshotView(state,geo);cards=[]
            current={c['id']:c for c in state['cards']};state['public_maps']=[]
            for row in self.store.all('maps'):
                c=current.get(row.get('card_id'));url=row.get('front_url') or row.get('url')
                if c and row.get('entity')=='publication' and row.get('status') in ('published','ready','access_retry','access_failed') and url and fingerprint(view,c)==row.get('fingerprint'):
                    state['public_maps'].append({'card_id':c['id'],'url':url})
            for c in state['cards']+state.get('archived_cards',[]):
                members=public_members(view,c)
                if c.get('geo_polygon') or members:cards.append({'card':{k:c.get(k) for k in ('id','number','geo_polygon','map_color')},'members':members,'name':public_name(view,c)+(' · Arkiveret' if c.get('archived') else '')})
            self.job={'token':secrets.token_hex(24),'revision':state['revision'],'state':state,'geo':geo,'cards':cards,'images':{},'front_images':{},'size':0,'until':time.monotonic()+3600}
            return {**{k:self.job[k] for k in ('token','revision','cards')},'fronts':[c['id'] for c in state['cards']+state.get('archived_cards',[])]}
    def require(self,token):
        job=self.job
        if not job or not secrets.compare_digest(str(token),job['token']) or time.monotonic()>job['until']:raise ValueError('Eksporten er udløbet. Start igen.')
        if self.store.revision!=job['revision']:self.job=None;raise ValueError('Data er ændret. Start eksporten igen for at få én samlet version.')
        return job
    def image(self,data):
        with self.lock,self.store.lock:
            job=self.require(data.get('token'));ident=data.get('card_id')
            front=data.get('side')=='front'
            allowed={c['id'] for c in job['state']['cards']+job['state'].get('archived_cards',[])} if front else {c['card']['id'] for c in job['cards']}
            if ident not in allowed:raise ValueError('Ukendt eksportkort.')
            images=job['front_images'] if front else job['images']
            raw=png_bytes(data.get('png'));old=images.get(ident,b'');size=job['size']-len(old)+len(raw)
            if size>MAX_IMAGES:raise ValueError('Kortbillederne fylder mere end 100 MB. Eksporten er stoppet.')
            images[ident]=raw;job['size']=size;return {'ok':True}
    def finish(self,token):
        with self.lock:
            job=self.require(token)
            if len(job['images'])!=len(job['cards']):raise ValueError('Ikke alle digitale kort er dannet. Ingen eksportpakke er hentet.')
            state=job['state'];files=tables(state,job['geo']);cards=state['cards']+state.get('archived_cards',[]);refs={c['id']:c['number'] for c in cards}
            if len(job['front_images'])!=len(cards):raise ValueError('Ikke alle forsider er dannet. Ingen eksportpakke er hentet.')
            files['PDF/01-alle-forsider.pdf']=image_pdf([job['front_images'][c['id']] for c in cards]) if cards else text_pdf('Forsider',[])
            files['PDF/02-alle-IB-bagsider.pdf']=text_pdf('IB-bagsider',[(str(c['number']),[str(r.get('road',''))+' '+str(r.get('number',''))+' · '+str(r.get('date_text') or r.get('date','')) for r in state['ib'] if r['card_id']==c['id']]) for c in cards])
            files['PDF/03-alle-digitale-kort.pdf']=image_pdf([job['images'][c['card']['id']] for c in job['cards']]) if job['cards'] else text_pdf('Digitale kort',[])
            files['PDF/04-alle-opgaver.pdf']=text_pdf('Alle opgaver',[(('Kort '+refs.get(r.get('card_id'),'')+' · ' if r.get('card_id') else '')+('Udført' if r.get('resolved') else 'Åben'),[r.get('text',''),'Oprettet: '+str(r.get('created','')),'Gentagelse: '+json.dumps(r.get('recurrence'),ensure_ascii=False),'Historik: '+json.dumps(r.get('task_history',[]),ensure_ascii=False)]) for r in state['notes']])
            days=[state['today']]
            for kind,keys in [('cards',('last_completed',)),('archived_cards',('last_completed',)),('loans',('assigned','cycle_start','returned')),('completions',('date','previous_completed'))]:
                days.extend(r.get(k) for r in state.get(kind,[]) for k in keys if r.get(k))
            years=sorted({date.fromisoformat(d).year+(date.fromisoformat(d).month>=9) for d in days})
            for year in range(min(years),max(years)+1):files['S-13/S-13-%d-%d.pdf'%(year-1,year)]=s13_pdf(state,year)
            files['LAES-MIG.txt']=('LTM · lokalt læsearkiv\n\nIndeholder private navne, udlån, IB og opgaver. Opbevar pakken privat.\nPDF: aktive og arkiverede kort, hvor data findes. Forsider på original blank formular, IB pr. kort, digitale kort med indlejret OpenStreetMap samt alle opgaver. Store tekstmængder fortsætter på næste side. Kort uden geografi findes i forsider/CSV, ikke som opdigtede digitale kort.\nS-13: hvert tjenesteår fra ældste gemte dato til nyeste; aktive og arkiverede kort indgår.\nCSV: UTF-8 med semikolon. Præcise adresser bevares; ældre vejlinjer er mærket som vejlinjer. Ingen intervaller opfindes. Tekst der kan opfattes som regnearksformler får en indledende apostrof. CSV bevarer Unicode; tegn udenfor PDF-fontens tegnsæt angives med U+kode i læse-PDF.\nIngen adgangskoder, API-nøgler, forbindelsesfiler, sessionsnøgler eller rå indstillinger er medtaget. Pakken erstatter ikke LTM-sikkerhedskopien og kan ikke gendannes som en backup. Eksporten godkender ikke genprint og ændrer ikke Google-adgang.\n').encode('utf-8')
            files['SHA256SUMS.txt']=''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n' for k,v in sorted(files.items())).encode()
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
                for name,raw in sorted(files.items()):archive.writestr(name,raw)
            with self.store.lock:
                self.require(token)
                self.job=None
            return out.getvalue()
