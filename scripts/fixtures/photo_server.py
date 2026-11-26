"""Disposable real HTTP server with invented records; no external services."""
import json
import os
import signal
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'distrikt/app'))
from server import Server
from store import Store
from photo_ocr import validate_png


class SyntheticOCR:
    """Deterministic OCR only; HTTP, CSP, decoding and import remain production code."""
    def available(self):return {'available':True,'languages':['dan','eng']}
    def start(self,data):
        validate_png(data.get('png'))
        return {'id':'fictional-job','status':'running'}
    def status(self,ident):return {'status':'done','text':'Fiktivvej 8 - 24.10.2026'}
    def cancel(self,ident):return {'ok':True}
    def close(self):pass


with tempfile.TemporaryDirectory(prefix='ltm-fictional-browser-') as folder:
    store=Store(folder)
    store.mutate('geo.import',{'records':[dict(id='fictional-a',entity='address',road='Fiktivvej',number='8',postcode='9999',lng=10,lat=55,count=1)],'source':'Invented test data'})
    card=store.mutate('geo.assign',{'address_ids':['fictional-a'],'number':'901'})['id']
    store.mutate('revision.approve',{'card_id':card,'side':'front'})
    store.mutate('revision.approve',{'card_id':card,'side':'back'})
    store.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),store,access_host='127.0.0.1',password='Fictional-pass-123')
    if os.environ.get('LTM_NATIVE_OCR')!='1':server.photo_ocr=SyntheticOCR()
    def stop(signum,frame):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    print(json.dumps({'origin':server.origin,'card':card}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
