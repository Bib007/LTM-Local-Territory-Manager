"""Preview and import local Territory Helper exports."""
import csv
import hashlib
import io
import json
import re
import unicodedata
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime
from html.parser import HTMLParser

from boundary_import import _points, preview_boundary
from geography import number_key, street_rows, valid_coordinate
from history_import import day
from history_loans import LoanPreview, apply_loans
from ui_errors import UIError


MAX_DISTRICTS = 500


def grouped_import_addresses(card):
    """Recognize unedited address rows written by the first migration beta."""
    members = card.get('imported_addresses') or []
    if not members or any(not re.fullmatch(r'[a-f0-9]{32}', a.get('id', '')) for a in members):
        return None
    original = [{key: a[key] for key in ('road', 'numbers', 'count', 'type')} for a in members
                if all(key in a for key in ('road', 'numbers', 'count', 'type'))]
    if len(original) != len(members) or original != card.get('addresses'):
        return None
    rows = street_rows(members)
    return rows if len(rows) <= 300 else None


FIELDS = {
    'id': 'id territoryid territoryidentifier publisherid publisheridentifier distriktsid forkynderid',
    'card_id': 'territoryid territoryidentifier cardid distriktsid',
    'number': 'territorynumber cardnumber kortnummer distriktsnummer distrikt territory number nummer',
    'type': 'territorytype territorytypename distriktstype type',
    'code': 'territorytypecode typecode distriktskode code',
    'name': 'label territorylabel territoryname cardname navn distriktsnavn etiket mærke distriktsmærke name',
    'person': 'publisher publishername forkynder forkyndernavn assignedto tildelttil name navn',
    'person_id': 'publisherid publisheridentifier forkynderid',
    'first': 'firstname fornavn',
    'last': 'lastname surname efternavn',
    'road': 'street streetname road vej vejnavn gade addressstreet',
    'house': 'housenumber streetnumber addressnumber number husnummer nummer',
    'address': 'address formattedaddress locationaddress adresse adressebetegnelse',
    'post': 'postcode postalcode zip zipcode postnummer',
    'floor': 'floor etage',
    'door': 'door apartment unit side dør lejlighed enhed',
    'lat': 'latitude lat breddegrad',
    'lng': 'longitude lng lon længdegrad',
    'assigned': 'assigned dateassigned assigneddate assignmentdate udleveret udleveringsdato tildelt tildelingsdato',
    'returned': 'returned datereturned returneddate returndate afleveret afleveringsdato returneret indleveret',
    'complete': 'completed iscompleted worked gennemgået fuldført',
    'complete_date': 'datecompleted completeddate completiondate gennemgangsdato',
    'date': 'date datecreated created createddate dato datooprettet oprettet registreringsdato',
    'notes': 'notes note description kommentar bemærkning noter notater',
    'boundary': 'boundary coordinates grænse polygon',
}
KINDS = ('cards', 'locations', 'ib', 'publishers', 'assignments', 'geometry', 'kml')
CSV_NAMES = {
    'cards': ('distrikter', 'territories'),
    'locations': ('lokationer', 'locations'),
    'ib': ('ib', 'dnc', 'do not calls', 'do not call'),
    'publishers': ('forkyndere', 'publishers'),
    'assignments': ('tildelinger', 'assignments'),
}


def key(value):
    return re.sub(r'[^\w]+', '', str(value or '').strip().casefold()).replace('_', '')


def norm(value):
    return ' '.join(unicodedata.normalize('NFC', str(value or '')).casefold().split())


def get(row, field):
    return next((row[k] for k in FIELDS[field].split() if row.get(k)), '')


def classify(filename, content):
    name, _, extension = filename.casefold().rpartition('.')
    if extension in ('json', 'geojson', 'kml'):
        return 'kml' if extension == 'kml' else 'geometry'
    if extension != 'csv':
        raise UIError('Importen understøtter CSV, JSON og KML.')
    header = set()
    if content.strip():
        # Read only the header for classification. The same CSV parser later handles quoted records.
        try:
            first = content.lstrip('\ufeff').splitlines()[0]
            dialect = csv.Sniffer().sniff(first, delimiters=',;\t')
            header = {key(value) for value in next(csv.reader([first], dialect))}
        except (csv.Error, IndexError, StopIteration):
            pass
    has = lambda field: bool(header.intersection(FIELDS[field].split()))
    if has('assigned') and has('returned') and has('number'):
        return 'assignments'
    if has('first') and has('last'):
        return 'publishers'
    if has('number') and (has('boundary') or (has('id') and has('name'))):
        return 'cards'
    # The two Territory Helper address exports have the same columns.
    # Use their export filenames to tell them apart.
    stem = re.sub(r'\s*\(\d+\)$', '', name).strip()
    for kind, aliases in CSV_NAMES.items():
        if any(re.search(r'(?:^|[\s_-])' + re.escape(alias).replace(' ', '[ _-]+') + r'$', stem) for alias in aliases):
            return kind
    raise UIError('Filtypen kunne ikke genkendes for {file}. Brug filnavnet fra Territory Helper.', file=filename)


def upload_files(data):
    uploads = data.get('uploads')
    if not isinstance(uploads, list) or not 1 <= len(uploads) <= len(KINDS):
        raise UIError('Vælg én eksportfil på højst 2 MB pr. filtype.')
    files, names = {}, {}
    for upload in uploads:
        if not isinstance(upload, dict):
            raise UIError('Vælg en eksportfil fra Territory Helper.')
        filename, content = upload.get('name'), upload.get('content')
        if (not isinstance(filename, str) or not 1 <= len(filename) <= 240
                or not isinstance(content, str) or len(content.encode('utf-8')) > 2_000_000):
            raise UIError('Vælg én eksportfil på højst 2 MB pr. filtype.')
        kind = classify(filename, content)
        if kind in files:
            raise UIError('Der er valgt flere filer af samme type. Fjern en af filerne.')
        files[kind], names[kind] = content, filename
    return files, names


def read_csv(content):
    if not content.strip():
        return []
    try:
        delimiter = csv.Sniffer().sniff(content.splitlines()[0], delimiters=',;\t').delimiter
        rows = csv.reader(io.StringIO(content), delimiter=delimiter, strict=True)
        names = [key(n) for n in next(rows)]
        if not names or len(set(names)) != len(names) or len(names) > 120:
            raise ValueError()
        result = []
        for line, values in enumerate(rows, 2):
            if line > 15001 or len(values) != len(names):
                raise ValueError()
            if any(v.strip() for v in values):
                result.append(dict(zip(names, (v.strip() for v in values))))
        return result
    except (StopIteration, csv.Error, ValueError):
        raise UIError('CSV-filen har ugyldige kolonner eller rækker.') from None


def text_field(value, limit, *, required=False):
    if len(value) > limit or (required and not value):
        raise UIError('Et påkrævet felt mangler eller er for langt.')
    return value


class NoteText(HTMLParser):
    """Keep visible note text and block boundaries from exported formatting."""
    block = {'p', 'div', 'br', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'section'}
    hidden = {'script', 'style', 'template'}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = []

    def handle_starttag(self, tag, attrs):
        if tag in self.hidden:
            self.skip.append(tag)
        elif tag in self.block and not self.skip:
            self.parts.append('\n')
            if tag == 'li':
                self.parts.append('• ')

    def handle_endtag(self, tag):
        if self.skip and self.skip[-1] == tag:
            self.skip.pop()
        elif tag in self.block and not self.skip:
            self.parts.append('\n')

    def handle_data(self, value):
        if not self.skip:
            self.parts.append(value)


def note_text(value):
    if re.search(r'</?[A-Za-z][A-Za-z0-9]*(?:\s|/?>)', value):
        parser = NoteText()
        parser.feed(value)
        parser.close()
        value = '\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())
    return text_field(value, 64000)


def date_field(value):
    if not value:
        return None
    try:
        if re.match(r'^\d{4}-\d{2}-\d{2}[T ]', value):
            return datetime.fromisoformat(value.replace('Z', '+00:00')).date().isoformat()
        return day(re.sub(r'\s+\d{1,2}:\d{2}(?::\d{2})?$', '', value))
    except ValueError:
        raise UIError('Eksporten indeholder en ugyldig dato.') from None


def optional_point(row):
    lat, lng = get(row, 'lat'), get(row, 'lng')
    if not (lat or lng):
        return {}
    x, y = valid_coordinate([lng.replace(',', '.'), lat.replace(',', '.')])
    return {'lng': x, 'lat': y}


def address(row):
    road, house = get(row, 'road'), get(row, 'house')
    if not road or not house:
        match = re.fullmatch(r'(.+?)\s+(\d+[A-Za-zÆØÅæøå]?)(?:,\s*\d{4}(?:\s+.*)?)?', get(row, 'address'))
        if match:
            road, house = road or match[1], house or match[2]
    if not road or len(road) > 120:
        raise UIError('Vejnavnet mangler eller er for langt.')
    if not house or len(house) > 80:
        raise UIError('Husnummeret mangler eller er for langt.')
    floor, door = get(row, 'floor'), get(row, 'door')
    post = text_field(get(row, 'post'), 4)
    if post and not re.fullmatch(r'\d{4}', post):
        raise UIError('Postnummer skal være fire cifre eller stå tomt.')
    return {'road': text_field(road, 120, required=True),
            'number': text_field(house, 80, required=True),
            'postcode': post, 'floor': text_field(floor, 20), 'door': text_field(door, 30),
            **optional_point(row)}


def card_number(row):
    number, code = get(row, 'number'), get(row, 'code')
    return code + '-' + number if code and number and not norm(number).startswith(norm(code) + '-') else number


def polygon(value):
    raw = json.loads(value) if isinstance(value, str) else value
    if isinstance(raw, dict):
        rings = raw.get('coordinates')
        if raw.get('type') != 'Polygon' or not isinstance(rings, list) or len(rings) != 1:
            raise UIError('Kortet skal have én polygon uden huller.')
        raw = rings[0]
        if isinstance(raw, list):
            raw = [p[:2] if isinstance(p, list) else p for p in raw]
    elif isinstance(raw, list) and raw:
        if isinstance(raw[0], dict):
            points = [{key(k): v for k, v in p.items()} for p in raw]
            raw = [[p.get('lng', p.get('lon', p.get('longitude'))),
                    p.get('lat', p.get('latitude'))] for p in points]
        elif isinstance(raw[0], list) and len(raw[0]) == 2 and isinstance(raw[0][0], (int, float)) and 54 <= raw[0][0] <= 58.5:
            raw = [[x, y] for y, x in raw]
    return _points(raw, 5000)


def geometry_rows(content):
    try:
        raw = json.loads(content)
        if isinstance(raw, dict) and raw.get('type') == 'FeatureCollection':
            return [({key(k): str(v) for k, v in (f.get('properties') or {}).items() if v is not None},
                     f.get('geometry')) for f in raw['features']]
        if isinstance(raw, dict):
            raw = raw.get('Territories', raw.get('territories'))
        if not isinstance(raw, list):
            raise ValueError()
        rows = [{key(k): v for k, v in row.items()} for row in raw]
        return [({k: str(v) for k, v in row.items() if v is not None and isinstance(v, (str, int))}, get(row, 'boundary')) for row in rows]
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        raise UIError('Distrikternes JSON-fil kunne ikke læses.') from None


def entry_fields(kind, row, people):
    if kind == 'assignments':
        names = people.get(norm(get(row, 'person_id')), [])
        name = get(row, 'person')
        incomplete = key(row.get('ikkegennemgået') or row.get('notcompleted'))
        completed = key(get(row, 'complete')) in ('true', 'yes', 'ja', '1') or incomplete in ('false', 'no', 'nej', '0')
        return {'publisher': name or (names[0] if len(names) == 1 else ''),
                'assigned': get(row, 'assigned'), 'returned': get(row, 'returned'),
                'complete_date': get(row, 'complete_date'), 'completed': '1' if completed else ''}
    return {field: get(row, field) for field in ('road', 'house', 'address', 'post', 'floor', 'door', 'lat', 'lng', 'date', 'notes')}


def parse_entry(kind, fields):
    if kind == 'assignments':
        assigned, returned = date_field(fields['assigned']), date_field(fields['returned'])
        completed = date_field(fields['complete_date'])
        if completed and completed != returned:
            raise UIError('Gennemgangsdato og afleveringsdato skal stemme overens.')
        return {'publisher': text_field(fields['publisher'], 100, required=True), 'assigned': assigned,
                'returned': returned, 'completed': bool(completed) or bool(returned and fields['completed'] == '1')}
    row = {FIELDS[field].split()[0]: value for field, value in fields.items()}
    record = {**address(row), 'note': text_field(fields['notes'], 500)}
    number_key(record['number'])
    if kind == 'ib':
        record['date'] = date_field(fields['date'])
        if record['date'] and record['date'] > date.today().isoformat():
            raise UIError('En IB-dato ligger i fremtiden.')
        if len(ib_number(record)) > 80:
            raise UIError('En IB-adresse har et for langt husnummer, etage eller dør.')
    return record


def issue(kind, fields, message, source=None):
    return {'id': uuid.uuid4().hex, 'kind': kind, 'fields': fields, 'message': str(message), 'source': source or {}}


def loan_plan(store, card, assignments):
    planner = LoanPreview(store, date.today().isoformat(), store.history_cutoff())
    rows, rejected = [], []
    for assignment in sorted(assignments, key=lambda a: a['assigned'] or ''):
        row = {}
        try:
            planner.add(row, card, assignment['publisher'], assignment['assigned'],
                        assignment['returned'], completed=assignment['completed'])
        except ValueError as error:
            rejected.append(issue('assignments', {
                'publisher': assignment['publisher'], 'assigned': assignment['assigned'] or '',
                'returned': assignment['returned'] or '', 'complete_date': '',
                'completed': '1' if assignment['completed'] else '',
            }, error))
            row['status'] = 'invalid'
        rows.append(row)
    return planner, rows, rejected


def note_roads(store, note):
    """Match complete road-list lines against names in the local DAR download."""
    from street_suggestions import ranges

    names = defaultdict(dict)
    for address in store.all('geo'):
        if (address.get('entity') == 'address' and not address.get('retired')
                and address.get('source', '').startswith('DAR') and address.get('postcode')):
            names[norm(address['road'])][address['postcode']] = address['road']

    matches = {}
    for line in note.splitlines():
        match = re.fullmatch(r'\s*[•*\-]?\s*(.+?)\s+(\d.*|hele vejen)\s*', line, re.I)
        if not match:
            continue
        possible = names.get(norm(match[1].rstrip(':')))
        if not possible or len(possible) != 1:
            continue
        numbers = match[2].strip()
        try:
            ranges(numbers)
        except ValueError:
            continue
        postcode, road = next(iter(possible.items()))
        matches[road, postcode, numbers] = {'road': road, 'postcode': postcode, 'numbers': numbers}
    return list(matches.values())[:50]


def preview(store, data):
    if data.get('note_card_id'):
        card = store.require('cards', data['note_card_id'])
        return {'roads': note_roads(store, card.get('import_note', ''))}
    files, source_names = upload_files(data) if 'uploads' in data else (data.get('files'), {})
    if not isinstance(files, dict) or set(files) - set(KINDS) or any(
            not isinstance(v, str) or len(v.encode('utf-8')) > 2_000_000 for v in files.values()):
        raise UIError('Vælg én eksportfil på højst 2 MB pr. filtype.')
    files = {k: v.lstrip('\ufeff') for k, v in files.items()}
    csv_rows = {k: read_csv(files.get(k, '')) for k in KINDS[:5]}
    geometry = geometry_rows(files['geometry']) if files.get('geometry') else []
    source_cards = csv_rows['cards'] or [r for r, _ in geometry]
    if not source_cards or len(source_cards) > MAX_DISTRICTS:
        raise UIError(f'Vælg en eksport med 1–{MAX_DISTRICTS} distrikter.')
    issues = Counter()
    unlinked = []
    cards, identity, numbers = [], defaultdict(list), defaultdict(list)
    repeated = Counter(norm(card_number(row)) for row in source_cards)
    source_occurrences = Counter()
    for row in source_cards:
        source_number = card_number(row)
        card_type = get(row, 'type')
        number = (f'{card_type}-{source_number}' if source_number and card_type and
                  repeated[norm(source_number)] > 1 else source_number)
        source_key = (norm(get(row, 'id')), norm(card_type), norm(source_number))
        source_occurrences[source_key] += 1
        import_id = hashlib.sha256(json.dumps([source_key, source_occurrences[source_key]]).encode()).hexdigest()
        card = {'index': len(cards), 'number': number, 'name': get(row, 'name')[:100],
                'type': card_type, 'note': '', 'polygon': [], 'locations': [], 'ib': [], 'assignments': [], 'errors': [], 'pending': [], 'import_id': import_id}
        if not number or len(number) > 30:
            card['errors'].append('Kortnummeret skal indeholde 1–30 tegn.')
        if len(get(row, 'name')) > 100:
            card['pending'].append(issue('name', {'name': get(row, 'name')}, 'Kortnavnet må højst have 100 tegn.'))
        try:
            card['note'] = note_text(get(row, 'notes'))
        except ValueError:
            card['pending'].append(issue('note', {'notes': get(row, 'notes')}, 'Det eksporterede kortnotat er for langt.'))
        cards.append(card)
        for label in {number, get(row, 'number')}:
            numbers[norm(label)].append(card)
        if get(row, 'id'):
            identity[norm(get(row, 'id'))].append(card)

    def match(row, id_fields=('card_id',), *, geometry_file=False):
        ident = next((get(row, f) for f in id_fields if get(row, f)), '')
        number = card_number(row if geometry_file else {k: v for k, v in row.items() if k not in ('number', 'nummer')})
        if ident and identity:
            candidates = identity.get(norm(ident), [])
            if number and candidates and not any(c in numbers.get(norm(number), []) for c in candidates):
                return None
        else:
            candidates = numbers.get(norm(number), [])
        card_type = norm(get(row, 'type'))
        if card_type:
            candidates = [card for card in candidates if not card['type'] or norm(card['type']) == card_type]
        return candidates[0] if len(candidates) == 1 else None

    def put_boundary(card, value):
        if not value:
            return
        try:
            points = polygon(value)
            if card['polygon'] and {tuple(p) for p in points} != {tuple(p) for p in card['polygon']}:
                raise UIError('Eksportfilerne har forskellige grænser for kortet.')
            if not card['polygon']:
                card['polygon'] = points
        except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
            card['pending'].append(issue('boundary', {'boundary': value if isinstance(value, str) else json.dumps(value)},
                                         'Kontrollér kortets grænse i eksportfilerne.'))

    for row, value in geometry:
        card = match(row, ('id', 'card_id'), geometry_file=True)
        if card is None:
            issues['geometry'] += 1
            unlinked.append(issue('boundary', {'boundary': value if isinstance(value, str) else json.dumps(value)},
                                  'Rækker uden entydigt kort', row))
        else:
            put_boundary(card, value)
            if not card['note'] and get(row, 'notes'):
                try:
                    card['note'] = note_text(get(row, 'notes'))
                except ValueError:
                    card['pending'].append(issue('note', {'notes': get(row, 'notes')}, 'Det eksporterede kortnotat er for langt.'))
    for card, row in zip(cards, source_cards):
        put_boundary(card, get(row, 'boundary'))
    if files.get('kml'):
        labels = defaultdict(list)
        for card in cards:
            labels[norm(card['number'])].append(card)
            if card['name']:
                labels[norm(card['number'] + ' - ' + card['name'])].append(card)
        for boundary in preview_boundary(files['kml'], 'card', max_boundaries=MAX_DISTRICTS)['boundaries']:
            matches = labels.get(norm(boundary['name']), [])
            if len(matches) != 1:
                issues['kml'] += 1
                unlinked.append(issue('boundary', {'boundary': json.dumps(boundary.get('points', []))},
                                      'Rækker uden entydigt kort', boundary))
            elif 'points' in boundary:
                put_boundary(matches[0], boundary['points'])
            else:
                matches[0]['pending'].append(issue('boundary', {'boundary': ''},
                    'Kontrollér kortets grænse i eksportfilerne.', boundary))

    people = defaultdict(list)
    for row in csv_rows['publishers']:
        ident = get(row, 'id')
        name = get(row, 'person') or ' '.join(filter(None, (get(row, 'first'), get(row, 'last'))))
        if ident and name and name not in people[norm(ident)]:
            people[norm(ident)].append(name)
    for kind in ('locations', 'ib', 'assignments'):
        seen = defaultdict(set)
        for row in csv_rows[kind]:
            card = match(row)
            fields = entry_fields(kind, row, people)
            if card is None:
                issues[kind] += 1
                unlinked.append(issue(kind, fields, 'Rækker uden entydigt kort', row))
                continue
            try:
                if kind == 'assignments':
                    names = people.get(norm(get(row, 'person_id')), [])
                    name = get(row, 'person')
                    if len(names) > 1 or names and name and norm(name) != norm(names[0]):
                        raise UIError('Forkynderen i tildelingen kunne ikke matches entydigt.')
                record = parse_entry(kind, fields)
                fingerprint = tuple(record.items())
                if fingerprint not in seen[card['index']]:
                    card[kind].append(record)
                    seen[card['index']].add(fingerprint)
            except (ValueError, TypeError, OverflowError) as error:
                card['pending'].append(issue(kind, fields, error, row))


    duplicates = Counter(norm(c['number']) for c in cards)
    occupied = {norm(c['number']) for c in store.all('cards') + store.all('cards', deleted=True)}
    for card in cards:
        if duplicates[norm(card['number'])] != 1 or norm(card['number']) in occupied:
            card['errors'].append('Kortnummeret findes allerede eller er ikke entydigt.')
        ib_addresses = {(norm(a['road']), norm(a['number']), a['postcode'], norm(a['floor']), norm(a['door'])) for a in card['ib']}
        if len(ib_addresses) < len(card['ib']):
            card['errors'].append('Flere forskellige IB-rækker har samme adresse.')
        _, card['loan_review'], rejected = loan_plan(store, {'id': uuid.uuid4().hex}, card['assignments'])
        card['errors'] = list(dict.fromkeys(card['errors'] + [entry['message'] for entry in card['pending'] + rejected]))
    batch_id = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    token = store.setup_remember('territory-helper', {'owner': data.get('_owner'), 'cards': cards, 'unlinked': unlinked,
                                                     'batch_id': batch_id})
    # Recovery payloads remain server-side until a user opens the follow-up.
    public = [{key: value for key, value in card.items() if key not in ('pending', 'import_id')} for card in cards]
    return {'token': token, 'cards': public, 'unmatched': dict(issues), 'sources': source_names}


def ib_number(address):
    unit = ' '.join(filter(None, (address['floor'], address['door'])))
    return f"{address['number']}, {unit}" if unit else address['number']


def imported_location(address, ident=None):
    return dict(address, id=ident or uuid.uuid4().hex, numbers=address['number'], count=1,
                type='Lejlighed' if address['floor'] or address['door'] else 'Hus')


def save_ib(store, ident, address, *, existing=None):
    saved = store._mutate('ib.save', {'id': existing, 'card_id': ident, 'road': address['road'], 'number': ib_number(address),
                                    'postcode': address['postcode'], 'date': address['date'],
                                    'date_text': '' if address['date'] else 'Ukendt'})
    if address['note']:
        store.put('ib', dict(store.require('ib', saved['id']), import_note=address['note']))


def save_assignments(store, planner):
    allocation = planner.payload()
    apply_loans(store, allocation)
    for row in sorted(planner.events.values(), key=lambda row: row['date']):
        card = dict(store.require('cards', row['card_id']))
        entry = store.create_completion(card, row['date'], row['loan_id'])
        store.put('completions', dict(entry, visits=0, visits_unknown=True, source='history-import'))
    return len(allocation['loans'])


def save_followup(store, ident, import_id, pending, warnings):
    if not (pending or warnings):
        return
    key = json.dumps(['checks', ident or import_id, 'territory-helper'], separators=(',', ':'))
    text = '\n'.join(dict.fromkeys([*warnings, *(entry['message'] for entry in pending)]))
    existing = next((row for row in store.all('notes') if row.get('followup_key') == key), None)
    saved = store._mutate('note.save', {'id': existing['id'] if existing else None, 'card_id': ident,
                                       'followup_key': key, 'text': text[:1000]})
    item = dict(store.require('notes', saved['id']), territory_helper_issues=pending, territory_helper_warnings=warnings,
                resolved=False, resolved_at=None)
    store.put('notes', item)


def legacy_match(card, existing, imported_numbers):
    members = existing.get('imported_addresses')
    if members is None or any(not re.fullmatch(r'[a-f0-9]{32}', member.get('id', '')) for member in members):
        return False
    if norm(existing['number']) in imported_numbers:
        return True

    def identity(row):
        return tuple(norm(row.get(key)) for key in ('road', 'number', 'postcode', 'floor', 'door'))
    incoming = {identity(row) for row in card['locations']}
    return bool(incoming.intersection(map(identity, members)) or
                card['polygon'] and card['polygon'] == existing.get('geo_polygon'))


def recover_legacy(store, source, existing):
    pending = list(source['pending'])
    ident = existing['id']
    old_ib = [row for row in store.all('ib') if row['card_id'] == ident]
    for entry in pending:
        if entry['kind'] != 'ib':
            continue
        fields = entry['fields']
        old_number = ib_number({'number': fields['house'], 'floor': fields['floor'], 'door': fields['door']})
        match = next((row for row in old_ib if norm(row['road']) == norm(fields['road']) and
                      norm(row['number']) == norm(old_number) and row.get('postcode', '') == fields['post']), None)
        if match:
            entry['target_id'] = match['id']
    planner, _, rejected = loan_plan(store, existing, source['assignments'])
    save_assignments(store, planner)
    card = dict(store.require('cards', ident), territory_helper_import_id=source['import_id'])
    store.put('cards', card)
    save_followup(store, ident, source['import_id'], pending + rejected, [])
    return {'id': ident, 'number': card['number']}


def apply(store, data):
    plan = store.setup_require_preview(data, 'territory-helper')
    if plan['owner'] != data.get('_owner'):
        raise PermissionError()
    bulk = data.get('all') is True
    index = data.get('index')
    if not bulk and (type(index) is not int or not 0 <= index < len(plan['cards'])):
        raise UIError('Vælg et kort i forhåndsvisningen.')
    active = store.all('cards')
    existing = active + store.all('cards', deleted=True)
    active_by_number = {norm(c['number']): c for c in active}
    occupied = {norm(c['number']) for c in existing}
    requested_numbers = {norm(c['number']) for c in plan['cards']}
    imported_numbers = {norm(number) for note in store.all('notes')
                        if note.get('action') == 'setup.territory-helper.apply'
                        for number in note.get('cards', [])}
    by_import = {c.get('territory_helper_import_id'): c for c in existing}
    saved = []
    for card in plan['cards'] if bulk else [plan['cards'][index]]:
        if card['import_id'] in by_import:
            saved.append({'index': card['index'], 'id': by_import[card['import_id']]['id'], 'number': by_import[card['import_id']]['number']})
            continue
        number = card['number']
        old = active_by_number.get(norm(number))
        if old and not old.get('territory_helper_import_id') and legacy_match(card, old, imported_numbers):
            saved.append({'index': card['index'], **recover_legacy(store, card, old)})
            continue
        if not number or len(number) > 30 or norm(number) in occupied:
            suffix = 1
            number = f'TH-{card["index"] + 1}'
            while norm(number) in occupied or norm(number) in requested_numbers:
                suffix += 1
                number = f'TH-{card["index"] + 1}-{suffix}'
        saved.append({'index': card['index'], **save_card(store, card, number)})
        occupied.add(norm(number))
    if plan['unlinked']:
        key = json.dumps(['checks', plan['batch_id'], 'territory-helper'], separators=(',', ':'))
        if not any(note.get('followup_key') == key for note in store.all('notes') + store.all('notes', deleted=True)):
            save_followup(store, None, plan['batch_id'], plan['unlinked'], [])
    return {'saved': saved, 'skipped': []} if bulk else saved[0]


def save_card(store, card, number):
    pending = list(card['pending'])
    warnings = []
    if number != card['number']:
        pending.append(issue('number', {'number': card['number']}, 'Vælg et gyldigt og ledigt kortnummer.'))
    members = [imported_location(a) for a in card['locations']]
    addresses = street_rows(members)
    if len(addresses) > 300:
        warnings.append('Hele vejlisten kunne ikke vises på ét kort. Kontrollér de importerede adresser.')
    kind = {'city': 'By', 'by': 'By', 'rural': 'Land', 'land': 'Land'}.get(norm(card['type']), 'Ukendt')
    ident = store._mutate('card.save', {'number': number, 'name': card['name'], 'kind': kind,
                                      'temporary': not addresses, 'addresses': addresses[:300]})['id']
    item = dict(store.require('cards', ident), territory_helper_import_id=card['import_id'])
    if card['note']:
        item['import_note'] = card['note']
    item['imported_addresses'] = members
    if card['polygon']:
        item.update(geo_polygon=card['polygon'], geo_outline_source='manual')
    store.put('cards', item)
    ib_keys = set()
    for a in card['ib']:
        key = (norm(a['road']), norm(ib_number(a)), a['postcode'])
        if key in ib_keys:
            pending.append(issue('ib', {'road': a['road'], 'house': a['number'], 'address': '',
                'post': a['postcode'], 'floor': a['floor'], 'door': a['door'], 'lat': '', 'lng': '',
                'date': a['date'] or '', 'notes': a['note']}, 'Flere forskellige IB-rækker har samme adresse.'))
            continue
        save_ib(store, ident, a)
        ib_keys.add(key)
    item = dict(store.require('cards', ident), front_revision=False, back_revision=False)
    store.put('cards', item)
    planner, _, rejected = loan_plan(store, item, card['assignments'])
    loans = save_assignments(store, planner)
    save_followup(store, ident, card['import_id'], pending + rejected, warnings)
    return {'id': ident, 'number': number, 'ib': len(ib_keys), 'loans': loans}


def review(store, data, *, repair=False):
    note = dict(store.require('notes', data.get('id')))
    pending = note.get('territory_helper_issues')
    if pending is None:
        raise UIError('Vælg en opfølgning fra Territory Helper.')
    if not repair:
        return {'card_id': note.get('card_id'), 'issues': pending}
    entry = next((item for item in pending if item['id'] == data.get('issue_id')), None)
    if entry is None:
        raise UIError('Rækken er allerede behandlet. Åbn opfølgningen igen.')
    fields = data.get('fields')
    if (not isinstance(fields, dict) or fields.keys() != entry['fields'].keys()
            or any(not isinstance(value, str) or len(value) > 2_000_000 for value in fields.values())):
        raise UIError('Ugyldige data.')
    fields = {key: value.strip() for key, value in fields.items()}
    card = dict(store.require('cards', note.get('card_id') or data.get('card_id')))
    ident, kind = card['id'], entry['kind']
    if kind in ('number', 'name'):
        field = {'number': 'number', 'name': 'name'}[kind]
        store._mutate('card.save', {**card, field: fields[field]})
    elif kind == 'note':
        store.put('cards', dict(card, import_note=note_text(fields['notes'])))
    elif kind == 'boundary':
        points = polygon(fields['boundary'])
        store.put('cards', dict(card, geo_polygon=points, geo_outline_source='manual', front_revision=True))
    else:
        record = parse_entry(kind, fields)
        if kind == 'locations':
            members = card.get('imported_addresses', [])
            member = imported_location(record, entry['id'])
            fields_to_compare = ('road', 'number', 'postcode', 'floor', 'door')
            if not any(all(norm(old.get(key)) == norm(member.get(key)) for key in fields_to_compare) for old in members):
                grouped = street_rows(members + [member])
                # Keep manual edits and any DAR-linked address selection intact.
                if not card.get('geo_addresses'):
                    current = card.get('addresses', [])
                    previous = street_rows(members)[:300]
                    if current == previous:
                        card['addresses'] = grouped[:300]
                    else:
                        extra = street_rows([member])[0]
                        if len(current) >= 300:
                            raise UIError('Hele vejlisten kunne ikke vises på ét kort. Kontrollér de importerede adresser.')
                        card['addresses'] = current + [extra]
                    card['temporary'] = False
                card.update(imported_addresses=members + [member], front_revision=True)
                store.put('cards', card)
        elif kind == 'ib':
            number = ib_number(record)
            if any(old['id'] != entry.get('target_id') and old['card_id'] == ident and norm(old['road']) == norm(record['road'])
                   and norm(old['number']) == norm(number) and old.get('postcode', '') == record['postcode']
                   for old in store.all('ib')):
                raise UIError('Denne adresse er allerede registreret som IB.')
            save_ib(store, ident, record, existing=entry.get('target_id'))
        else:
            planner, rows, rejected = loan_plan(store, card, [record])
            if rejected:
                raise UIError(rejected[0]['message'])
            if rows[0]['status'] != 'ready':
                raise UIError(rows[0]['message'])
            save_assignments(store, planner)
    pending = [item for item in pending if item['id'] != entry['id']]
    warnings = note.get('territory_helper_warnings', [])
    note.update(territory_helper_issues=pending, resolved=not pending and not warnings)
    if pending or warnings:
        note['text'] = '\n'.join(dict.fromkeys([*warnings, *(item['message'] for item in pending)]))[:1000]
    store.put('notes', note)
    return {'remaining': len(pending)}
