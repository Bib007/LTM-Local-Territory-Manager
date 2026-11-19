"""Temporary fictional geometry for the neighbour-boundary browser regression."""
import json,math,signal,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from store import Store
from server import Server
with tempfile.TemporaryDirectory(prefix='ltm-fictional-outline-') as root:
    s=Store(root);scale=111320*math.cos(math.radians(55))
    def point(x,y):return [round(10+x/scale,7),round(55+y/111320,7)]
    def address(ident,x,y):
        lng,lat=point(x,y)
        return dict(id=ident,entity='address',road='Fiktivvej',number=ident,postcode='9999',lng=lng,lat=lat,count=1,type='Hus')
    target=s.mutate('card.save',{'number':'F001','temporary':True})['id']
    neighbor=s.mutate('card.save',{'number':'F002','temporary':True})['id']
    records=[address('1',-40,0),address('3',40,0),address('2',0,70)]
    with s.transaction():
        for a in records:s.put('geo',a)
        s.put('cards',{**s.require('cards',neighbor),'geo_polygon':[point(-10,-500),point(10,-500),point(10,500),point(-10,500)],'address_ids':['2'],'geo_addresses':[records[2]]})
    s.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),s)
    def stop(*args):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    print(json.dumps({'origin':server.origin,'target':target,'neighbor':neighbor}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();s.close()
