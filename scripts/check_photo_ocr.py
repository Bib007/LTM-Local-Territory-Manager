#!/usr/bin/env python3
"""Read an explicit synthetic PNG with the real local OCR, without database/network."""
import base64
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'distrikt/app'))
# Container callers set PYTHONPATH=/opt/distrikt/app, keeping the same adapter.
from photo_ocr import PhotoOCR

service=PhotoOCR()
try:
    status=service.available()
    if not status['available']:raise SystemExit('Local OCR engine/language is missing.')
    if '--require-danish' in sys.argv and set(status['languages'])!={'dan','eng'}:raise SystemExit('Danish and English OCR data are required.')
    sample=Path(__file__).resolve().parent/'fixtures'/'ocr-fiktiv.png'
    ident=service.start({'png':base64.b64encode(sample.read_bytes()).decode()})['id']
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        result=service.status(ident)
        if result['status']!='running':break
        time.sleep(.05)
    else:raise SystemExit('Local OCR smoke test timed out.')
    if result['status']!='done' or 'Fiktivvej 8 - 24.10.2026' not in result['text']:raise SystemExit('Synthetic OCR line was not recognized.')
    service.cancel(ident)
    print('Real local OCR: invented PNG, expected address/date, RAM result and cancellation passed; languages: '+','.join(status['languages']))
finally:service.close()
