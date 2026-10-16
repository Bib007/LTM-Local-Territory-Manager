"""Read boundary files locally. Parsing never saves records or follows KML links."""
import json
import math
import re
import xml.etree.ElementTree as ET
from geography import valid_polygon

MAX_BYTES = 2000000
KML_NAMESPACES = {'', 'http://www.opengis.net/kml/2.2',
                  'http://earth.google.com/kml/2.0', 'http://earth.google.com/kml/2.1',
                  'http://earth.google.com/kml/2.2', 'http://www.opengis.net/kml/2.3'}


def _tag(node):
    tag = node.tag
    if not isinstance(tag, str):return ''
    if tag.startswith('{'):
        ns, tag = tag[1:].split('}', 1)
        if ns not in KML_NAMESPACES:return ''
    return tag


def _children(node, name):return [n for n in node if _tag(n) == name]


def _points(raw, limit):
    if not isinstance(raw, list):raise ValueError('Grænsen mangler koordinater.')
    if len(raw) > limit + 1:raise ValueError(f'Grænsen må højst have {limit} hjørner.')
    if raw and raw[0] == raw[-1]:raw = raw[:-1]
    try:points = valid_polygon(raw, limit=limit)
    except (TypeError, OverflowError):raise ValueError('Grænsen indeholder ugyldige koordinater.') from None
    if len({tuple(p) for p in points}) != len(points):raise ValueError('Grænsen har gentagne hjørner.')
    return points


def _kml_coordinates(ring, limit):
    nodes = _children(ring, 'coordinates')
    if len(nodes) != 1:raise ValueError('Grænsen skal have én koordinatliste.')
    tuples = (nodes[0].text or '').split()
    if len(tuples) > limit + 1:raise ValueError(f'Grænsen må højst have {limit} hjørner.')
    points = []
    for item in tuples:
        values = item.split(',')
        if len(values) not in (2, 3):raise ValueError('Ugyldigt KML-koordinat. Brug længdegrad,breddegrad[,højde].')
        try:numbers = [float(v) for v in values]
        except (ValueError, OverflowError):raise ValueError('KML-filen indeholder et ugyldigt tal.') from None
        if not all(math.isfinite(v) for v in numbers):raise ValueError('KML-filen indeholder et ugyldigt tal.')
        points.append(numbers[:2])
    return points


def _kml(content, limit):
    if re.search(r'<!\s*(DOCTYPE|ENTITY)\b', content, re.I):
        raise ValueError('KML med DTD eller XML-entiteter understøttes ikke. Eksporter en almindelig KML-fil.')
    try:root = ET.fromstring(content)
    except (ET.ParseError, ValueError):raise ValueError('KML-filen kunne ikke læses. Kontroller, at filen er en gyldig KML-fil.') from None
    if _tag(root) != 'kml':raise ValueError('Filen er ikke en KML-fil med et kml-rodelement.')
    nodes = list(root.iter())
    if len(nodes) > 20000:raise ValueError('KML-filen indeholder for mange elementer. Eksporter kun grænserne.')
    boundaries, skipped = [], 0
    stack = [(root, '', '', 0, False)]
    while stack:
        node, folder, placemark, depth, in_polygon = stack.pop()
        if depth > 50:raise ValueError('KML-filen er for dybt indlejret.')
        tag = _tag(node)
        if tag in ('Document', 'Folder', 'Placemark'):
            names = _children(node, 'name')
            name = ''.join(names[0].itertext()).strip()[:200] if names else ''
            if tag == 'Placemark':placemark = name
            elif name:folder = name
        is_boundary = tag == 'Polygon' or tag in ('LinearRing', 'LineString') and not in_polygon
        if is_boundary:
            if len(boundaries) >= 100:raise ValueError('Filen må højst indeholde 100 grænser. Eksporter et mindre udvalg.')
            item = {'index':len(boundaries), 'name':placemark or folder or f'Grænse {len(boundaries)+1}'}
            try:
                if tag == 'Polygon':
                    if _children(node, 'innerBoundaryIs'):raise ValueError('Grænsen har huller. Importer én sammenhængende ydergrænse uden huller.')
                    outer = _children(node, 'outerBoundaryIs')
                    rings = _children(outer[0], 'LinearRing') if len(outer) == 1 else []
                    if len(rings) != 1:raise ValueError('Polygonen mangler én tydelig ydergrænse.')
                    raw = _kml_coordinates(rings[0], limit)
                else:
                    raw = _kml_coordinates(node, limit)
                    if not raw or raw[0] != raw[-1]:raise ValueError('Linjen er ikke lukket. Eksporter en polygon eller en lukket grænselinje.')
                item['points'] = _points(raw, limit)
            except (ValueError, TypeError, OverflowError) as error:item['error'] = str(error)
            boundaries.append(item)
            # The ring inside a polygon is part of that polygon, never an extra boundary.
            continue
        if tag in ('Point', 'NetworkLink', 'Model', 'Track'):skipped += 1
        stack.extend((child, folder, placemark, depth+1, in_polygon or tag == 'Polygon') for child in reversed(list(node)))
    if not boundaries:raise ValueError('KML-filen indeholder ingen polygoner eller lukkede grænselinjer. Markører og netværkslinks kan ikke bruges som grænse.')
    if not any('points' in b for b in boundaries):raise ValueError(boundaries[0]['name']+': '+boundaries[0]['error'])
    return {'format':'KML', 'boundaries':boundaries, 'skipped':skipped}


def _geojson(content, limit):
    try:geo = json.loads(content)
    except (ValueError, RecursionError):raise ValueError('Grænsefilen kunne ikke læses. Vælg en KML- eller GeoJSON-fil.') from None
    if not isinstance(geo, dict):raise ValueError('Brug en GeoJSON Polygon i WGS84.')
    crs = geo.get('crs')
    if crs and (not isinstance(crs, dict) or not isinstance(crs.get('properties'), dict) or crs['properties'].get('name') not in ('EPSG:4326','urn:ogc:def:crs:OGC:1.3:CRS84','urn:ogc:def:crs:EPSG::4326')):
        raise ValueError('Eksporter grænsen i WGS84 / EPSG:4326 først.')
    if geo.get('type') == 'FeatureCollection':
        features = geo.get('features')
        if not isinstance(features, list) or len(features) != 1:raise ValueError('GeoJSON-filen skal indeholde præcis én grænse.')
        geo = features[0]
    if not isinstance(geo, dict):raise ValueError('Brug en GeoJSON Feature med én Polygon.')
    properties = geo.get('properties') or {}
    name = str(properties.get('name') or 'Importeret grænse')[:200] if isinstance(properties, dict) else 'Importeret grænse'
    if geo.get('type') == 'Feature':geo = geo.get('geometry') or {}
    if not isinstance(geo, dict):raise ValueError('Grænsefilen mangler en Polygon-geometri.')
    rings = geo.get('coordinates')
    if geo.get('type') != 'Polygon' or not isinstance(rings, list) or len(rings) != 1:
        raise ValueError('Brug én Polygon uden huller. Flere distrikter importeres ikke som én grænse.')
    return {'format':'GeoJSON', 'boundaries':[{'index':0, 'name':name, 'points':_points(rings[0], limit)}], 'skipped':0}


def preview_boundary(content, scope='main'):
    if not isinstance(content, str) or len(content.encode('utf-8')) > MAX_BYTES:raise ValueError('Grænsefilen er for stor (maks. 2 MB).')
    if scope not in ('main', 'card'):raise ValueError('Vælg samlet grænse eller distriktskort.')
    content = content.lstrip('\ufeff \t\r\n')
    if not content:raise ValueError('Grænsefilen er tom.')
    limit = 5000
    result = _kml(content, limit) if content.startswith('<') else _geojson(content, limit)
    if len(result['boundaries']) == 1:result['points'] = result['boundaries'][0]['points']
    return dict(result, limit=limit)
