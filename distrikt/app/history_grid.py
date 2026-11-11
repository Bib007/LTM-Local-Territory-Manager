"""Safe, additive edits for the quick assignment-history grid.

No migration: use the existing loans/completions/card records. Every write is
performed inside Store.guarded_mutate's SQLite transaction and audit trail.
"""
from datetime import date
from history_loans import overlaps


def _day(value, required=True):
    from store import valid_day
    if value in (None, '') and not required:
        return None
    return valid_day(value)


def _check_revision(store, data):
    if not isinstance(data.get('revision'), str) or data['revision'] != store.revision:
        raise ValueError('Historikken er ændret i et andet vindue. Opdater før du gemmer.')


def _check_interval(store, card_id, assigned, returned, exclude=None):
    proposed = {'assigned': assigned, 'returned': returned}
    for other in store.all('loans'):
        if other['card_id'] != card_id or other['id'] == exclude:
            continue
        if overlaps(proposed, other):
            raise ValueError('Datoerne overlapper en anden udlevering. Ingen ændringer er gemt.')
    for old in store.all('loans', deleted=True):
        if old['card_id'] == card_id and overlaps(proposed, old):
            raise ValueError('En tidligere udlevering findes i Gendan ved fejl. Afklar den først.')


def _known_dates(store, card_id):
    return [e for e in store.all('completions') if e['card_id'] == card_id]


def mutate_grid(store, action, data):
    from store import new_id
    _check_revision(store, data)
    if action == 'history.grid.add':
        card = store.require('cards', data.get('card_id'))
        publisher = store.require('publishers', data.get('publisher_id'))
        assigned = _day(data.get('assigned'))
        returned = _day(data.get('returned'), False)
        completed = data.get('completed') is True
        if returned and returned < assigned:
            raise ValueError('Indlevering kan ikke være før udlevering.')
        if card.get('archived') and not returned:
            raise ValueError('Et arkiveret kort kan ikke have et aktivt udlån.')
        if completed and not returned:
            raise ValueError('Vælg indleveringsdato før du markerer kortet gennemgået.')
        _check_interval(store, card['id'], assigned, returned)
        matches = [l for l in store.all('loans') if l['card_id'] == card['id']
                   and l.get('publisher_id') == publisher['id'] and l['assigned'] == assigned
                   and l.get('returned') == returned]
        if matches:
            raise ValueError('Udleveringen er allerede registreret.')
        events = [e for e in _known_dates(store, card['id']) if returned and e['date'] == returned]
        if len(events) > 1 or events and events[0].get('loan_id'):
            raise ValueError('Der er allerede en anden gennemgang på indleveringsdatoen.')
        if completed and any(e['card_id'] == card['id'] and e['date'] == returned
                             for e in store.all('completions', deleted=True)):
            raise ValueError('Gennemgangen findes i Gendan ved fejl.')
        loan = {'id': new_id(), 'card_id': card['id'], 'publisher_id': publisher['id'],
                'assigned': assigned, 'cycle_start': assigned, 'returned': returned,
                'initial': True, 'source': 'history-grid'}
        store.put('loans', loan)
        if not returned:
            store.put('cards', dict(card, in_folder=False))
        if completed:
            if events:
                store.put('completions', dict(events[0], loan_id=loan['id'], assigned=assigned))
            else:
                previous = max((d for e in _known_dates(store, card['id'])
                                for d in (e.get('date'), e.get('previous_completed'))
                                if d and d < returned), default=None)
                store.put('completions', {'id': new_id(), 'card_id': card['id'],
                    'date': returned, 'loan_id': loan['id'], 'assigned': assigned,
                    'previous_completed': previous, 'visits': 0,
                    'visits_unknown': True, 'source': 'history-grid'})
            if not card.get('last_completed') or returned > card['last_completed']:
                store.put('cards', dict(store.require('cards', card['id']), last_completed=returned))
        return {'id': loan['id']}
    if action == 'history.grid.edit':
        loan = store.require('loans', data.get('id'))
        card = store.require('cards', loan['card_id'])
        field = data.get('field')
        if field not in ('assigned', 'returned'):
            raise ValueError('Kun udleverings- og indleveringsdato kan rettes her.')
        stamp = _day(data.get('date'), field == 'assigned')
        previous = loan.get(field)
        if stamp == previous:
            return {'id': loan['id'], 'unchanged': True}
        assigned = stamp if field == 'assigned' else loan['assigned']
        returned = stamp if field == 'returned' else loan.get('returned')
        if returned and returned < assigned:
            raise ValueError('Indlevering kan ikke være før udlevering.')
        if card.get('archived') and not returned:
            raise ValueError('Et arkiveret kort kan ikke stå som udleveret.')
        if loan.get('cycle_start') and field == 'assigned' and loan['cycle_start'] != loan['assigned'] and stamp > loan['cycle_start']:
            raise ValueError('Datoen ligger efter næste gennemgang i samme udlån.')
        events = sorted([e for e in _known_dates(store, loan['card_id'])
                         if e.get('loan_id') == loan['id']], key=lambda e: e['date'])
        if events and assigned > events[0]['date']:
            raise ValueError('Udleveringen kan ikke være efter første gennemgang.')
        if returned and events and returned < events[-1]['date'] and not (
                field == 'returned' and previous and events[-1]['date'] == previous):
            raise ValueError('Indleveringen kan ikke være før seneste gennemgang.')
        _check_interval(store, loan['card_id'], assigned, returned, exclude=loan['id'])
        changed = dict(loan)
        changed[field] = stamp
        if field == 'assigned':
            if loan.get('cycle_start', previous) == previous:
                changed['cycle_start'] = stamp
            if events and events[0].get('assigned') == previous:
                store.put('completions', dict(events[0], assigned=stamp))
        else:
            linked = [e for e in events if e['date'] == previous] if previous else []
            if len(linked) > 1:
                raise ValueError('Flere sammenknyttede gennemgange. Ret historikken særskilt.')
            if linked:
                if not stamp:
                    raise ValueError('Indleveringsdato med registreret gennemgang kan ikke slettes.')
                other_events = [e for e in _known_dates(store, loan['card_id']) if e['id'] != linked[0]['id']]
                if any(e['date'] == stamp for e in other_events):
                    raise ValueError('Gennemgangen findes allerede på den nye dato.')
                if any(min(stamp, previous) < e['date'] < max(stamp, previous) for e in other_events):
                    raise ValueError('Datoen kan ikke flyttes forbi en anden gennemgang.')
                if any(e['card_id'] == card['id'] and e['date'] == stamp
                       for e in store.all('completions', deleted=True)):
                    raise ValueError('Datoen findes i Gendan ved fejl.')
                store.put('completions', dict(linked[0], date=stamp))
                for e in other_events:
                    if e.get('previous_completed') == previous:
                        store.put('completions', dict(e, previous_completed=stamp))
                if card.get('last_completed') == previous:
                    remaining = [stamp] + [e['date'] for e in other_events]
                    remaining += [e.get('previous_completed') for e in other_events if e.get('previous_completed') and e['previous_completed'] != previous]
                    store.put('cards', dict(card, last_completed=max(remaining)))
                elif stamp > (card.get('last_completed') or ''):
                    store.put('cards', dict(card, last_completed=stamp))
            if not previous and stamp:
                store.put('cards', dict(store.require('cards', card['id']), in_folder=False))
        store.put('loans', changed)
        return {'id': changed['id']}
    raise ValueError('Ukendt historikhandling.')
