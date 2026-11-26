"""Normal HTTP app with only disposable fictional data, for W127 browser tests."""
import sys,json,signal,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from store import Store
from server import Server
with tempfile.TemporaryDirectory(prefix='ltm-fictional-columns-') as root:
    store=Store(root)
    store.mutate('card.save',{'number':'F001','name':'Opdigtet prøvekort','temporary':True})
    store.mutate('setup.onboarding.save',{'answers':{'mode':'desk','boundary':'later','cards':'numbers','ib':'later'},'tour_completed':True})
    server=Server(('127.0.0.1',0),store)
    def stop(*args):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop)
    print(json.dumps({'origin':server.origin}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();store.close()
