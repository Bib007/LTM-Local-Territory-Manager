"""Read-only preview and atomic approval of exact DAR matches across active cards.

Only already recorded IB entries with a unique, unlinked DAR address on their
own card are eligible. Ambiguities stay manual. No remote lookup is performed.
"""
from collections import Counter, defaultdict

from admin_store import signature
from ib_address_suggestions import preview, address_match
from ui_errors import UIError


def prepare(store):
    cards = sorted((c for c in store.all('cards') if not c.get('archived')),
                   key=lambda c: (str(c.get('number', '')).casefold(), c['id']))
    active_ids = {c['id'] for c in cards}
    ib = [row for row in store.all('ib') if row.get('card_id') in active_ids]
    by_card = defaultdict(list)
    for row in ib:
        by_card[row['card_id']].append(row)

    # A text duplicated on another card is not a safe automatic approval,
    # even when each card locally finds a candidate.
    text_counts = Counter((address_match(row), str(row.get('postcode') or ''))
                          for row in ib)
    already_linked = {row['address_id'] for row in store.all('ib')
                      if row.get('address_id')}
    candidate = {}
    fingerprints = []
    for card in cards:
        rows = by_card[card['id']]
        if not rows:
            continue
        per_card, changes = preview(store, card['id'])
        fingerprints.append((card['id'], per_card['expected']))
        for row in rows:
            if row.get('address_id') or row['id'] not in changes:
                continue
            address_id = changes[row['id']]
            if (text_counts[(address_match(row), str(row.get('postcode') or ''))] != 1
                    or address_id in already_linked):
                continue
            candidate[row['id']] = (card['id'], address_id)

    # Protect against unusual historical data with the same address appearing
    # on multiple cards. Leave every competing IB row for manual review.
    target_counts = Counter(target for _, target in candidate.values())
    safe = {ident: match for ident, match in candidate.items()
            if target_counts[match[1]] == 1}

    counts = Counter(card_id for card_id, _ in safe.values())
    summary = [
        {'card_id': card['id'], 'number': card['number'],
         'matches': counts[card['id']],
         'remaining': sum(not row.get('address_id') for row in by_card[card['id']])
                      - counts[card['id']]}
        for card in cards if any(not row.get('address_id')
                                  for row in by_card[card['id']])
    ]
    expected = signature([fingerprints, sorted((ident, *match)
                                               for ident, match in safe.items()),
                          [(row['card_id'], row['id'], row.get('address_id'))
                           for row in sorted(ib, key=lambda x: x['id'])]])
    result = {'matches': len(safe),
              'remaining': sum(row['remaining'] for row in summary),
              'cards': summary, 'expected': expected}
    return result, safe


def mutate(store, action, data):
    plan, safe = prepare(store)
    if action == 'ib.global.preview':
        return plan
    if (data.get('expected') != plan['expected']
            or type(data.get('count')) is not int
            or data['count'] != plan['matches']):
        raise UIError('IB-forslagene er ændret. Åbn forhåndsvisningen igen.')
    if data.get('confirm') != 'GODKEND SIKRE IB' or not safe:
        raise UIError('Bekræft antallet af sikre IB-adressematch først.')

    # Store.guarded_mutate owns a single transaction and profile review.
    # Any failed IB save rolls back the whole batch; no partial approvals.
    for ident, (card_id, address_id) in sorted(safe.items()):
        store._mutate('ib.save', {'id': ident, 'card_id': card_id,
                                  'address_id': address_id},
                      ib_address_only=True)
    return {'count': len(safe), 'remaining': plan['remaining'],
            'cards': sum(1 for row in plan['cards'] if row['matches'])}
