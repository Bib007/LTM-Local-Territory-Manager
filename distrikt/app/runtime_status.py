"""Small, private-data-free heartbeat over the fixed local Supervisor proxy."""
import copy
import json
import os
import threading
import time
from datetime import datetime, timezone
import urllib.request
from runtime_pressure import resource_pressure
from runtime_probe import Observation,NoRedirect


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
 'unresponsive':'LTM har vedvarende problemer med HTTP-svar eller intern status. En gemning kan stadig være i gang. Ingen automatisk genstart udføres.',
}


class RuntimeStatus:
    def __init__(self,schedule,version,beta=False,enabled=None,token=None,
                 pressure=resource_pressure,clock=time.monotonic,transport=supervisor_post,probe=None,task_status=None):
        self.schedule=schedule;self.task_status=task_status or (lambda:self.schedule.status())
        self.version=version;self.channel='beta' if beta else 'stable'
        self.entity='sensor.ltm_'+self.channel+'_drift'
        self.token=os.environ.get('SUPERVISOR_TOKEN','') if token is None else token
        requested=(os.environ.get('DISTRIKT_HOME_ASSISTANT')=='1' and os.environ.get('DISTRIKT_HA_STATUS') in ('1','true')) if enabled is None else enabled
        self.enabled=bool(requested and self.token)
        self.pressure=pressure;self.clock=clock;self.transport=transport
        self.lock=threading.RLock();self.stop=threading.Event();self.thread=None
        self.high_since=None;self.test_at=None;self.last_sent=None;self.failed=False;self.value=None
        self.sampler=Observation(self.sample,clock)
        self.probe=Observation(probe,clock) if probe else None
        self.problem_since=None

    def sample(self):
        # Read Store-backed status before taking the bridge lock. App snapshots
        # hold Store while reading this bridge; reversing that order deadlocks HA.
        reading=self.pressure();task=self.task_status()
        with self.lock:
            now=self.clock()
            self.high_since=(now if self.high_since is None else self.high_since) if reading['high'] else None
            high=self.high_since is not None and now-self.high_since>=120
            bad=task.get('enabled') and task.get('status')=='waiting' and task.get('retry_streak',0)>=4 and task.get('retry_reason') not in ('pressure','budget')
            state='error' if bad else 'pressure' if high else 'working' if task.get('status')=='running' else 'waiting' if task.get('enabled') and task.get('status') in ('waiting','scheduled','stopping') else 'idle' if reading['available'] else 'unknown'
            # Allowlist only. In particular never copy last_problem, source
            # messages, job identifiers, addresses, account names or file paths.
            value={'state':state,'attributes':{'friendly_name':'LTM '+('Beta ' if self.channel=='beta' else '')+'drift',
                'icon':'mdi:heart-pulse','version':self.version,'channel':self.channel,
                'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'message':MESSAGES[state],'pressure_available':reading['available'],
                'pressure_scope':'system','pressure_window_seconds':60}}
            return value

    def status(self):
        with self.lock:return {'available':self.enabled,'entity':self.entity,'last_sent':self.last_sent,
            'delivery_failed':self.failed,'value':copy.deepcopy(self.value)}

    def publish(self):
        if not self.enabled:return
        try:
            sample_status,sampled=self.sampler.poll()
            probe_status,probe_value=self.probe.poll() if self.probe else ('ok','not_configured')
            http=probe_value if probe_status=='ok' else probe_status
            diagnostic=('http_'+http if http in ('timeout','error','invalid_response') else
                'runtime_busy' if http=='busy' else 'status_'+sample_status if sample_status in ('timeout','error') else
                'starting' if http=='pending' or sample_status=='pending' else 'none')
            with self.lock:
                now=self.clock()
                # Busy is a point observation, not evidence of continuous lock
                # contention. A timely sampler traverses BOTH application locks
                # and proves progress, even when the HTTP probe hits that read.
                # Cached success grants only the Observation deadline's grace;
                # a blocked sampler then becomes timeout independently.
                bad=diagnostic not in ('none','starting') and not (diagnostic=='runtime_busy' and sample_status=='ok')
                self.problem_since=(now if self.problem_since is None else self.problem_since) if bad else None
                value=copy.deepcopy(sampled) if sampled else {'state':'unknown','attributes':{'version':self.version,'channel':self.channel}}
                if self.problem_since is not None and now-self.problem_since>=120:value['state']='unresponsive'
                value['attributes'].update(updated_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    message=('Afventer første driftsmåling.' if diagnostic=='starting' else MESSAGES[value['state']]),
                    http_status=http,status_sample=sample_status,
                    diagnostic=diagnostic,problem_seconds=min(86400,int(now-self.problem_since)) if bad else 0)
                self.value=copy.deepcopy(value)
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
