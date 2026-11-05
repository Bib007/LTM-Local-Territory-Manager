"""Serve fictional assignments and profiles from a disposable local store."""
import json
import signal
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'distrikt/app'))
from server import Server
from store import Store


def stop(*args):
    raise SystemExit(0)


with tempfile.TemporaryDirectory(prefix='ltm-fictional-loan-deletion-') as root:
    store = Store(root)

    def write(action, **data):
        return store.mutate(action, data)

    card = write('card.save', number='F42', name='Fictional card', temporary=True)['id']
    archive = write('card.save', number='F43', name='Fictional archived card', temporary=True)['id']

    def issue(card_id, publisher_name, day):
        return write('loan.issue', card_id=card_id, publisher_name=publisher_name, date=day, initial=True)['id']

    older = issue(card, 'Fictional older', '2025-10-01')
    write('loan.finish', id=older, date='2025-10-02')
    mistake = issue(card, 'Fictional mistaken', '2025-10-04')
    write('loan.finish', id=mistake, date='2025-10-04', complete=True, note='Fictional preserved note')
    neighbor = issue(card, 'Fictional same-day neighbor', '2025-10-04')
    write('loan.finish', id=neighbor, date='2025-10-05', complete=True)
    recent = issue(card, 'Fictional recent', '2025-10-07')
    write('loan.finish', id=recent, date='2025-10-08')
    latest = issue(card, 'Fictional latest', '2025-10-08')
    write('loan.finish', id=latest, date='2025-10-09')
    active = issue(card, 'Fictional active', '2025-10-09')
    write('loan.finish', id=active, date='2025-10-10', complete=True, retain=True)
    archived = issue(archive, 'Fictional archived', '2025-10-02')
    write('loan.finish', id=archived, date='2025-10-03')
    with store.transaction():
        store.put('cards', {**store.require('cards', archive), 'archived': True})
        store.put('loans', {**store.require('loans', archived), 'publisher_id': 'fictional-missing'})
    write('setup.onboarding.save', answers={'mode':'desk','boundary':'later','cards':'numbers','ib':'later'}, tour_completed=True)

    server = Server(('127.0.0.1', 0), store)
    accounts = server.accounts
    password = 'Fictional-browser-password'
    accounts.bootstrap('Fictional admin', password)
    admin = accounts.login('Fictional admin', password, 'fictional-admin')
    rights = ['reports.view','cards.view','history.view','loans.view','publishers.view']
    reader_role = accounts.save_role(admin, 'Fictional history reader', rights)
    accounts.save_user(admin, 'Fictional reader', [reader_role], password=password)
    reader = accounts.login('Fictional reader', password, 'fictional-reader')
    for token in (admin, reader):
        accounts.complete_intro(token)

    def cookie(token):
        return {'name': server.profiles.cookie, 'value': token, 'url': server.origin}

    print(json.dumps(dict(origin=server.origin, admin=cookie(admin), reader=cookie(reader),
                         card=card, mistake=mistake, neighbor=neighbor, active=active,
                         older=older, recent=recent, latest=latest, archived=archived)), flush=True)
    signal.signal(signal.SIGTERM, stop)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        store.close()
