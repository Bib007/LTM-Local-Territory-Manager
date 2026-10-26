"""Shared startup choices, isolated paths and a real authenticated bound server."""
import contextlib
import http.cookiejar
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import launcher
from access import Access,write_private


class StartGuideTests(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(os.environ,dict(os.environ));self.environment.start()
    def tearDown(self):self.environment.stop()

    def test_platform_start_file_reuses_its_own_local_data(self):
        folder=Path(__file__).resolve().parents[1]
        start=folder/('Start-LTM.cmd' if os.name=='nt' else 'Start-LTM.command' if sys.platform=='darwin' else 'Start-LTM.sh')
        with tempfile.TemporaryDirectory(prefix='ltm fictional ') as directory:
            locations=launcher.paths(Path(directory));config=locations['config'];config.parent.mkdir()
            write_private(config,{'mode':'local'})
            command=([os.environ.get('COMSPEC','cmd.exe'),'/d','/c',str(start)] if os.name=='nt' else ['bash' if sys.platform=='darwin' else 'sh',str(start)])+['--root',directory,'--no-browser']
            try:
                for _ in range(2):
                    result=subprocess.run(command,capture_output=True,text=True,timeout=20)
                    self.assertEqual(result.returncode,0,result.stderr)
                    info=json.loads((locations['local']/'run.json').read_text())
                    if _==0:pid=info['pid']
                    else:self.assertEqual(info['pid'],pid)
                self.assertFalse(locations['server'].exists())
                self.assertEqual(json.loads(config.read_text()),{'mode':'local'})
            finally:
                launcher.server.stop_running(locations['local'])
                deadline=time.monotonic()+7
                while time.monotonic()<deadline:
                    if not (locations['local']/'run.json').exists():
                        try:(locations['local']/'start.log').unlink(missing_ok=True)
                        except PermissionError:pass
                        else:break
                    time.sleep(.05)
                else:self.fail('Local child did not release its files')

    def test_paths_preserve_stable_local_data_and_separate_beta_and_server(self):
        with patch.object(launcher.server,'VERSION','1.12.1'):
            stable=launcher.paths(Path('fictional-root'))
        with patch.object(launcher.server,'VERSION','1.12.2-beta.74'):
            beta=launcher.paths(Path('fictional-root'))
        self.assertEqual(stable['local'],Path('fictional-root/Distrikt'))
        self.assertEqual(len(set(stable.values())|set(beta.values())),6)
        self.assertNotIn('app',stable['config'].parts)

    def test_private_network_only_and_no_implicit_port_conversion(self):
        for host in ('8.8.8.8','0.0.0.0','127.0.0.1','::1','example.invalid','192.168.1.2:8787','http://192.168.1.2'):
            with self.subTest(host=host),self.assertRaises(ValueError):launcher.validate({'mode':'server','host':host,'port':8787})
        for port in (True,'8787',0,80,65536):
            with self.subTest(port=port),self.assertRaises(ValueError):launcher.validate({'mode':'server','host':'192.168.1.2','port':port})
        self.assertEqual(launcher.validate({'mode':'server','host':'192.168.1.2','port':8787})['port'],8787)

    def test_menu_cancel_and_beta_port(self):
        self.assertIsNone(launcher.configure(lambda _: '0'))
        answers=iter(['2','192.168.1.2',''])
        with patch.object(launcher.server,'VERSION','1.12.2-beta.74'):
            self.assertEqual(launcher.configure(lambda _:next(answers))['port'],8788)

    def test_password_is_confirmed_hashed_private_and_not_saved_in_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);data=root/'server';password='Fictional-private-123'
            with self.assertRaises(ValueError):launcher.prepare_password(data,lambda _: 'short')
            self.assertFalse(data.exists())
            values=iter([password,'mismatch'])
            with self.assertRaises(ValueError):launcher.prepare_password(data,lambda _:next(values))
            self.assertFalse(data.exists())
            launcher.prepare_password(data,lambda _:password)
            self.assertTrue(Access(data).verify(password));self.assertNotIn(password,(data/'access.json').read_text())
            launcher.prepare_password(data,lambda _:self.fail('Existing login must not be replaced'))
            if os.name!='nt':self.assertEqual((data/'access.json').stat().st_mode&0o777,0o600)
            with patch('builtins.input',side_effect=['2','192.168.1.2','8788']),patch.object(launcher,'prepare_password'),patch.object(launcher,'launch'):
                launcher.main(['--root',directory])
            saved=launcher.paths(root)['config'];self.assertEqual(set(json.loads(saved.read_text())),{'mode','host','port'})

    def test_invalid_settings_do_not_start_or_change_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path=launcher.paths(Path(directory))['config'];path.parent.mkdir();path.write_text('{bad-json')
            with patch.object(launcher,'launch') as run,self.assertRaisesRegex(ValueError,'--configure'):
                launcher.main(['--root',directory])
            run.assert_not_called();self.assertEqual(path.read_text(),'{bad-json')

    def test_server_launch_is_bound_and_never_opens_browser(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(launcher.server,'main') as run,patch.object(launcher.server,'running',return_value=None),patch.object(launcher,'prepare_password'):
            with patch.dict(os.environ,{},clear=False):
                launcher.launch({'mode':'server','host':'192.168.1.2','port':8788},launcher.paths(Path(directory)))
            args=run.call_args.args[0];self.assertIn('--no-browser',args);self.assertEqual(args[args.index('--bind')+1],'192.168.1.2');self.assertIn('--lan',args)

    def test_running_server_never_silently_changes_listening_address(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(launcher.server,'running',return_value={'public_url':'http://192.168.1.2:8788'}),patch.object(launcher.server,'main') as run:
            launcher.launch({'mode':'server','host':'192.168.1.2','port':8788},launcher.paths(Path(directory)))
            run.assert_not_called()
            with self.assertRaisesRegex(ValueError,'Ctrl.C'):launcher.launch({'mode':'server','host':'192.168.1.3','port':8788},launcher.paths(Path(directory)))

    def test_real_server_bound_to_one_interface_requires_login_and_stops_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            data=Path(directory);Access(data,'Fictional-private-123')
            with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
            process=subprocess.Popen([sys.executable,str(Path(launcher.server.__file__)),'--serve','--lan','--bind','127.0.0.1','--access-host','127.0.0.1','--port',str(port),'--data-dir',directory,'--no-browser'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            try:
                for _ in range(150):
                    if process.poll() is not None:self.fail('Fictional bound server failed to start')
                    if (data/'run.json').exists():break
                    time.sleep(.05)
                info=json.loads((data/'run.json').read_text());self.assertEqual(info['public_url'],'http://127.0.0.1:'+str(port))
                with self.assertRaises(urllib.error.HTTPError) as rejected:urllib.request.urlopen(info['url']+'/api/state',timeout=3)
                self.assertEqual(rejected.exception.code,401)
                client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
                req=urllib.request.Request(info['url']+'/api/login',data=json.dumps({'password':'Fictional-private-123'}).encode(),headers={'Content-Type':'application/json'})
                with client.open(req,timeout=5) as response:self.assertTrue(json.load(response)['ok'])
                req=urllib.request.Request(info['url']+'/api/state',headers={'X-Distrikt-Token':info['token']})
                with client.open(req,timeout=3) as response:self.assertEqual(json.load(response)['cards'],[])
            finally:
                process.terminate();process.wait(timeout=8)
                if process.stderr:process.stderr.close()
            self.assertFalse((data/'run.json').exists());self.assertTrue((data/'access.json').exists())


if __name__=='__main__':unittest.main()
