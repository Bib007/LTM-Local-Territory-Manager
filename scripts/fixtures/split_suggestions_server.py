"""Real temporary server with fictional geographic membership for manual planning."""
import json
import signal
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from server import Server
from store import Store

with tempfile.TemporaryDirectory(prefix='ltm-fictional-split-') as root:
    store=Store(root)
    area=store.mutate('area.save',{'name':'Fictional area'})['id']
    groups=[('source','101',8),('target','102',2),('issued','104',8)]
    records=[{'id':prefix+str(i),'entity':'address','road':'Fictional road','number':str(group*20+i),'postcode':'9999','lng':10+i*.001,'lat':55+group*.001,'count':1,'type':'Hus'} for group,(prefix,number,size) in enumerate(groups) for i in range(size)]
    store.mutate('geo.import',{'records':records,'source':'Fictional local test','label':'Invented addresses'})
    cards={}
    for prefix,number,size in groups:
        ident=store.mutate('geo.assign',{'number':number,'name':'Fictional <card>','address_ids':[prefix+str(i) for i in range(size)]})['id']
        store.mutate('card.save',{**store.require('cards',ident),'area_id':area})
        cards[prefix]=ident
    store.mutate('loan.issue',{'card_id':cards['issued'],'publisher_name':'Fictional person','initial':True,'date':'2026-01-01'})
    store.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),store);accounts=server.accounts
    accounts.bootstrap('Fictional admin','Fictional-password-123')
    admin=accounts.login('Fictional admin','Fictional-password-123','fictional-admin')
    def stop(*args):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    print(json.dumps({'origin':server.origin,'cards':cards,'cookie':{'name':server.profiles.cookie,'value':admin,'url':server.origin}}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
