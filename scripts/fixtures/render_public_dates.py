"""Real publication recipe, approval and queued PNG with an offline Drive."""
import base64
import json
from pathlib import Path
import sys
import tempfile

root=Path(__file__).resolve().parents[2]/'distrikt'
sys.path[:0]=[str(root/'app'),str(root/'tests')]
from sharing import Publications
from store import Store
from test_sharing import FakeDrive


def run(stage,fixture,data):
    with tempfile.TemporaryDirectory() as folder:
        store=Store(folder)
        try:
            card=next(card for card in fixture['cards'] if card['id']==data['card_id'])
            with store.transaction():
                store.put('cards',dict(card,last_completed='2026-10-01'))
                store.put('loans',{'id':'fictional-loan','card_id':card['id'],'assigned':'2026-10-10'})
                for address in fixture['addresses']:store.put('geo',dict(address,entity='address'))
                for ignored in fixture['ignored']:store.put('ignored',ignored)
                for ib in fixture['ib']:store.put('ib',ib)
            publications=Publications(store)
            publications.drive=FakeDrive()
            if stage=='prepare':return publications.prepare(card['id'])
            if stage=='date-preview':return publications.date_preview(data)
            result=publications.enqueue(data)
            publications.process_one()
            [(png,_)]=publications.drive.uploads
            assert store.require('maps',publications.key(card['id']))['status']=='published'
            return {**result,'png':'data:image/png;base64,'+base64.b64encode(png).decode()}
        finally:
            store.close()


payload=json.load(sys.stdin)
print(json.dumps(run(sys.argv[1],payload['fixture'],payload['data'])))
