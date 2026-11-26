"""Ephemeral real server with fictional task accounts; no owner data."""
import json
import signal
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from server import Server
from store import Store

with tempfile.TemporaryDirectory(prefix='ltm-fictional-task-') as root:
    store=Store(root)
    card=store.mutate('card.save',{'number':'F101','name':'Fictional card','temporary':True})['id']
    store.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),store);accounts=server.accounts
    accounts.bootstrap('Fictional admin','Fictional-password-123')
    admin=accounts.login('Fictional admin','Fictional-password-123','fictional-admin')
    role=accounts.save_role(admin,'Fictional note editor',['cards.view','notes.view','notes.edit'])
    reader=accounts.save_user(admin,'Fictional reader <test>',[role],password='Fictional-password-456')
    token=accounts.login('Fictional reader <test>','Fictional-password-456','fictional-reader')
    cookie=lambda value:{'name':server.profiles.cookie,'value':value,'url':server.origin}
    def stop(*args):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    print(json.dumps({'origin':server.origin,'card':card,'reader_id':reader,'admin':cookie(admin),'reader':cookie(token)}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
