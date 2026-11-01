"""Fictional clocks, pressure and transport: no owner's HA is contacted."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock,MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from runtime_status import RuntimeStatus,supervisor_post,NoRedirect


class RuntimeStatusTests(unittest.TestCase):
    def setUp(self):
        self.now=0;self.task={'enabled':True,'status':'scheduled'}
        self.reading={'available':True,'high':False}
        self.schedule=Mock();self.schedule.status.side_effect=lambda:self.task.copy()
        self.sent=[]
        self.bridge=RuntimeStatus(self.schedule,'fictional',True,enabled=True,token='fictional-secret',
            pressure=lambda:self.reading,clock=lambda:self.now,
            transport=lambda *args:self.sent.append(args))

    def test_normal_wait_and_budget_are_not_errors_and_pressure_is_sustained(self):
        self.assertEqual(self.bridge.sample()['state'],'waiting')
        self.task.update(status='waiting',retry_streak=9,retry_reason='budget')
        self.assertEqual(self.bridge.sample()['state'],'waiting')
        self.reading['high']=True
        self.bridge.sample();self.now=119
        self.assertEqual(self.bridge.sample()['state'],'waiting')
        self.now=120;self.assertEqual(self.bridge.sample()['state'],'pressure')
        self.reading['high']=False;self.assertEqual(self.bridge.sample()['state'],'waiting')
        self.reading['high']=True;self.now=121
        self.assertEqual(self.bridge.sample()['state'],'waiting','A new spike starts a fresh observation')

    def test_repeated_failures_are_visible_without_private_error_payload(self):
        self.task.update(status='waiting',retry_streak=3,retry_reason='source',last_problem='PRIVATE IB TOKEN path')
        self.assertEqual(self.bridge.sample()['state'],'waiting')
        self.task['retry_streak']=4;self.bridge.publish()
        self.assertEqual(self.sent[0][1]['state'],'error')
        wire=json.dumps(self.sent[0][1]);self.assertNotIn('PRIVATE',wire);self.assertNotIn('fictional-secret',wire)
        self.assertEqual(self.sent[0][0],'states/sensor.ltm_beta_drift')
        self.assertIsNotNone(self.bridge.status()['last_sent'])
        self.task.update(status='complete',retry_streak=0)
        self.assertEqual(self.bridge.sample()['state'],'idle')

    def test_missing_metrics_stay_unknown_and_bridge_delivery_failure_is_explicit(self):
        self.task.update(status='idle',enabled=False);self.reading.update(available=False)
        self.assertEqual(self.bridge.sample()['state'],'unknown')
        self.bridge.transport=Mock(side_effect=OSError('PRIVATE upstream path'))
        self.bridge.publish();status=self.bridge.status()
        self.assertTrue(status['delivery_failed']);self.assertIsNone(status['last_sent'])
        self.assertNotIn('PRIVATE',json.dumps(status))
        self.bridge.transport=lambda *args:None;self.bridge.publish()
        self.assertFalse(self.bridge.status()['delivery_failed'])

    def test_notification_test_is_fixed_and_not_replayed_after_unknown_result(self):
        self.bridge.transport=Mock(side_effect=OSError('PRIVATE'))
        with self.assertRaisesRegex(ValueError,'ukendt'):self.bridge.test_notification()
        self.bridge.transport.assert_called_once_with('events/ltm_status_test',{'entity_id':'sensor.ltm_beta_drift'},'fictional-secret')
        with self.assertRaisesRegex(ValueError,'Vent et minut'):self.bridge.test_notification()
        self.now=60;self.bridge.transport=lambda *args:self.sent.append(args)
        self.assertTrue(self.bridge.test_notification()['ok']);self.assertEqual(len(self.sent),1)

    def test_runtime_opt_out_and_desktop_do_not_publish(self):
        for env in ({'DISTRIKT_HOME_ASSISTANT':'1','DISTRIKT_HA_STATUS':'false','SUPERVISOR_TOKEN':'fictional'},
                    {'DISTRIKT_HA_STATUS':'true','SUPERVISOR_TOKEN':'fictional'},
                    {'DISTRIKT_HOME_ASSISTANT':'1','DISTRIKT_HA_STATUS':'true'}):
            with patch.dict(os.environ,env,clear=True):
                bridge=RuntimeStatus(self.schedule,'fictional',transport=Mock())
            bridge.start();bridge.publish();self.assertIsNone(bridge.thread)
            bridge.transport.assert_not_called()
            with self.assertRaises(ValueError):bridge.test_notification()
        with patch.dict(os.environ,{'DISTRIKT_HOME_ASSISTANT':'1','DISTRIKT_HA_STATUS':'true','SUPERVISOR_TOKEN':'fictional'},clear=True):
            self.assertTrue(RuntimeStatus(self.schedule,'fictional').enabled)

    def test_transport_is_fixed_local_bounded_and_refuses_redirects(self):
        opener=MagicMock();opener.open.return_value.__enter__.return_value=Mock()
        with patch('urllib.request.build_opener',return_value=opener) as factory:
            supervisor_post('states/sensor.ltm_beta_drift',{'state':'idle'},'fictional')
        req=opener.open.call_args.args[0]
        self.assertEqual(req.full_url,'http://supervisor/core/api/states/sensor.ltm_beta_drift')
        self.assertEqual(opener.open.call_args.kwargs,{'timeout':3})
        opener.open.return_value.__enter__.return_value.read.assert_called_once_with(1024)
        self.assertEqual(factory.call_args.args[0].proxies,{})
        redirect=factory.call_args.args[1];self.assertIsInstance(redirect,NoRedirect)
        self.assertIsNone(redirect.redirect_request(None,None,302,'',{},'https://example.invalid'))

if __name__=='__main__':unittest.main()
