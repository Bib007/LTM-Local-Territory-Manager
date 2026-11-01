"""Offline browser fixture invokes the real, bounded public date renderer."""
import base64
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'distrikt/app'))
from sharing import png_bytes
from publication_dates import render

data=json.load(sys.stdin)
assert data['date_fingerprint']=='FICTIONAL_DATES'
png=render(png_bytes(data['png']),{'completed':'2026-10-01','assigned':'2026-10-10'})
print(json.dumps({'png':'data:image/png;base64,'+base64.b64encode(png).decode(),'date_fingerprint':'FICTIONAL_DATES'}))
