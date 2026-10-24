#!/usr/bin/env python3
"""Snapshot only public display assets; never reads the app's runtime data."""
from pathlib import Path
import argparse
import hashlib
import json
import re
ROOT=Path(__file__).resolve().parents[1]
ASSETS={'shared/style.css':'style.css','shared/workspace.css':'workspace.css','shared/theme.css':'theme.css','shared/theme.js':'theme.js','brand-logo.svg':'brand-logo.svg','brand-logo-light.svg':'brand-logo-light.svg'}
def sync(check=False):
    files={name:(ROOT/'distrikt/app'/source).read_bytes() for name,source in ASSETS.items()}
    version=re.search(r"^VERSION='([^']+)'",(ROOT/'distrikt/app/server.py').read_text(),re.M)[1]
    files['design.json']=(json.dumps({'version':version,'files':{n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}},indent=2)+'\n').encode()
    for name,raw in files.items():
        dest=ROOT/'demo'/name
        if check:
            if not dest.is_file() or dest.is_symlink() or dest.read_bytes()!=raw:raise ValueError('Demo display snapshot needs updating: '+name)
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');sync(p.parse_args().check)
