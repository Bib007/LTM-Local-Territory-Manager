"""Flat DAR v3 queries from documented fields; no database or credentials here.

Used by Downloads. A DarQuery instance pins the same registration
and effect instant across entities and pages. The local schema and a real public
test area are verified separately in the owner’s local installation.
"""
import json
import math
from datetime import datetime, timezone
from dar_paging import collect_pages, IncompleteResult, IncompleteLimit
from dar_join import point_coordinates
from postcode import SourceLimit

# Explicit projections avoid relying on the provider's incomplete join relations.
FIELDS = {
    'DAR_Adresse': 'id_lokalId status adressebetegnelse etagebetegnelse doerbetegnelse husnummer',
    'DAR_Husnummer': 'id_lokalId status husnummertekst navngivenVej postnummer adgangspunkt',
    'DAR_Adressepunkt': 'id_lokalId position { crs dimension wkt }',
    'DAR_NavngivenVej': 'id_lokalId status vejnavn vejnavnebeliggenhed_vejnavnelinje { crs dimension wkt }',
    'DAR_Postnummer': 'id_lokalId status postnr navn',
}
FILTERS = {
    'DAR_Adresse': ('id_lokalId', 'husnummer'),
    'DAR_Husnummer': ('id_lokalId', 'navngivenVej', 'postnummer', 'adgangspunkt'),
    'DAR_Adressepunkt': ('id_lokalId',),
    'DAR_NavngivenVej': ('id_lokalId', 'vejnavn'),
    'DAR_Postnummer': ('id_lokalId', 'postnr'),
}


def snapshot_time(value=None):
    if value is None:
        value = datetime.now(timezone.utc)
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('Ugyldigt DAR-tidspunkt.') from None
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('DAR-tidspunktet skal have tidszone.')
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


class DarQuery:
    def __init__(self, request, *, snapshot=None, page_size=100, check_cancel=lambda: None, on_page=lambda entity, nodes: None):
        if type(page_size) is not int or not 1 <= page_size <= 1000:
            raise ValueError('DAR-sidestørrelsen skal være mellem 1 og 1000.')
        self.request = request
        self.snapshot = snapshot_time(snapshot)
        self.page_size = page_size
        self.check_cancel = check_cancel
        self.on_page = on_page

    def _arguments(self, entity, filters):
        """Fetch a bounded scope. Only documented scalar equality filters allowed.

        Values are JSON string literals (valid GraphQL string literals), never
        interpolated query fragments. No unfiltered nationwide fetch is allowed.
        """
        if entity not in FIELDS or not isinstance(filters, dict) or not filters:
            raise ValueError('Vælg en afgrænset DAR-forespørgsel.')
        # Points have their own lifecycle (8 = in use), and point status is not
        # consistently exposed by services. Current parent addresses/houses are
        # checked separately; point versions remain pinned to the same snapshot.
        clauses = [] if entity=='DAR_Adressepunkt' else ['status: { eq: "3" }']
        for field, value in sorted(filters.items()):
            if field not in FILTERS[entity] or not isinstance(value, str) or not value.strip() or len(value) > 1000:
                raise ValueError('Ugyldigt DAR-opslagsfelt eller værdi.')
            clauses.append(field + ': { eq: ' + json.dumps(value, ensure_ascii=True) + ' }')
        # Freeze filters before paging; a caller mutating its dict cannot change scope.
        return ('where: { ' + ', '.join(clauses) + ' }, '
                     'virkningstid: ' + json.dumps(self.snapshot) + ', '
                     'registreringstid: ' + json.dumps(self.snapshot) + ', '
                'first: ' + str(self.page_size))

    @staticmethod
    def _selection(entity, arguments, after=None, alias=None):
        cursor = '' if after is None else ', after: ' + json.dumps(after, ensure_ascii=True)
        return ((alias + ': ' if alias else '') + entity + '(' + arguments + cursor + ') { nodes { '
                + FIELDS[entity] + ' } pageInfo { hasNextPage endCursor } }')

    def _page(self,entity,arguments,after,size):
        prefix,separator,_=arguments.rpartition('first: ')
        if not separator:raise ValueError('Ugyldig DAR-sideafgrænsning.')
        while True:
            self.check_cancel()
            self.on_page(entity, [])
            try:return self.request('query { '+self._selection(entity,prefix+'first: '+str(size),after)+' }'),size
            except SourceLimit:
                if size==1:raise
                size=max(1,size//5)

    def collect(self, entity, filters, *, max_pages=2000, max_nodes=200000):
        """Collect one complete equality-filtered scope before returning any rows."""
        arguments = self._arguments(entity, filters)
        size=self.page_size

        def fetch(after):
            nonlocal size
            envelope,size=self._page(entity,arguments,after,size)
            # A broken/changed filter must fail, not silently retire local data.
            data = envelope.get('data') if isinstance(envelope, dict) else None
            connection = data.get(entity) if isinstance(data, dict) else None
            if isinstance(connection, dict) and isinstance(connection.get('nodes'), list):
                for row in connection['nodes']:
                    if (not isinstance(row, dict) or (entity!='DAR_Adressepunkt' and row.get('status') != '3') or
                            any(row.get(field) != value for field, value in filters_copy.items())):
                        raise IncompleteResult('DAR-svaret stemte ikke med det afgrænsede opslag.')
                    if entity=='DAR_Adressepunkt':point_coordinates(row)
            return envelope

        filters_copy = dict(filters)
        return collect_pages(fetch, entity, check_cancel=self.check_cancel,
                             max_pages=max_pages, max_nodes=max_nodes, on_page=lambda nodes: self.on_page(entity, nodes))

    def collect_bbox(self, bounds, *, max_pages=2000, max_nodes=200000):
        """Complete points within a <=9 km² UTM32 tile; no local polygon upload.

        The documented spatial operator is within. Expand the query rectangle by
        one centimetre so boundary points aren't lost to strict within semantics,
        then filter to the original inclusive rectangle locally.
        """
        if (not isinstance(bounds, (list, tuple)) or len(bounds) != 4 or
                any(type(v) not in (int, float) or not math.isfinite(v) for v in bounds)):
            raise ValueError('Ugyldigt DAR-udsnit.')
        w, s, e, n = bounds
        if not (100000 <= w < e <= 1000000 and 5900000 <= s < n <= 6500000) or (e-w)*(n-s) > 9000000:
            raise ValueError('Vælg et DAR-udsnit på højst 9 km² i UTM32.')
        pw, ps, pe, pn = w-.01, s-.01, e+.01, n+.01
        ring = [(pw, ps), (pe, ps), (pe, pn), (pw, pn), (pw, ps)]
        wkt = 'POLYGON ((' + ', '.join(format(x, '.9f') + ' ' + format(y, '.9f') for x, y in ring) + '))'
        arguments = ('where: { position: { within: { wkt: '
                     + json.dumps(wkt) + ', crs: 25832 } } }, virkningstid: '
                     + json.dumps(self.snapshot) + ', registreringstid: ' + json.dumps(self.snapshot)
                     + ', first: ' + str(self.page_size))
        size=self.page_size

        def fetch(after):
            nonlocal size
            result,size=self._page('DAR_Adressepunkt',arguments,after,size)
            data = result.get('data') if isinstance(result, dict) else None
            connection = data.get('DAR_Adressepunkt') if isinstance(data, dict) else None
            if isinstance(connection, dict) and isinstance(connection.get('nodes'), list):
                for node in connection['nodes']:
                    if not isinstance(node, dict):
                        raise IncompleteResult('DAR-udsnittet indeholdt en ugyldig punktstatus.')
                    x, y = point_coordinates(node)
                    if not (pw <= x <= pe and ps <= y <= pn):
                        raise IncompleteResult('DAR-svaret stemte ikke med det geografiske udsnit.')
            return result

        points = collect_pages(fetch, 'DAR_Adressepunkt', check_cancel=self.check_cancel,
                               max_pages=max_pages, max_nodes=max_nodes, on_page=lambda nodes: self.on_page('DAR_Adressepunkt', nodes))
        return [row for row in points if w <= point_coordinates(row)[0] <= e and s <= point_coordinates(row)[1] <= n]

    def collect_many(self, entity, field, values, *, require_all=False,
                     batch_size=10, max_requests=2000, max_nodes=200000):
        """Collect complete scopes through one unaliased root per request.

        DAR rejects even a single root alias. Keep each scope's filters, cursor
        and snapshot unchanged and share the request/node budgets across them.
        batch_size is retained for call compatibility; it never combines roots.
        No rows escape if any scope, required ID or later page fails.
        """
        if (entity not in FILTERS or field not in FILTERS[entity] or
                type(batch_size) is not int or not 1 <= batch_size <= 10 or
                type(max_requests) is not int or max_requests < 1 or
                type(max_nodes) is not int or max_nodes < 1 or
                not isinstance(values, (list, tuple)) or len(values) > 200000 or
                (require_all and field != 'id_lokalId')):
            raise ValueError('Ugyldigt afgrænset DAR-masseopslag.')
        # Copy and validate all scopes before any network access.
        scopes = []
        seen_values = set()
        for value in values:
            arguments = self._arguments(entity, {field: value})
            if value not in seen_values:
                scopes.append((value, arguments))
                seen_values.add(value)
        rows, identities = [], set()
        requests_left = max_requests

        def request(query):
            nonlocal requests_left
            self.check_cancel()
            if requests_left <= 0:
                raise IncompleteLimit('DAR-opslaget kræver for mange anmodninger. Vælg et mindre område.')
            requests_left -= 1
            result = self.request(query)
            self.check_cancel()
            return result

        worker = DarQuery(request, snapshot=self.snapshot, page_size=self.page_size,
                          check_cancel=self.check_cancel, on_page=self.on_page)
        for value, _ in scopes:
            found = worker.collect(entity, {field: value}, max_nodes=max_nodes,
                                   max_pages=max_requests + 1)
            if require_all and len(found) != 1:
                raise IncompleteResult('Et nødvendigt DAR-ID manglede. Ingen adresser er klar til import.')
            if len(rows) + len(found) > max_nodes:
                raise IncompleteLimit('DAR-opslaget indeholdt for mange resultater.')
            for node in found:
                if node['id_lokalId'] in identities:
                    raise IncompleteResult('Datafordeleren gentog et ID på tværs af opslag.')
                identities.add(node['id_lokalId'])
            rows.extend(found)
        self.check_cancel()
        return rows
