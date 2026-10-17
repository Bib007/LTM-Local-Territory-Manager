"""Flat DAR v3 queries from documented fields; no database or credentials here.

Not connected to Downloads yet. A DarQuery instance pins the same registration
and effect instant across entities and pages. The local schema and a real public
test area must still be verified before activating the import adapter.
"""
import json
from datetime import datetime, timezone
from dar_paging import collect_pages, IncompleteResult

# Explicit projections avoid relying on the provider's incomplete join relations.
FIELDS = {
    'DAR_Adresse': 'id_lokalId status adressebetegnelse etagebetegnelse doerbetegnelse husnummer',
    'DAR_Husnummer': 'id_lokalId status husnummertekst navngivenVej postnummer adgangspunkt',
    'DAR_Adressepunkt': 'id_lokalId status position { crs dimension wkt }',
    'DAR_NavngivenVej': 'id_lokalId status vejnavn vejnavnebeliggenhed_vejnavnelinje { crs dimension wkt }',
    'DAR_Postnummer': 'id_lokalId status postnr navn',
}
FILTERS = {
    'DAR_Adresse': ('id_lokalId', 'husnummer'),
    'DAR_Husnummer': ('id_lokalId', 'navngivenVej', 'postnummer'),
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
    def __init__(self, request, *, snapshot=None, page_size=100, check_cancel=lambda: None):
        if type(page_size) is not int or not 1 <= page_size <= 1000:
            raise ValueError('DAR-sidestørrelsen skal være mellem 1 og 1000.')
        self.request = request
        self.snapshot = snapshot_time(snapshot)
        self.page_size = page_size
        self.check_cancel = check_cancel

    def _arguments(self, entity, filters):
        """Fetch a bounded scope. Only documented scalar equality filters allowed.

        Values are JSON string literals (valid GraphQL string literals), never
        interpolated query fragments. No unfiltered nationwide fetch is allowed.
        """
        if entity not in FIELDS or not isinstance(filters, dict) or not filters:
            raise ValueError('Vælg en afgrænset DAR-forespørgsel.')
        clauses = ['status: { eq: "3" }']
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

    def collect(self, entity, filters, *, max_pages=2000, max_nodes=200000):
        """Collect one complete equality-filtered scope before returning any rows."""
        arguments = self._arguments(entity, filters)

        def fetch(after):
            query = 'query { ' + self._selection(entity, arguments, after) + ' }'
            envelope = self.request(query)
            # A broken/changed filter must fail, not silently retire local data.
            data = envelope.get('data') if isinstance(envelope, dict) else None
            connection = data.get(entity) if isinstance(data, dict) else None
            if isinstance(connection, dict) and isinstance(connection.get('nodes'), list):
                for row in connection['nodes']:
                    if (not isinstance(row, dict) or row.get('status') != '3' or
                            any(row.get(field) != value for field, value in filters_copy.items())):
                        raise IncompleteResult('DAR-svaret stemte ikke med det afgrænsede opslag.')
            return envelope

        filters_copy = dict(filters)
        return collect_pages(fetch, entity, check_cancel=self.check_cancel,
                             max_pages=max_pages, max_nodes=max_nodes)

    def collect_many(self, entity, field, values, *, require_all=False,
                     batch_size=10, max_requests=2000, max_nodes=200000):
        """Batch first pages with aliases; retain complete independent pagination.

        Uses only the existing scalar equality filters, avoiding assumptions about
        provider-specific IN filters. One alias has its own cursor and scope. Most
        ID lookups finish on their first page, reducing transport round trips.
        Any missing alias, partial error or missing required ID fails the whole call.
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
                raise IncompleteResult('DAR-opslaget kræver for mange anmodninger. Vælg et mindre område.')
            requests_left -= 1
            result = self.request(query)
            self.check_cancel()
            return result

        for start in range(0, len(scopes), batch_size):
            batch = scopes[start:start + batch_size]
            selections = [self._selection(entity, arguments, alias='scope_' + str(i))
                          for i, (_, arguments) in enumerate(batch)]
            envelope = request('query { ' + ' '.join(selections) + ' }')
            data = envelope.get('data') if isinstance(envelope, dict) else None
            if (not isinstance(data, dict) or envelope.get('errors') or
                    any('scope_' + str(i) not in data for i in range(len(batch)))):
                raise IncompleteResult('Datafordelerens masseopslag kunne ikke hentes fuldstændigt.')
            for i, (value, _) in enumerate(batch):
                initial = {'data': {entity: data['scope_' + str(i)]}}
                first = True

                def fetch(query):
                    nonlocal first
                    if first:
                        first = False
                        return initial
                    return request(query)

                worker = DarQuery(fetch, snapshot=self.snapshot, page_size=self.page_size,
                                  check_cancel=self.check_cancel)
                # collect_pages validates every alias's first and subsequent pages.
                found = worker.collect(entity, {field: value}, max_nodes=max_nodes,
                                       max_pages=max_requests + 1)
                if require_all and len(found) != 1:
                    raise IncompleteResult('Et nødvendigt DAR-ID manglede. Ingen adresser er klar til import.')
                if len(rows) + len(found) > max_nodes:
                    raise IncompleteResult('DAR-opslaget indeholdt for mange resultater.')
                for node in found:
                    if node['id_lokalId'] in identities:
                        raise IncompleteResult('Datafordeleren gentog et ID på tværs af opslag.')
                    identities.add(node['id_lokalId'])
                rows.extend(found)
        self.check_cancel()
        return rows
