#!/usr/bin/env python3
"""Local desktop or authenticated private LAN server. Only approved PNGs leave it."""
import argparse
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
import ipaddress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from store import Store, MODULES
from pdf_export import s13_pdf
from geodata import Downloads
from access import Access, LOGIN, private_client, write_private
from portable import Restores, snapshot, MAX_ARCHIVE
from sharing import Publications

APP=Path(__file__).resolve().parent
VERSION='1.11.0'
DEFAULT_DATA=(Path.home()/'Library'/'Application Support'/'Distrikt' if sys.platform=='darwin' else Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local'/'share')))/'Distrikt')

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self, address, store, access_host=None, password=None):
        super().__init__(address,Handler)
        self.store=store
        self.downloads=Downloads(store)
        self.token=secrets.token_urlsafe(32)
        self.origin='http://127.0.0.1:%s'%self.server_port
        self.access=Access(store.root,password) if access_host else None
        self.hosts={'127.0.0.1:%s'%self.server_port}
        self.public_url=self.origin
        if access_host:
            parsed=urlsplit('http://'+access_host)
            if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or not parsed.hostname or parsed.port:
                raise ValueError('Angiv kun HA-maskinens lokale IP-adresse eller værtsnavn, uden port eller http://.')
            host=parsed.hostname.lower()
            if not all(c.isalnum() or c in '.-' for c in host):raise ValueError('Ugyldigt lokalt værtsnavn.')
            try:
                ip=ipaddress.ip_address(host)
                if not private_client(str(ip)):raise ValueError('Brug en privat lokal IP-adresse.')
            except ValueError:
                if not host.endswith('.local'):raise ValueError('Brug en privat IP-adresse eller et .local-værtsnavn.')
            self.hosts.add('%s:%s'%(host,self.server_port))
            self.public_url='http://%s:%s'%(host,self.server_port)
        self.restores=Restores(store,VERSION)
        self.sharing=Publications(store)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):
        # Names, addresses and history must not appear in logs.
        pass
    def send(self,data,kind='application/json',status=200,headers=None):
        if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False).encode('utf8')
        headers=dict(headers or {})
        if len(data)>16384 and any(v.strip().split(';')[0]=='gzip' and not __import__('re').search(r'q=0(?:\.0*)?\s*$',v) for v in self.headers.get('Accept-Encoding','').split(',')):
            data=__import__('gzip').compress(data,compresslevel=4);headers['Content-Encoding']='gzip';headers['Vary']='Accept-Encoding'
        self.send_response(status)
        self.send_header('Content-Type',kind+('; charset=utf-8' if kind in ('text/html','text/css','text/javascript','application/json') else ''))
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        for key,value in (headers or {}).items():self.send_header(key,value)
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://tile.openstreetmap.org; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers();self.wfile.write(data)
    def allowed(self,token=False,public=False):
        host=self.headers.get('Host','').lower()
        if host not in self.server.hosts:
            self.send({'error':'Ukendt lokal vært. Brug den konfigurerede lokale adresse.'},status=403);return False
        origin=self.headers.get('Origin')
        if origin and origin!='http://'+host:
            self.send({'error':'Kun den lokale app har adgang.'},status=403);return False
        if self.server.access:
            if not private_client(self.client_address[0]):
                self.send({'error':'Kun hjemmenetværk og VPN har adgang.'},status=403);return False
            if not public and not self.server.access.valid(self.headers.get('Cookie')):
                self.send({'error':'Log ind igen på den lokale adresse.'},status=401);return False
        if token and self.headers.get('X-Distrikt-Token')!=self.server.token:
            self.send({'error':'Genindlæs appen, og prøv igen.'},status=403);return False
        return True
    def do_GET(self):
        parsed=urlsplit(self.path);path=parsed.path;q=parse_qs(parsed.query)
        public=path in ('/','/login.js','/style.css','/api/ping')
        if not self.allowed(public=public):return
        try:
            if path=='/api/ping':return self.send({'app':'Distrikt','version':VERSION})
            if path=='/':
                if self.server.access and not self.server.access.valid(self.headers.get('Cookie')):return self.send(LOGIN.encode(),'text/html')
                html=(APP/'index.html').read_text().replace('__TOKEN__',self.server.token)
                if self.server.access:html=html.replace('Lokalt på din Mac','Privat server · LAN / VPN').replace('Kun på denne computer','På din private server').replace('<button class="stop" data-action="stop">Luk den lokale app</button>','<button class="stop" data-action="logout">Log ud</button>')
                else:html=html.replace('Lokalt på din Mac','Lokalt på din computer').replace('Kun på denne computer','Kun på denne computer')
                return self.send(html.encode(),'text/html')
            if path in ('/app.js','/workspace.js','/setup-ui.js','/overview-map.js','/login.js','/transfer-ui.js','/share-ui.js','/navigation.js','/ib-ui.js','/basemaps.js','/geo.js','/road-search.js','/map-export.js','/printing.js','/admin.js','/district-map.js','/main-boundary.js','/boundary-import.js','/s13-template.js','/report-print.js','/report-map.js','/style.css','/workspace.css'):
                return self.send((APP/path[1:]).read_bytes(),'text/javascript' if path.endswith('.js') else 'text/css')
            if path in ('/vendor/leaflet.js','/vendor/leaflet.css'):
                return self.send((APP/path[1:]).read_bytes(),'text/javascript' if path.endswith('.js') else 'text/css')
            if path=='/s12-template.png':return self.send((APP.parent/'templates'/'S-12-source.png').read_bytes(),'image/png')
            if path=='/s13-background.jpg':return self.send((APP.parent/'templates'/'S-13-background.jpg').read_bytes(),'image/jpeg')
            if path=='/card-qr.svg':return self.send(self.server.sharing.qr(q.get('card_id',[''])[0],require_current=True),'image/svg+xml')
            if path.startswith('/api/') and not self.allowed(token=True):return
            if path=='/api/setup/ib-template.csv':
                from setup_store import ib_template
                return self.send(ib_template(),'text/csv',headers={'Content-Disposition':'attachment; filename=IB-import-skabelon.csv'})
            if path=='/api/geo':return self.send(self.server.store.geo_state())
            if path=='/api/geo/job':return self.send(self.server.downloads.status(q.get('id',[''])[0]))
            if path=='/api/geo/suggest':return self.send(self.server.downloads.suggest(q.get('road',[''])[0],q.get('postcode',[''])[0]))
            if path=='/api/state':
                self.server.store.purge_expired()
                with self.server.store.lock:
                    result=self.server.store.state();result['public_maps']=self.server.sharing.front_links()
                return self.send(result)
            if path=='/api/storage':return self.send(self.server.store.storage_info())
            if path=='/api/activity':return self.send({'items':self.server.store.activity()})
            if path=='/api/map':
                with self.server.store.lock:
                    m=self.server.store.get('maps','background')
                return self.send(m or {})
            if path=='/api/export/s13':
                year=int(q.get('year',['0'])[0])
                if not 2000<=year<=2200:raise ValueError('Ugyldigt tjenesteår.')
                return self.send(s13_pdf(self.server.store.state(),year),'application/pdf')
            if path=='/api/export/backup':return self.send(snapshot(self.server.store,VERSION),'application/zip',headers={'Content-Disposition':'attachment; filename="Distrikt-sikkerhedskopi.zip"'})
            if path=='/api/share/status':return self.send(self.server.sharing.status())
            if path=='/api/share/qr':return self.send(self.server.sharing.qr(q.get('card_id',[''])[0]),'image/svg+xml')
            if path=='/api/restore/safety':
                name=q.get('name',[''])[0]
                if not name.startswith('foer-import-') or Path(name).name!=name or not name.endswith('.zip'):raise ValueError('Ukendt sikkerhedskopi.')
                return self.send((self.server.store.root/'backups'/name).read_bytes(),'application/zip')
            if path=='/api/data-info':return self.send({'path':str(self.server.store.root),'cutoff':self.server.store.history_cutoff(),'server_mode':bool(self.server.access),'address':self.server.public_url})
            return self.send({'error':'Siden findes ikke.'},status=404)
        except (ValueError,KeyError,TypeError) as e:self.send({'error':str(e)},status=400)
        except Exception:self.send({'error':'Lokal læsefejl. Data er ikke sendt nogen steder.'},status=500)
    def do_POST(self):
        if self.path=='/api/login':
            if not self.allowed(public=True):return
            try:
                if not self.server.access:raise ValueError('Login bruges kun i serverversionen.')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Ugyldigt format.')
                length=int(self.headers.get('Content-Length',0))
                if not 0<length<4096:raise ValueError('Ugyldigt login.')
                data=json.loads(self.rfile.read(length));session=self.server.access.login(data.get('password'),self.client_address[0])
                return self.send({'ok':True},headers={'Set-Cookie':'distrikt_session='+session+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200'})
            except (ValueError,TypeError,AttributeError):return self.send({'error':'Forkert adgangskode eller for mange forsøg. Vent fem minutter efter gentagne forsøg.'},status=401)
        if not self.allowed(token=True):return
        if self.path=='/api/restore/preview':
            try:
                if self.headers.get('Content-Type')!='application/zip':raise ValueError('Vælg en ZIP-sikkerhedskopi.')
                length=int(self.headers.get('Content-Length',0))
                if not 0<length<=MAX_ARCHIVE:raise ValueError('Sikkerhedskopien må højst fylde 100 MB.')
                return self.send(self.server.restores.preview(self.rfile.read(length)))
            except ValueError as error:return self.send({'error':str(error)},status=400)
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send({'error':'Ugyldigt format.'},status=415)
        try:
            length=int(self.headers.get('Content-Length',0))
            if not 0<length<=16000000:raise ValueError('Forespørgslen er for stor eller tom.')
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise ValueError('Ugyldige data.')
            if self.path=='/api/logout':
                if self.server.access:self.server.access.logout(self.headers.get('Cookie'))
                return self.send({'ok':True},headers={'Set-Cookie':'distrikt_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
            if self.path=='/api/restore/apply':
                if self.server.downloads.status().get('status')=='running':raise ValueError('Sæt adressehentningen på pause før import.')
                with self.server.sharing.lock:return self.send(self.server.restores.apply(data.get('token')))
            if self.path=='/api/share/connect':
                with self.server.sharing.lock:
                    before=self.server.sharing.drive.status();old_auth=json.loads(self.server.sharing.drive.path.read_text()) if self.server.sharing.drive.connected() else None
                    result=self.server.sharing.drive.connect(data)
                    if before.get('account') and before['account']!=result.get('account'):
                        with self.server.store.lock:has_shared=any(r.get('file_id') and r.get('status')!='private' for r in self.server.sharing.rows())
                        if has_shared:
                            write_private(self.server.sharing.drive.path,old_auth);self.server.sharing.drive.access='';self.server.sharing.drive.expires=0
                            raise ValueError('Fjern først offentlig adgang til kortene på den gamle Google-konto. Forbind derefter den nye konto.')
                        with self.server.store.transaction():
                            for row in self.server.sharing.rows():
                                for key in ('file_id','url','queued_png'):row.pop(key,None)
                                row.update(status='review',error='Ny Google-konto: publicér igen. QR-links fra den tidligere konto ændres.');self.server.store.put('maps',row)
                    return self.send(result)
            if self.path=='/api/share/disconnect':
                with self.server.sharing.lock:self.server.sharing.drive.disconnect()
                return self.send({'ok':True})
            if self.path=='/api/share/prepare':return self.send(self.server.sharing.prepare(data.get('card_id')))
            if self.path=='/api/share/publish':return self.send(self.server.sharing.enqueue(data))
            if self.path=='/api/share/withdraw':return self.send(self.server.sharing.withdraw(data.get('card_id')))
            if self.path=='/api/share/retry':return self.send(self.server.sharing.retry(data.get('card_id')))
            if self.path=='/api/geo/download':return self.send(self.server.downloads.start(data.get('kind'),data.get('data',{})))
            if self.path=='/api/geo/pause':return self.send(self.server.downloads.pause(data.get('job_id')))
            if self.path=='/api/mutate':
                if data.get('action') in ('geo.main.prune','geo.main.save') and self.server.downloads.status().get('status')=='running':raise ValueError('Sæt hentningen på pause før grænsen gemmes eller adresser ryddes op.')
                result=self.server.store.mutate(data.get('action'),data.get('data',{}))
                return self.send({'ok':True,'result':result,'revision':self.server.store.revision})
            if self.path=='/api/open-data':
                if not self.server.access:
                    if sys.platform=='darwin':subprocess.Popen(['/usr/bin/open',str(self.server.store.root)])
                    elif sys.platform=='win32':os.startfile(str(self.server.store.root))
                return self.send({'ok':True,'path':str(self.server.store.root)})
            if self.path=='/api/shutdown':
                if self.server.access:raise ValueError('Stop serverversionen fra Home Assistant.')
                self.send({'ok':True});threading.Thread(target=self.server.shutdown,daemon=True).start();return
            return self.send({'error':'Ukendt handling.'},status=404)
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:self.send({'error':str(e)},status=400)
        except Exception:self.send({'error':'Ændringen blev ikke gemt. Prøv igen; eksisterende data er bevaret.'},status=500)

def running(data):
    try:
        info=json.loads((data/'run.json').read_text())
        url=info['url']
        parsed=urlsplit(url)
        if parsed.scheme!='http' or parsed.hostname!='127.0.0.1':return None
        req=urllib.request.Request(url+'/api/ping')
        with urllib.request.urlopen(req,timeout=1) as r:
            ping=json.load(r)
        if ping.get('app')=='Distrikt':return dict(info,version=ping['version'])
    except Exception:pass
    return None

def stop_running(data):
    info=running(data)
    if info:
        req=urllib.request.Request(info['url']+'/api/shutdown',data=b'{}',method='POST',headers={'Content-Type':'application/json','X-Distrikt-Token':info['token']})
        with urllib.request.urlopen(req,timeout=3) as r:r.read()
    return bool(info)

def acquire_lock(path):
    stream=open(path,'a+b')
    try:
        if sys.platform=='win32':
            import msvcrt
            stream.seek(0);stream.write(b'0');stream.flush();stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return stream
    except OSError:stream.close();return None

def main():
    p=argparse.ArgumentParser();p.add_argument('--data-dir',default=os.environ.get('DISTRIKT_DATA_DIR',str(DEFAULT_DATA)));p.add_argument('--serve',action='store_true');p.add_argument('--stop',action='store_true');p.add_argument('--no-browser',action='store_true');p.add_argument('--lan',action='store_true');p.add_argument('--access-host');p.add_argument('--port',type=int,default=8787);args=p.parse_args()
    data=Path(args.data_dir).expanduser().resolve();data.mkdir(parents=True,exist_ok=True,mode=0o700)
    if args.lan and (not args.serve or not args.access_host):raise ValueError('Servertilstand kræver --serve --lan --access-host med en lokal IP-adresse.')
    if args.stop:stop_running(data);return
    info=running(data)
    if not args.serve:
        if info and info['version']!=VERSION:
            stop_running(data)
            for _ in range(30):
                if not running(data):break
                time.sleep(.1)
            info=None
        if not info:
            log=open(data/'start.log','a')
            subprocess.Popen([sys.executable,str(APP/'server.py'),'--serve','--data-dir',str(data)],cwd=str(APP),stdin=subprocess.DEVNULL,stdout=log,stderr=log,**({'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS} if sys.platform=='win32' else {'start_new_session':True}))
            for _ in range(60):
                info=running(data)
                if info:break
                time.sleep(.1)
        if not info:raise RuntimeError('Appen kunne ikke starte. Se start.log i datamappen.')
        if not args.no_browser:webbrowser.open(info['url'])
        print('Distrikt er startet: '+info['url']);return
    if info:return
    lock=acquire_lock(data/'app.lock')
    if lock is None:return
    store=Store(data);server=Server(('0.0.0.0',args.port) if args.lan else ('127.0.0.1',0),store,access_host=args.access_host if args.lan else None,password=os.environ.pop('DISTRIKT_PASSWORD',None) if args.lan else None)
    server.sharing.start()
    run={'url':server.origin,'token':server.token,'pid':os.getpid(),'version':VERSION}
    runpath=data/'run.json';runpath.write_text(json.dumps(run));os.chmod(runpath,0o600)
    def cleanup_loop():
        while not stop_event.wait(60):
            try:store.purge_expired()
            except Exception:pass
    stop_event=threading.Event();threading.Thread(target=cleanup_loop,daemon=True).start()
    def shutdown(signum,frame):threading.Thread(target=server.shutdown,daemon=True).start()
    signal.signal(signal.SIGTERM,shutdown);signal.signal(signal.SIGINT,shutdown)
    try:server.serve_forever(poll_interval=.2)
    finally:
        stop_event.set();server.sharing.close();server.server_close();store.close()
        try:runpath.unlink()
        except FileNotFoundError:pass
        lock.close()

if __name__=='__main__':
    try:main()
    except Exception as e:print('Distrikt: '+str(e),file=sys.stderr);sys.exit(1)
