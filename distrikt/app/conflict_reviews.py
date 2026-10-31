"""Unconnected prototype for reviewing locally stored edit conflicts.

The caller must authenticate and check access to each module before using
either function. Conflict values may contain private information.
"""
from copy import deepcopy
from datetime import datetime, timezone


def pending(store, allowed_modules):
    """Return only unresolved notices from explicitly authorized modules."""
    if not isinstance(allowed_modules, (set, frozenset)):
        raise ValueError('Explicit module permissions required')
    with store.lock:
        return [deepcopy(row) for row in store.all('settings')
                if row.get('entity') == 'edit-conflict'
                and not row.get('resolved') and row.get('module') in allowed_modules]


def acknowledge(store, ident, allowed_modules, actor_id):
    """Mark a specific notice reviewed atomically; do not change its record."""
    if not isinstance(allowed_modules, (set, frozenset)) or not isinstance(actor_id, str) or not actor_id:
        raise ValueError('Explicit module permissions and actor required')
    with store.transaction():
        row = store.get('settings', ident)
        if not row or row.get('entity') != 'edit-conflict' or row.get('module') not in allowed_modules:
            raise ValueError('Review unavailable')
        if row.get('resolved'):
            return False
        row['resolved'] = True
        row['reviewed_by'] = actor_id
        row['reviewed_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        store.put('settings', row)
        return True
