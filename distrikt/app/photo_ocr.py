"""Private local OCR jobs. Images/text never enter the store or an external API."""
import base64
import binascii
import os
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import uuid
import zlib
from pathlib import Path

MAX_BYTES=6000000
MAX_PIXELS=4000000
MAX_TEXT=100000
TIMEOUT=25


def validate_png(content):
    if not isinstance(content,str) or len(content)>4*((MAX_BYTES+2)//3):raise ValueError('Det klargjorte billede må højst fylde 6 MB.')
    try:raw=base64.b64decode(content,validate=True)
    except (ValueError,binascii.Error):raise ValueError('Billedet kunne ikke afkodes.') from None
    if len(raw)>MAX_BYTES or not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Vælg et gyldigt PNG-billede.')
    offset=8;header=False;pixels=False;end=False
    while offset+12<=len(raw):
        size=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8];last=offset+12+size
        if last>len(raw) or size>MAX_BYTES:raise ValueError('PNG-billedet er beskadiget.')
        data=raw[offset+8:offset+8+size]
        if zlib.crc32(kind+data)&0xffffffff!=struct.unpack('>I',raw[last-4:last])[0]:raise ValueError('PNG-billedet er beskadiget.')
        if not header:
            if kind!=b'IHDR' or size!=13:raise ValueError('PNG-billedet er beskadiget.')
            width,height,depth,colour,compression,filtering,interlace=struct.unpack('>IIBBBBB',data)
            if not width or not height or width*height>MAX_PIXELS or max(width,height)>4000:raise ValueError('Klargør billedet i mindre opløsning før genkendelse.')
            if depth!=8 or colour not in (0,2,4,6) or compression or filtering or interlace:raise ValueError('Brug et almindeligt PNG-billede uden sammenfletning.')
            header=True
        elif kind in (b'IHDR',b'acTL'):raise ValueError('Animerede eller ugyldige PNG-billeder understøttes ikke.')
        if kind==b'IDAT':pixels=True
        if kind==b'IEND':
            if size or last!=len(raw):raise ValueError('PNG-billedet er beskadiget.')
            end=True;break
        offset=last
    if not header or not pixels or not end:raise ValueError('PNG-billedet er ufuldstændigt.')
    return raw


def engine_path():
    found=shutil.which('tesseract')
    if found:return found
    # GUI launches may have a shorter PATH than a terminal. Only standard installs.
    candidates=['/opt/homebrew/bin/tesseract','/usr/local/bin/tesseract']
    if os.name=='nt':
        for key in ('ProgramFiles','ProgramFiles(x86)'):
            if os.environ.get(key):candidates.append(str(Path(os.environ[key])/'Tesseract-OCR'/'tesseract.exe'))
    return next((p for p in candidates if Path(p).is_file() and os.access(p,os.X_OK)),None)


class PhotoOCR:
    def __init__(self):self.lock=threading.Lock();self.jobs={};self.active=None;self.closed=False
    def available(self):
        engine=engine_path()
        if not engine:return {'available':False,'languages':[]}
        try:
            result=subprocess.run([engine,'--list-langs'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=3,check=False)
            if result.returncode:return {'available':False,'languages':[]}
            languages=[name for name in ('dan','eng') if name in result.stdout.decode('utf-8',errors='replace').splitlines()]
            return {'available':bool(languages),'languages':languages}
        except (OSError,subprocess.TimeoutExpired):return {'available':False,'languages':[]}
    def _expire(self):
        now=time.monotonic()
        for ident in list(self.jobs):
            if ident!=self.active and self.jobs[ident]['until']<now:del self.jobs[ident]
    def start(self,data):
        raw=validate_png(data.get('png'));status=self.available();engine=engine_path()
        if not status['available'] or not engine:raise ValueError('Lokal tekstgenkendelse mangler. Installér Tesseract og danske sprogdata på LTM-systemet.')
        with self.lock:
            self._expire()
            if self.closed:raise ValueError('Tekstgenkendelsen er lukket.')
            if self.active:raise ValueError('Et billede læses allerede. Vent, eller stop den aktive læsning.')
            # At most two RAM-only results; each expires and is removed after cancel.
            while len(self.jobs)>=2:del self.jobs[next(iter(self.jobs))]
            ident=uuid.uuid4().hex;stop=threading.Event();self.active=ident
            self.jobs[ident]={'status':'running','until':time.monotonic()+300,'stop':stop,'text':''}
            worker=threading.Thread(target=self._run,args=(ident,raw,engine,'+'.join(status['languages']),stop),daemon=True)
            self.jobs[ident]['thread']=worker
            worker.start()
        return {'id':ident,'status':'running'}
    def status(self,ident):
        with self.lock:
            self._expire();job=self.jobs.get(ident)
            if not job:raise ValueError('Billedlæsningen er udløbet. Vælg billedet igen.')
            return {k:v for k,v in job.items() if k in ('status','text','error')}
    def cancel(self,ident):
        with self.lock:
            job=self.jobs.pop(ident,None)
            if job:
                job['stop'].set()
                if job.get('timer'):job['timer'].cancel()
        if job:job['thread'].join(.5)
        return {'ok':True}
    def close(self):
        with self.lock:
            self.closed=True
            for job in self.jobs.values():
                job['stop'].set()
                if job.get('timer'):job['timer'].cancel()
            workers=[job['thread'] for job in self.jobs.values() if job.get('thread')]
            self.jobs.clear()
        for worker in workers:worker.join(1)
    def _run(self,ident,raw,engine,language,stop):
        text='';error='';process=None
        try:
            with tempfile.TemporaryDirectory(prefix='ltm-local-ocr-') as directory:
                source=Path(directory)/'input.png';source.write_bytes(raw);source.chmod(0o600);prefix=Path(directory)/'text'
                env=dict(os.environ,OMP_THREAD_LIMIT='1')
                process=subprocess.Popen([engine,str(source),str(prefix),'-l',language,'--psm','6'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
                try:
                    deadline=time.monotonic()+TIMEOUT
                    while process.poll() is None:
                        if stop.wait(.1):raise ValueError('Billedlæsningen er stoppet.')
                        if time.monotonic()>deadline:raise ValueError('Billedlæsningen tog for lang tid. Prøv et tydeligere udsnit.')
                    if process.returncode:raise ValueError('Billedet kunne ikke læses. Prøv et tydeligere billede.')
                    output=prefix.with_suffix('.txt')
                    if not output.is_file() or output.stat().st_size>MAX_TEXT:raise ValueError('Billedet indeholder for meget tekst. Vælg et mindre udsnit.')
                    text=output.read_text(encoding='utf-8',errors='replace')
                finally:
                    if process.poll() is None:process.kill();process.wait()
        except ValueError as exc:error=str(exc)
        except Exception:error='Den lokale billedlæsning kunne ikke gennemføres.'
        finally:
            if process is not None and process.poll() is None:process.kill();process.wait()
            with self.lock:
                job=self.jobs.get(ident)
                if job and not stop.is_set():
                    job.update(status='error' if error else 'done',text='' if error else text,error=error,until=time.monotonic()+300)
                    timer=threading.Timer(300,lambda:self.cancel(ident));timer.daemon=True;job['timer']=timer;timer.start()
                if self.active==ident:self.active=None
