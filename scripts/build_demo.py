#!/usr/bin/env python3
"""Publish only this explicit browser-demo allowlist, never application/data folders."""
from pathlib import Path
import argparse
import shutil
import hashlib
import json
from sync_demo_design import ASSETS

ROOT=Path(__file__).resolve().parents[1]
FILES=('index.html','demo.css','demo.js','model.js','mark.svg','vendor/leaflet.js','vendor/leaflet.css','vendor/Leaflet-LICENSE.txt',*ASSETS.keys(),'design.json')

def build(output):
    output=output.resolve()
    if output==ROOT or ROOT in output.parents and output.parts[len(ROOT.parts):len(ROOT.parts)+1]!=('dist',):
        raise ValueError('Use a separate output folder, normally dist/demo.')
    manifest=json.loads((ROOT/'demo/design.json').read_text())
    if set(manifest['files'])!=set(ASSETS):raise ValueError('Unexpected demo display manifest.')
    for name,digest in manifest['files'].items():
        source=ROOT/'demo'/name
        if source.is_symlink() or not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=digest:raise ValueError('Demo display checksum mismatch: '+name)
    output.mkdir(parents=True,exist_ok=True)
    # Keep repeated builds safe without deleting arbitrary paths.
    unexpected=[p for p in output.rglob('*') if p.is_file() and p.relative_to(output).as_posix() not in FILES+('.nojekyll',)]
    if unexpected:raise ValueError('Unexpected files in demo output; use a fresh output directory.')
    for name in FILES:
        source=ROOT/'demo'/name
        if source.is_symlink() or not source.is_file():raise ValueError('Missing/unsafe demo source: '+name)
        dest=output/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    (output/'.nojekyll').write_text('')
    print('Browser-only fictional demo:',output,'—',len(FILES),'allowlisted assets')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'dist/demo');args=p.parse_args();build(args.output)
