"""Connect complete DAR GraphQL results to existing transactional downloads."""
import math
import re
import time
from address_checkpoint import GRAPHQL_SOURCE, REST_SOURCE
from dar_adapter import DarAdapter
from dar_query import DarQuery
from dar_paging import IncompleteResult
from geography import utm32_to_wgs84
from postcode import SourceUnavailable, SourceTimeout, SourceLimit


def road_lines(roads):
    result = []
    for road in roads:
        geometry = road.get('vejnavnebeliggenhed_vejnavnelinje')
        if geometry is None:
            continue
        if (not isinstance(geometry, dict) or geometry.get('crs') != 25832 or
                geometry.get('dimension') not in ('XY', 'XYZ') or
                not isinstance(geometry.get('wkt'), str) or
                not re.match(r'^(MULTILINESTRING|LINESTRING)\s*(Z\s*)?\(', geometry['wkt'])):
            raise IncompleteResult('DAR-vejen havde ugyldig geometri. Hentningen er ikke gemt.')
        dimension = 2 if geometry['dimension'] == 'XY' else 3
        header = re.match(r'^(MULTILINESTRING|LINESTRING)\s*(Z\s*)?', geometry['wkt'])
        if header[2] and dimension != 3:
            raise IncompleteResult('DAR-vejens dimension og geometri stemte ikke overens.')
        body = geometry['wkt'][header.end():]
        part_pattern = r'\(\s*[^()]+\s*\)'
        pattern = part_pattern if header[1] == 'LINESTRING' else r'\(\s*' + part_pattern + r'(\s*,\s*' + part_pattern + r')*\s*\)'
        if not re.fullmatch(pattern, body):
            raise IncompleteResult('DAR-vejen havde et ukendt linjeformat.')
        parts = re.findall(r'\(([^()]+)\)', geometry['wkt'])
        if not parts:
            raise IncompleteResult('DAR-vejen manglede en gyldig vejlinje.')
        for index, part in enumerate(parts):
            points = []
            try:
                for text in part.split(','):
                    values = [float(v) for v in text.split()]
                    if len(values) != dimension or not all(math.isfinite(v) for v in values):
                        raise ValueError()
                    if not (100000 <= values[0] <= 1000000 and 5900000 <= values[1] <= 6500000):
                        raise ValueError()
                    points.append(utm32_to_wgs84(*values[:2]))
                if len(points) < 2:
                    raise ValueError()
            except (ValueError, OverflowError, ZeroDivisionError):
                raise IncompleteResult('DAR-vejen havde ugyldige koordinater.') from None
            result.append({'id': 'dar-road:' + road['id_lokalId'] + ':' + str(index),
                           'entity': 'road', 'name': road['vejnavn'], 'points': points, 'road_type': 'official'})
    return result


class DarDownload:
    def source_id(self):
        return GRAPHQL_SOURCE if self.address_source is not None and self.address_source.status()['configured'] else REST_SOURCE

    def source_schema(self):
        return self.address_source.status().get('schema_sha256') if self.address_source is not None else None

    def graph_adapter(self, snapshot=None, schema_sha256=None):
        expected_schema = schema_sha256 if schema_sha256 is not None else self.source_schema()
        def request(query):
            self.check_cancel()
            if expected_schema != self.source_schema():
                raise SourceUnavailable('Datafordelerens skema er ændret under hentningen. Start en ny opdatering; lokale adresser er bevaret.')
            with self.lock:
                job = self.active
                if job:
                    self.jobs[job].update(request_started=time.monotonic(), request_label='Datafordeleren GraphQL', request_timeout=20)
            try:
                result = self.address_source.query(query)
                if expected_schema != self.source_schema():
                    raise SourceUnavailable('Datafordelerens skema er ændret under hentningen. Start en ny opdatering; lokale adresser er bevaret.')
            except (SourceTimeout,SourceLimit):
                raise
            except ValueError as error:
                # Datafordeler.query has already removed provider text and keys.
                raise SourceUnavailable(str(error)) from None
            finally:
                with self.lock:
                    if job:
                        for field in ('request_started', 'request_label', 'request_timeout'):
                            self.jobs[job].pop(field, None)
            self.check_cancel()
            return result
        return DarAdapter(DarQuery(request, snapshot=snapshot, check_cancel=self.check_cancel))

    def graph_discover_postcode(self, post, progress):
        self.check_cancel()
        progress(message='Finder postnummer og den officielle vejliste via DAR GraphQL…', completed=0, total=0)
        result = self.graph_adapter().discover_postcode(post)
        if not result['roads']:
            raise ValueError('Ingen gældende veje fundet i postnummeret.')
        groups = {}
        for road in result['roads']:
            groups.setdefault(road['vejnavn'], []).append(road['id_lokalId'])
        manifest = {'id': 'postcode:' + post, 'entity': 'postcode_download', 'postcode': post, 'name': result['name'],
                    'snapshot': result['snapshot'], 'source': 'DAR / Datafordeleren', 'source_id': GRAPHQL_SOURCE,
                    'schema_sha256': self.source_schema(),
                    'status': 'running', 'roads': [{'id': identities[0], 'ids': identities, 'road': name, 'status': 'pending', 'count': 0}
                                                  for name, identities in groups.items()]}
        lines = road_lines(result['roads'])
        self.check_cancel()
        self.store.mutate('geo.postcode.save', {'manifest': manifest, 'lines': lines})
        return manifest
