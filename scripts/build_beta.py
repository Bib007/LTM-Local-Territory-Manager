#!/usr/bin/env python3
"""Build the isolated HA beta channel from the same program-only source manifest."""
import argparse
import hashlib
from pathlib import Path
import re
import zipfile
import build_release as release

REPOSITORY='https://github.com/Bib007/LTM-Local-Territory-Manager'

def changed(raw,old,new):
    text=raw.decode()
    if old not in text:raise ValueError('Beta preparation contract changed: '+old)
    return text.replace(old,new).encode()

def entries():
    version=release.version()
    if not re.fullmatch(r'\d+\.\d+\.\d+-beta\.\d+',version):raise ValueError('Beta publishing requires a numbered beta version.')
    prefix='Home-Assistant/'
    files={name[len(prefix):]:(raw,mode) for name,(raw,mode) in release.files().items() if name.startswith(prefix+'distrikt/')}
    config,mode=files['distrikt/config.yaml']
    config=changed(config,'name: Distrikt\n','name: Distrikt Beta\n')
    config=changed(config,'slug: distrikt\n','slug: distrikt_beta\n')
    config=changed(config,'boot: auto','boot: manual')
    config=changed(config,'8787','8788')
    files['distrikt/config.yaml']=(config,mode)
    run,mode=files['distrikt/run.sh']
    run=changed(run,'--port 8787','--port 8788')
    run=changed(run,'/data/distrikt','/data/distrikt-beta')
    run=changed(run,'set -euo pipefail','set -euo pipefail\nexport LTM_CHANNEL=beta')
    files['distrikt/run.sh']=(run,mode)
    index,mode=files['distrikt/app/index.html']
    index=changed(index,'<b>LTM</b>','<b>LTM Beta</b>')
    index=changed(index,'<body>','<body class="betaChannel">')
    index=changed(index,'<title>Local Territory Manager – JW</title>','<title>LTM Beta – Local Territory Manager</title>')
    files['distrikt/app/index.html']=(index,mode)
    guide=(release.ROOT/'docs/BETA.md').read_bytes()
    files['distrikt/DOCS.md']=(guide,0o644)
    files['distrikt/README.md']=('# Distrikt Beta\n\nAfprøv nye LTM-funktioner i små betaudgivelser ved siden af din stabile installation. Betaen bruger port 8788, egne data og eget login.\n\nLæs fanen **Dokumentation** for installation, opdatering og den aktuelle testliste. Start med opdigtede prøveoplysninger og en særskilt Google-konto til Drive-prøver.\n'.encode(),0o644)
    files['README.md']=(guide,0o644)
    files['repository.yaml']=(('name: Local Territory Manager - Beta\nurl: '+REPOSITORY+'#beta\nmaintainer: Bib007\n').encode(),0o644)
    manifest=''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n' for name,(raw,_) in sorted(files.items()))
    files['SHA256SUMS.txt']=(manifest.encode(),0o644)
    return files

def build(output,archive_output):
    files=entries()
    if output.exists() and any(output.iterdir()):raise ValueError('Choose an empty beta output directory.')
    output.mkdir(parents=True,exist_ok=True)
    for name,(raw,mode) in files.items():
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(mode)
    archive_output.mkdir(parents=True,exist_ok=True)
    target=archive_output/('LTM-HA-v'+release.version()+'.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,(raw,mode) in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));info.create_system=3;info.external_attr=(0o100000|mode)<<16;info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,raw)
    checksum=target.with_suffix(target.suffix+'.sha256');checksum.write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
    print(target)
    return target

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=release.ROOT/'dist/ha-beta');parser.add_argument('--archive-output',type=Path,default=release.ROOT/'dist');args=parser.parse_args();build(args.output,args.archive_output)
