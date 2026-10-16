"""Subprocess lifecycle on loopback; uses isolated test data, never default data."""
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

SERVER=Path(__file__).resolve().parents[1]/'app'/'server.py'

class LauncherTests(unittest.TestCase):
    def stop_isolated_server(self,data):
        """Wait for shutdown and release of the child-owned Windows log handle."""
        subprocess.run([sys.executable,str(SERVER),'--data-dir',str(data),'--stop'],check=True,capture_output=True,timeout=10)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if not (data/'run.json').exists():
                try:
                    (data/'start.log').unlink(missing_ok=True)
                except PermissionError:
                    # The server removes run.json just before interpreter exit.
                    # Windows may still hold the inherited log handle briefly.
                    pass
                else:return
            time.sleep(.05)
        self.fail('Isolated server failed to stop and release its log')

    def test_upgrade_from_previous_zip_keeps_all_records_and_print_profile(self):
        import zipfile
        previous=SERVER.parents[2]/'Distrikt-lokal-v1.10.1.zip'
        if not previous.exists():self.skipTest('Kræver den forrige program-ZIP ved siden af projektmappen.')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);data=root/'isolated-data'
            with zipfile.ZipFile(previous) as archive:archive.extractall(root/'previous')
            old=root/'previous'/'Distrikt-lokal'/'app'/'server.py'
            info=None
            def launch(server):
                result=subprocess.run([sys.executable,str(server),'--data-dir',str(data),'--no-browser'],capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,0,result.stderr)
                return json.loads((data/'run.json').read_text())
            def request(path,body=None):
                req=urllib.request.Request(info['url']+path,data=json.dumps(body).encode() if body else None,headers={'X-Distrikt-Token':info['token'],'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=5) as response:return json.load(response)
            def mutate(action,payload):return request('/api/mutate',{'action':action,'data':payload})['result']
            try:
                info=launch(old)
                c=mutate('card.save',{'number':'120','temporary':True})['id']
                p=mutate('publisher.save',{'name':'Fiktiv testperson'})['id']
                l=mutate('loan.issue',{'card_id':c,'publisher_id':p,'date':'2026-01-01','initial':True})['id']
                mutate('ib.save',{'card_id':c,'road':'Eksempelvej','number':'1','date':'2026-01-01'})
                mutate('visit.save',{'date':'2026-01-01','note':'Fiktiv kontrol'})
                mutate('print.profile.save',{'side':'back','profile':{'orientation':'portrait','paper':'cut','mode':'full','width':94,'height':146,'x':1,'y':-1}})
                before=request('/api/state');old_pid=info['pid'];files=set(f.name for f in data.glob('*.sqlite3'))
                info=launch(SERVER);after=request('/api/state')
                self.assertEqual(after['version'],'1.12.0-beta.2');self.assertNotEqual(info['pid'],old_pid)
                for key in ('cards','publishers','loans','ib','completions','visits','ignored','settings','areas'):self.assertEqual(before[key],after[key],key)
                self.assertEqual(files|{'kortnoter.sqlite3'},set(f.name for f in data.glob('*.sqlite3')));self.assertEqual(len(files),11)
                self.assertEqual(after['loans'][0]['id'],l)
            finally:
                if info:self.stop_isolated_server(data)

    def test_restart_and_reuse_preserve_records(self):
        with tempfile.TemporaryDirectory() as directory:
            command=[sys.executable,str(SERVER),'--data-dir',directory,'--no-browser']
            def launch():
                result=subprocess.run(command,capture_output=True,text=True,timeout=15)
                # This isolated test directory contains fictional records only.
                log=Path(directory)/'start.log'
                diagnostic=log.read_text(errors='replace') if result.returncode and log.exists() else ''
                self.assertEqual(result.returncode,0,result.stderr+'\n'+diagnostic)
                return json.loads((Path(directory)/'run.json').read_text())
            def request(info,path,body=None):
                req=urllib.request.Request(info['url']+path,data=json.dumps(body).encode() if body else None,headers={'X-Distrikt-Token':info['token'],'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=4) as response:return json.load(response)
            def stop(info):
                self.stop_isolated_server(Path(directory))
            info=None
            try:
                info=launch()
                self.assertEqual(re.match(r'^http://127\.0\.0\.1:\d+$',info['url']).group(),info['url'])
                ident=request(info,'/api/mutate',{'action':'card.save','data':{'number':'991','temporary':True}})['result']['id']
                same=launch();self.assertEqual(info['pid'],same['pid']);self.assertEqual(info['url'],same['url'])
                stop(info);info=None
                info=launch();self.assertEqual(request(info,'/api/state')['cards'][0]['id'],ident)
            finally:
                if info:stop(info)
