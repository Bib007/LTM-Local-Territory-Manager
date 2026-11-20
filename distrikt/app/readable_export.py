"""Explicit local export. Fixed allowlists; no credential/config-file discovery."""
import base64
import csv
import hashlib
import io
import json
import secrets
import struct
import tempfile
from xml.etree.ElementTree import Element, SubElement, tostring
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

def write_image_pdf(out, images, count, *, portrait=False):
    """Write one A4 page at a time; IB backs use portrait, maps/fronts landscape."""
    out.write(b'%PDF-1.4\n')
    offsets=[]

    def write(obj):
        offsets.append(out.tell())
        out.write(('%d 0 obj\n'%len(offsets)).encode())
        out.write(obj)
        out.write(b'\nendobj\n')

    write(b'<< /Type /Catalog /Pages 2 0 R >>')
    kids=' '.join('%d 0 R'%(4+3*i) for i in range(count))
    write(('<< /Type /Pages /Kids [%s] /Count %d >>'%(kids,count)).encode())
    for raw in images:
        packed,w,h=png_image(raw)
        image_id=len(offsets)+1
        write(('<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /DecodeParms << /Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns %d >> /Length %d >>\nstream\n'%(w,h,w,len(packed))).encode()+packed+b'\nendstream')
        size='[0 0 595.28 841.89]' if portrait else '[0 0 841.89 595.28]'
        write(('<< /Type /Page /Parent 2 0 R /MediaBox %s /Resources << /XObject << /Im1 %d 0 R >> >> /Contents %d 0 R >>'%(size,image_id,image_id+2)).encode())
        commands=b'q 553.091 0 0 780 21 30 cm /Im1 Do Q' if portrait else b'q 780 0 0 553.091 30 21 cm /Im1 Do Q'
        write(('<< /Length %d >>\nstream\n'%len(commands)).encode()+commands+b'\nendstream')
    xref=out.tell()
    out.write(('xref\n0 %d\n0000000000 65535 f \n'%(len(offsets)+1)).encode())
    for offset in offsets:out.write(('%010d 00000 n \n'%offset).encode())
    out.write(('trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n'%(len(offsets)+1,xref)).encode())


def map_kml(cards):
    document=Element('kml',{'xmlns':'http://www.opengis.net/kml/2.2'})
    root=SubElement(document,'Document')
    SubElement(root,'name').text='LTM distriktskort'
    for item in cards:
        card=item['card']
        folder=SubElement(root,'Folder')
        title=card['number']+' · '+item['name'] if item['name'] else card['number']
        SubElement(folder,'name').text=title
        polygon=card.get('geo_polygon') or []
        if len(polygon)>=3:
            mark=SubElement(folder,'Placemark')
            SubElement(mark,'name').text=title
            ring=SubElement(SubElement(SubElement(mark,'Polygon'),'outerBoundaryIs'),'LinearRing')
            points=[*polygon,polygon[0]] if polygon[-1]!=polygon[0] else polygon
            SubElement(ring,'coordinates').text=' '.join(f'{lng},{lat}' for lng,lat in points)
        for address in item['members']:
            mark=SubElement(folder,'Placemark')
            SubElement(mark,'name').text=' '.join(filter(None,(address['road'],address['number'])))
            SubElement(SubElement(mark,'Point'),'coordinates').text=f"{address['lng']},{address['lat']}"
    return tostring(document,encoding='utf-8',xml_declaration=True)


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
    # Keep current DAR values and local display overrides in separate columns.
    # Also export unmatched manual entries for review after a DAR split/merge.
    front_label_rows=[]
    for c in cards:
        for row in c.get('front_addresses',[]):
            if row.get('extra_road') or row.get('extra_numbers') or row.get('number_style')=='range':
                front_label_rows.append((c['id'],c['number'],'aktiv',','.join(row.get('source_ids',[])),
                    row['road'],row['numbers'],
                    ' – '.join(filter(None,(row['road'],row['extra_road']))),
                    ' – '.join(filter(None,(row.get('display_numbers') or row['numbers'],row['extra_numbers'])))))
        from front_labels import _match
        _,pending=_match(c.get('front_addresses',[]),c.get('front_line_overrides',[]))
        for entry in pending:
                front_label_rows.append((c['id'],c['number'],'afventer gennemgang',
                    ','.join(entry.get('source_ids') or []),entry.get('dar_road',''),
                    entry.get('dar_numbers',''),entry.get('road') or entry.get('dar_road',''),
                    entry.get('numbers') or entry.get('dar_numbers','')))
    add('forsidetekster',['kort_id','kortnummer','status','adresse_ider','dar_vej','dar_numre',
        'vist_vej','viste_numre'],front_label_rows)
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
            self.clear()
            self.job={'temp':tempfile.TemporaryDirectory(prefix='ltm-readable-'),'token':secrets.token_hex(24),'revision':state['revision'],'state':state,'geo':geo,'cards':cards,'images':{},'front_images':{},'back_images':{},'until':time.monotonic()+3600}
            return {**{k:self.job[k] for k in ('token','revision','cards')},'fronts':[c['id'] for c in state['cards']+state.get('archived_cards',[])]}
    def clear(self):
        if self.job:
            job,self.job=self.job,None
            job['temp'].cleanup()
    def cancel(self,token):
        with self.lock:
            if self.job and secrets.compare_digest(str(token),self.job['token']):self.clear()
            return {'ok':True}
    def require(self,token):
        job=self.job
        if job and time.monotonic()>job['until']:self.clear();job=None
        if not job or not secrets.compare_digest(str(token),job['token']):raise ValueError('Eksporten er udløbet. Start igen.')
        if self.store.revision!=job['revision']:self.clear();raise ValueError('Data er ændret. Start eksporten igen for at få én samlet version.')
        return job
    def image(self,data):
        with self.lock,self.store.lock:
            job=self.require(data.get('token'));ident=data.get('card_id')
            side=data.get('side') or 'map'
            if side not in ('front','back','map'):raise ValueError('Ukendt eksportside.')
            allowed={c['id'] for c in job['state']['cards']+job['state'].get('archived_cards',[])} if side in ('front','back') else {c['card']['id'] for c in job['cards']}
            if ident not in allowed:raise ValueError('Ukendt eksportkort.')
            if side=='back':
                page,total=data.get('page'),data.get('pages')
                if type(page) is not int or type(total) is not int or not (1<=total<=256 and 0<=page<total):raise ValueError('Ugyldig IB-side.')
                entry=job['back_images'].setdefault(ident,{'total':total,'images':{}})
                if entry['total']!=total:raise ValueError('IB-sideantallet er ændret. Start eksporten igen.')
                images=entry['images'];key=page
            else:
                images=job['front_images'] if side=='front' else job['images'];key=ident
            raw=png_bytes(data.get('png'))
            target=images.get(key) or Path(job['temp'].name)/(secrets.token_hex(16)+'.png')
            target.write_bytes(raw)
            images[key]=target
            return {'ok':True}
    def finish(self,token,out):
        with self.lock:
            job=self.require(token)
            if len(job['images'])!=len(job['cards']):raise ValueError('Ikke alle digitale kort er dannet. Ingen eksportpakke er hentet.')
            state=job['state'];files=tables(state,job['geo']);cards=state['cards']+state.get('archived_cards',[]);refs={c['id']:c['number'] for c in cards}
            if len(job['front_images'])!=len(cards):raise ValueError('Ikke alle forsider er dannet. Ingen eksportpakke er hentet.')
            backs=job['back_images']
            if len(backs)!=len(cards) or any(c['id'] not in backs or len(backs[c['id']]['images'])!=backs[c['id']]['total'] for c in cards):
                raise ValueError('Ikke alle IB-bagsider er dannet. Ingen eksportpakke er hentet.')
            back_pages=[backs[c['id']]['images'][index] for c in cards for index in range(backs[c['id']]['total'])]
            image_groups=[('PDF/01-alle-forsider.pdf','Forsider',[job['front_images'][c['id']] for c in cards],False),
                ('PDF/02-alle-IB-bagsider.pdf','IB-bagsider',back_pages,True),
                ('PDF/03-alle-digitale-kort.pdf','Digitale kort',[job['images'][c['card']['id']] for c in job['cards']],False)]
            files['PDF/04-alle-opgaver.pdf']=text_pdf('Alle opgaver',[(('Kort '+refs.get(r.get('card_id'),'')+' · ' if r.get('card_id') else '')+('Udført' if r.get('resolved') else 'Åben'),[r.get('text',''),'Oprettet: '+str(r.get('created','')),'Gentagelse: '+json.dumps(r.get('recurrence'),ensure_ascii=False),'Historik: '+json.dumps(r.get('task_history',[]),ensure_ascii=False)]) for r in state['notes']])
            days=[state['today']]
            for kind,keys in [('cards',('last_completed',)),('archived_cards',('last_completed',)),('loans',('assigned','cycle_start','returned')),('completions',('date','previous_completed'))]:
                days.extend(r.get(k) for r in state.get(kind,[]) for k in keys if r.get(k))
            years=sorted({date.fromisoformat(d).year+(date.fromisoformat(d).month>=9) for d in days})
            for year in range(min(years),max(years)+1):files['S-13/S-13-%d-%d.pdf'%(year-1,year)]=s13_pdf(state,year)
            files['LAES-MIG.txt']=('LTM · lokalt læsearkiv\n\nIndeholder private navne, udlån, IB og opgaver. Opbevar pakken privat.\nPDF: aktive og arkiverede kort, hvor data findes. Forsider på original blank formular, IB pr. kort, digitale kort med gemte grænser og adressepunkter samt alle opgaver. Store tekstmængder fortsætter på næste side. Kort uden geografi findes i forsider/CSV, ikke som opdigtede digitale kort.\nKML: gemte geografiske kortgrænser og adressepunkter.\nS-13: hvert tjenesteår fra ældste gemte dato til nyeste; aktive og arkiverede kort indgår.\nCSV: UTF-8 med semikolon. Præcise adresser bevares; ældre vejlinjer er mærket som vejlinjer. Ingen intervaller opfindes. Tekst der kan opfattes som regnearksformler får en indledende apostrof. CSV bevarer Unicode; tegn udenfor PDF-fontens tegnsæt angives med U+kode i læse-PDF.\nIngen adgangskoder, API-nøgler, forbindelsesfiler, sessionsnøgler eller rå indstillinger er medtaget. Pakken erstatter ikke LTM-sikkerhedskopien og kan ikke gendannes som en backup. Eksporten godkender ikke genprint og ændrer ikke Google-adgang.\n').encode('utf-8')
            files['KML/distriktskort.kml']=map_kml(job['cards'])
            checksums={}
            with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
                for name,raw in sorted(files.items()):
                    archive.writestr(name,raw)
                    checksums[name]=hashlib.sha256(raw).hexdigest()
                for name,title,images,portrait in image_groups:
                    if not images:
                        raw=text_pdf(title,[])
                        archive.writestr(name,raw)
                        checksums[name]=hashlib.sha256(raw).hexdigest()
                        continue
                    with tempfile.TemporaryFile() as pdf:
                        if portrait:write_image_pdf(pdf,(path.read_bytes() for path in images),len(images),portrait=True)
                        else:write_image_pdf(pdf,(path.read_bytes() for path in images),len(images))
                        pdf.seek(0)
                        digest=hashlib.sha256()
                        with archive.open(name,'w',force_zip64=True) as entry:
                            for chunk in iter(lambda:pdf.read(1024*1024),b''):
                                digest.update(chunk)
                                entry.write(chunk)
                        checksums[name]=digest.hexdigest()
                archive.writestr('SHA256SUMS.txt',''.join(value+'  '+name+'\n' for name,value in sorted(checksums.items())))
            with self.store.lock:
                self.require(token)
                self.clear()
