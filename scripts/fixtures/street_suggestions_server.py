"""Temporary app; invented DAR response, no network and no production data."""
import json
import signal
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from server import Server
from store import Store

with tempfile.TemporaryDirectory(prefix='ltm-fictional-streets-') as root:
    store=Store(root);cards=[]
    for index in range(2):
        road='Fictional road '+str(index)
        ident=store.mutate('card.save',{'number':'F'+str(index),'addresses':[{'road':road,'numbers':'1–5 (ulige)','count':3,'type':'Hus'}]})['id'];cards.append(ident)
    store.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),store)
    def road(data,progress):
        assert data['road'] in ('Fictional road 0','Fictional road 1') and data['postcode']=='9999'
        records=[dict(id=data['road']+str(n),entity='address',road=data['road'],number=str(n),postcode='9999',lng=10+n*.001,lat=55,count=1,type='Hus') for n in range(1,8)]
        result=store.mutate('geo.import',dict(records=records,source='DAR / Datafordeleren',label='Fictional test',complete_road={'road':data['road'],'postcode':'9999'}))
        return dict(result,road=data['road'],postcode='9999')
    server.downloads.road=road
    server.accounts.bootstrap('Fictional admin','Fictional-password-123')
    cookie=server.accounts.login('Fictional admin','Fictional-password-123','fictional-admin')
    def stop(*args):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    print(json.dumps({'origin':server.origin,'cards':cards,'cookie':{'name':server.profiles.cookie,'value':cookie,'url':server.origin}}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
