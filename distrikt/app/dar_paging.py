"""Collect one complete GraphQL entity result before allowing a local import.

The caller supplies fetch_page(after), retaining the same entity, fields, filters
and fixed registration/effect timestamp for every request. It returns a decoded
GraphQL envelope and sanitizes transport errors. No credentials or queries live
here. Downloads uses this building block through the DAR query adapter.
"""


class IncompleteResult(ValueError):
    """No result may be imported when paging cannot be verified."""


class IncompleteLimit(IncompleteResult):
    """A bounded scope can be retried as smaller geographic tiles."""


def collect_pages(fetch_page, entity, *, check_cancel=lambda: None,
                  max_pages=2000, max_nodes=200000, id_field='id_lokalId', on_page=lambda nodes: None):
    """Return importable nodes only after a valid terminal page.

    check_cancel raises the download's cancellation exception. Bounds deliberately
    fail rather than truncate; the caller must split an oversized query.
    on_page observes validated receipts for progress only, never an import.
    """
    if (type(max_pages) is not int or max_pages < 1 or
            type(max_nodes) is not int or max_nodes < 1):
        raise ValueError('Side- og resultatgrænser skal være positive heltal.')
    result, identities, cursors = [], set(), set()
    after = None
    for _ in range(max_pages):
        check_cancel()
        envelope = fetch_page(after)
        check_cancel()
        if not isinstance(envelope, dict) or envelope.get('errors'):
            # Upstream messages may contain URLs, credentials or request details.
            raise IncompleteResult('Datafordelerens svar kunne ikke hentes fuldstændigt.')
        data = envelope.get('data')
        connection = data.get(entity) if isinstance(data, dict) else None
        if not isinstance(connection, dict):
            raise IncompleteResult('Datafordeleren manglede det forventede resultat.')
        nodes, info = connection.get('nodes'), connection.get('pageInfo')
        if (not isinstance(nodes, list) or not isinstance(info, dict) or
                type(info.get('hasNextPage')) is not bool):
            raise IncompleteResult('Datafordeleren manglede gyldige sideoplysninger.')
        more, cursor = info['hasNextPage'], info.get('endCursor')
        # Nonempty pages have a last node, hence require its cursor even at EOF.
        if nodes and (not isinstance(cursor, str) or not cursor.strip()):
            raise IncompleteResult('Datafordeleren manglede en gyldig sidecursor.')
        if more and (not nodes or not isinstance(cursor, str) or not cursor.strip()):
            raise IncompleteResult('Datafordeleren angav en ufuldstændig næste side.')
        if cursor is not None and (not isinstance(cursor, str) or not cursor.strip()):
            raise IncompleteResult('Datafordeleren returnerede en ugyldig sidecursor.')
        if cursor is not None and cursor in cursors:
            raise IncompleteResult('Datafordeleren gentog en sidecursor. Hentningen er afbrudt.')
        if len(result) + len(nodes) > max_nodes:
            raise IncompleteLimit('Adresseopslaget er for stort. Hent et mindre område.')
        for node in nodes:
            identity = node.get(id_field) if isinstance(node, dict) else None
            if not isinstance(identity, str) or not identity.strip():
                raise IncompleteResult('Datafordeleren returnerede et resultat uden gyldigt ID.')
            # A fixed point-in-time query must return each entity once. Silently
            # deduplicating could hide an unstable or repeated upstream page.
            if identity in identities:
                raise IncompleteResult('Datafordeleren gentog et ID. Hentningen er afbrudt.')
            identities.add(identity)
        result.extend(nodes)
        on_page(nodes)
        if not more:
            return result
        cursors.add(cursor)
        after = cursor
    raise IncompleteLimit('Adresseopslaget har for mange sider. Hent et mindre område.')
