import copy
import json
import os
import threading
import urllib.request
import urllib.error
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from address_schedule import AddressSchedule, RECORD
from store import Store
from geodata import Downloads
from postcode import SourceUnavailable
from test_postcode import unit
from test_boundary_download import POLY

class AddressScheduleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.store.mutate('geo.main.save',{'points':POLY})
        self.downloads=Downloads(self.store);self.downloads.address_source=Mock()
        self.downloads.address_source.status.return_value={'configured':True}
        # Explicitly use the fictional legacy adapter; no provider is contacted.
        self.downloads.source_id=lambda:'dar-rest-v3';self.downloads.source_schema=lambda:None
        self.now=datetime(2026,10,21,12,tzinfo=timezone.utc)
        self.scheduler=AddressSchedule(self.store,self.downloads,True,lambda:self.now)
        self.rows=[unit('a')];self.fail=False;self.calls=[]
        def request(host,path,params=None,query=None):
            self.calls.append(copy.deepcopy(params))
            if self.fail:raise SourceUnavailable('Fiktiv netfejl')
            return len(self.rows) if params.get('count') else copy.deepcopy(self.rows) if params['page']==1 else []
        self.downloads.request=request
        def start(kind,data):
            self.downloads.active='fictional-job';self.downloads.cancel_event.clear()
            self.downloads.jobs['fictional-job']={'id':'fictional-job','kind':kind,'status':'running','message':''}
            self.downloads.run('fictional-job',kind,data)
            return {'job_id':'fictional-job'}
        self.downloads.start=start
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def configure(self,**changes):
        self.scheduler.configure(dict(enabled=True,days=7,time='02:00',_revision=self.store.revision,**changes))
    def due(self):
        self.configure();self.now+=timedelta(days=1)
    def complete(self):self.scheduler.tick();self.scheduler.tick()
    def test_configuration_is_ha_only_validated_and_does_not_run_immediately(self):
        for field,value in [('days',0),('days',True),('days',31),('time','25:00'),('enabled','yes')]:
            data=dict(enabled=True,days=7,time='02:00',_revision=self.store.revision);data[field]=value
            with self.assertRaises(ValueError):self.scheduler.configure(data)
        self.scheduler.configure(dict(enabled=True,days=7,time='02:00',_revision='old'))
        self.scheduler.configure(dict(enabled=True,days=7,time='02:00'))
        self.scheduler.available=False
        with self.assertRaises(ValueError):self.configure()
        self.scheduler.available=True;self.configure();self.scheduler.tick()
        self.assertFalse(self.calls);self.assertEqual(self.scheduler.status()['status'],'scheduled')
    def test_new_street_is_staged_and_requires_explicit_review(self):
        self.due();self.complete();status=self.scheduler.status()
        self.assertEqual(status['status'],'complete');self.assertEqual(status['last_result'],{'new':1,'changed':0,'retired':0})
        self.assertEqual(self.store.geo_state()['addresses'],[])
        changes=self.store.geo_state()['changes'];self.assertEqual(len(changes),1)
        self.store.mutate('address.change.review',{'id':changes[0]['id'],'decision':'accept'})
        self.assertEqual(len(self.store.geo_state()['addresses']),1)
        self.assertGreater(status['next_due'],status['completed_at'])
    def test_partial_results_do_not_retire_and_retry_survives_restart(self):
        self.store.mutate('geo.import',{'records':[{'id':'dar:old','road':'Fiktiv vej','number':'8','postcode':'9999','lng':9,'lat':55,'entity':'address','verified':True}], 'source':'DAR / Datafordeleren'})
        self.due();self.fail=True;self.complete();waiting=self.scheduler.status()
        self.assertEqual(waiting['status'],'waiting');self.assertEqual(self.store.geo_state()['changes'],[])
        snapshot=self.store.get('geo','main-boundary-download')['snapshot'];count=len(self.calls)
        self.scheduler=AddressSchedule(self.store,self.downloads,True,lambda:self.now)
        self.scheduler.tick();self.assertEqual(len(self.calls),count)
        self.now+=timedelta(minutes=16);self.fail=False;self.complete()
        self.assertEqual(self.scheduler.status()['status'],'complete')
        self.assertEqual(self.store.get('geo','main-boundary-download')['snapshot'],snapshot)
        changes=self.store.geo_state()['changes'];self.assertEqual({c['kind'] for c in changes},{'new','retired'})
        self.assertFalse(self.store.get('geo','dar:old').get('retired'))
    def test_duplicate_new_source_rows_cannot_bypass_review(self):
        self.rows=[unit('a'),unit('a')];self.due();self.complete()
        self.assertEqual(self.store.geo_state()['addresses'],[])
        self.assertEqual(self.scheduler.status()['status'],'waiting')
        self.assertEqual(self.store.geo_state()['changes'],[])
        address={'id':'dar:new','road':'Fiktiv vej','number':'1','postcode':'9999','lng':9,'lat':55,'entity':'address','verified':True}
        self.store.mutate('geo.import',{'records':[address,address],'source':'DAR / Datafordeleren','review_changes':True,'review_all':True,'check_run':'fictional'})
        self.assertEqual(self.store.geo_state()['addresses'],[])
        self.assertEqual(len(self.store.geo_state()['changes']),1)
    def test_persisted_retry_survives_store_close_and_reopen(self):
        self.due();self.fail=True;self.complete();before=self.scheduler.status()
        self.store.close();self.store=Store(self.tmp.name);self.downloads.store=self.store
        self.scheduler=AddressSchedule(self.store,self.downloads,True,lambda:self.now)
        self.assertEqual(self.scheduler.status()['run'],before['run'])
        self.now+=timedelta(minutes=16);self.fail=False;self.complete()
        self.assertEqual(self.scheduler.status()['status'],'complete')
    def test_completed_snapshot_supersedes_disappeared_new_proposal(self):
        self.due();self.complete();self.assertEqual(self.scheduler.status()['pending'],1)
        self.now+=timedelta(days=8);self.rows=[];self.complete()
        self.assertEqual(self.scheduler.status()['status'],'complete');self.assertEqual(self.scheduler.status()['pending'],0)
    def test_no_concurrent_download_and_disable_waiting_task(self):
        self.due();self.downloads.active='manual';self.scheduler.tick();self.assertFalse(self.calls)
        self.downloads.active=None;self.fail=True;self.complete();self.assertTrue(self.scheduler.busy())
        self.scheduler.configure(dict(enabled=False,days=7,time='02:00',_revision=self.store.revision))
        self.scheduler.tick();self.assertFalse(self.scheduler.busy());self.assertFalse(self.scheduler.status()['enabled'])
    def test_empty_snapshot_preserves_existing_addresses(self):
        self.store.mutate('geo.import',{'records':[{'id':'dar:old','road':'Fiktiv vej','number':'8','postcode':'9999','lng':9,'lat':55,'entity':'address','verified':True}], 'source':'DAR / Datafordeleren'})
        self.due();self.rows=[];self.complete()
        # REST empty snapshots are allowed by the existing adapter, but still only stage removal.
        self.assertFalse(self.store.get('geo','dar:old').get('retired'))
        self.assertEqual(self.store.geo_state()['changes'][0]['kind'],'retired')

class AddressTaskHTTPTests(unittest.TestCase):
    def setUp(self):
        from server import Server
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.store.mutate('geo.main.save',{'points':POLY})
        with patch.dict(os.environ,{'DISTRIKT_HOME_ASSISTANT':'1'}):self.server=Server(('127.0.0.1',0),self.store)
        self.server.address_source.status=Mock(return_value={'configured':True})
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.thread.join();self.server.server_close();self.store.close();self.tmp.cleanup()
    def api(self,path,data=None,token=True):
        headers={'X-Distrikt-Token':self.server.token} if token else {}
        raw=json.dumps(data).encode() if data is not None else None
        if raw is not None:headers['Content-Type']='application/json'
        with urllib.request.urlopen(urllib.request.Request(self.server.origin+path,raw,headers),timeout=3) as response:return json.load(response)
    def test_real_task_api_preserves_revision_and_server_only_contract(self):
        state=self.api('/api/state');self.assertTrue(state['address_task']['available'])
        data={'action':'address.task.configure','data':{'enabled':True,'days':3,'time':'02:15','_revision':state['revision']}}
        with self.assertRaises(urllib.error.HTTPError) as error:self.api('/api/mutate',data,False)
        self.assertEqual(error.exception.code,403)
        self.api('/api/mutate',data)
        saved=self.api('/api/state');self.assertEqual(saved['address_task']['days'],3);self.assertEqual(saved['address_task']['time'],'02:15');self.assertEqual(saved['areas'],[])
        self.assertNotEqual(saved['revision'],state['revision'])
        self.api('/api/mutate',data)  # Stale cross-tab revisions no longer block configuration.
        self.server.address_schedule.available=False
        data['data']['_revision']=saved['revision']
        with self.assertRaises(urllib.error.HTTPError):self.api('/api/mutate',data)
        self.assertEqual(self.api('/api/state')['address_task']['days'],3)

if __name__=='__main__':unittest.main()
