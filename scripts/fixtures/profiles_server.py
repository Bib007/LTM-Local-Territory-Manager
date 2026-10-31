"""Disposable normal LTM server for profile browser integration, invented data."""
import json
import signal
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from store import Store
from server import Server
from runtime_status import RuntimeStatus

with tempfile.TemporaryDirectory(prefix='ltm-fictional-profiles-') as root:
    store=Store(root)
    card=store.mutate('card.save',{'number':'F101','name':'Fiktivt kort','temporary':True})['id']
    store.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),store)
    server.runtime_status=RuntimeStatus(server.address_schedule,'fictional',True,enabled=True,token='fictional',
        pressure=lambda:{'available':True,'high':False},transport=lambda *args:None)
    server.runtime_status.publish()
    def stop(*args):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    print(json.dumps({'origin':server.origin,'card':card}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
