"""Only fictional ephemeral data; drives the real app and browser below."""
from pathlib import Path
import json,os,sys,tempfile,threading,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from server import Server
from store import Store
out=Path(os.environ.get('LTM_BROWSER_OUTPUT','/tmp/ltm-roles-guide/implementation/browser'));out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ltm-fictional-roles-',dir='/tmp') as folder:
 store=Store(folder);srv=Server(('127.0.0.1',0),store);a=srv.accounts
 admin_id=a.bootstrap('Fiktiv admin','Fiktiv-password-123');admin=a.login('Fiktiv admin','Fiktiv-password-123','fictional-admin')
 role=a.save_role(admin,'Fiktiv oversigtsrolle',['dashboard.view','reports.view']);reader=a.save_user(admin,'Fiktiv læser',[role],password='Fiktiv-password-456');reader_token=a.login('Fiktiv læser','Fiktiv-password-456','fictional-reader')
 card=store.mutate('card.save',{'number':'F101','name':'Fiktiv privat kortnavn','temporary':True})['id'];store.mutate('publisher.save',{'name':'Fiktiv privat person'});store.mutate('note.save',{'text':'Fiktiv privat note','card_id':card})
 cookie=lambda token:{'name':srv.profiles.cookie,'value':token,'url':srv.origin}
 fixture={'url':srv.origin,'admin':cookie(admin),'reader':cookie(reader_token),'reader_id':reader,'out':str(out)}
 thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start()
 try:
  env={**os.environ,'LTM_ROLES_FIXTURE':json.dumps(fixture)}
  result=subprocess.run(['/Users/tobiaslarsen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node',str(Path(__file__).resolve().parents[1]/'check_roles_guides_browser.cjs')],env=env,capture_output=True,text=True,timeout=110)
  proof={'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'onboarding':store.state()['settings'].get('onboarding'),'reader_intro':a.data['users'][reader].get('intro')};(out/'result.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2));sys.exit(result.returncode)
 finally:srv.shutdown();srv.server_close();thread.join();store.close()
