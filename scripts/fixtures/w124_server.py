"""Loopback-only disposable W124 browser fixture; controls use parent stdin."""
import json
import signal
import sys
import tempfile
import threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from store import Store
from server import Server

with tempfile.TemporaryDirectory(prefix='ltm-fictional-w124-') as root:
    store=Store(root)
    card=store.mutate('card.save',{'number':'F101','name':'Fiktivt kort','temporary':True})['id']
    note=store.mutate('note.save',{'text':'Fiktiv opgave','card_id':card})['id']
    publisher=store.mutate('publisher.save',{'name':'Fiktiv person'})['id']
    area=store.mutate('area.save',{'name':'Fiktivt område'})['id']
    store.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),store)
    server.accounts.bootstrap('Fiktiv admin','Fiktiv-password-123')
    flags={'fail':False}
    original_state=server.app_state
    def state(*args,**kwargs):
        if flags['fail']:
            flags['fail']=False
            raise ValueError('Fictional post-commit snapshot failure')
        return original_state(*args,**kwargs)
    server.app_state=state
    def commands():
        for line in sys.stdin:
            command=json.loads(line)
            with server.accounts.lock,store.lock:
                if command['op']=='fail-read':flags['fail']=True
                elif command['op']=='expire-editors':
                    for item in server.profiles.bases._items.values():
                        if item.get('protected'):item['until']=0
                elif command['op']=='counts':pass
                else:raise ValueError('Unknown fictional fixture control')
                print(json.dumps({'id':command['id'],'ok':True,'snapshots':len(server.profiles.bases._items)}),flush=True)
    threading.Thread(target=commands,daemon=True).start()
    def stop(*args):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    print(json.dumps({'origin':server.origin,'card':card,'note':note,'publisher':publisher,'area':area}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
