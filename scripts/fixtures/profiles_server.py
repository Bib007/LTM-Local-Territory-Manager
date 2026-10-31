"""Disposable normal LTM server for profile browser integration, invented data."""
import json
import signal
import sys
import tempfile
import io
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from store import Store
from server import Server
from runtime_status import RuntimeStatus
from ib_import import template_xlsx

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
    ib_file=Path(root)/'fiktiv-ib.xlsx'
    with zipfile.ZipFile(io.BytesIO(template_xlsx())) as source,zipfile.ZipFile(ib_file,'w') as target:
        for name in source.namelist():
            raw=source.read(name)
            if name=='xl/worksheets/sheet1.xml':
                sheet=raw.decode();start=sheet.index('<sheetData>');end=sheet.index('</sheetData>')
                table='<row r="1"><c r="A1" t="inlineStr"><is><t>kortnummer</t></is></c><c r="B1" t="inlineStr"><is><t>vejnavn</t></is></c><c r="C1" t="inlineStr"><is><t>husnummer</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>F101</t></is></c><c r="B2" t="inlineStr"><is><t>Fiktiv Excelvej</t></is></c><c r="C2" t="inlineStr"><is><t>01A</t></is></c></row>'
                raw=(sheet[:start]+'<sheetData>'+table+sheet[end:]).encode()
            target.writestr(name,raw)
    print(json.dumps({'origin':server.origin,'card':card,'ib_file':str(ib_file)}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
