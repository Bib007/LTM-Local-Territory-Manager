"""Small, private-data-free heartbeat over the fixed local Supervisor proxy."""
import copy
import json
import os
import threading
import time
from datetime import datetime, timezone
import urllib.request
from runtime_pressure import resource_pressure


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


def supervisor_post(path,payload,token):
    # Neither target nor path comes from HTTP input. Do not forward the token
    # to a proxy, a redirect, or any public host; never log provider responses.
    request=urllib.request.Request('http://supervisor/core/api/'+path,
        data=json.dumps(payload,allow_nan=False).encode(),
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=3) as response:response.read(1024)


MESSAGES={
 'idle':'LTM svarer. Ingen adressekontrol kører.',
 'working':'LTM svarer. Adressekontrollen arbejder.',
 'waiting':'LTM svarer. Adressekontrollen venter eller holder en planlagt pause.',
 'error':'Adressekontrollen er gentagne gange afbrudt. Se den private LTM-app.',
 'pressure':'Systemet har været under vedvarende ressourcepres i mindst to minutter.',
 'unknown':'LTM svarer, men ressourcemålingerne er ikke tilgængelige.',
 'stopped':'LTM er stoppet.',
}


class RuntimeStatus:
    def __init__(self,schedule,version,beta=False,enabled=None,token=None,
                 pressure=resource_pressure,clock=time.monotonic,transport=supervisor_post):
        self.schedule=schedule;self.version=version;self.channel='beta' if beta else 'stable'
        self.entity='sensor.ltm_'+self.channel+'_drift'
        self.token=os.environ.get('SUPERVISOR_TOKEN','') if token is None else token
        requested=(os.environ.get('DISTRIKT_HOME_ASSISTANT')=='1' and os.environ.get('DISTRIKT_HA_STATUS') in ('1','true')) if enabled is None else enabled
        self.enabled=bool(requested and self.token)
        self.pressure=pressure;self.clock=clock;self.transport=transport
        self.lock=threading.RLock();self.stop=threading.Event();self.thread=None
        self.high_since=None;self.test_at=None;self.last_sent=None;self.failed=False;self.value=None

    def sample(self):
        with self.lock:
            now=self.clock();reading=self.pressure();task=self.schedule.status()
            self.high_since=(now if self.high_since is None else self.high_since) if reading['high'] else None
            high=self.high_since is not None and now-self.high_since>=120
            bad=task.get('enabled') and task.get('status')=='waiting' and task.get('retry_streak',0)>=4 and task.get('retry_reason') not in ('pressure','budget')
            state='error' if bad else 'pressure' if high else 'working' if task.get('status')=='running' else 'waiting' if task.get('enabled') and task.get('status') in ('waiting','scheduled','stopping') else 'idle' if reading['available'] else 'unknown'
            # Allowlist only. In particular never copy last_problem, source
            # messages, job identifiers, addresses, account names or file paths.
            self.value={'state':state,'attributes':{'friendly_name':'LTM '+('Beta ' if self.channel=='beta' else '')+'drift',
                'icon':'mdi:heart-pulse','version':self.version,'channel':self.channel,
                'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'message':MESSAGES[state],'pressure_available':reading['available'],
                'pressure_scope':'system','pressure_window_seconds':60}}
            return copy.deepcopy(self.value)

    def status(self):
        with self.lock:return {'available':self.enabled,'entity':self.entity,'last_sent':self.last_sent,
            'delivery_failed':self.failed,'value':copy.deepcopy(self.value)}

    def publish(self):
        if not self.enabled:return
        try:
            value=self.sample()
            self.transport('states/'+self.entity,value,self.token)
            with self.lock:self.last_sent=value['attributes']['updated_at'];self.failed=False
        except Exception:
            with self.lock:self.failed=True

    def test_notification(self):
        with self.lock:
            if not self.enabled:raise ValueError('Slå driftsstatus til i Home Assistants appindstillinger først.')
            now=self.clock()
            if self.test_at is not None and now-self.test_at<60:raise ValueError('Vent et minut før en ny prøvebesked.')
            # Reserve before send: an unknown result must not be replayed.
            self.test_at=now
        try:self.transport('events/ltm_status_test',{'entity_id':self.entity},self.token)
        except Exception:raise ValueError('Prøvens resultat er ukendt. Kontrollér Home Assistant; vent et minut før et nyt forsøg.') from None
        return {'ok':True,'message':'Prøvehændelsen er sendt til Home Assistant. Kontrollér beskeden på den valgte enhed.'}

    def start(self):
        if self.enabled and self.thread is None:
            self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start()

    def loop(self):
        while not self.stop.is_set():
            self.publish();self.stop.wait(30)

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=4)
            if not self.thread.is_alive():
                try:self.transport('states/'+self.entity,{'state':'stopped','attributes':{'message':MESSAGES['stopped'],'channel':self.channel}},self.token)
                except Exception:pass
