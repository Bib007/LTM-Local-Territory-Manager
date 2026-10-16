#!/usr/bin/env python3
"""Reproducible program-only ZIP. No user database folder is ever opened."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'distrikt'
REQUIRED=('S-12-source.png','S-13-background.jpg','S-13-fields.json','S-13-fillable.pdf')
BLOCKED_SUFFIXES=('.sqlite','.sqlite3','.db','.pyc','.log')
ROOT_DOCS=('repository.yaml','README.md','README.da.md','README.en.md','LICENSE','CHANGELOG.md','ROADMAP.md','CONTRIBUTING.md','CONTRIBUTING.en.md','Dette-skal-hjaelpes-manuelt.md')
BRAND_FILES=('mark.svg','logo-light.svg','logo-dark.svg','README.md')

def version():
    value=re.search(r"^VERSION='([^']+)'",(SRC/'app/server.py').read_text(),re.M).group(1)
    config=(SRC/'config.yaml').read_text()
    if f'version: "{value}"' not in config:raise ValueError('Server and HA versions differ.')
    return value

def files():
    missing=[n for n in REQUIRED if not (SRC/'templates'/n).is_file()]
    if missing:raise ValueError('Release incomplete: missing blank form assets: '+', '.join(missing))
    result={}
    for section in ('app','templates','tests','translations'):
        for p in sorted((SRC/section).rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts:continue
            if p.is_symlink():raise ValueError('Symlink not allowed in release: '+str(p))
            if p.suffix in BLOCKED_SUFFIXES:raise ValueError('Private/runtime file in source tree: '+str(p))
            relative=p.relative_to(SRC).as_posix()
            if any(part.startswith('.') for part in p.relative_to(SRC).parts):continue
            result['Distrikt-lokal/'+relative]=(p.read_bytes(),0o644)
            if section in ('app','templates','translations'):result['Home-Assistant/distrikt/'+relative]=(p.read_bytes(),0o644)
    for p in sorted(SRC.iterdir()):
        if p.is_file() and p.suffix in ('.cmd','.command','.md'):
            result['Distrikt-lokal/'+p.name]=(p.read_bytes(),0o755 if p.suffix=='.command' else 0o644)
    for n in ('Dockerfile','config.yaml','run.sh','DOCS.md','README.md','CHANGELOG.md'):
        p=SRC/n;result['Home-Assistant/distrikt/'+n]=(p.read_bytes(),0o755 if n=='run.sh' else 0o644)
    for n in ROOT_DOCS:
        p=ROOT/n
        if not p.is_file():raise ValueError('Missing release document: '+n)
        result[n]=(p.read_bytes(),0o644)
    for n in BRAND_FILES:
        p=ROOT/'assets'/'brand'/n
        if not p.is_file() or p.is_symlink():raise ValueError('Missing/unsafe brand asset: '+n)
        result['assets/brand/'+n]=(p.read_bytes(),0o644)
    for p in sorted((ROOT/'docs').glob('*.md')):result['docs/'+p.name]=(p.read_bytes(),0o644)
    p=ROOT/'Opdater-Home-Assistant-Mac.command';result[p.name]=(p.read_bytes(),0o755)
    prefix='Home-Assistant/distrikt/'
    manifest=''.join(hashlib.sha256(raw).hexdigest()+'  '+name[len(prefix):]+'\n' for name,(raw,_) in sorted(result.items()) if name.startswith(prefix))
    result['Home-Assistant/SHA256SUMS.txt']=(manifest.encode(),0o644)
    result['START-HER.txt']=(('Local Territory Manager '+version()+'\n\nLæs README.md eller docs/INSTALL.md. Engelsk: README.en.md.\nMac/Windows: startfil i Distrikt-lokal.\nHA: privat backup først; stop kun appen, brug kopieringshjælpen og opdater eksisterende installation.\nDatabaser og login medfølger ikke.\n').encode(),0o644)
    return result

def build(output):
    entries=files();output.mkdir(parents=True,exist_ok=True);path=output/('LTM-v'+version()+'.zip')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,(raw,mode) in sorted(entries.items()):
            item=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));item.create_system=3;item.external_attr=(0o100000|mode)<<16;item.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(item,raw)
    digest=hashlib.sha256(path.read_bytes()).hexdigest();(output/(path.name+'.sha256')).write_text(digest+'  '+path.name+'\n')
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():raise ValueError('ZIP CRC failed.')
        if any(n.endswith(BLOCKED_SUFFIXES) for n in archive.namelist()):raise ValueError('Runtime data in archive.')
    print(json.dumps({'file':str(path),'sha256':digest,'files':len(entries),'bytes':path.stat().st_size}))
    return path

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'dist');args=parser.parse_args();build(args.output)
