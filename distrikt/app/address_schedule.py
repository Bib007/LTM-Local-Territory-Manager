"""Durable HA address-check task. Only complete snapshots can propose removals."""
import copy
import re
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from admin_store import signature

RECORD='address-check-task'

def utcnow():return datetime.now(timezone.utc)
def iso(value):return value.isoformat(timespec='seconds')
def next_night(current,days,clock):
    # Use the host's HA-configured local timezone, including its DST rules.
    local=current.astimezone();hour,minute=map(int,clock.split(':'))
    day=local.date()+timedelta(days=days)
    naive=datetime.combine(day,datetime.min.time()).replace(hour=hour,minute=minute)
    return iso(naive.astimezone(timezone.utc))

class AddressSchedule:
    def __init__(self,store,downloads,available=False,clock=utcnow):
        self.store=store;self.downloads=downloads;self.available=available;self.clock=clock
        self.lock=threading.RLock();self.stop=threading.Event();self.thread=None;self.job=None
    def row(self):return copy.deepcopy(self.store.get('settings',RECORD) or {'id':RECORD,'entity':'address_task','enabled':False,'days':7,'time':'02:00','status':'idle'})
    def status(self):
        with self.store.lock:
            row=self.row();row['available']=self.available
            row['pending']=self.store.geo_info().get('changes',0)
        return row
    def busy(self):
        with self.store.lock:return bool(self.row().get('run'))
    def configure(self,data):
        with self.lock:
            if not self.available:raise ValueError('Automatisk adressekontrol findes på Home Assistant.')
            enabled=data.get('enabled');days=data.get('days');clock=data.get('time')
            if type(enabled)!=bool or type(days)!=int or not 1<=days<=30 or not isinstance(clock,str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',clock):
                raise ValueError('Vælg 1–30 dage og et gyldigt klokkeslæt.')
            with self.store.transaction():
                if data.get('_revision')!=self.store.revision:raise ValueError('Data er ændret. Genindlæs opgaven før du gemmer.')
                row=self.row()
                if row.get('run'):
                    if enabled:raise ValueError('Vent på den igangværende adressekontrol, før tidsplanen ændres.')
                    row.update(enabled=False,status='stopping',message='Stopper efter det aktuelle opslag…');self.store.put('settings',row)
                    self.downloads.cancel_event.set()
                    return {'ok':True}
                if enabled and not self.store.main_boundary():raise ValueError('Gem den samlede distriktsgrænse før automatisk adressekontrol.')
                if enabled and not self.downloads.address_source.status().get('configured'):raise ValueError('Forbind Datafordeleren under Kortdata først.')
                row.update(enabled=enabled,days=days,time=clock,status='scheduled' if enabled else 'idle',next_due=next_night(self.clock(),0,clock))
                if row['next_due']<=iso(self.clock()):row['next_due']=next_night(self.clock(),1,clock)
                self.store.put('settings',row)
            return {'ok':True}
    def start(self):
        if self.available and self.thread is None:
            self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start()
    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=3)
        if self.job:
            self.downloads.cancel_event.set()
            until=time.monotonic()+125
            while self.downloads.status(self.job)['status']=='running' and time.monotonic()<until:threading.Event().wait(.1)
    def loop(self):
        while not self.stop.is_set():
            try:self.tick()
            except Exception:
                # Never log credentials/provider payloads. Retry after restart or transient local errors.
                pass
            self.stop.wait(10)
    def tick(self):
        if not self.available:return
        with self.lock:
            current=self.clock()
            with self.store.lock:row=self.row()
            if not row.get('enabled'):
                if row.get('run'):
                    if self.job and self.downloads.status(self.job)['status']=='running':return
                    self.job=None
                    with self.store.transaction():
                        row=self.row();row.pop('run',None);row.update(status='idle',message='Automatisk adressekontrol er slået fra.');self.store.put('settings',row)
                return
            if self.job:
                job=self.downloads.status(self.job)
                if job['status']=='running':return
                self.job=None
                result=job.get('result') or {}
                if job['status']=='done' and result.get('complete'):
                    with self.store.transaction():
                        row=self.row();run=row.pop('run',{})
                        counts={kind:0 for kind in ('new','changed','retired')}
                        for a in self.store.all('geo'):
                            if a.get('entity')=='address_change' and a.get('check_run')==run.get('id'):counts[a['kind']]+=1
                        row.update(status='complete',completed_at=iso(current),last_result=counts,message='Adressekontrollen er færdig. Gennemgå og godkend ændringerne.',next_due=next_night(current,row['days'],row['time']))
                        row.pop('retry_at',None);self.store.put('settings',row)
                    return
                with self.store.transaction():
                    row=self.row();attempt=row.get('attempt',0)+1
                    row.update(status='waiting',attempt=attempt,retry_at=iso(current+timedelta(minutes=min(360,15*2**min(attempt-1,5)))),message='Adressekontrollen venter efter en afbrydelse. Færdige udsnit er bevaret; den prøver automatisk igen.')
                    self.store.put('settings',row)
                return
            if row.get('run') and row.get('retry_at','')>iso(current):return
            if not row.get('run') and row.get('next_due','9999')>iso(current):return
            # The shared Downloads reservation rejects simultaneous interactive work.
            with self.downloads.lock:
                if self.downloads.active:return
            with self.store.transaction():
                row=self.row();boundary=self.store.main_boundary()
                if not boundary:return
                key=signature(boundary['points']);run=row.get('run')
                if run and run['boundary_key']!=key:
                    row.pop('run',None);row.update(status='waiting',next_due=next_night(current,1,row['time']),message='Grænsen er ændret. En ny kontrol køres næste nat.');self.store.put('settings',row);return
                if not run:run={'id':uuid.uuid4().hex,'boundary_key':key};row.update(run=run,attempt=0,started_at=iso(current))
                manifest=self.store.get('geo','main-boundary-download') or {}
                refresh=manifest.get('check_run')!=run['id']
                row.update(status='running',message='Kontrollerer adresser indenfor den samlede grænse…');self.store.put('settings',row)
            try:self.job=self.downloads.start('boundary',{'refresh':refresh,'review_all':True,'check_run':run['id']})['job_id']
            except ValueError:
                with self.store.transaction():
                    row=self.row();row.update(status='waiting',retry_at=iso(current+timedelta(minutes=15)));self.store.put('settings',row)
