"""Local-only, separate SQLite files. No network, telemetry or external dependency."""
import json
import re
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from geo_store import GeoStore
from admin_store import AdminStore
from workflow_store import WorkflowStore
from setup_store import SetupStore

MODULES = {'settings': 'indstillinger', 'cards': 'kort', 'publishers': 'forkyndere',
           'loans': 'udleveringer', 'completions': 'gennemgange', 'ib': 'ib',
           'visits': 'ktm_besoeg', 'maps': 'kortbilleder', 'geo': 'geodata', 'ignored': 'se_bort_fra', 'notes': 'kortnoter'}
ADDRESS_TYPES = ['Hus', 'Lejlighed', 'Lejlighedskompleks', 'Butik', 'Kontor', 'Virksomhed', 'Andet']

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def today():
    return date.today().isoformat()

def valid_day(value, field='Dato', future=False):
    try:
        d = date.fromisoformat(str(value))
    except (ValueError, TypeError):
        raise ValueError(field + ' skal være en gyldig dato.')
    if not future and d > date.today():
        raise ValueError(field + ' må ikke ligge i fremtiden.')
    return d.isoformat()

def new_id():
    return uuid.uuid4().hex

def clean_text(value, maxlen=100, required=False):
    value = str(value or '').strip()
    if len(value) > maxlen:
        raise ValueError('Teksten er for lang.')
    if required and not value:
        raise ValueError('Udfyld det krævede felt.')
    return value

class Store(SetupStore,WorkflowStore,AdminStore,GeoStore):
    def __init__(self, root):
        self.workflow_init()
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        for filename in MODULES.values():
            existing = self.root / (filename + '.sqlite3')
            if existing.exists() and existing.stat().st_size:
                probe = sqlite3.connect(existing.as_uri() + '?mode=ro', uri=True)
                try:
                    version = probe.execute('PRAGMA user_version').fetchone()[0]
                    tables = probe.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                    if version != 1 or not any(t[0] == 'records' for t in tables):
                        raise RuntimeError('Ukendt databaseformat: ' + filename + '. Data er ikke ændret.')
                finally:
                    probe.close()
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(self.root / (MODULES['settings'] + '.sqlite3')), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA busy_timeout=10000')
        for module, filename in MODULES.items():
            alias = 'main' if module == 'settings' else module
            path = self.root / (filename + '.sqlite3')
            if alias != 'main':
                self.db.execute('ATTACH DATABASE ? AS ' + alias, (str(path),))
            version = self.db.execute('PRAGMA ' + alias + '.user_version').fetchone()[0]
            if version not in (0, 1):
                raise RuntimeError('Databaseversion understøttes ikke: ' + filename + '. Brug den nyeste app. Data er ikke ændret.')
            self.db.execute('PRAGMA ' + alias + '.journal_mode=DELETE')
            self.db.execute('PRAGMA ' + alias + '.synchronous=FULL')
            self.db.execute('PRAGMA ' + alias + '.secure_delete=ON')
            self.db.execute('CREATE TABLE IF NOT EXISTS ' + alias + '.records (id TEXT PRIMARY KEY, payload TEXT NOT NULL, deleted_at TEXT, batch TEXT)')
            self.db.execute('PRAGMA ' + alias + '.user_version=1')
            os.chmod(path, 0o600)
        self.db.commit()
        with self.transaction():
            # Remove the credential belonging to the retired aerial-photo feature only.
            self.db.execute("DELETE FROM geo.records WHERE id = ?",('basemap-config',))
            if not self.get('settings', 'config'):
                self.put('settings', {'id': 'config', 'congregation': '', 'folder_minimum': 30,
                    'rural_mode': 'auto', 'rural_minimum': 5, 'require_revision': False, 'schema': 1})
        self.purge_expired()

    @contextmanager
    def transaction(self):
        with self.lock:
            before=self.db.total_changes
            self._dirty_modules=set()
            self.db.execute('BEGIN IMMEDIATE')
            try:
                yield
                self.db.commit()
                if self.db.total_changes!=before:
                    self.revision=uuid.uuid4().hex
                    if not self._dirty_modules or self._dirty_modules.intersection({'geo','cards','ignored'}):self._geo_cache=None
                    if not self._dirty_modules or 'geo' in self._dirty_modules:self._info_cache=None
            except Exception:
                self.db.rollback()
                raise

    def alias(self, module):
        if module not in MODULES:
            raise ValueError('Ukendt datafil.')
        return 'main' if module == 'settings' else module

    def all(self, module, deleted=False):
        sql = 'SELECT * FROM ' + self.alias(module) + '.records WHERE deleted_at IS ' + ('NOT NULL' if deleted else 'NULL')
        rows = self.db.execute(sql).fetchall()
        return [dict(json.loads(r['payload']), **({'_deleted_at': r['deleted_at'], '_batch': r['batch']} if deleted else {})) for r in rows]

    def get(self, module, ident, deleted=False):
        row = self.db.execute('SELECT * FROM ' + self.alias(module) + '.records WHERE id=?', (ident,)).fetchone()
        if row and (deleted or not row['deleted_at']):
            return json.loads(row['payload'])
        return None

    def put(self, module, item):
        self._dirty_modules.add(module)
        self.workflow_track(module,item['id'])
        self.db.execute('INSERT INTO ' + self.alias(module) + '.records(id,payload) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload', (item['id'], json.dumps(item, ensure_ascii=False)))
        return item

    def require(self, module, ident):
        item = self.get(module, ident)
        if not item:
            raise ValueError('Posten findes ikke længere. Opdater siden.')
        return item

    def active_loan(self, card_id):
        return next((l for l in self.all('loans') if l['card_id'] == card_id and not l.get('returned')), None)

    def state(self):
        with self.lock:
            result = {m: self.all(m) for m in MODULES if m not in ('maps','geo')}
            result['settings'] = self.get('settings', 'config')
            result['areas'] = [x for x in self.all('settings') if x['id'] != 'config' and not x.get('entity')]
            result['notes']=[n for n in result['notes'] if n.get('entity')!='activity']
            result['archived_cards']=[c for c in result['cards'] if c.get('archived')]
            result['cards']=[c for c in result['cards'] if not c.get('archived')]
            result['revision']=self.revision
            result['undo_available']=bool(self._undo and self._undo['revision']==self.revision and self._undo['until']>__import__('time').monotonic())
            result['maps'] = [{k: v for k, v in m.items() if k != 'image'} for m in self.all('maps') if m.get('entity')!='publication']
            result['recovery'] = self.recovery()
            result['today'] = today()
            result['version'] = '1.12.0-beta.1'
            result['geo_info'] = self.geo_info()
            return result

    def purge_expired(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(timespec='seconds')
        with self.transaction():
            for m in MODULES:
                self.db.execute('DELETE FROM ' + self.alias(m) + '.records WHERE deleted_at IS NOT NULL AND deleted_at<=?', (cutoff,))

    def recovery(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(timespec='seconds')
        rows = []
        for m in MODULES:
            if m=='maps':
                continue
            for item in self.all(m, deleted=True):
                if item['_deleted_at'] > cutoff:
                    rows.append({'batch': item['_batch'], 'at': item['_deleted_at'],
                        'label': 'Adresser uden for samlet grænse' if m=='geo' else item.get('number') or item.get('name') or item.get('date') or item.get('road') or m})
        groups = {}
        for row in rows:
            if row['batch'] not in groups:
                groups[row['batch']] = dict(row, count=0)
            groups[row['batch']]['count'] += 1
        return sorted(groups.values(), key=lambda r: r['at'], reverse=True)

    def mark_deleted(self, module, ident, batch, stamp):
        self._dirty_modules.add(module)
        self.workflow_track(module,ident)
        self.db.execute('UPDATE ' + self.alias(module) + '.records SET deleted_at=?,batch=? WHERE id=? AND deleted_at IS NULL', (stamp, batch, ident))

    def create_completion(self, card, day, loan_id=None):
        loan = self.get('loans', loan_id) if loan_id else None
        item = {'id': new_id(), 'card_id': card['id'], 'date': day, 'loan_id': loan_id,
                'assigned': loan.get('cycle_start') if loan else None, 'previous_completed': card.get('last_completed'),
                'visits':sum(a.get('count',0) for a in card.get('addresses',[]))}
        self.put('completions', item)
        if not card.get('last_completed') or day > card['last_completed']:
            card['last_completed'] = day
            self.put('cards', card)
        return item

    def mutate(self, action, data):
        with self.lock:return self.guarded_mutate(action,data)

    def guarded_mutate(self, action, data):
        self.purge_expired()
        with self.transaction():
            if data.get('_revision') is not None and data['_revision']!=self.revision:
                raise ValueError('Data er ændret fra en anden fane eller enhed. Genindlæs data før du gemmer; dine felter er ikke overskrevet.')
            self._tracking={}
            try:
                result = self._mutate(action, data)
                if action in ('restore','delete','recovery.purge','history.cleanup'):self._dirty_modules.update(MODULES)
                touched=self._tracking
                changed=any(before!=tuple(after) if after else before is not None for (m,i),before in touched.items() for after in [self.db.execute('SELECT id,payload,deleted_at,batch FROM '+self.alias(m)+'.records WHERE id=?',(i,)).fetchone()])
                if changed and not action.startswith(('geo.import','geo.postcode','geo.main.download')):
                    self._tracking=None
                    targets=set();fields=set()
                    for (module,ident),previous in touched.items():
                        after=self.get(module,ident) or {};old=json.loads(previous[1]) if previous else {}
                        current=after or old
                        if module=='cards':
                            if current.get('number'):targets.add(current['number'])
                            fields.update(k for k in set(old)|set(after) if k not in ('id','created') and old.get(k)!=after.get(k))
                        elif current.get('card_id'):
                            target=self.get('cards',current['card_id'])
                            if target:targets.add(target['number'])
                    self.put('notes',{'id':new_id(),'entity':'activity','at':datetime.now(timezone.utc).isoformat(timespec='microseconds'),'action':action,'count':len(touched),'card_id':None,'cards':sorted(targets),'fields':sorted(fields)})
                reversible=action in ('card.save','card.color','publisher.save','loan.issue','loan.finish','folder.set','note.save','note.resolve','note.task','completion.record','visit.save','ib.save','revision.approve')
                candidate={'rows':touched,'action':action,'until':__import__('time').monotonic()+120} if changed and reversible else None
            finally:self._tracking=None
        if candidate:
            candidate['revision']=self.revision;self._undo=candidate
        elif changed:self._undo=None
        return result

    def _mutate(self, action, data, *, geographic=False):
        if action.startswith('setup.'):return self.setup_mutate(action,data)
        if action.startswith(('filter.','workflow.','card.restructure.','address.change.')) or action in ('backup.record','note.task'):
            return self.workflow_mutate(action,data)
        if action in ('card.bulk.preview','card.bulk.create','card.bulk.edit.preview','card.bulk.edit','loan.correct.preview','loan.correct'):
            return self.admin_mutate(action,data)
        if isinstance(action,str) and (action.startswith('geo.') or action.startswith('ignore.')):
            return self.geo_mutate(action,data)
        if action == 'card.color':
            card = self.require('cards', data['card_id'])
            color = data.get('map_color')
            if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                raise ValueError('Vælg en gyldig kortfarve.')
            card['map_color'] = color.lower()
            self.put('cards', card)
            return {'id': card['id']}
        if action == 'card.save':
            old = self.get('cards', data.get('id')) if data.get('id') else None
            if data.get('id') and not old:
                raise ValueError('Kortet findes ikke længere.')
            card = dict(old or {'id': new_id(), 'in_folder': False, 'last_completed': None, 'created': now(), 'front_revision': False, 'back_revision': False})
            number = clean_text(data.get('number'), 30, True)
            # Reserve deleted numbers during recovery so restoration cannot collide.
            reserved = self.all('cards') + self.all('cards', deleted=True)
            if any(c['number'].casefold() == number.casefold() and c['id'] != card['id'] for c in reserved):
                raise ValueError('Kortnummeret findes allerede (evt. i 48-timers gendannelse).')
            card.update(number=number, name=clean_text(data.get('name'), 100), area_id=data.get('area_id') or '',
                        kind=data.get('kind', 'Ukendt'), temporary=bool(data.get('temporary', True)))
            color = data.get('map_color', card.get('map_color', '#477596'))
            if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                raise ValueError('Vælg en gyldig kortfarve.')
            card['map_color'] = color.lower()
            if card['kind'] not in ('By', 'Land', 'Ukendt'):
                raise ValueError('Vælg By, Land eller Ukendt.')
            if card['area_id'] and not self.get('settings', card['area_id']):
                raise ValueError('Området findes ikke.')
            addresses = data.get('addresses', [])
            if not isinstance(addresses, list) or len(addresses) > 300:
                raise ValueError('For mange adresser på ét kort.')
            normalized = []
            for a in addresses:
                if not isinstance(a, dict):
                    raise ValueError('Ugyldig adresse.')
                count = int(a.get('count', 1))
                if not 1 <= count <= 10000:
                    raise ValueError('Antal besøg skal være mellem 1 og 10.000.')
                typ = a.get('type', 'Hus')
                if typ not in ADDRESS_TYPES:
                    raise ValueError('Ugyldig adressetype.')
                normalized.append({'road': clean_text(a.get('road'), 120, True), 'numbers': clean_text(a.get('numbers'), 100, True), 'count': count, 'type': typ})
            if not card['temporary'] and not normalized:
                raise ValueError('Tilføj en vejliste eller behold kortet som midlertidigt.')
            if old and (old.get('address_ids') or old.get('geo_addresses')) and normalized != old.get('addresses', []) and not geographic:
                raise ValueError('Vejlisten følger de valgte huse. Brug Tegn og vælg adresser for at ændre den.')
            card['addresses'] = normalized
            if old and (old.get('addresses', []) != normalized or old['number'] != number or old.get('name') != card['name'] or (old.get('area_id') != card['area_id'] and not card['name'])):
                card['front_revision'] = True
            if old and old['number'] != number:
                card['back_revision'] = True
            self.put('cards', card)
            if data.get('initial_completed') and not old:
                self.create_completion(card, valid_day(data['initial_completed']))
            return {'id': card['id']}
        if action == 'publisher.save':
            old = self.get('publishers', data.get('id')) if data.get('id') else None
            if data.get('id') and not old:
                raise ValueError('Posten er ændret eller slettet. Opdater siden.')
            item = dict(old or {'id': new_id()})
            item['name'] = clean_text(data.get('name'), 100, True)
            if any(p['name'].casefold() == item['name'].casefold() and p['id'] != item['id'] for p in self.all('publishers')):
                raise ValueError('Navnet findes allerede. Vælg den eksisterende forkynder.')
            self.put('publishers', item)
            return {'id': item['id']}
        if action == 'loan.issue':
            c = self.require('cards', data['card_id'])
            if c.get('archived'):raise ValueError('Kortet er arkiveret efter sammenlægning.')
            if self.active_loan(c['id']):
                raise ValueError('Kortet er allerede udleveret.')
            config = self.require('settings', 'config')
            if config['require_revision'] and (c.get('front_revision') or c.get('back_revision')):
                raise ValueError('Kortets ændrede side skal printes og godkendes først.')
            if data.get('publisher_id'):
                publisher = self.require('publishers', data['publisher_id'])
            else:
                name = clean_text(data.get('publisher_name'), 100, True)
                publisher = next((p for p in self.all('publishers') if p['name'].casefold() == name.casefold()), None)
                if not publisher:
                    ident = self._mutate('publisher.save', {'name': name})['id']
                    publisher = self.require('publishers', ident)
            day = valid_day(data.get('date'))
            initial = bool(data.get('initial', False))
            if not initial and not c['in_folder']:
                raise ValueError('Læg kortet i mappen først, eller vælg registrering af et eksisterende udlån.')
            item = {'id': new_id(), 'card_id': c['id'], 'publisher_id': publisher['id'],
                'assigned': day, 'cycle_start': day, 'returned': None, 'initial': initial}
            self.put('loans', item)
            c['in_folder'] = False
            self.put('cards', c)
            return {'id': item['id']}
        if action == 'note.save':
            c=self.require('cards',data['card_id']) if data.get('card_id') else None
            item=dict(self.require('notes',data['id']) if data.get('id') else {'id':new_id(),'date':today(),'created':now(),'resolved':False})
            if item.get('entity')=='activity':raise ValueError('Vælg en note.')
            item['card_id']=c['id'] if c else None
            item['task']=bool(data.get('task',item.get('task',False)))
            item['text']=clean_text(data.get('text'),1000,True)
            self.put('notes',item);return {'id':item['id']}
        if action == 'note.resolve':
            item=self.require('notes',data.get('id'))
            if item.get('entity')=='activity':raise ValueError('Vælg en note.')
            if item.get('card_id'):self.require('cards',item['card_id'])
            if type(data.get('resolved'))!=bool:raise ValueError('Ugyldig notestatus.')
            item.update(resolved=data['resolved'],resolved_at=now() if data['resolved'] else None)
            self.put('notes',item);return {'id':item['id']}
        if action == 'loan.finish':
            loan = self.require('loans', data['id'])
            if loan.get('returned'):
                raise ValueError('Kortet er allerede afleveret.')
            c = self.require('cards', loan['card_id'])
            day = valid_day(data.get('date'))
            if day < loan['cycle_start']:
                raise ValueError('Datoen skal være efter udlevering / seneste gennemgang.')
            note=clean_text(data.get('note'),1000)
            complete = bool(data.get('complete'))
            retain = bool(data.get('retain'))
            if retain and not complete:
                raise ValueError('En ny gennemgang kan kun starte efter en afsluttet gennemgang.')
            if complete:
                self.create_completion(c, day, loan['id'])
            if retain:
                loan['cycle_start'] = day
            else:
                loan['returned'] = day
                c['in_folder'] = False
                self.put('cards', c)
            self.put('loans', loan)
            if note:self.put('notes',{'id':new_id(),'card_id':c['id'],'loan_id':loan['id'],'date':day,'text':note,'created':now(),'resolved':False})
            return {'id': loan['id']}
        if action == 'folder.set':
            ids = data.get('ids', [])
            if not isinstance(ids, list):
                raise ValueError('Ugyldig kortliste.')
            for ident in ids:
                c = self.require('cards', ident)
                if self.active_loan(ident):
                    raise ValueError('Et udlånt kort kan ikke lægges i mappen.')
                c['in_folder'] = bool(data.get('in_folder'))
                self.put('cards', c)
            return {'count': len(ids)}
        if action == 'area.save':
            old = self.get('settings', data.get('id')) if data.get('id') else None
            if data.get('id') and not old:
                raise ValueError('Posten er ændret eller slettet. Opdater siden.')
            if old and old['id'] == 'config':
                raise ValueError('Ugyldigt område.')
            name = clean_text(data.get('name'), 80, True)
            if any(a['id'] != 'config' and a.get('name', '').casefold() == name.casefold() and a['id'] != data.get('id') for a in self.all('settings') + self.all('settings', deleted=True)):
                raise ValueError('Områdenavnet findes allerede (evt. i 48-timers gendannelse).')
            item = dict(old or {'id': new_id()})
            item['name'] = name
            if old and old.get('name') != name:
                for c in self.all('cards'):
                    if c.get('area_id') == item['id'] and not c.get('name'):
                        c['front_revision'] = True
                        self.put('cards', c)
            self.put('settings', item)
            return {'id': item['id']}
        if action == 'area.delete':
            ident = data.get('id')
            if ident == 'config':
                raise ValueError('Ugyldigt område.')
            self.require('settings', ident)
            restore_cards = []
            for c in self.all('cards'):
                if c.get('area_id') == ident:
                    restore_cards.append(c['id'])
                    c['area_id'] = ''
                    if not c.get('name'): c['front_revision'] = True
                    self.put('cards', c)
            area_item = self.require('settings', ident)
            area_item['restore_cards'] = restore_cards
            self.put('settings', area_item)
            batch, stamp = new_id(), now()
            self.mark_deleted('settings', ident, batch, stamp)
            return {'batch': batch}
        if action == 'settings.save':
            c = dict(self.require('settings', 'config'))
            minimum = int(data.get('folder_minimum', 30))
            rural = int(data.get('rural_minimum', 5))
            mode = data.get('rural_mode', 'auto')
            if mode == 'auto':
                rural = min(rural, minimum)
            if not 0 <= minimum <= 1000 or not 0 <= rural <= minimum or mode not in ('auto', 'manual'):
                raise ValueError('Kontrollér minimum og antal landkort.')
            c.update(congregation=clean_text(data.get('congregation'), 100), folder_minimum=minimum,
                rural_mode=mode, rural_minimum=rural, require_revision=bool(data.get('require_revision')))
            self.put('settings', c)
            return {}
        if action == 'completion.record':
            card = self.require('cards', data.get('card_id'))
            if self.active_loan(card['id']):
                raise ValueError('Kortet er udleveret. Brug Gennemgået · behold kort eller Aflever.')
            day = valid_day(data.get('date'))
            if any(e['card_id'] == card['id'] and e['date'] == day for e in self.all('completions')):
                raise ValueError('Gennemgangen er allerede registreret på denne dato.')
            note=clean_text(data.get('note'),1000)
            item = self.create_completion(card, day)
            if note:self.put('notes',{'id':new_id(),'card_id':card['id'],'completion_id':item['id'],'date':day,'text':note,'created':now(),'resolved':False})
            return {'id': item['id']}
        if action == 'print.profile.save':
            import math
            side = data.get('side')
            if side not in ('front', 'back'):
                raise ValueError('Vælg forside eller bagside.')
            profile = dict(data.get('profile') or {})
            for key, low, high in (('width', 50, 190), ('height', 50, 277), ('x', -10, 10), ('y', -10, 10)):
                try:
                    value = float(profile[key])
                except (KeyError, ValueError, TypeError):
                    raise ValueError('Kontrollér mål og placering.')
                if not math.isfinite(value) or not low <= value <= high:
                    raise ValueError('Kontrollér mål og placering.')
                profile[key] = value
            if profile.get('orientation') not in ('portrait', 'landscape') or profile.get('paper') not in ('cut', 'a4') or profile.get('mode') not in ('full', 'data'):
                raise ValueError('Kontrollér retning, papir og tryk.')
            if (profile['orientation'] == 'portrait') != (profile['height'] >= profile['width']):
                raise ValueError('Retning og kortmål stemmer ikke overens.')
            profile = {key: profile[key] for key in ('orientation', 'paper', 'mode', 'width', 'height', 'x', 'y')}
            config = dict(self.require('settings', 'config'))
            profiles = dict(config.get('print_profiles') or {})
            profiles[side] = profile
            config['print_profiles'] = profiles
            self.put('settings', config)
            return {}
        if action == 'visit.save':
            day = valid_day(data.get('date'))
            old = self.get('visits', data.get('id')) if data.get('id') else None
            if data.get('id') and not old:
                raise ValueError('Posten er ændret eller slettet. Opdater siden.')
            item = dict(old or {'id': new_id()})
            item.update(date=day, note=clean_text(data.get('note'), 200))
            self.put('visits', item)
            return {'id': item['id']}
        if action == 'ib.save':
            c = self.require('cards', data['card_id'])
            old = self.get('ib', data.get('id')) if data.get('id') else None
            if data.get('id') and not old:
                raise ValueError('Posten er ændret eller slettet. Opdater siden.')
            if old and old['card_id'] != c['id']:
                raise ValueError('IB tilhører et andet kort.')
            item = dict(old or {'id': new_id(), 'card_id': c['id']})
            payload = dict(data)
            address_id = clean_text(payload.get('address_id'), 160)
            if address_id:
                addresses = c.get('geo_addresses') or [self.get('geo', ident) for ident in c.get('address_ids', [])]
                address = next((a for a in addresses if a and a.get('id') == address_id), None)
                if not address:
                    raise ValueError('Adressen er ikke på dette distriktskort. Vælg en adresse fra kortets liste.')
                payload['road'] = address['road']
                payload['number'] = address['number'] + (', ' + ' '.join(str(address[k]) for k in ('floor', 'door') if address.get(k)) if address.get('floor') or address.get('door') else '')
                if any(i['id'] != item['id'] and i['card_id'] == c['id'] and (i.get('address_id') == address_id or i['road'].casefold() == payload['road'].casefold() and i['number'].casefold() == payload['number'].casefold()) for i in self.all('ib')):
                    raise ValueError('Denne adresse er allerede registreret som IB.')
                item['address_id'] = address_id
            elif 'address_id' in payload:
                item.pop('address_id', None)
            item.update(road=clean_text(payload.get('road'), 120, True), number=clean_text(payload.get('number'), 80, True), date=valid_day(payload.get('date')))
            self.put('ib', item)
            c['back_revision'] = True
            self.put('cards', c)
            return {'id': item['id']}
        if action == 'revision.approve':
            c = self.require('cards', data['card_id'])
            side = data.get('side')
            if side not in ('front', 'back'):
                raise ValueError('Vælg forside eller bagside.')
            c[side + '_revision'] = False
            c[side + '_approved'] = now()
            self.put('cards', c)
            return {}
        if action == 'map.save':
            import base64
            image = data.get('image', '')
            if image:
                if len(image) > 8000000:
                    raise ValueError('Kortbilledet må højst være 5 MB.')
                try:
                    header, encoded = image.split(',', 1)
                    content = base64.b64decode(encoded, validate=True)
                except Exception:
                    raise ValueError('Ugyldigt billede.')
                if not ((header == 'data:image/png;base64' and content.startswith(b'\x89PNG\r\n\x1a\n')) or (header == 'data:image/jpeg;base64' and content.startswith(b'\xff\xd8'))):
                    raise ValueError('Brug PNG eller JPEG.')
                if len(content) > 5 * 1024 * 1024:
                    raise ValueError('Kortbilledet må højst være 5 MB.')
                self.put('maps', {'id': 'background', 'image': image, 'name': clean_text(data.get('name'), 150)})
                # A new background invalidates all outlines to prevent misleading geography.
                for c in self.all('cards'):
                    if c.get('polygon'):
                        c['polygon'] = []
                        self.put('cards', c)
            return {}
        if action == 'map.outline':
            c = self.require('cards', data['card_id'])
            points = data.get('points', [])
            if not isinstance(points, list) or (points and len(points) < 3) or len(points) > 150:
                raise ValueError('En grænse skal have mindst tre punkter.')
            norm = []
            for pt in points:
                if len(pt) != 2:
                    raise ValueError('Ugyldigt punkt.')
                x, y = float(pt[0]), float(pt[1])
                if not (0 <= x <= 1000 and 0 <= y <= 700):
                    raise ValueError('Punkt uden for kortet.')
                norm.append([round(x, 2), round(y, 2)])
            c['polygon'] = norm
            self.put('cards', c)
            return {}
        if action == 'delete':
            module = data.get('module')
            if module not in ('cards', 'ib', 'visits', 'loans', 'completions', 'ignored', 'notes'):
                raise ValueError('Denne post kan ikke slettes her.')
            item = self.require(module, data['id'])
            if module == 'loans' and not item.get('returned'):
                raise ValueError('Aflever kortet før udlånshistorikken slettes.')
            batch, stamp = new_id(), now()
            self.mark_deleted(module, item['id'], batch, stamp)
            if module == 'cards':
                for m in ('loans', 'completions', 'ib', 'notes'):
                    for child in self.all(m):
                        if child['card_id'] == item['id']:
                            self.mark_deleted(m, child['id'], batch, stamp)
            if module == 'ib':
                c = self.require('cards', item['card_id'])
                c['back_revision'] = True
                self.put('cards', c)
            if module == 'completions':
                c = self.require('cards', item['card_id'])
                if c.get('last_completed') == item['date']:
                    remaining = [e['date'] for e in self.all('completions') if e['card_id'] == c['id']]
                    if item.get('previous_completed'): remaining.append(item['previous_completed'])
                    c['last_completed'] = max(remaining, default=None)
                    self.put('cards', c)
            return {'batch': batch}
        if action == 'recovery.purge':
            batch=data.get('batch')
            if not isinstance(batch,str) or not batch:raise ValueError('Vælg en post fra Gendan ved fejl.')
            count=0
            for module in MODULES:
                if module=='maps':continue
                cursor=self.db.execute('DELETE FROM '+self.alias(module)+'.records WHERE deleted_at IS NOT NULL AND batch=?',(batch,))
                count+=cursor.rowcount
            if not count:raise ValueError('Posten findes ikke længere i Gendan ved fejl.')
            return {'count':count}
        if action == 'restore':
            batch = data.get('batch')
            entries = [(m, item) for m in MODULES for item in self.all(m, deleted=True) if item['_batch'] == batch]
            if not entries:
                raise ValueError('Gendannelsesperioden er udløbet.')
            for module, item in entries:
                if module=='cards':
                    from geo_store import address_key
                    keys={address_key(a) for a in item.get('geo_addresses',[])};ids=set(item.get('address_ids',[]))
                    if any(ids.intersection(c.get('address_ids',[])) or keys.intersection(address_key(a) for a in c.get('geo_addresses',[])) for c in self.all('cards')):
                        raise ValueError('Adresser fra det slettede kort er nu på et andet kort. Fjern dem derfra før gendannelse.')
                    if any(i['address_id'] in ids for i in self.all('ignored')):raise ValueError('En adresse fra kortet er nu markeret Se bort fra. Fjern markeringen før gendannelse.')
                if module == 'ignored':
                    from geo_store import address_key
                    a=self.get('geo',item['address_id'])
                    if not a:raise ValueError('Adressen findes ikke længere.')
                    if any(i['address_id']==item['address_id'] for i in self.all('ignored')):
                        raise ValueError('Adressen er allerede markeret Se bort fra.')
                    if any(item['address_id'] in c.get('address_ids',[]) or any(address_key(a)==address_key(old) for old in c.get('geo_addresses',[])) for c in self.all('cards')):
                        raise ValueError('Adressen er nu på et distriktskort. Fjern den fra kortet før gendannelse af Se bort fra.')
                if module in ('ib', 'loans', 'completions') and not self.get('cards', item['card_id']) and not any(m == 'cards' and i['id'] == item['card_id'] for m, i in entries):
                    raise ValueError('Gendan kortet først.')
                if module == 'loans' and not item.get('returned') and self.active_loan(item['card_id']):
                    raise ValueError('Kortet har allerede et nyt aktivt udlån.')
                self.db.execute('UPDATE ' + self.alias(module) + '.records SET deleted_at=NULL,batch=NULL WHERE id=?', (item['id'],))
                if module == 'settings' and item.get('restore_cards'):
                    for ident in item['restore_cards']:
                        c = self.get('cards', ident)
                        if c and not c.get('area_id'):
                            c['area_id'] = item['id']
                            if not c.get('name'): c['front_revision'] = True
                            self.put('cards', c)
                    clean = self.require('settings', item['id'])
                    clean.pop('restore_cards', None)
                    self.put('settings', clean)
                if module == 'ib' and self.get('cards', item['card_id']):
                    c = self.require('cards', item['card_id']); c['back_revision'] = True; self.put('cards', c)
                if module == 'completions' and self.get('cards', item['card_id']):
                    c = self.require('cards', item['card_id'])
                    c['last_completed'] = max(c.get('last_completed') or '', item['date'])
                    self.put('cards', c)
            return {}
        if action == 'history.cleanup':
            cutoff = self.history_cutoff()
            batch, stamp, count = new_id(), now(), 0
            for m in ('loans', 'completions'):
                for item in self.all(m):
                    day = item.get('returned') if m == 'loans' else item['date']
                    if day and day < cutoff:
                        self.mark_deleted(m, item['id'], batch, stamp); count += 1
            return {'batch': batch, 'count': count}
        raise ValueError('Ukendt handling.')

    def history_cutoff(self):
        d = date.today()
        try:
            return d.replace(year=d.year-2).isoformat()
        except ValueError:
            return d.replace(year=d.year-2, day=28).isoformat()

    def close(self):
        self.db.close()
