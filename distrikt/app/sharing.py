"""Only explicitly prepared public files are sent to Google Drive; never the database."""
import base64
import hashlib
import io
import json
import os
import re
import struct
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path
from access import write_private
from publication_dates import ApprovedImages,dates,date_key,render as render_dates
from pdf_export import shared_card_pdf
from resource_paths import vendor_dir
sys.path.insert(0,str(vendor_dir()))
import qrcode

SCOPE='https://www.googleapis.com/auth/drive.file'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args):return None

def request(url,data=None,headers=None,method=None):
    req=urllib.request.Request(url,data=data,headers=headers or {},method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=30) as r:return json.load(r) if r.status!=204 else {}
    except urllib.error.HTTPError as e:
        if e.code in (401,403):raise ValueError('Google afviste adgangen. Kontrollér kontoen og forbind Google igen.') from None
        raise ValueError('Google svarede med HTTP '+str(e.code)+'. Prøv igen senere.') from None
    except (urllib.error.URLError,TimeoutError,OSError):raise ValueError('Ingen forbindelse til Google. Upload forsøges igen senere.') from None

class Drive:
    def __init__(self,root):self.path=Path(root)/'drive-auth.json';self.access='';self.expires=0;self.lock=threading.RLock()
    def connected(self):return self.path.exists()
    def token(self):
        with self.lock:
            if time.monotonic()<self.expires:return self.access
            if not self.connected():raise ValueError('Forbind Google Drive under Indstillinger → Forbindelser først.')
            config=json.loads(self.path.read_text())
            data=urllib.parse.urlencode({k:config[k] for k in ('client_id','client_secret','refresh_token')}|{'grant_type':'refresh_token'}).encode()
            result=request('https://oauth2.googleapis.com/token',data,{'Content-Type':'application/x-www-form-urlencoded'})
            self.access=result['access_token'];self.expires=time.monotonic()+min(int(result.get('expires_in',3600)),3600)-60
            return self.access
    def api(self,path,data=None,method=None,content_type='application/json',upload=False):
        if not path.startswith('/') or '://' in path:raise ValueError('Ugyldig Google-handling.')
        body=json.dumps(data).encode() if isinstance(data,dict) else data
        return request(('https://www.googleapis.com/upload/drive/v3' if upload else 'https://www.googleapis.com/drive/v3')+path,body,{'Authorization':'Bearer '+self.token(),'Content-Type':content_type},method)
    def connect(self,config):
        if not isinstance(config,dict):raise ValueError('Vælg forbindelsesfilen fra Google-guiden.')
        wanted={k:config.get(k) for k in ('client_id','client_secret','refresh_token')}
        if any(not isinstance(v,str) or not v or len(v)>8192 for v in wanted.values()) or not wanted['client_id'].endswith('.apps.googleusercontent.com'):raise ValueError('Ugyldig Google-forbindelsesfil.')
        # Validate the new connection before replacing a working one.
        data=urllib.parse.urlencode(dict(wanted,grant_type='refresh_token')).encode()
        result=request('https://oauth2.googleapis.com/token',data,{'Content-Type':'application/x-www-form-urlencoded'})
        scopes=result.get('scope','').split()
        if scopes and scopes!=[SCOPE]:raise ValueError('Forbindelsen skal kun bruge drive.file-adgang. Kør den medfølgende Google-guide.')
        token=result['access_token']
        info=request('https://www.googleapis.com/drive/v3/about?fields=user(displayName,emailAddress)',headers={'Authorization':'Bearer '+token})
        wanted['account']=info.get('user',{}).get('emailAddress','')
        with self.lock:write_private(self.path,wanted);self.access=token;self.expires=time.monotonic()+min(int(result.get('expires_in',3600)),3600)-60
        return self.status()
    def status(self):
        with self.lock:
            value=json.loads(self.path.read_text()) if self.connected() else {}
            return {'connected':bool(value),'account':value.get('account','')}
    def disconnect(self):
        with self.lock:self.path.unlink(missing_ok=True);self.access='';self.expires=0
    @staticmethod
    def valid_id(file_id):
        if not isinstance(file_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{5,200}',file_id):raise ValueError('Ugyldigt Google-filnummer.')

    def upload(self,png,file_id=None):
        if not file_id:
            created=self.api('/files?fields=id',{'name':'Distriktskort-'+os.urandom(6).hex()+'.png','mimeType':'image/png','description':'Offentligt kortbillede. Ingen IB, noter, navne eller kontooplysninger.'},'POST')
            file_id=created['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]{5,200}',file_id):raise ValueError('Ugyldigt Google-filnummer.')
        self.api('/files/'+file_id+'?uploadType=media',png,'PATCH','image/png',True)
        return file_id
    def upload_pdf(self,pdf,number,file_id=None):
        if file_id:
            self.valid_id(file_id)
        mime='application/pdf'
        safe_number=re.sub(r'[^A-Za-z0-9_-]+','-',str(number)).strip('-') or 'kort'
        metadata={'name':'Distriktskort-'+safe_number+'.pdf','mimeType':mime,
                  'description':'Offentligt distriktskort. Digitalt kort og printforside.'}
        boundary='ltm-'+os.urandom(18).hex()
        part=('--'+boundary+'\r\n').encode()
        body=(part+b'Content-Type: application/json; charset=UTF-8\r\n\r\n'
              +json.dumps(metadata).encode()+b'\r\n'
              +part+b'Content-Type: application/pdf\r\n\r\n'
              +pdf+('\r\n--'+boundary+'--\r\n').encode())
        path='/files'+('/'+file_id if file_id else '')+'?uploadType=multipart&fields=id,mimeType'
        result=self.api(path,body,'PATCH' if file_id else 'POST',
                        'multipart/related; boundary='+boundary,True)
        ident=result.get('id')
        self.valid_id(ident)
        if result.get('mimeType')!=mime or (file_id and ident!=file_id):
            raise ValueError('Google bekræftede ikke kortet som PDF. Kontrollér filen i Drive.')
        return ident

    def share(self,file_id):
        self.valid_id(file_id)
        permissions=self.api('/files/'+file_id+'/permissions?fields=permissions(id,type,role)')['permissions']
        if not any(p['type']=='anyone' and p['role']=='reader' for p in permissions):self.api('/files/'+file_id+'/permissions',{'type':'anyone','role':'reader','allowFileDiscovery':False},'POST')
        return self.link(file_id)
    def link(self,file_id):
        self.valid_id(file_id)
        info=self.api('/files/'+file_id+'?fields=id,webViewLink,resourceKey')
        link=info.get('webViewLink','')
        parsed=urllib.parse.urlsplit(link)
        if parsed.scheme!='https' or parsed.hostname!='drive.google.com' or parsed.username or parsed.password:raise ValueError('Google returnerede et ukendt visningslink.')
        if info.get('resourceKey') and 'resourcekey=' not in link.lower():link+=('&' if '?' in link else '?')+'resourcekey='+urllib.parse.quote(info['resourceKey'])
        return link
    def unshare(self,file_id):
        self.valid_id(file_id)
        for p in self.api('/files/'+file_id+'/permissions?fields=permissions(id,type)')['permissions']:
            if p['type']=='anyone':self.api('/files/'+file_id+'/permissions/'+p['id'],method='DELETE')

DATE_RENDER_REVISION=7
PDF_RENDER_REVISION=11
RENDER_REVISION=12

def public_members(store,c):
    addresses=c.get('geo_addresses') or [a for a in store.all('geo') if a.get('entity')=='address' and a['id'] in c.get('address_ids',[])]
    ignored={a['address_id'] for a in store.all('ignored')}
    retired={a['id'] for a in store.all('geo') if a.get('entity')=='address' and a.get('retired')}
    ib=[i for i in store.all('ib') if i['card_id']==c['id']]
    clean=lambda s:re.sub(r'[\s.,]+','',str(s or '').lower())
    def blocked(a):
        return any(i.get('address_id')==a['id'] if i.get('address_id') else clean(i.get('road'))==clean(a.get('road')) and clean(i.get('number')) in (clean(a.get('number')),clean(' '.join(str(a.get(k) or '') for k in ('number','floor','door')))) for i in ib)
    # A saved point remains visible on the reviewed public image, but must not
    # be counted as an outstanding visit or carry private IB metadata.
    result=[]
    for a in addresses:
        if a['id'] in ignored|retired or a.get('retired'):continue
        saved=blocked(a)
        fields=('id','road','number','lng','lat','count') if saved else ('id','road','number','floor','door','postcode','lng','lat','count')
        row={k:a.get(k) for k in fields}
        if saved:row['saved_point']=True
        result.append(row)
    return result

def public_manual_front(store,c):
    """Return only manual front rows that can be checked safely against IB."""
    if c.get('geo_polygon') or c.get('geo_addresses') or c.get('address_ids'):
        return [],False
    ib=[i for i in store.all('ib') if i.get('card_id')==c['id']]
    norm=lambda value:re.sub(r'[^\w]+','',str(value or '').casefold(),flags=re.UNICODE)
    by_road={}
    for item in ib:by_road.setdefault(norm(item.get('road')),[]).append(str(item.get('number') or ''))
    rows=[];withheld=False
    for item in c.get('addresses') or []:
        road=str(item.get('road') or '').strip();numbers=str(item.get('numbers') or '').strip()
        if not road or not numbers:continue
        ib_numbers=by_road.get(norm(road),[])
        # Only a single, plainly written unit can be compared exactly. Ranges,
        # lists and descriptive labels are deliberately not interpreted.
        exact=bool(re.fullmatch(r'\d+[a-zA-ZÆØÅæøå]?',numbers))
        if ib_numbers:
            units=[]
            for ib_number in ib_numbers:
                match=re.match(r'^\s*(\d+[a-zA-ZÆØÅæøå]?)(?:\s|,|$)',ib_number)
                if not match:
                    units=[];break
                units.append(norm(match.group(1)))
            if not exact or not units or norm(numbers) in units:
                withheld=True;continue
        rows.append({'road':road,'numbers':numbers,
            'count':None if item.get('count_unknown') else item.get('count',0),
            'count_unknown':bool(item.get('count_unknown'))})
    return rows,withheld

def public_name(store,c):
    area=store.get('settings',c.get('area_id')) if c.get('area_id') else None
    return c.get('name') or (area or {}).get('name','')

def fingerprint(store,c,legacy=False):
    content={'number':c['number'],'color':c.get('map_color','#477596'),'polygon':c.get('geo_polygon',[]),'members':sorted(public_members(store,c),key=lambda a:a['id'])}
    manual_rows,withheld=public_manual_front(store,c)
    if not c.get('geo_polygon') and not c.get('geo_addresses') and not c.get('address_ids') and c.get('addresses'):
        source_rows=[{'road':str(a.get('road') or ''),'numbers':str(a.get('numbers') or ''),'count':None if a.get('count_unknown') else a.get('count',0),'count_unknown':bool(a.get('count_unknown'))} for a in c['addresses']]
        content['manual_front']={'rows':manual_rows,'source_rows':source_rows,'withheld':withheld,'layout':'manual-front-v1'}
    if not legacy:
        content['name']=public_name(store,c)
        content['front_line_overrides']=c.get('front_line_overrides') or []
    if c.get('archived'):content['archived']=True
    return hashlib.sha256(json.dumps(content,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def png_bytes(value):
    if not isinstance(value,str) or not value.startswith('data:image/png;base64,'):raise ValueError('Vælg et PNG-kortbillede fra appen.')
    try:raw=base64.b64decode(value.split(',',1)[1],validate=True)
    except Exception:raise ValueError('Ugyldigt PNG-billede.') from None
    if len(raw)>8*1024*1024 or raw[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG-billedet er ugyldigt eller for stort.')
    pos=8;out=bytearray(raw[:8]);types=[];compressed=bytearray();channels=0
    while pos<len(raw):
        if pos+12>len(raw):raise ValueError('Ufuldstændigt PNG-billede.')
        length=struct.unpack('>I',raw[pos:pos+4])[0];kind=raw[pos+4:pos+8];end=pos+12+length
        if end>len(raw):raise ValueError('Ufuldstændigt PNG-billede.')
        data=raw[pos+8:end-4]
        if zlib.crc32(kind+data)&0xffffffff!=struct.unpack('>I',raw[end-4:end])[0]:raise ValueError('Beskadiget PNG-billede.')
        if kind==b'IHDR':
            if types or length!=13 or struct.unpack('>II',data[:8])!=(2200,1560) or data[8:] not in (b'\x08\x06\x00\x00\x00',b'\x08\x02\x00\x00\x00'):raise ValueError('Kortbilledet har et ukendt format.')
            channels=4 if data[9]==6 else 3
        if kind==b'IEND' and length:raise ValueError('Ugyldigt PNG-slutpunkt.')
        if kind==b'IDAT':compressed.extend(data)
        if kind in (b'IHDR',b'IDAT',b'IEND'):out.extend(raw[pos:end]);types.append(kind)
        pos=end
        if kind==b'IEND':break
    if not types or types[0]!=b'IHDR' or types[-1]!=b'IEND' or b'IDAT' not in types or pos!=len(raw):raise ValueError('Ufuldstændigt PNG-billede.')
    try:
        dec=zlib.decompressobj();pixels=dec.decompress(compressed,2200*1560*4+1561)
        if not dec.eof or dec.unconsumed_tail or dec.unused_data or len(pixels)!=1560*(1+2200*channels) or any(pixels[i]>4 for i in range(0,len(pixels),1+2200*channels)):raise ValueError()
    except Exception:raise ValueError('PNG-pixeldata er ugyldige.') from None
    return bytes(out)

class Publications:
    def __init__(self,store):
        self.store=store;self.images=ApprovedImages(store.root);self.drive=Drive(store.root);self.lock=threading.RLock();self.stop=threading.Event();self.worker=None
        with store.transaction():
            for row in self.rows():
                c=store.get('cards',row['card_id'])
                if c and row.get('render_revision')!=RENDER_REVISION and not row.get('render_refresh'):
                    row['render_refresh']=True;store.put('maps',row)
                # Preserve unchanged existing links while their layout awaits manual refresh.
                if c and row.get('status')=='published' and row.get('fingerprint')==fingerprint(store,c,legacy=True):
                    row.update(fingerprint=fingerprint(store,c),render_refresh=True);store.put('maps',row)
                if row.get('status')=='published' and row.get('url') and not row.get('front_url') and c and fingerprint(store,c)==row.get('fingerprint'):
                    c['front_revision']=True;store.put('cards',c)
                    row['front_url']=row['url'];store.put('maps',row)
    @staticmethod
    def key(card_id):return 'publication:'+card_id
    def rows(self):return [r for r in self.store.all('maps') if r.get('entity')=='publication']
    def status(self):
        with self.store.lock:
            rows=[]
            for row in self.rows():
                c=self.store.get('cards',row['card_id']);r={k:v for k,v in row.items() if k not in ('png','queued_png','approved_front_image')}
                r['number']=c['number'] if c else 'Slettet kort'
                r['outdated']=not self.current(row)
                r['date_update_pending']=bool(c and row.get('date_updates') and row.get('fingerprint')==fingerprint(self.store,c) and row.get('date_fingerprint')!=date_key(dates(self.store,c)))
                r['issued']=self.issued(row['card_id'])
                r['close_pending']=(not r['issued'] or row.get('manual_withdraw')) and bool(row.get('file_id') and (row.get('url') or row.get('possibly_public')))
                r['access_pending']=r['close_pending'] or row.get('status') in ('published','ready','access_retry','access_failed') and (row.get('status') not in ('published','ready') or r['issued']!=(row.get('status')=='published'))
                rows.append(r)
            return dict(self.drive.status(),cards=rows)
    def front_links(self):
        with self.store.lock:
            links=[]
            for row in self.rows():
                c=self.store.get('cards',row['card_id'])
                if row.get('status') in ('published','ready','access_retry','access_failed') and (row.get('front_url') or row.get('url')) and c and self.current(row):
                    links.append({'card_id':c['id'],'url':row.get('front_url') or row['url']})
            return links

    def issued(self,card_id):
        c=self.store.get('cards',card_id)
        return bool(c and not c.get('archived') and self.store.active_loan(card_id))

    def current(self,row):
        c=self.store.get('cards',row['card_id'])
        return bool(c and fingerprint(self.store,c)==row.get('fingerprint') and (not row.get('date_updates') or row.get('date_fingerprint')==date_key(dates(self.store,c))))

    def sync_access(self,row):
        """Reconcile an approved image, including approved date updates; no identities."""
        with self.store.transaction():
            target='published' if self.current(row) and self.issued(row['card_id']) else 'ready'
            if row.get('access_target')!=target:row['access_attempts']=0
            row.update(status='access_retry',access_target=target)
            # A permission POST can succeed even if its response is lost.
            if target=='published':row['possibly_public']=True
            self.store.put('maps',row)
        try:
            if target=='published':link=self.drive.share(row['file_id'])
            else:
                self.drive.unshare(row['file_id'])
                link=row.get('front_url') or self.drive.link(row['file_id'])
            # Do not leave access open if a return/deletion/edit arrived during the request.
            with self.store.lock:current=self.current(row);still_issued=self.issued(row['card_id'])
            if target=='published' and (not current or not still_issued):
                self.drive.unshare(row['file_id']);target='ready'
            with self.store.transaction():
                # Hold the store lock for this final check and state transition.
                current=self.current(row)
                if target=='published' and (not current or not self.issued(row['card_id'])):
                    # The worker retries the withdrawal; never report this as closed.
                    row.update(status='access_retry',access_target='ready',next_try=0)
                    self.store.put('maps',row);return
                c=self.store.get('cards',row['card_id'])
                row['date_retry_allowed']=bool(not current and row.get('date_updates') and c and fingerprint(self.store,c)==row.get('fingerprint'))
                if current and c and row.get('front_url')!=link:
                    c['front_revision']=True;self.store.put('cards',c)
                row.update(status=target if current else 'review',url=link if target=='published' else '',front_url=link,error='' if current else 'Kortet er ændret. Dan et nyt kortbillede.',possibly_public=target=='published',next_try=0,access_attempts=0,withdraw_attempts=0,close_attempts=0,next_close=0,close_error='')
                if target=='published':row['published']=datetime.now(timezone.utc).isoformat()
                row.pop('queued_png',None);row.pop('date_close_pending',None);self.store.put('maps',row)
        except Exception:
            with self.store.transaction():
                attempts=row.get('access_attempts',0)+1
                row.update(status='access_failed' if attempts>=5 else 'access_retry',access_attempts=attempts,next_try=time.time()+min(300,15*2**attempts),error='Google-adgangen er ikke bekræftet. Billedet kan stadig være offentligt. Kontrollér forbindelsen, og prøv adgangsændringen igen.')
                self.store.put('maps',row)

    def prepare(self,card_id):
        with self.store.lock:
            c=self.store.require('cards',card_id)
            manual_rows,manual_ib_withheld=public_manual_front(self.store,c)
            has_geo=bool(c.get('geo_polygon') or c.get('geo_addresses') or c.get('address_ids'))
            if not has_geo and not manual_rows and not manual_ib_withheld:raise ValueError('Tilføj kortets grænse, adresser eller sikre manuelle vejlinjer først.')
            public_dates=dates(self.store,c)
            public_card={k:c.get(k) for k in ('id','number','map_color')}
            if c.get('geo_polygon'):public_card['geo_polygon']=c['geo_polygon']
            public_card.update(name=public_name(self.store,c),public_dates=public_dates)
            # Send the same fields for every dot, regardless of its IB status.
            members=[{k:a[k] for k in ('id','road','number','lng','lat','count')}
                     for a in public_members(self.store,c)]
            from geography import front_summaries
            if has_geo:
                public_card['front_line_overrides']=c.get('front_line_overrides') or []
                source=c.get('geo_addresses') or [a for a in self.store.all('geo') if a.get('entity')=='address' and a['id'] in c.get('address_ids',[])]
                postcodes={a['id']:a.get('postcode','') for a in source}
                public_card['geo_addresses']=[dict(a,postcode=postcodes.get(a['id'],'')) for a in members]
                roads={}
                for a in members:
                    roads.setdefault(a['road'],[]).append(a)
                public_card['addresses']=[{'road':road,'numbers':', '.join(a['number'] for a in units),'count':sum(a['count'] for a in units)} for road,units in sorted(roads.items())]
                front_summaries([public_card])
                public_card.pop('front_line_overrides',None)
                public_card.pop('geo_addresses')
            else:
                public_card['addresses']=manual_rows
                public_card['temporary']=bool(c.get('temporary'))
            return {'render_revision':RENDER_REVISION,'fingerprint':fingerprint(self.store,c),'date_fingerprint':date_key(public_dates),'date_updates':True,'pdf':True,'dates':public_dates,'card':public_card,'members':members,'manual_front_rows':manual_rows,'manual_ib_withheld':manual_ib_withheld,'geography_missing':not has_geo}
    def date_preview(self,data):
        png=png_bytes(data.get('png'))
        with self.store.lock:
            c=self.store.require('cards',data.get('card_id'))
            if data.get('fingerprint')!=fingerprint(self.store,c) or data.get('date_fingerprint')!=date_key(dates(self.store,c)):
                raise ValueError('Kortet eller datoerne er ændret. Dan og kontrollér et nyt kortbillede.')
            png=render_dates(png,dates(self.store,c))
            return {'png':'data:image/png;base64,'+base64.b64encode(png).decode(),'date_fingerprint':data['date_fingerprint']}
    def stage_date_update(self):
        with self.store.transaction():
            rows=self.rows()
            first_due=next((r['card_id'] for r in rows if r.get('status') in ('queued','retry') and r.get('next_try',0)<=time.time()),None)
            for row in rows:
                if first_due and row['card_id']!=first_due:continue
                if row.get('status')=='review' and not row.get('date_retry_allowed'):continue
                if row.get('manual_withdraw') or row.get('render_revision') not in (DATE_RENDER_REVISION,9,10,PDF_RENDER_REVISION,RENDER_REVISION) or not row.get('date_updates') or row.get('date_error') or row.get('status') not in ('published','ready','access_retry','access_failed','queued','retry','failed','review'):continue
                c=self.store.get('cards',row['card_id'])
                if not c or fingerprint(self.store,c)!=row.get('fingerprint'):continue
                values=dates(self.store,c);key=date_key(values)
                if key==row.get('date_fingerprint'):continue
                try:
                    if row.get('render_revision',0)>=PDF_RENDER_REVISION:
                        self.images.load(row.get('approved_front_image'))
                    png=render_dates(self.images.load(row.get('approved_image')),values)
                except (OSError,ValueError):
                    row['date_error']='Det godkendte lokale kortbillede mangler eller er beskadiget. Opdater Google Drive-upload for at godkende et nyt billede.'
                    self.store.put('maps',row);continue
                row.update(status='queued',date_retry_allowed=False,date_fingerprint=key,date_values=values,queued_png=base64.b64encode(png).decode(),attempts=0,next_try=0,error='',date_close_pending=bool(row.get('file_id') and (row.get('url') or row.get('possibly_public'))),generation=os.urandom(12).hex())
                self.store.put('maps',row)
                return True
        return False
    def enqueue(self,data):
        revision=data.get('render_revision',1)
        if type(revision) is not int or revision not in range(1,RENDER_REVISION+1):raise ValueError('Ukendt kortlayout. Genindlæs appen og dan kortbilledet igen.')
        png=png_bytes(data.get('png'))
        front=png_bytes(data.get('front_png')) if revision>=PDF_RENDER_REVISION else None
        if not self.drive.connected():raise ValueError('Forbind Google Drive først.')
        with self.lock,self.store.transaction():
            c=self.store.require('cards',data['card_id']);fp=fingerprint(self.store,c)
            if data.get('fingerprint')!=fp:raise ValueError('Kortet er ændret, mens billedet blev dannet. Åbn kortet igen og publicér på ny.')
            old=self.store.get('maps',self.key(c['id'])) or {}
            if old.get('approved_front_image') and front is None:
                raise ValueError('Genindlæs appen, og godkend begge PDF-sider igen.')
            dated=revision>=DATE_RENDER_REVISION
            if dated:
                values=dates(self.store,c)
                if data.get('date_updates') is not True or data.get('date_fingerprint')!=date_key(values):
                    raise ValueError('Kortets datoer skal kontrolleres og godkendes med et nyt kortbillede.')
                png=render_dates(png,values)
                approved_image=self.images.save(png)
            row=dict(old,id=self.key(c['id']),entity='publication',card_id=c['id'],fingerprint=fp,status='queued',render_revision=revision,render_refresh=revision<RENDER_REVISION,error='',attempts=0,withdraw_attempts=0,access_attempts=0,access_target='',close_attempts=0,next_close=0,close_error='',next_try=0,queued_png=base64.b64encode(png).decode(),generation=os.urandom(12).hex())
            for field in ('approved_front_image','date_updates','date_fingerprint','date_values','approved_image','date_error','date_close_pending','manual_withdraw','date_retry_allowed'):row.pop(field,None)
            if front is not None:row['approved_front_image']=self.images.save(front)
            if dated:row.update(date_updates=True,date_fingerprint=date_key(values),date_values=values,approved_image=approved_image,date_close_pending=bool(old.get('file_id') and (old.get('url') or old.get('possibly_public'))))
            self.store.put('maps',row)
        with self.lock,self.store.lock:
            try:self.images.prune({r[key] for r in self.rows() for key in ('approved_image','approved_front_image') if r.get(key)})
            except OSError:pass
        return {'ok':True,'status':'queued'}
    def process_one(self):
        with self.lock:
            if not self.drive.connected():return
            if self.stage_date_update():return
            with self.store.lock:
                rows=self.rows()
                stale=next((r for r in rows if r.get('file_id') and (r.get('url') or r.get('queued_png') or r.get('possibly_public') or r.get('status')=='withdraw_retry') and r.get('status') not in ('private','withdraw_failed') and r.get('next_try',0)<=time.time() and (not self.current(r) or r.get('manual_withdraw'))),None)
            if stale:
                try:
                    self.drive.unshare(stale['file_id'])
                    with self.store.transaction():
                        stale.update(status='private' if stale.get('manual_withdraw') else 'review',url='',possibly_public=False,error='' if stale.get('manual_withdraw') else 'Kortet er ændret eller slettet. Offentlig adgang er fjernet; dan et nyt billede.',next_try=0);stale.pop('queued_png',None);self.store.put('maps',stale)
                except Exception:
                    with self.store.transaction():
                        attempts=stale.get('withdraw_attempts',0)+1;stale.update(status='withdraw_failed' if attempts>=5 else 'withdraw_retry',withdraw_attempts=attempts,next_try=time.time()+60,error='Kunne ikke fjerne offentlig adgang til det gamle billede. Kontrollér Google-forbindelsen.');self.store.put('maps',stale)
                return
            # A delayed/failed replacement upload must not keep the OLD image open
            # until its next upload attempt. Close it without discarding the new PNG.
            with self.store.lock:
                closing=next((r for r in rows if r.get('status') in ('queued','retry','failed') and r.get('file_id') and (r.get('url') or r.get('possibly_public')) and (not self.issued(r['card_id']) or r.get('date_close_pending')) and r.get('close_attempts',0)<5 and r.get('next_close',0)<=time.time()),None)
            if closing:
                try:
                    self.drive.unshare(closing['file_id'])
                    with self.store.transaction():closing.update(url='',possibly_public=False,close_attempts=0,next_close=0,close_error='',date_close_pending=False);self.store.put('maps',closing)
                except Exception:
                    with self.store.transaction():
                        attempts=closing.get('close_attempts',0)+1
                        closing.update(close_attempts=attempts,next_close=time.time()+60,close_error='Google-adgangen kunne ikke lukkes. Det gamle billede kan stadig være offentligt. Prøv adgangsændringen igen.');self.store.put('maps',closing)
                return
            with self.store.lock:
                access_row=None
                for r in sorted(rows,key=lambda r:self.issued(r['card_id'])):
                    if r.get('status') not in ('published','ready','access_retry','access_failed') or not r.get('file_id') or not self.current(r):continue
                    target='published' if self.issued(r['card_id']) else 'ready'
                    changed=r.get('access_target',r.get('status'))!=target
                    if r.get('status') in ('published','ready') and r['status']==target:continue
                    if not changed and (r.get('status')=='access_failed' or r.get('next_try',0)>time.time()):continue
                    access_row=r;break
            if access_row:self.sync_access(access_row);return
            with self.store.lock:
                row=next((r for r in rows if r.get('status') in ('queued','retry') and r.get('next_try',0)<=time.time()),None)
                if not row:return
                c=self.store.get('cards',row['card_id'])
                if not self.current(row):
                    with self.store.transaction():row.update(status='review',date_retry_allowed=bool(row.get('date_updates') and c and fingerprint(self.store,c)==row.get('fingerprint')),error='Kortet er ændret. Dan et nyt kortbillede.');row.pop('queued_png',None);self.store.put('maps',row)
                    return
            try:
                # Replacing an existing public file must not briefly publish an unassigned card.
                with self.store.lock:issued=self.issued(row['card_id'])
                if not issued and (row.get('url') or row.get('possibly_public')):
                    self.drive.unshare(row['file_id'])
                    with self.store.transaction():row.update(url='',possibly_public=False);self.store.put('maps',row)
                png=base64.b64decode(row['queued_png'])
                if row.get('render_revision',0)>=PDF_RENDER_REVISION:
                    pdf=shared_card_pdf(png,self.images.load(row.get('approved_front_image')))
                    file_id=self.drive.upload_pdf(pdf,c['number'],row.get('file_id'))
                else:
                    file_id=self.drive.upload(png,row.get('file_id'))
                # Persist the created ID before sharing so retries update the same file.
                with self.store.transaction():row['file_id']=file_id;self.store.put('maps',row)
                if self.stop.is_set():return
                self.sync_access(row)
            except Exception as exc:
                with self.store.transaction():
                    row['attempts']=row.get('attempts',0)+1;row.update(status=('failed' if row['attempts']>=5 else 'retry') if row.get('queued_png') else 'review',error=str(exc) if isinstance(exc,ValueError) else 'Upload mislykkedes. Prøv igen.',next_try=time.time()+min(300,15*2**row['attempts']));self.store.put('maps',row)
    def start(self):
        def loop():
            while not self.stop.wait(5):
                try:self.process_one()
                except Exception:pass
        self.worker=threading.Thread(target=loop,daemon=True);self.worker.start()
    def close(self):
        self.stop.set()
        if self.worker:self.worker.join(timeout=150)
    def withdraw(self,card_id):
        with self.lock:
            # Persist the owner's stop before the external request. A lost
            # withdrawal reply must not permit a later automatic date upload.
            with self.store.transaction():
                row=self.store.require('maps',self.key(card_id))
                row.update(manual_withdraw=True,status='withdraw_retry',withdraw_attempts=0,next_try=0)
                row.pop('queued_png',None);self.store.put('maps',row)
            try:
                if row.get('file_id'):self.drive.unshare(row['file_id'])
            except Exception:
                with self.store.transaction():
                    row.update(error='Google-adgangen er ikke bekræftet lukket. Appen forsøger igen; automatisk datoopdatering er stoppet.',next_try=0)
                    self.store.put('maps',row)
                return {'ok':True,'status':'withdraw_retry'}
            with self.store.transaction():
                row.update(status='private',url='',possibly_public=False,close_error='',error='');self.store.put('maps',row)
            return {'ok':True,'status':'private'}
    def retry(self,card_id):
        with self.lock,self.store.transaction():
            row=self.store.require('maps',self.key(card_id))
            if row.get('close_error'):
                row.update(close_attempts=0,next_close=0,close_error='');self.store.put('maps',row)
                return {'ok':True}
            if row.get('status') in ('access_retry','access_failed'):
                row.update(status='access_retry',next_try=0,access_attempts=0,error='');self.store.put('maps',row)
                return {'ok':True}
            if row.get('status') in ('withdraw_retry','withdraw_failed'):
                row.update(status='withdraw_retry',next_try=0,withdraw_attempts=0,error='');self.store.put('maps',row)
                return {'ok':True}
            if not row.get('queued_png'):raise ValueError('Åbn kortet og dan et nyt kortbillede.')
            row.update(status='queued',next_try=0,attempts=0,error='');self.store.put('maps',row)
        return {'ok':True}
    def qr(self,card_id,require_current=False):
        with self.store.lock:
            row=self.store.require('maps',self.key(card_id));url=row.get('front_url') or row.get('url')
            if require_current:
                c=self.store.get('cards',card_id)
                if not self.current(row):raise ValueError('Kortbilledet er ændret. Publicér igen før QR-print.')
        if row.get('status') not in ('published','ready','access_retry','access_failed') or not url:raise ValueError('Upload og kontrollér kortet før QR-koden dannes.')
        code=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=1,border=4);code.add_data(url);code.make(fit=True);matrix=code.get_matrix();size=len(matrix)
        path=''.join('M%d %dh1v1h-1z'%(x,y) for y,line in enumerate(matrix) for x,value in enumerate(line) if value)
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges"><rect width="100%%" height="100%%" fill="white"/><path d="%s" fill="black"/></svg>'%(size,size,path)).encode()
