"""Temporary app; invented DAR response, no network and no production data."""
import json
import io
import base64
import zipfile
from xml.sax.saxutils import escape
import signal
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from server import Server
from store import Store

def workbook(headers,values):
    from ib_import import template_xlsx
    out=io.BytesIO()
    table=''.join('<row r="'+str(i)+'">'+''.join('<c r="'+chr(65+j)+str(i)+'" t="inlineStr"><is><t>'+escape(str(v))+'</t></is></c>' for j,v in enumerate(row))+'</row>' for i,row in enumerate([headers,values],1))
    with zipfile.ZipFile(io.BytesIO(template_xlsx())) as source,zipfile.ZipFile(out,'w') as dest:
        for name in source.namelist():
            raw=source.read(name)
            if name=='xl/workbook.xml':raw=raw.replace(b'name="IB"',b'name="Import"')
            if name=='xl/worksheets/sheet1.xml':
                text=raw.decode();start=text.index('<sheetData>');end=text.index('</sheetData>');raw=(text[:start]+'<sheetData>'+table+text[end:]).encode()
            dest.writestr(name,raw)
    return base64.b64encode(out.getvalue()).decode()

with tempfile.TemporaryDirectory(prefix='ltm-fictional-streets-') as root:
    store=Store(root);cards=[]
    for index in range(2):
        road='Fictional road '+str(index)
        ident=store.mutate('card.save',{'number':'F'+str(index),'addresses':[{'road':road,'numbers':('hele vejen (kun ulige)' if index==0 else '23-25 & 24-26'),'count':4,'type':'Hus'}]})['id'];cards.append(ident)
    failed_card=store.mutate('card.save',{'number':'F-ERR','addresses':[{'road':'Unlisted <Test> Way','numbers':'11–19','count':4,'type':'Hus'}]})['id']
    store.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),store)
    def road(data,progress):
        if data['road']=='Unlisted <Test> Way' and data['postcode']=='9999':
            raise ValueError('Vejnavn og postnummer kunne ikke findes entydigt i DAR.')
        assert data['road'] in ('Fictional road 0','Fictional road 1') and data['postcode']=='9999'
        records=[dict(id=data['road']+str(n),entity='address',road=data['road'],number=str(n),postcode='9999',lng=10+n*.001,lat=55,count=1,type='Hus') for n in (range(1,8) if data['road'].endswith('0') else range(21,31))]
        result=store.mutate('geo.import',dict(records=records,source='DAR / Datafordeleren',label='Fictional test',complete_road={'road':data['road'],'postcode':'9999'}))
        return dict(result,road=data['road'],postcode='9999')
    server.downloads.road=road
    server.accounts.bootstrap('Fictional admin','Fictional-password-123')
    cookie=server.accounts.login('Fictional admin','Fictional-password-123','fictional-admin')
    def stop(*args):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    fronts=[workbook(['Card','Street','Range','Visits'],['M'+str(i),'Manual road '+str(i),'hele vejen' if i==0 else '23-25 & 24-26',12]) for i in range(2)]
    backs=[workbook(['Card','Street','Number','Date'],['M'+str(i),'Manual road '+str(i),'1A' if i==0 else '23-25 & 24-26','marts 2024' if i==0 else '2024']) for i in range(2)]
    print(json.dumps({'origin':server.origin,'cards':cards,'failed_card':failed_card,'fronts':fronts,'backs':backs,'cookie':{'name':server.profiles.cookie,'value':cookie,'url':server.origin}}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
