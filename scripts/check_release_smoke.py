#!/usr/bin/env python3
"""Start an extracted real program with empty temporary data; never reads user data."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
import build_release


def check():
    with tempfile.TemporaryDirectory(prefix='ltm-package-smoke-') as work:
        root=Path(work)
        with contextlib.redirect_stdout(io.StringIO()):
            first=build_release.build(root/'first')
            second=build_release.build(root/'second')
        if first.read_bytes()!=second.read_bytes():raise ValueError('Program ZIP is not reproducible.')
        with zipfile.ZipFile(first) as archive:
            if archive.testzip():raise ValueError('Invalid program ZIP.')
            archive.extractall(root/'unpacked')
            for line in archive.read('Home-Assistant/SHA256SUMS.txt').decode().splitlines():
                digest,name=line.split('  ',1)
                if hashlib.sha256(archive.read('Home-Assistant/distrikt/'+name)).hexdigest()!=digest:
                    raise ValueError('HA checksum mismatch: '+name)
        data=root/'invented-empty-data'
        process=subprocess.Popen([sys.executable,str(root/'unpacked/Distrikt-lokal/app/server.py'),'--serve','--no-browser','--data-dir',str(data)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            info=None
            for _ in range(200):
                if process.poll() is not None:raise RuntimeError('Packaged server exited before startup.')
                try:info=json.loads((data/'run.json').read_text());break
                except (FileNotFoundError,json.JSONDecodeError):time.sleep(.05)
            if info is None:raise RuntimeError('Packaged server did not start.')
            with urllib.request.urlopen(info['url'],timeout=3) as response:
                if 'Local Territory Manager' not in response.read().decode():raise ValueError('Missing app shell.')
            request=urllib.request.Request(info['url']+'/api/state',headers={'X-Distrikt-Token':info['token']})
            with urllib.request.urlopen(request,timeout=3) as response:state=json.load(response)
            if state['cards'] or state['publishers']:raise ValueError('Expected an empty local installation.')
            if state['version']!=build_release.version():raise ValueError('Packaged UI version differs from server/config.')
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            if process.stderr:process.stderr.close()
        launcher=root/'unpacked/Distrikt-lokal/app/launcher.py';guide_root=root/'fictional start guide'
        for name in ('Start-LTM.cmd','Start-LTM.command','Start-LTM.sh'):
            if not (launcher.parent.parent/name).is_file():raise ValueError('Missing shared start file: '+name)
        local_data=guide_root/('Distrikt-beta' if '-beta.' in build_release.version() else 'Distrikt')
        try:
            result=subprocess.run([sys.executable,str(launcher),'--root',str(guide_root),'--no-browser'],input='1\n',text=True,capture_output=True,timeout=20)
            if result.returncode:raise RuntimeError('Extracted shared start guide failed: '+result.stderr)
            info=json.loads((local_data/'run.json').read_text())
            with urllib.request.urlopen(info['url']+'/api/ping',timeout=3) as response:
                if json.load(response)['version']!=build_release.version():raise ValueError('Start guide launched the wrong version.')
        finally:
            subprocess.run([sys.executable,str(launcher.parent/'server.py'),'--data-dir',str(local_data),'--stop'],check=True,capture_output=True,timeout=10)
            for _ in range(100):
                if not (local_data/'run.json').exists():
                    try:(local_data/'start.log').unlink(missing_ok=True)
                    except PermissionError:pass
                    else:break
                time.sleep(.05)
            else:raise RuntimeError('Shared start guide did not stop and release its data.')
    print('Real package: identical ZIPs, HA checksums, extracted legacy/shared starts, empty isolated data and matching versions passed.')


if __name__=='__main__':check()
