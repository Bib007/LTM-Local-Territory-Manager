"""Join complete flat DAR entity sets without writing or skipping broken addresses.

All inputs must come from one fixed snapshot and complete page collections.
This pure normalizer cannot establish completeness of the caller's input sets.
"""
import math
import re
from dar_paging import IncompleteResult
from geography import decode_dar


def _fail():
    # Do not echo upstream text, raw records or lookup values into download errors.
    raise IncompleteResult('DAR-adresserne kunne ikke sammenkobles fuldstændigt. Ingen adresser er klar til import.')


def _text(row, field):
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        _fail()
    return value


def _index(rows):
    result = {}
    if not isinstance(rows, list):
        _fail()
    for row in rows:
        if not isinstance(row, dict):
            _fail()
        ident = _text(row, 'id_lokalId')
        if ident in result:
            _fail()
        result[ident] = row
    return result


def _related(row, field, index):
    found = index.get(_text(row, field))
    if found is None or found.get('status') != '3':
        _fail()
    return found


def _point(row):
    position = row.get('position')
    if not isinstance(position, dict) or position.get('crs') != 25832:
        _fail()
    dimension = position.get('dimension')
    if dimension not in ('XY', 'XYZ'):
        _fail()
    wkt = position.get('wkt')
    if not isinstance(wkt, str):
        _fail()
    match = re.fullmatch(r'POINT\s*(Z\s*)?\(\s*([^()]+)\s*\)', wkt)
    if not match or (match[1] and dimension != 'XYZ'):
        _fail()
    try:
        coords = [float(v) for v in match[2].split()]
    except ValueError:
        _fail()
    if len(coords) != (2 if dimension == 'XY' else 3) or not all(math.isfinite(v) for v in coords):
        _fail()
    # DAR's UTM32 envelope for Denmark (incl. Bornholm); reject plausible-looking
    # WGS84 or corrupt metre coordinates before the inverse projection.
    if not (100000 <= coords[0] <= 1000000 and 5900000 <= coords[1] <= 6500000):
        _fail()
    return coords[:2]


def join_addresses(addresses, houses, points, roads, posts, *, postcode=None, road=None):
    """Return existing LTM address shape only when every in-scope join succeeds.

    A road can cross postcode boundaries. Scope filtering uses explicit flat
    references before requiring an in-scope address point. No fallback coordinates
    or made-up address IDs are allowed. The return value is entirely in memory.
    """
    if postcode is not None and (not isinstance(postcode, str) or not re.fullmatch(r'\d{4}', postcode)):
        raise ValueError('Vælg et firecifret postnummer.')
    if road is not None and (not isinstance(road, str) or not road.strip()):
        raise ValueError('Vælg et vejnavn.')
    address_index, house_index, point_index, road_index, post_index = (
        _index(rows) for rows in (addresses, houses, points, roads, posts))
    normalized = []
    for address in address_index.values():
        if address.get('status') != '3':
            _fail()
        house = _related(address, 'husnummer', house_index)
        post = _related(house, 'postnummer', post_index)
        code = _text(post, 'postnr')
        if not re.fullmatch(r'\d{4}', code):
            _fail()
        if postcode is not None and code != postcode:
            continue
        named = _related(house, 'navngivenVej', road_index)
        name = _text(named, 'vejnavn')
        if road is not None and name != road:
            _fail()
        coords = _point(_related(house, 'adgangspunkt', point_index))
        for field in ('etagebetegnelse', 'doerbetegnelse'):
            # null and empty both mean absent; a missing projected field is unsafe.
            if field not in address or (address[field] is not None and not isinstance(address[field], str)):
                _fail()
        normalized.append({
            'id_lokalid': address['id_lokalId'], 'status': '3',
            'adressebetegnelse': _text(address, 'adressebetegnelse'),
            'etagebetegnelse': address['etagebetegnelse'], 'doerbetegnelse': address['doerbetegnelse'],
            'husnummer': {
                'id_lokalid': house['id_lokalId'], 'vejnavn': name,
                'husnummertekst': _text(house, 'husnummertekst'), 'postnummer': {'postnr': code},
                'adgangspunkt': {'geometri': {'coordinates': coords,
                    'crs': {'properties': {'name': 'EPSG:25832'}}}},
            },
        })
    try:
        return decode_dar(normalized)
    except (ValueError, OverflowError, ZeroDivisionError):
        _fail()
