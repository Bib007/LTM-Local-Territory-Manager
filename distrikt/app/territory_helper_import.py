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
from history_loans import LoanPreview, apply_loans, overlaps
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
            if line > 15001:
                raise ValueError()
            if not any(v.strip() for v in values):
                continue
            if len(values) != len(names):
                raise ValueError()
            result.append({**dict(zip(names, (v.strip() for v in values))), '_row': line})
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
    if not house:
        raise UIError('Eksporten har et tomt husnummerfelt for denne adresse.')
    if len(house) > 80:
        raise UIError('Husnummerfeltet har {count} tegn. LTM kan gemme op til 80 tegn.', count=len(house))
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
    if isinstance(raw, list):
        # Consecutive duplicate vertices do not change the shape. Leave other
        # repeats to the polygon validator.
        raw = [point for index, point in enumerate(raw) if index == 0 or point != raw[index - 1]]
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
    try:
        number_key(record['number'])
    except ValueError:
        raise UIError('Husnummerfeltet skal indeholde ét husnummer, fx 42 eller 42B. Et interval eller flere numre kræver separate adresser.') from None
    if kind == 'ib':
        record['date'] = date_field(fields['date'])
        if record['date'] and record['date'] > date.today().isoformat():
            raise UIError('En IB-dato ligger i fremtiden.')
        if len(ib_number(record)) > 80:
            raise UIError('En IB-adresse har et for langt husnummer, etage eller dør.')
    return record


def issue(kind, fields, message, source=None, *, file='', reason=None):
    result = {'id': uuid.uuid4().hex, 'kind': kind, 'fields': fields, 'message': str(message),
              'source': source or {}, 'file': file, 'params': getattr(message, 'ui_params', {})}
    if isinstance(message, UIError):
        result['message'] = message.ui_key
    if reason:
        result['detail'] = str(reason)
    return result


def diagnostic(entry):
    source, fields = entry.get('source', {}), entry['fields']
    context = {key: value for key, value in fields.items()
               if key in ('road', 'house', 'address', 'post', 'floor', 'door', 'lat', 'lng', 'publisher',
                          'assigned', 'returned', 'date', 'number', 'name')}
    context.update(card_number=get(source, 'number') if 'number' not in source and 'nummer' not in source else
                   get({key: value for key, value in source.items() if key not in ('number', 'nummer')}, 'number'),
                   card_id=get(source, 'card_id'), kml_name=source.get('placemark', source.get('name', '') if 'index' in source else ''),
                   folder=source.get('folder', ''), row=source.get('_row'),
                   kml_index=source.get('kml_index', source.get('index', -1) + 1 if 'index' in source else None))
    entry = {k: entry[k] for k in ('id', 'kind', 'message', 'params', 'file', 'detail') if k in entry}
    entry['context'] = {key: str(value)[:200] for key, value in context.items() if value or key == 'house'}
    return entry


def polygon_key(points):
    """Canonical ring, ignoring the starting corner, closing point and winding."""
    if not points:
        return ()
    ring = [tuple(p) for p in points]
    index = ring.index(min(ring))
    rotated = tuple(ring[index:] + ring[:index])
    return min(rotated, (rotated[0], *reversed(rotated[1:])))


def label_key(value):
    return norm(re.sub(r'\s*[-–—:·]\s*', ' ', value))



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
    kml_matches = {}
    cards, identity, numbers = [], defaultdict(dict), defaultdict(dict)
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
                'type': card_type, 'source_number': source_number, 'raw_number': get(row, 'number'),
                'note': '', 'polygon': [], 'boundary_file': '', 'locations': [], 'ib': [], 'assignments': [], 'errors': [], 'pending': [], 'import_id': import_id}
        if not number or len(number) > 30:
            card['errors'].append('Kortnummeret skal indeholde 1–30 tegn.')
        if len(get(row, 'name')) > 100:
            card['pending'].append(issue('name', {'name': get(row, 'name')}, 'Kortnavnet må højst have 100 tegn.'))
        try:
            card['note'] = note_text(get(row, 'notes'))
        except ValueError:
            card['pending'].append(issue('note', {'notes': get(row, 'notes')}, 'Det eksporterede kortnotat er for langt.'))
        cards.append(card)
        for label in {number, source_number, get(row, 'number')} - {''}:
            numbers[norm(label)][card['index']] = card
        if get(row, 'id'):
            identity[norm(get(row, 'id'))][card['index']] = card

    def match(row, id_fields=('card_id',), *, geometry_file=False):
        ident = next((get(row, f) for f in id_fields if get(row, f)), '')
        number = card_number(row if geometry_file else {k: v for k, v in row.items() if k not in ('number', 'nummer')})
        number_matches = numbers.get(norm(number), {})
        card_type = norm(get(row, 'type'))
        if ident and identity:
            candidates = identity.get(norm(ident), {})
            if not candidates:
                return None, UIError('Kort-id {id} findes ikke i distriktslisten.', id=ident)
            if number and not (candidates.keys() & number_matches.keys()):
                return None, UIError('Kort-id {id} stemmer ikke med kortnummer {number} i distriktslisten.', id=ident, number=number)
        elif number:
            candidates = number_matches
        else:
            return None, 'Rækken har hverken et kortnummer eller et kort-ID, der kan bruges.'
        matches = [c for c in candidates.values() if not card_type or not c['type'] or norm(c['type']) == card_type]
        if len(matches) == 1:
            return matches[0], ''
        if len(matches) > 1:
            return None, UIError('Rækken passer på flere distrikter: {cards}.',
                                 cards=', '.join(c['number'] for c in matches))
        return None, UIError('Fandt intet distrikt med kortnummer {number} og den angivne distriktstype.',
                             number=number or ident)

    def file_label(kind):
        return source_names.get(kind) or {'cards': 'Distrikter · CSV', 'locations': 'Lokationer · CSV',
            'ib': 'IB · CSV', 'assignments': 'Tildelinger · CSV', 'geometry': 'Distrikter · JSON',
            'kml': 'Distrikter · KML'}[kind]

    def put_boundary(card, value, source, kind):
        if not value:
            return
        fields = {'boundary': value if isinstance(value, str) else json.dumps(value)}
        file = file_label(kind)
        try:
            points = polygon(value)
        except (ValueError, TypeError, AttributeError, OverflowError, RecursionError) as error:
            detail = 'Koordinaterne kan ikke læses som JSON.' if isinstance(error, json.JSONDecodeError) else str(error)
            card['pending'].append(issue('boundary', fields, 'Grænsen er ugyldig.', source, file=file, reason=detail))
            return
        if not card['polygon']:
            card.update(polygon=points, boundary_file=file)
        elif polygon_key(points) != polygon_key(card['polygon']):
            message = UIError('Grænserne i {first} og {second} har forskellige hjørner. LTM beholdt grænsen fra {first}.',
                              first=card['boundary_file'], second=file)
            card['pending'].append(issue('boundary', fields, message, source, file=file))

    for row, value in geometry:
        card, reason = match(row, ('id', 'card_id'), geometry_file=True)
        if card is None:
            issues['geometry'] += 1
            unlinked.append(issue('boundary', {'boundary': value if isinstance(value, str) else json.dumps(value)},
                                  reason, row, file=file_label('geometry')))
        else:
            put_boundary(card, value, row, 'geometry')
            if not card['note'] and get(row, 'notes'):
                try:
                    card['note'] = note_text(get(row, 'notes'))
                except ValueError:
                    card['pending'].append(issue('note', {'notes': get(row, 'notes')}, 'Det eksporterede kortnotat er for langt.'))
    for card, row in zip(cards, source_cards):
        put_boundary(card, get(row, 'boundary'), row, 'cards' if csv_rows['cards'] else 'geometry')
    if files.get('kml'):
        labels, rings = defaultdict(dict), defaultdict(dict)
        for card in cards:
            for number in {card['number'], card['source_number'], card['raw_number']} - {''}:
                for alias in (number, f"Kort {number}", f"{card['type']} {number}", f"{number} {card['name']}",
                              f"{card['type']} {number} {card['name']}", f"Kort {number} {card['name']}",
                              f"Territory {number} {card['name']}", f"{card['name']} {number}"):
                    labels[label_key(alias)][card['index']] = card
            if card['name']:
                labels[label_key(card['name'])][card['index']] = card
            if card['polygon']:
                rings[polygon_key(card['polygon'])][card['index']] = card
        for boundary in preview_boundary(files['kml'], 'card', max_boundaries=MAX_DISTRICTS, include_source=True)['boundaries']:
            metadata = {key(k): v for k, v in boundary.pop('metadata').items()}
            name, folder = boundary['placemark'], boundary['folder']
            boundary['kml_index'] = boundary['index'] + 1
            points = boundary.pop('raw_points', None) or boundary.pop('points', [])
            if any(get(metadata, f) for f in ('card_id', 'id', 'number')):
                card, reason = match(metadata, ('card_id', 'id'), geometry_file=True)
            else:
                candidates = labels.get(label_key(name), {})
                if candidates and folder:
                    by_folder = [c for c in candidates.values() if norm(c['type']) == norm(folder)]
                    if by_folder:
                        candidates = {c['index']: c for c in by_folder}
                same_shape = rings.get(polygon_key(points), {}) if points and not boundary.get('error') else {}
                if same_shape:
                    candidates = ({i: c for i, c in candidates.items() if i in same_shape}
                                  if candidates else same_shape) or candidates
                card = next(iter(candidates.values())) if len(candidates) == 1 else None
                if len(candidates) > 1:
                    reason = UIError('KML-navnet passer på flere distrikter: {cards}.',
                                     cards=', '.join(c['number'] for c in candidates.values()))
                elif name:
                    reason = 'KML-navnet matcher ikke et kortnummer eller kortnavn i distriktslisten.'
                else:
                    reason = 'KML-elementet har intet navn, kortnummer eller kort-ID, og grænsen matcher ingen unik kendt grænse.'
            if card is None:
                issues['kml'] += 1
                unlinked.append(issue('boundary', {'boundary': json.dumps(points)}, reason, boundary,
                                      file=file_label('kml'), reason=boundary.get('error')))
            elif boundary.get('error'):
                card['pending'].append(issue('boundary', {'boundary': json.dumps(points)}, 'Grænsen er ugyldig.',
                                             boundary, file=file_label('kml'), reason=boundary['error']))
            else:
                put_boundary(card, points, boundary, 'kml')
                if polygon_key(card['polygon']) == polygon_key(points):
                    kml_matches[boundary['index']] = card['import_id']

    people = defaultdict(list)
    for row in csv_rows['publishers']:
        ident = get(row, 'id')
        name = get(row, 'person') or ' '.join(filter(None, (get(row, 'first'), get(row, 'last'))))
        if ident and name and name not in people[norm(ident)]:
            people[norm(ident)].append(name)
    for kind in ('locations', 'ib', 'assignments'):
        seen = defaultdict(set)
        for row in csv_rows[kind]:
            card, reason = match(row)
            fields = entry_fields(kind, row, people)
            if card is None:
                issues[kind] += 1
                unlinked.append(issue(kind, fields, reason, row, file=file_label(kind)))
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
                card['pending'].append(issue(kind, fields, error, row, file=file_label(kind)))


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
                                                     'batch_id': batch_id, 'kml_matches': kml_matches})
    # Recovery payloads remain server-side until a user opens the follow-up.
    public = [{**{key: value for key, value in card.items() if key not in ('pending', 'import_id')},
               'diagnostics': [diagnostic(entry) for entry in card['pending'][:20]]} for card in cards]
    return {'token': token, 'cards': public, 'unmatched': dict(issues), 'sources': source_names,
            'unmatched_details': [diagnostic(entry) for entry in unlinked[:100]]}


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
    text = '\n'.join(dict.fromkeys([*warnings, *(entry['message'].format(**entry.get('params', {})) if entry.get('params') else entry['message'] for entry in pending)]))
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
    active_ids = {c['id'] for c in active}
    kml_import_ids = set(plan['kml_matches'].values())
    occupied = {norm(c['number']) for c in existing}
    requested_numbers = {norm(c['number']) for c in plan['cards']}
    imported_numbers = {norm(number) for note in store.all('notes')
                        if note.get('action') == 'setup.territory-helper.apply'
                        for number in note.get('cards', [])}
    by_import = {c.get('territory_helper_import_id'): c for c in existing}
    saved = []
    for card in plan['cards'] if bulk else [plan['cards'][index]]:
        if card['import_id'] in by_import:
            old = by_import[card['import_id']]
            if (card['import_id'] in kml_import_ids and old['id'] in active_ids
                    and not old.get('archived') and not old.get('geo_polygon') and not old.get('geo_updated')):
                store.put('cards', dict(old, geo_polygon=card['polygon'], geo_outline_source='manual'))
            saved.append({'index': card['index'], 'id': old['id'], 'number': old['number']})
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
    key = json.dumps(['checks', plan['batch_id'], 'territory-helper'], separators=(',', ':'))
    prior = next((note for note in store.all('notes') if note.get('followup_key') == key), None)
    if prior and not prior.get('resolved'):
        refresh_unlinked(store, plan, prior, saved)
    elif not prior and plan['unlinked'] and not any(note.get('followup_key') == key for note in store.all('notes', deleted=True)):
        save_followup(store, None, plan['batch_id'], plan['unlinked'], [])
    return {'saved': saved, 'skipped': []} if bulk else saved[0]


def refresh_unlinked(store, plan, note, saved):
    """Refresh outstanding diagnostics for the same files without reopening fixed rows."""
    pending = note.get('territory_helper_issues') or []
    current_by_kml_index = {entry['source']['index']: entry for entry in plan['unlinked']
                            if 'index' in entry['source']}
    source_cards = {card['import_id']: card for card in plan['cards']}
    applied = {plan['cards'][row['index']]['import_id']: store.get('cards', row['id']) for row in saved}
    remaining = []
    for entry in pending:
        index = entry.get('source', {}).get('index')
        if entry['kind'] != 'boundary' or index is None:
            remaining.append(entry)
            continue
        if index in current_by_kml_index:
            remaining.append(dict(current_by_kml_index[index], id=entry['id']))
            continue
        linked = plan['kml_matches'].get(index)
        card = applied.get(linked)
        if not card or polygon_key(card.get('geo_polygon')) != polygon_key(source_cards[linked]['polygon']):
            remaining.append(entry)
    if remaining != pending:
        update_followup(store, note, remaining)


def update_followup(store, note, pending):
    warnings = note.get('territory_helper_warnings', [])
    note = dict(note, territory_helper_issues=pending, resolved=not pending and not warnings)
    if pending or warnings:
        messages = [entry['message'].format(**entry.get('params', {})) if entry.get('params') else entry['message']
                    for entry in pending]
        note['text'] = '\n'.join(dict.fromkeys([*warnings, *messages]))[:1000]
    store.put('notes', note)


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


def review_details(store, card_id, pending):
    card_issues = [{**entry, **diagnostic(entry)} for entry in pending]
    assignments = [entry for entry in card_issues if entry['kind'] == 'assignments']
    if not card_id or not assignments:
        return card_issues
    loans = [(loan, deleted) for deleted in (False, True) for loan in store.all('loans', deleted=deleted)
             if loan['card_id'] == card_id]
    people = {person['id']: person['name'] for deleted in (False, True)
              for person in store.all('publishers', deleted=deleted)}
    for entry in assignments:
        try:
            proposed = parse_entry('assignments', entry['fields'])
        except ValueError:
            continue
        if not proposed['assigned'] or (proposed['returned'] and proposed['returned'] < proposed['assigned']):
            continue
        conflicts = []
        for loan, deleted in loans:
            name = people.get(loan['publisher_id'], '')
            same_loan = (norm(name) == norm(proposed['publisher']) and
                         all(loan.get(field) == proposed[field] for field in ('assigned', 'returned')))
            if (overlaps(proposed, loan) and (deleted or not same_loan)
                    or deleted and proposed['assigned'] == loan['assigned']):
                conflicts.append({'publisher': name, 'assigned': loan['assigned'],
                                  'returned': loan.get('returned'), 'deleted': deleted})
        entry['overlapping_loans'] = sorted(conflicts, key=lambda row: row['assigned'])
    return card_issues


def review(store, data, *, repair=False):
    note = dict(store.require('notes', data.get('id')))
    pending = note.get('territory_helper_issues')
    if pending is None:
        raise UIError('Vælg en opfølgning fra Territory Helper.')
    if not repair:
        return {'card_id': note.get('card_id'), 'issues': review_details(store, note.get('card_id'), pending)}
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
    update_followup(store, note, pending)
    return {'remaining': len(pending), 'issues': review_details(store, note.get('card_id'), pending)}
