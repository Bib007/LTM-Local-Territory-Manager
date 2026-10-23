"""Long fictional previews remain observable through short authenticated requests."""
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from setup_jobs import SetupJobs
from ui_errors import UIError
from store import Store
from server import Server

class SetupJobsTests(unittest.TestCase):
    def test_status_does_not_wait_on_a_long_preview_and_input_is_copied(self):
        entered=threading.Event();finish=threading.Event();seen=[]
        def calculate(action,data):
            entered.set();finish.wait(3);seen.append((action,data));return {'token':'fictional','cards':[]}
        store=Mock();store.mutate=calculate;store.revision='fictional';jobs=SetupJobs(store)
        data={'areas':[{'name':'Fiktivt område'}]};job=jobs.start('setup.preview',data)['job_id'];self.assertTrue(entered.wait(1))
        data['areas'][0]['name']='Changed by caller'
        try:
            before=time.monotonic();self.assertEqual(jobs.status(job)['status'],'running');self.assertLess(time.monotonic()-before,.2)
            with self.assertRaises(ValueError):jobs.start('setup.adjust.preview',{})
        finally:finish.set()
        for _ in range(100):
            if jobs.status(job)['status']!='running':break
            time.sleep(.01)
        self.assertEqual(jobs.status(job)['response']['result']['token'],'fictional')
        self.assertEqual(seen,[('setup.preview',{'areas':[{'name':'Fiktivt område'}]})])
        with self.assertRaises(ValueError):jobs.start('setup.apply',{})
    def test_typed_errors_preserve_parameters_and_unexpected_errors_hide_details(self):
        for error,expected in [(UIError('Området {name} findes allerede. Vælg det fra listen.',name='Fiktivt'), 'Området Fiktivt findes allerede. Vælg det fra listen.'),(RuntimeError('FICTIONAL_INTERNAL_VALUE'),'Kortforslaget kunne ikke beregnes. Eksisterende kort er ikke ændret.')]:
            store=Mock();store.mutate.side_effect=error;jobs=SetupJobs(store)
            job=jobs.start('setup.preview',{})['job_id']
            for _ in range(100):
                result=jobs.status(job)
                if result['status']!='running':break
                time.sleep(.01)
            self.assertEqual(result['error'],expected);self.assertNotIn('FICTIONAL_INTERNAL_VALUE',json.dumps(result))

class SetupJobsHTTPTests(unittest.TestCase):
    def test_archived_job_endpoint_remains_authenticated(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(folder);server=Server(('127.0.0.1',0),store);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                for token,status in ((False,403),(True,400)):
                    headers={'X-Distrikt-Token':server.token} if token else {}
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(urllib.request.Request(server.origin+'/api/setup/job?id=fictional',headers=headers),timeout=1)
                    self.assertEqual(error.exception.code,status)
            finally:server.shutdown();thread.join();server.server_close();store.close()

if __name__=='__main__':unittest.main()
