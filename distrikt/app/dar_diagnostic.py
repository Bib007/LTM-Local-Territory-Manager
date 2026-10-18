"""Read-only, fictional-scope DAR probes. Never return provider text or rows."""
import json
import re
import time
from dar_query import DarQuery
from address_source import reject_graphql
from dar_paging import collect_pages, IncompleteResult

SENTINEL = '00000000-0000-4000-8000-000000000000'
# Fixed vocabulary, not a redaction of arbitrary provider text. Unknown words,
# paths, extension values, IDs and response data never reach the report.
WORDS = frozenset(('alias', 'aliases', 'root', 'multiple', 'single', 'filter',
                   'filters', 'argument', 'arguments', 'field', 'fields',
                   'allowed', 'supported', 'invalid', 'maximum', 'size', 'limit',
                   'complexity', 'cost', 'syntax', 'validation', 'unauthorized',
                   'authenticated', 'authorization', 'timeout'))


def describe_errors(result, query):
    """Only app-owned categories plus whitelisted codes and diagnostic words."""
    try:
        reject_graphql(result, query)
    except ValueError as error:
        match = re.search(r'\((GQL-[A-Z]+)(?: ·|\))', str(error))
        category = match[1] if match else 'GQL-RESULT'
    errors = result.get('errors') if isinstance(result, dict) else None
    errors = errors if isinstance(errors, list) else []
    codes, words = set(), set()
    for error in errors:
        if not isinstance(error, dict):
            continue
        ext = error.get('extensions')
        code = ext.get('code') if isinstance(ext, dict) else None
        if isinstance(code, str) and re.fullmatch(r'HC\d{4}', code):
            codes.add(code)
        message = error.get('message')
        if isinstance(message, str):
            words.update(set(re.findall(r'[a-z]+', message.casefold())) & WORDS)
    return {'status': category, 'codes': sorted(codes)[:8],
            'terms': sorted(words), 'error_count': min(len(errors), 100)}


def probes(snapshot=None):
    """Contrast identical projections and filters with/without aliases.

    One fixed synthetic ID/name, first=1, no user's road or district polygon.
    Queries do not enumerate or return any address records in the report.
    """
    query = DarQuery(None, snapshot=snapshot, page_size=1)
    for entity, field in (('DAR_Postnummer', 'id_lokalId'),
                          ('DAR_NavngivenVej', 'vejnavn'),
                          ('DAR_Husnummer', 'adgangspunkt'),
                          ('DAR_Adresse', 'husnummer'),
                          ('DAR_Adressepunkt', 'id_lokalId')):
        value = 'LTM_FIKTIV_KONTRAKTPROEVE_00000000' if field == 'vejnavn' else SENTINEL
        arguments = query._arguments(entity, {field: value})
        for variant in ('plain', 'alias', 'batch'):
            selections = [query._selection(entity, arguments,
                          alias=None if variant == 'plain' else 'scope_' + str(i))
                          for i in range(10 if variant == 'batch' else 1)]
            yield entity, variant, 'query { ' + ' '.join(selections) + ' }'


def diagnose(source, snapshot=None):
    """Use the installed transport without connect(), writes or import jobs."""
    # _auth is read in-process. The key is used only by the existing transport,
    # never returned, echoed, written, or included in an exception report.
    with source.lock:
        key = source._auth().get('api_key')
    if not key:
        return {'status': 'NOT-CONFIGURED', 'probes': []}
    report = []
    deadline = time.monotonic() + 40
    for entity, variant, query in probes(snapshot):
        row = {'entity': entity, 'variant': variant}
        if time.monotonic() >= deadline:
            row['status'] = 'NOT-TESTED'
            report.append(row)
            continue
        try:
            raw = source._request(key, query=query, return_graphql_errors=True)
            result = json.loads(raw)
            if (not isinstance(result, dict) or result.get('errors') or
                    not isinstance(result.get('data'), dict)):
                row.update(describe_errors(result, query))
            else:
                expected = [entity] if variant == 'plain' else [
                    'scope_' + str(i) for i in range(10 if variant == 'batch' else 1)]
                try:
                    for name in expected:
                        envelope = {'data': {entity: result['data'].get(name)}}
                        collect_pages(lambda _: envelope, entity, max_pages=1, max_nodes=1)
                    row['status'] = 'ACCEPTED'
                except IncompleteResult:
                    row['status'] = 'GQL-RESULT'
        except Exception:
            # Transport failures can contain URLs/keys even in exception repr.
            row['status'] = 'TRANSPORT-FAILED'
            deadline = 0
        report.append(row)
    return {'status': 'COMPLETE', 'probes': report}
