"""Bounded observations: one worker per source, no Store/account locks in publisher."""
import json
import secrets
import threading
import time
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


def http_probe(origin,key):
    # Server supplies its own bound origin. Never accept a URL from HTTP input,
    # forward browser credentials, follow redirects or use environment proxies.
    challenge=secrets.token_hex(16)
    request=urllib.request.Request(origin+'/api/runtime/probe',headers={
        'X-LTM-Probe-Key':key,'X-LTM-Probe-Challenge':challenge})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=3) as response:
        body=response.read(513)
        if response.status!=200 or len(body)>512:return 'invalid_response'
        value=json.loads(body)
        if value.get('challenge')!=challenge or value.get('status') not in ('ok','busy'):
            return 'invalid_response'
        return value['status']


class Observation:
    """A blocked/slow-drip source cannot stall polling or spawn more workers.

    Socket timeout alone is per operation, not a total response deadline. The
    independent caller judges elapsed monotonic time even if the worker hangs.
    """
    def __init__(self,read,clock=time.monotonic,timeout=5,interval=30):
        self.read=read;self.clock=clock;self.timeout=timeout;self.interval=interval
        self.lock=threading.Lock();self.thread=None;self.started=None;self.result=None

    def poll(self):
        with self.lock:
            now=self.clock()
            if self.thread is None or (not self.thread.is_alive() and now-self.started>=self.interval):
                self.started=now
                self.thread=threading.Thread(target=self._read,daemon=True)
                self.thread.start()
            if self.thread.is_alive() and now-self.started>=self.timeout:return 'timeout',None
            return self.result or ('pending',None)

    def _read(self):
        try:result=('ok',self.read())
        except Exception:result=('error',None) # No exception/provider text leaves here.
        with self.lock:
            self.result=('timeout',None) if self.clock()-self.started>=self.timeout else result
