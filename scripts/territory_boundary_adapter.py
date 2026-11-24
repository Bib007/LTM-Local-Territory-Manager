"""Offline, explicitly approved conversion of ONE territory boundary (not addresses)."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'distrikt' / 'app'))
from boundary_import import preview_boundary

MAX_BYTES = 2_000_000
NWS_FIELDS = {'Number', 'CategoryCode', 'Suffix', 'Boundary'}
REQUIRED_NWS = {'Number', 'Boundary'}


def _identifiers(number, category, suffix):
    if not isinstance(number, str) or not re.fullmatch(r'[1-9][0-9]*', number):
        raise ValueError('Number skal være et positivt heltal uden foranstillede nuller.')
    if not isinstance(category, str) or not re.fullmatch(r'[A-Za-z0-9_-]{0,20}', category):
        raise ValueError('CategoryCode må kun indeholde korte bogstaver, tal, - og _.')
    if not isinstance(suffix, str) or not re.fullmatch(r'[A-Za-z0-9-]{0,12}', suffix):
        raise ValueError('Suffix må kun indeholde korte bogstaver, tal og -.')
    return number, category, suffix


def nws_to_geojson(content):
    """Accept a strict, publicly documented NW Scheduler *territories* CSV subset."""
    if len(content.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Filen er for stor (2 MB).')
    try:
        reader = csv.DictReader(io.StringIO(content.lstrip('\ufeff'), newline=''), strict=True)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers) or not REQUIRED_NWS <= set(headers) or set(headers) - NWS_FIELDS:
            raise ValueError('Kun Number, CategoryCode, Suffix og Boundary understøttes; fjern øvrige felter lokalt.')
        rows = list(reader)
    except csv.Error:
        raise ValueError('Ugyldig komma-separeret CSV.') from None
    if len(rows) != 1 or None in rows[0] or any(key is None for key in rows[0]):
        raise ValueError('Vælg præcis én distriktsrække, med korrekt CSV-citering.')
    row = rows[0]
    if any(row.get(k) is None for k in ('Number', 'Boundary')) or any(
            key in row and row[key] is None for key in row):
        raise ValueError('En CSV-række mangler et påkrævet felt.')
    number, category, suffix = _identifiers(*(row.get(k, '').strip() for k in ('Number', 'CategoryCode', 'Suffix')))
    boundary = row['Boundary'].strip()
    if not boundary or len(boundary) > MAX_BYTES:
        raise ValueError('Boundary mangler eller er for stor.')
    try:
        ring = json.loads('[' + boundary + ']')
    except (ValueError, RecursionError):
        raise ValueError('Boundary skal være [longitude,latitude] adskilt med komma.') from None
    if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
        raise ValueError('Boundary skal være en lukket polygon med mindst tre hjørner.')
    feature = {'type': 'Feature',
               'properties': {'name': 'Territory ' + number + ('-' + suffix if suffix else ''),
                              'nws': {'Number': number, 'CategoryCode': category, 'Suffix': suffix}},
               'geometry': {'type': 'Polygon', 'coordinates': [ring]}}
    # Reuse LTM's actual import validation, including WGS84 and its current Danish bounds.
    checked = preview_boundary(json.dumps(feature, ensure_ascii=False))
    return json.dumps(feature, ensure_ascii=False, indent=2) + '\n', _summary('NWS CSV → LTM GeoJSON', checked, number)


def geojson_to_nws(content, number=None, category=None, suffix=None):
    """Only geometry + non-personal identifiers; all other properties fail closed."""
    if len(content.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Filen er for stor (2 MB).')
    try:
        geo = json.loads(content.lstrip('\ufeff'))
    except (ValueError, RecursionError):
        raise ValueError('Ugyldig GeoJSON.') from None
    if not isinstance(geo, dict) or geo.get('type') not in ('Feature', 'Polygon'):
        raise ValueError('Brug én GeoJSON Feature eller Polygon.')
    properties = geo.get('properties', {}) if geo.get('type') == 'Feature' else {}
    if not isinstance(properties, dict) or set(properties) - {'name', 'nws'}:
        raise ValueError('GeoJSON indeholder andre egenskaber; private felter må ikke eksporteres.')
    metadata = properties.get('nws', {})
    if not isinstance(metadata, dict) or set(metadata) - NWS_FIELDS or 'Boundary' in metadata:
        raise ValueError('Ukendt NW Scheduler-metadata i GeoJSON.')
    number = number if number is not None else metadata.get('Number')
    category = category if category is not None else metadata.get('CategoryCode', '')
    suffix = suffix if suffix is not None else metadata.get('Suffix', '')
    number, category, suffix = _identifiers(number, category, suffix)
    for key, chosen in (('Number', number), ('CategoryCode', category), ('Suffix', suffix)):
        if key in metadata and metadata[key] != chosen:
            raise ValueError('Angivet ' + key + ' afviger fra filens metadata.')
    checked = preview_boundary(content)
    if len(checked['boundaries']) != 1 or 'points' not in checked['boundaries'][0]:
        raise ValueError('Kun én gyldig polygon kan eksporteres.')
    points = checked['boundaries'][0]['points']
    boundary = ','.join(json.dumps(p, separators=(',', ':')) for p in points + [points[0]])
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(('Number', 'CategoryCode', 'Suffix', 'Boundary'))
    writer.writerow((number, category, suffix, boundary))
    return output.getvalue(), _summary('LTM GeoJSON → NWS CSV', checked, number)


def th_to_geojson(content):
    """Convert a single reviewed Territory Helper-style KML polygon locally."""
    if len(content.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Filen er for stor (2 MB).')
    checked = preview_boundary(content)
    if checked['format'] != 'KML' or len(checked['boundaries']) != 1 or checked['skipped']:
        raise ValueError('Vælg en KML-fil med præcis én polygon uden andre objekter.')
    item = checked['boundaries'][0]
    if 'points' not in item:
        raise ValueError('KML-grænsen er ugyldig.')
    ring = item['points'] + [item['points'][0]]
    feature = {'type': 'Feature', 'properties': {'name': 'Imported territory boundary'},
               'geometry': {'type': 'Polygon', 'coordinates': [ring]}}
    return json.dumps(feature, ensure_ascii=False, indent=2) + '\n', _summary('TH KML → LTM GeoJSON', checked, '-')


def geojson_to_th(content):
    """Produce ordinary KML 2.2 Polygon; no comments, labels or person records."""
    if len(content.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Filen er for stor (2 MB).')
    try:
        geo = json.loads(content.lstrip('\ufeff'))
    except (ValueError, RecursionError):
        raise ValueError('Ugyldig GeoJSON.') from None
    if not isinstance(geo, dict) or geo.get('type') not in ('Feature', 'Polygon'):
        raise ValueError('Brug én GeoJSON Feature eller Polygon.')
    properties = geo.get('properties', {}) if geo.get('type') == 'Feature' else {}
    if not isinstance(properties, dict) or set(properties) - {'name', 'nws'}:
        raise ValueError('GeoJSON indeholder andre egenskaber; private felter må ikke eksporteres.')
    if 'nws' in properties and (not isinstance(properties['nws'], dict) or
                               set(properties['nws']) - {'Number', 'CategoryCode', 'Suffix'}):
        raise ValueError('Ukendte oplysninger i GeoJSON-metadata.')
    checked = preview_boundary(content)
    if len(checked['boundaries']) != 1 or 'points' not in checked['boundaries'][0]:
        raise ValueError('Kun én gyldig polygon kan eksporteres.')
    points = checked['boundaries'][0]['points']
    coordinates = ' '.join(f'{lon},{lat},0' for lon, lat in points + [points[0]])
    # Fixed, non-personal label avoids carrying KML/GeoJSON free text across systems.
    output = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark>'
              '<name>Territory boundary</name><Polygon><outerBoundaryIs><LinearRing>'
              '<coordinates>' + escape(coordinates) + '</coordinates>'
              '</LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>\n')
    return output, _summary('LTM GeoJSON → TH KML', checked, '-')


def _summary(direction, checked, number):
    return {'retning': direction, 'distrikt': number,
            'grænser': len(checked['boundaries']),
            'hjørner': len(checked['boundaries'][0]['points']),
            'bemærkning': 'Kun én grænse; ingen adresser, IB, noter, navne eller historik.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('direction', choices=('nws-to-ltm', 'ltm-to-nws', 'th-to-ltm', 'ltm-to-th'))
    parser.add_argument('source', type=Path)
    parser.add_argument('target', type=Path)
    parser.add_argument('--number', help='Numerisk distriktsnummer ved LTM → NWS')
    parser.add_argument('--category-code', help='Eksisterende NW Scheduler-kategorikode')
    parser.add_argument('--suffix', help='Valgfrit NW Scheduler-suffiks')
    parser.add_argument('--approve', help='Brug kode fra en særskilt forhåndsvisning af samme indhold')
    args = parser.parse_args(argv)
    try:
        if args.source.resolve() == args.target.resolve():
            raise ValueError('Kildefilen må aldrig overskrives.')
        if args.source.stat().st_size > MAX_BYTES:
            raise ValueError('Filen er for stor (2 MB).')
        content = args.source.read_text(encoding='utf-8-sig')
        result, summary = {
            'nws-to-ltm': lambda: nws_to_geojson(content),
            'ltm-to-nws': lambda: geojson_to_nws(content, args.number, args.category_code, args.suffix),
            'th-to-ltm': lambda: th_to_geojson(content),
            'ltm-to-th': lambda: geojson_to_th(content),
        }[args.direction]()
        code = hashlib.sha256((args.direction + '\n' + result).encode('utf-8')).hexdigest()[:16]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if args.approve is None:
            print('Kun forhåndsvisning. Ingen fil skrevet. Gentag med --approve ' + code + ' efter kontrol.')
            return 0
        if args.approve != code:
            raise ValueError('Bekræftelseskoden matcher ikke denne fil og konvertering.')
        # Exclusive create: never overwrite an existing file or a symlink.
        fd = os.open(args.target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='') as dest:
                dest.write(result)
        except BaseException:
            args.target.unlink(missing_ok=True)
            raise
        print('Målfil oprettet lokalt. Kontrollér den i målprogrammets importvisning; intet er importeret.')
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print('Konvertering afvist: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
