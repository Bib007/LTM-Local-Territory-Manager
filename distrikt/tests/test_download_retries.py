import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from geodata import Downloads
from postcode import Paused,SourceTimeout

class DownloadRetryTests(unittest.TestCase):
    def setUp(self):
        self.d=Downloads(None)
        self.d.cancel_event=Mock()
        self.d.cancel_event.is_set.return_value=False
        self.d.cancel_event.wait.return_value=False
    def response(self,value):return io.BytesIO(json.dumps(value).encode())
    def request(self):return self.d.request('services.datafordeler.dk','/DAR/test',{'page':2})
    def test_transient_page_retried_without_changing_query(self):
        with patch('urllib.request.urlopen',side_effect=[TimeoutError(),self.response([{'id':'public'}])]) as call:
            self.assertEqual(self.request(),[{'id':'public'}])
            self.assertEqual(call.call_count,2)
            self.assertEqual(call.call_args_list[0].args[0].full_url,call.call_args_list[1].args[0].full_url)
            self.d.cancel_event.wait.assert_called_once_with(2)
    def test_exhausted_timeout_has_specific_safe_error(self):
        with patch('urllib.request.urlopen',side_effect=urllib.error.URLError(TimeoutError('secret URL')) ) as call:
            with self.assertRaisesRegex(ValueError,'45 sekunder.*genprøvet 2'):self.request()
            self.assertEqual(call.call_count,3)
            self.assertEqual([x.args[0] for x in self.d.cancel_event.wait.call_args_list],[2,5])
    def test_pause_interrupts_backoff(self):
        self.d.cancel_event.wait.return_value=True
        with patch('urllib.request.urlopen',side_effect=TimeoutError()) as call:
            with self.assertRaises(Paused):self.request()
            self.assertEqual(call.call_count,1)
    def test_auth_and_permanent_http_errors_not_retried(self):
        for code in (400,401,403,404):
            with self.subTest(code=code),patch('urllib.request.urlopen',side_effect=urllib.error.HTTPError('secret',code,'secret',{},None)) as call:
                with self.assertRaises(ValueError):self.request()
                self.assertEqual(call.call_count,1)
    def test_rate_limit_cooldown_honoured(self):
        error=urllib.error.HTTPError('secret',429,'secret',{'Retry-After':'60'},None)
        with patch('urllib.request.urlopen',side_effect=[error,self.response(5)]):self.assertEqual(self.request(),5)
        self.d.cancel_event.wait.assert_called_once_with(60)
        for header in ('120','Wed, 07 Oct 2026 18:00:00 GMT'):
            error=urllib.error.HTTPError('secret',429,'secret',{'Retry-After':header},None)
            with patch('urllib.request.urlopen',side_effect=error) as call:
                with self.assertRaises(ValueError):self.request()
                self.assertEqual(call.call_count,1)
    def test_bad_json_and_server_error_can_recover(self):
        error=urllib.error.HTTPError('secret',503,'secret',{},None)
        with patch('urllib.request.urlopen',side_effect=[io.BytesIO(b'<html>'),error,self.response(7)]):self.assertEqual(self.request(),7)
    def test_retry_status_includes_stage_cause_and_restores_after_success(self):
        self.d.active='test';self.d.jobs['test']={'message':'Henter udsnit 4 af 28…'}
        def wait(delay):
            message=self.d.jobs['test']['message']
            self.assertIn('udsnit 4 af 28',message);self.assertIn('45 sekunder',message)
            return False
        self.d.cancel_event.wait.side_effect=wait
        with patch('urllib.request.urlopen',side_effect=[TimeoutError(),self.response(0)]):self.assertEqual(self.request(),0)
        self.assertEqual(self.d.jobs['test']['message'],'Henter udsnit 4 af 28…')

    def test_boundary_timeout_hands_off_to_split_without_same_size_retries(self):
        self.d.active='test';self.d.jobs['test']={'kind':'boundary','message':'Henter udsnit 1…'}
        for error in (TimeoutError(),urllib.error.URLError(TimeoutError())):
            with patch('urllib.request.urlopen',side_effect=error) as call:
                with self.assertRaises(SourceTimeout):self.request()
                self.assertEqual(call.call_count,1)
        self.d.cancel_event.wait.assert_not_called()

    def test_boundary_live_wait_status_and_longer_timeout(self):
        self.d.active='test';self.d.jobs['test']={'kind':'boundary','message':'Henter udsnit 7…','status':'running'}
        def respond(request,timeout):
            self.assertEqual(timeout,120)
            self.assertIn('DAR-adresseside',self.d.status('test')['message'])
            self.assertIn('højst 120 sek.',self.d.status('test')['message'])
            return self.response(0)
        with patch('urllib.request.urlopen',side_effect=respond):self.assertEqual(self.request(),0)
        self.assertEqual(self.d.status('test')['message'],'Henter udsnit 7…')
        self.assertNotIn('request_started',self.d.jobs['test'])

    def test_suggestion_requests_not_retried(self):
        with patch('urllib.request.urlopen',side_effect=TimeoutError()) as call:
            with self.assertRaises(ValueError):self.d.request('adressevaelger.dk','/soeg')
            self.assertEqual(call.call_count,1)
            self.d.cancel_event.wait.assert_not_called()
