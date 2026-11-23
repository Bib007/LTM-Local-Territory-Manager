"""Only temporary fictional stores and local HTTP; never contact an owner's HA."""
import json
from pathlib import Path
import sys
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from runtime_probe import Observation,http_probe,NoRedirect
from runtime_status import RuntimeStatus
from server import Server,Handler
from store import Store


class ObservationTests(unittest.TestCase):
    def test_stuck_source_has_total_deadline_and_only_one_worker(self):
        now=[0];entered=threading.Event();release=threading.Event();calls=[]
        def blocked():
            calls.append(1);entered.set();release.wait(3);return 'ok'
        reading=Observation(blocked,clock=lambda:now[0])
        try:
            self.assertEqual(reading.poll(),('pending',None));self.assertTrue(entered.wait(1))
            now[0]=5
            for _ in range(10):self.assertEqual(reading.poll(),('timeout',None))
            self.assertEqual(len(calls),1)
            release.set();reading.thread.join(1)
            self.assertEqual(reading.poll(),('timeout',None),'A late success must not erase the missed deadline')
            now[0]=30;reading.poll();reading.thread.join(1)
            self.assertEqual(reading.poll(),('ok','ok'))
        finally:release.set();reading.thread.join(1)

    def test_failed_source_does_not_expose_exception_text(self):
        reading=Observation(Mock(side_effect=ValueError('PRIVATE IB TOKEN')))
        reading.poll();reading.thread.join(1)
        self.assertEqual(reading.poll(),('error',None))

    def test_http_transport_is_fixed_no_proxy_redirect_or_browser_credentials(self):
        opener=Mock();response=Mock(status=200)
        opener.open.return_value.__enter__=Mock(return_value=response)
        opener.open.return_value.__exit__=Mock(return_value=False)
        response.read.return_value=b'{"status":"ok","challenge":"' + b'a'*32 + b'"}'
        with patch('runtime_probe.secrets.token_hex',return_value='a'*32),patch('urllib.request.build_opener',return_value=opener) as factory:
            self.assertEqual(http_probe('http://127.0.0.1:1234','fictional-probe-key'),'ok')
        request=opener.open.call_args.args[0]
        self.assertEqual(request.full_url,'http://127.0.0.1:1234/api/runtime/probe')
        self.assertEqual(set(dict(request.header_items())),{'X-ltm-probe-key','X-ltm-probe-challenge'})
        self.assertEqual(opener.open.call_args.kwargs,{'timeout':3})
        response.read.assert_called_once_with(513)
        self.assertEqual(factory.call_args.args[0].proxies,{})
        self.assertIsInstance(factory.call_args.args[1],NoRedirect)
        self.assertIsNone(factory.call_args.args[1].redirect_request(None,None,302,'',{},'https://example.invalid'))


class RuntimeProbeHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='ltm-fictional-probe-')
        self.store=Store(self.temp.name)
        self.server=Server(('127.0.0.1',0),self.store,access_host='192.168.1.77',password='Fictional-password-123')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.now=0;self.sent=[]
        self.bridge=RuntimeStatus(self.server.address_schedule,'fictional',enabled=True,token='fictional-HA-token',
            pressure=lambda:{'available':True,'high':False},clock=lambda:self.now,
            transport=lambda *args:self.sent.append(args),probe=lambda:http_probe(self.server.origin,self.server.runtime_probe_key),task_status=self.server.runtime_task_status)

    def tearDown(self):
        for reading in (self.bridge.sampler,self.bridge.probe):
            if reading.thread:reading.thread.join(2)
        self.server.shutdown();self.server.server_close();self.thread.join(2)
        self.store.close();self.temp.cleanup()

    def test_public_ping_stays_responsive_while_a_save_holds_account_lock(self):
        # A legitimate write may hold the profile lock for a long snapshot.
        # That must not make the browser falsely declare its server offline.
        acquired=threading.Event();release=threading.Event()
        def held_lock():
            with self.server.accounts.lock:
                acquired.set();release.wait(4)
        worker=threading.Thread(target=held_lock,daemon=True);worker.start()
        try:
            self.assertTrue(acquired.wait(2))
            request=urllib.request.Request(self.server.origin+'/api/ping')
            with urllib.request.urlopen(request,timeout=1.5) as response:
                self.assertEqual(json.load(response)['app'],'Distrikt')
        finally:
            release.set();worker.join(2)
            self.assertFalse(worker.is_alive())

    def settled(self):
        # Establish a quiet recovery observation, rather than racing the probe
        # against the sampler's own brief Store read (legitimately 'busy').
        for reading in (self.bridge.sampler,self.bridge.probe):
            reading.poll();reading.thread.join(2)
            self.assertFalse(reading.thread.is_alive())
        self.bridge.publish()
        return self.sent[-1][1]

    def test_parallel_publish_short_sampler_reads_never_accumulate_busy_alarm(self):
        entered=threading.Event()
        def ordinary_read():
            with self.store.lock:
                entered.set();time.sleep(.1)
                return {'status':'idle'}
        def overlapping_probe():
            if not entered.wait(2):raise AssertionError('sampler never entered')
            return http_probe(self.server.origin,self.server.runtime_probe_key)
        self.bridge.probe.read=overlapping_probe
        values=[]
        with patch.object(self.server.address_schedule,'status',ordinary_read):
            for now in (0,30,60,90,120,150):
                self.now=now;entered.clear()
                self.bridge.publish()
                for reading in (self.bridge.sampler,self.bridge.probe):
                    reading.thread.join(2)
                    self.assertFalse(reading.thread.is_alive())
                self.bridge.publish()
                value=self.sent[-1][1]
                values.append(value)
        self.assertEqual([v['state'] for v in values],['idle']*6,values)
        for value in values:
            self.assertEqual(value['attributes']['http_status'],'busy')
            self.assertEqual(value['attributes']['problem_seconds'],0,value)

    def test_parallel_sampler_progress_clears_a_real_alarm_despite_busy_snapshots(self):
        entered=threading.Event()
        def ordinary_read():
            with self.store.lock:
                entered.set();time.sleep(.1)
                return {'status':'idle'}
        def overlapping_probe():
            if not entered.wait(2):raise AssertionError('sampler never entered')
            return http_probe(self.server.origin,self.server.runtime_probe_key)
        with self.store.lock:
            self.bridge.publish();self.bridge.probe.thread.join(2)
            self.assertFalse(self.bridge.probe.thread.is_alive())
            self.now=6;self.bridge.publish()
            self.now=126;self.bridge.publish();self.bridge.probe.thread.join(2)
            self.assertEqual(self.sent[-1][1]['state'],'unresponsive')
        self.bridge.sampler.thread.join(2)
        self.assertFalse(self.bridge.sampler.thread.is_alive())
        self.bridge.probe.read=overlapping_probe
        with patch.object(self.server.address_schedule,'status',ordinary_read):
            self.now=156
            self.bridge.publish()
            for reading in (self.bridge.sampler,self.bridge.probe):
                reading.thread.join(2)
                self.assertFalse(reading.thread.is_alive())
            self.bridge.publish()
        value=self.sent[-1][1]
        self.assertEqual(value['state'],'idle',value)
        self.assertEqual(value['attributes']['http_status'],'busy')
        self.assertEqual(value['attributes']['problem_seconds'],0)

    def request(self,headers):
        return urllib.request.urlopen(urllib.request.Request(self.server.origin+'/api/runtime/probe',headers=headers),timeout=1)

    def test_probe_is_private_even_with_normal_server_token_and_checks_host_origin_challenge(self):
        before=self.store.revision
        valid={'X-LTM-Probe-Key':self.server.runtime_probe_key,'X-LTM-Probe-Challenge':'a'*32}
        for headers,code in (({},403),({'X-Distrikt-Token':self.server.token},403),({'X-LTM-Probe-Key':'ø'},403),
                ({**valid,'Origin':self.server.origin},403),({**valid,'Host':'example.invalid'},403),
                ({**valid,'X-LTM-Probe-Challenge':'bad'},400)):
            with self.subTest(headers=list(headers)):
                with self.assertRaises(urllib.error.HTTPError) as error:self.request(headers)
                self.assertEqual(error.exception.code,code)
                self.assertNotIn(self.server.runtime_probe_key,error.exception.read().decode())
        fake=Mock(server=self.server,client_address=('192.168.1.8',123),headers=valid)
        Handler.runtime_probe(fake)
        self.assertEqual(fake.send.call_args.kwargs['status'],403)
        with self.request(valid) as response:
            self.assertEqual(json.load(response),{'status':'ok','challenge':'a'*32})
            self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(self.store.revision,before)

    def test_busy_store_and_account_locks_cannot_block_heartbeat_and_recover_without_restart(self):
        before=self.store.revision
        self.assertEqual(self.settled()['state'],'idle')
        for lock in (self.store.lock,self.server.accounts.lock):
            with self.subTest(lock=type(lock).__name__):
                with lock:
                    self.now+=30
                    self.bridge.publish()
                    self.bridge.probe.thread.join(1)
                    value=self.sent[-1][1]
                    self.bridge.publish();value=self.sent[-1][1]
                    self.assertEqual(value['attributes']['diagnostic'],'runtime_busy')
                    self.assertNotEqual(value['state'],'unresponsive','Short saves do not alert')
                    # A cached success is not a fresh completion. The blocked
                    # sampler must independently exceed its deadline first.
                    self.now+=6;self.bridge.publish()
                    self.assertEqual(self.sent[-1][1]['attributes']['status_sample'],'timeout')
                    if lock is self.store.lock:
                        free=self.server.accounts.lock.acquire(blocking=False)
                        self.assertTrue(free,'Monitoring must not retain Accounts while waiting for Store')
                        if free:self.server.accounts.lock.release()
                    self.now+=120
                    started=time.monotonic();self.bridge.publish()
                    self.assertLess(time.monotonic()-started,1)
                    self.bridge.probe.thread.join(1)
                    self.assertEqual(self.sent[-1][1]['state'],'unresponsive')
                    self.assertTrue(self.sent[-1][1]['attributes']['updated_at'])
                # The original worker finishes; a fresh sample establishes recovery.
                self.bridge.sampler.thread.join(1)
                self.now+=30
                self.assertEqual(self.settled()['state'],'idle')
        self.assertNotIn('fictional-HA-token',json.dumps([row[1] for row in self.sent]))
        self.assertEqual(self.store.revision,before)
        self.assertTrue(self.thread.is_alive())

    def test_blocked_http_does_not_prevent_publishing_or_spawn_repeated_requests(self):
        entered=threading.Event();release=threading.Event();calls=[]
        original=Handler.runtime_probe
        def blocked(handler):
            calls.append(1);entered.set();release.wait(3);original(handler)
        with patch.object(Handler,'runtime_probe',blocked):
            try:
                self.bridge.publish();self.assertTrue(entered.wait(1))
                self.now=6;self.bridge.publish()
                self.assertEqual(self.sent[-1][1]['attributes']['diagnostic'],'http_timeout')
                self.now=126
                for _ in range(3):self.bridge.publish()
                self.assertEqual(self.sent[-1][1]['state'],'unresponsive')
                self.assertEqual(len(calls),1)
            finally:release.set();self.bridge.probe.thread.join(1)
        self.now=156;self.assertEqual(self.settled()['state'],'idle')

    def test_slow_drip_response_is_bounded_by_total_time_not_socket_activity(self):
        entered=threading.Event();release=threading.Event()
        def slow(handler):
            handler.send_response(200);handler.send_header('Content-Length','100');handler.end_headers()
            handler.wfile.write(b'{');handler.wfile.flush();entered.set()
            release.wait(3)
            handler.wfile.write(b' '*99)
        with patch.object(Handler,'runtime_probe',slow):
            try:
                self.bridge.publish();self.assertTrue(entered.wait(1))
                self.now=6;self.bridge.publish();self.now=126;self.bridge.publish()
                self.assertEqual(self.sent[-1][1]['state'],'unresponsive')
                self.assertEqual(self.sent[-1][1]['attributes']['diagnostic'],'http_timeout')
            finally:release.set();self.bridge.probe.thread.join(1)

    def test_status_sampler_can_stall_while_http_and_delivery_continue(self):
        entered=threading.Event();release=threading.Event()
        def stalled():entered.set();release.wait(3);return {'available':True,'high':False}
        with patch.object(self.bridge,'pressure',stalled):
            try:
                self.bridge.publish();self.assertTrue(entered.wait(1));self.bridge.probe.thread.join(1)
                self.now=6;self.bridge.publish()
                self.assertEqual(self.sent[-1][1]['attributes']['diagnostic'],'status_timeout')
                self.now=126;self.bridge.publish();self.bridge.probe.thread.join(1)
                self.assertEqual(self.sent[-1][1]['state'],'unresponsive')
                self.assertEqual(self.sent[-1][1]['attributes']['http_status'],'ok')
            finally:release.set();self.bridge.sampler.thread.join(1)
        self.now=156;self.assertEqual(self.settled()['state'],'idle')

    def test_refused_http_connection_is_reported_without_exception_or_url(self):
        with socket.socket() as closed_listener:
            closed_listener.bind(('127.0.0.1',0))
            origin='http://127.0.0.1:'+str(closed_listener.getsockname()[1])
        # Close the reserved socket before connecting. A bound but still open
        # socket can time out instead of refusing immediately on macOS.
        self.bridge.probe.read=lambda:http_probe(origin,'fictional')
        value=self.settled()
        self.assertEqual(value['attributes']['diagnostic'],'http_error')
        self.assertNotIn(origin,json.dumps(value))

    def test_stale_or_unexpected_http_body_is_rejected(self):
        for body in ({'status':'ok','challenge':'old-cached-response'}, {'status':'PRIVATE IB TOKEN'}, ['PRIVATE'], 'x'*600):
            def wrong(handler):handler.send(body)
            with self.subTest(body=type(body).__name__),patch.object(Handler,'runtime_probe',wrong):
                self.now+=30;value=self.settled()
                self.assertIn(value['attributes']['diagnostic'],('http_error','http_invalid_response'))
                self.assertNotIn('PRIVATE',json.dumps(value))


if __name__=='__main__':unittest.main()
