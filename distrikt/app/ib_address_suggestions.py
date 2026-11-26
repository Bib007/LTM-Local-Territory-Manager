"""Review and apply precise, local DAR suggestions for one card's IB entries."""
import re
import unicodedata
from collections import Counter, defaultdict

from admin_store import signature
from card_import import norm
from ui_errors import UIError


DAR_SOURCES = {'DAR / Adressevælger', 'DAR / Datafordeleren'}


def card_addresses(store, card):
    return card.get('geo_addresses') or card.get('imported_addresses') or [
        store.get('geo', ident) for ident in card.get('address_ids', [])
    ]


def address_fields(address):
    unit = ' '.join(str(address[key]) for key in ('floor', 'door') if address.get(key))
    return {'road': address['road'], 'number': address['number'] + (', ' + unit if unit else ''),
            'postcode': str(address.get('postcode') or '')}


def address_match(address):
    number = address['number'].casefold().strip()
    house = re.match(r'^(\d+)(\s*[a-zæøå])?(?=[\s,.]|$)', number)
    unit = re.sub(r'[\s.,]+', ' ', number[house.end():]).strip() if house else ''
    return (norm(unicodedata.normalize('NFC', address['road'])),
            (house[1], (house[2] or '').strip(), unit) if house else (number, '', ''))


def label(address):
    return ' '.join([address['road'], address['number']]) + (
        ' · ' + address['postcode'] if address.get('postcode') else ''
    )


def preview(store, card_id):
    card = store.require('cards', card_id)
    if card.get('archived'):
        raise UIError('Vælg et aktivt kort.')
    items = sorted((item for item in store.all('ib') if item['card_id'] == card_id),
                   key=lambda item: (norm(item['road']), item['number'], item['id']))
    ignored = {item['address_id'] for item in store.all('ignored')}
    owners = defaultdict(set)
    text_owners = defaultdict(set)
    for item in items:
        if item.get('address_id'):
            owners[item['address_id']].add(item['id'])
        text_owners[item['road'].casefold(), item['number'].casefold()].add(item['id'])

    details, by_unit = {}, defaultdict(list)
    for address in card_addresses(store, card):
        if not address:
            continue
        ident = address['id']
        current = store.get('geo', ident)
        if not current or current.get('entity') != 'address':
            continue
        fields = address_fields(address)
        if (current.get('source') not in DAR_SOURCES or current.get('retired')
                or address.get('retired') or ident in ignored or address_fields(current) != fields):
            continue
        details[ident] = fields
        by_unit[address_match(fields)].append(ident)

    candidates = []
    ambiguous = set()
    for item in items:
        linked = item.get('address_id')
        matches = ([linked] if linked in details else []) if linked else [
            ident for ident in by_unit[address_match(item)]
            if not item.get('postcode') or item['postcode'] == details[ident]['postcode']
        ]
        ident = matches[0] if len(matches) == 1 else None
        if ident:
            fields = details[ident]
            peers = text_owners[fields['road'].casefold(), fields['number'].casefold()]
            if (owners[ident] | peers) - {item['id']}:
                ambiguous.add(ident)
        candidates.append(ident)

    counts = Counter(candidates)
    rows, changes = [], {}
    for item, ident in zip(items, candidates):
        fields = details.get(ident) if counts[ident] == 1 and ident not in ambiguous else None
        eligible = fields and (item.get('address_id') != ident
                               or any((item.get(key) or '') != value for key, value in fields.items()))
        if eligible:
            changes[item['id']] = ident
        rows.append({'id': item['id'], 'before': label(item), 'after': label(fields) if fields else '',
                     'selectable': bool(eligible)})
    return {'rows': rows, 'expected': signature([card_id, items, rows, changes])}, changes


def mutate(store, action, data):
    card_id = data.get('card_id')
    plan, changes = preview(store, card_id)
    if action == 'ib.bulk.preview':
        return plan
    if data.get('expected') != plan['expected']:
        raise UIError('Adresseforslagene er ændret. Åbn listen igen.')
    selected = data.get('selected')
    if (not isinstance(selected, list) or not selected or len(selected) > len(changes)
            or any(not isinstance(ident, str) or ident not in changes for ident in selected)
            or len(set(selected)) != len(selected)):
        raise UIError('Markér mindst ét gyldigt DAR-forslag.')
    for ident in selected:
        store._mutate('ib.save', {'id': ident, 'card_id': card_id, 'address_id': changes[ident]},
                      ib_address_only=True)
    return {'count': len(selected)}
