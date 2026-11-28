"""Preview and import local Territory Helper exports."""
import csv
import io
import json
import re
import unicodedata
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime
from html.parser import HTMLParser

from boundary_import import _points, preview_boundary
from geography import street_rows, valid_coordinate
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


def loan_plan(store, card, assignments):
    planner = LoanPreview(store, date.today().isoformat(), store.history_cutoff())
    rows = []
    for assignment in sorted(assignments, key=lambda a: a['assigned'] or ''):
        row = {}
        planner.add(row, card, assignment['publisher'], assignment['assigned'],
                    assignment['returned'], completed=assignment['completed'])
        rows.append(row)
    return planner, rows


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
    cards, identity, numbers = [], defaultdict(list), defaultdict(list)
    repeated = Counter(norm(card_number(row)) for row in source_cards)
    for row in source_cards:
        source_number = card_number(row)
        card_type = get(row, 'type')
        number = (f'{card_type}-{source_number}' if source_number and card_type and
                  repeated[norm(source_number)] > 1 else source_number)
        card = {'index': len(cards), 'number': number, 'name': text_field(get(row, 'name'), 100),
                'type': card_type, 'note': '', 'polygon': [], 'locations': [], 'ib': [], 'assignments': [], 'errors': []}
        if not number or len(number) > 30:
            card['errors'].append('Kortnummeret skal indeholde 1–30 tegn.')
        try:
            card['note'] = note_text(get(row, 'notes'))
        except ValueError:
            card['errors'].append('Det eksporterede kortnotat er for langt.')
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
            card['errors'].append('Kontrollér kortets grænse i eksportfilerne.')

    for row, value in geometry:
        card = match(row, ('id', 'card_id'), geometry_file=True)
        if card is None:
            issues['geometry'] += 1
        else:
            put_boundary(card, value)
            if not card['note'] and get(row, 'notes'):
                try:
                    card['note'] = note_text(get(row, 'notes'))
                except ValueError:
                    card['errors'].append('Det eksporterede kortnotat er for langt.')
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
            elif 'points' in boundary:
                put_boundary(matches[0], boundary['points'])
            else:
                matches[0]['errors'].append('Kontrollér kortets grænse i eksportfilerne.')

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
            if card is None:
                issues[kind] += 1
                continue
            try:
                if kind == 'assignments':
                    person_id = get(row, 'person_id')
                    names = people.get(norm(person_id), [])
                    name = get(row, 'person')
                    if len(names) > 1 or names and name and norm(name) != norm(names[0]):
                        raise UIError('Forkynderen i tildelingen kunne ikke matches entydigt.')
                    assigned, returned = date_field(get(row, 'assigned')), date_field(get(row, 'returned'))
                    completed = date_field(get(row, 'complete_date'))
                    if completed and completed != returned:
                        raise UIError('Gennemgangsdato og afleveringsdato skal stemme overens.')
                    person = names[0] if names else name
                    incomplete = key(row.get('ikkegennemgået') or row.get('notcompleted'))
                    explicitly_completed = key(get(row, 'complete')) in ('true', 'yes', 'ja', '1') or incomplete in ('false', 'no', 'nej', '0')
                    record = {'publisher': text_field(person, 100, required=True), 'assigned': assigned,
                              'returned': returned, 'completed': bool(completed) or bool(returned and explicitly_completed)}
                    if record['completed'] and not returned:
                        raise UIError('En gennemgang mangler en afleveringsdato.')
                else:
                    record = {**address(row), 'note': text_field(get(row, 'notes'), 500)}
                    if kind == 'ib':
                        record['date'] = date_field(get(row, 'date'))
                        if record['date'] and record['date'] > date.today().isoformat():
                            raise UIError('En IB-dato ligger i fremtiden.')
                        if len(ib_number(record)) > 80:
                            raise UIError('En IB-adresse har et for langt husnummer, etage eller dør.')
                fingerprint = tuple(record.items())
                if fingerprint not in seen[card['index']]:
                    card[kind].append(record)
                    seen[card['index']].add(fingerprint)
            except (ValueError, TypeError, OverflowError) as error:
                card['errors'].append(str(error))

    duplicates = Counter(norm(c['number']) for c in cards)
    occupied = {norm(c['number']) for c in store.all('cards') + store.all('cards', deleted=True)}
    for card in cards:
        if duplicates[norm(card['number'])] != 1 or norm(card['number']) in occupied:
            card['errors'].append('Kortnummeret findes allerede eller er ikke entydigt.')
        ib_addresses = {(norm(a['road']), norm(a['number']), a['postcode'], norm(a['floor']), norm(a['door'])) for a in card['ib']}
        if len(ib_addresses) < len(card['ib']):
            card['errors'].append('Flere forskellige IB-rækker har samme adresse.')
        try:
            _, card['loan_review'] = loan_plan(store, {'id': uuid.uuid4().hex}, card['assignments'])
        except ValueError as error:
            card['errors'].append(str(error))
            card['loan_review'] = []
        card['errors'] = list(dict.fromkeys(card['errors']))
    token = store.setup_remember('territory-helper', {'owner': data.get('_owner'), 'cards': cards})
    return {'token': token, 'cards': cards, 'unmatched': dict(issues), 'sources': source_names}


def ib_number(address):
    unit = ' '.join(filter(None, (address['floor'], address['door'])))
    return f"{address['number']}, {unit}" if unit else address['number']


def apply(store, data):
    plan = store.setup_require_preview(data, 'territory-helper')
    if plan['owner'] != data.get('_owner'):
        raise PermissionError()
    if data.get('all') is True:
        occupied = {norm(c['number']) for c in store.all('cards') + store.all('cards', deleted=True)}
        saved, skipped = [], []
        for index, card in enumerate(plan['cards']):
            if not card['number'] or len(card['number']) > 30 or norm(card['number']) in occupied:
                skipped.append({'index': index, 'number': card['number']})
                continue
            saved.append({'index': index, **save_card(store, card)})
            occupied.add(norm(card['number']))
        return {'saved': saved, 'skipped': skipped}
    index = data.get('index')
    if type(index) is not int or not 0 <= index < len(plan['cards']):
        raise UIError('Vælg et kort i forhåndsvisningen.')
    card = plan['cards'][index]
    if card['errors']:
        raise UIError('Ret kortets importfejl før du godkender.')
    return save_card(store, card)


def save_card(store, card):
    warnings = list(card['errors'])
    members = [dict(a, numbers=a['number'], count=1, type='Lejlighed' if a['floor'] or a['door'] else 'Hus')
               for a in card['locations']]
    addresses = street_rows(members)
    if len(addresses) > 300:
        warnings.append('Hele vejlisten kunne ikke vises på ét kort. Kontrollér de importerede adresser.')
        addresses = addresses[:300]
    kind = {'city': 'By', 'by': 'By', 'rural': 'Land', 'land': 'Land'}.get(norm(card['type']), 'Ukendt')
    ident = store._mutate('card.save', {'number': card['number'], 'name': card['name'], 'kind': kind,
                                      'temporary': not addresses, 'addresses': addresses})['id']
    item = dict(store.require('cards', ident))
    if card['note']:
        item['import_note'] = card['note']
    item['imported_addresses'] = [dict(a, id=uuid.uuid4().hex) for a in members]
    if card['polygon']:
        item.update(geo_polygon=card['polygon'], geo_outline_source='manual')
    store.put('cards', item)
    ib_keys = set()
    for a in card['ib']:
        number = ib_number(a)
        key_ = (norm(a['road']), norm(number), a['postcode'])
        if key_ in ib_keys:
            continue
        ib_keys.add(key_)
        saved = store._mutate('ib.save', {'card_id': ident, 'road': a['road'], 'number': number,
                                        'postcode': a['postcode'], 'date': a['date'],
                                        'date_text': '' if a['date'] else 'Ukendt'})
        if a['note']:
            store.put('ib', dict(store.require('ib', saved['id']), import_note=a['note']))
    item = dict(store.require('cards', ident), front_revision=False, back_revision=False)
    store.put('cards', item)
    try:
        planner, _ = loan_plan(store, item, card['assignments'])
    except ValueError as error:
        warnings.append(str(error))
        planner, _ = loan_plan(store, item, [])
    allocation = planner.payload()
    apply_loans(store, allocation)
    for row in sorted(planner.events.values(), key=lambda row: row['date']):
        # The number of today's locations does not establish historical visits.
        stored = dict(store.require('cards', ident))
        entry = store.create_completion(stored, row['date'], row['loan_id'])
        store.put('completions', dict(entry, visits=0, visits_unknown=True, source='history-import'))
    if warnings:
        description = '\n'.join(dict.fromkeys(warnings))
        key_ = json.dumps(['checks', ident, 'territory-helper'], separators=(',', ':'))
        store._mutate('note.save', {'card_id': ident, 'followup_key': key_, 'text': description[:1000]})
    return {'id': ident, 'number': card['number'], 'ib': len(ib_keys), 'loans': len(allocation['loans'])}
