"""Short requests around long, read-only local district previews."""
import copy
import threading
import time
import uuid
from ui_errors import error_payload

class SetupJobs:
    def __init__(self,store):self.store=store;self.lock=threading.Lock();self.jobs={};self.active=None
    def start(self,action,data):
        if action not in ('setup.preview','setup.adjust.preview'):raise ValueError('Ukendt forhåndsvisning.')
        with self.lock:
            if self.active:raise ValueError('En kortberegning kører allerede. Vent på den før et nyt forslag.')
            self.jobs={k:v for k,v in self.jobs.items() if v['until']>time.monotonic()}
            if len(self.jobs)>=6:self.jobs.pop(next(iter(self.jobs)))
            ident=uuid.uuid4().hex;self.active=ident
            self.jobs[ident]={'status':'running','until':time.monotonic()+1800}
        threading.Thread(target=self.run,args=(ident,action,copy.deepcopy(data)),daemon=True).start()
        return {'job_id':ident}
    def run(self,ident,action,data):
        try:
            result=self.store.mutate(action,data)
            outcome={'status':'done','response':{'result':result,'revision':self.store.revision}}
        except (ValueError,KeyError,TypeError) as error:outcome={'status':'error',**error_payload(error)}
        except Exception:outcome={'status':'error','error':'Kortforslaget kunne ikke beregnes. Eksisterende kort er ikke ændret.'}
        with self.lock:
            self.jobs[ident].update(outcome);self.active=None
    def status(self,ident):
        with self.lock:
            job=self.jobs.get(ident)
            if not job or job['until']<=time.monotonic():raise ValueError('Kortberegningen er udløbet. Lav et nyt forslag.')
            return copy.deepcopy({k:v for k,v in job.items() if k!='until'})
