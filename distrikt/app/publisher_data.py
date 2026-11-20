"""Service functions are territory records, never account permissions."""
from card_import import norm

ROLES={'':'Ingen gruppefunktion','overseer':'Gruppetilsynsmand','assistant':'Assistent'}
UNGROUPED = 'Ikke i en tjenestegruppe'


def names(person):
    """Current name and retained import names, once per case-insensitive key."""
    values = [person['name']]
    if isinstance(person.get('aliases'), list):
        values.extend(value for value in person['aliases'] if isinstance(value, str))
    unique = {}
    for value in values:
        key = value.strip().casefold()
        if key:
            unique.setdefault(key, value.strip())
    return list(unique.values())


def normalized(data,old=None):
    from store import clean_text
    result=dict(old or {})
    result['name']=clean_text(data.get('name'),100,True)
    result['group']=clean_text(data.get('group',result.get('group','')),100)
    result['group_role']=data.get('group_role',result.get('group_role',''))
    result['pioneer']=data.get('pioneer',result.get('pioneer',False))
    if not isinstance(result['group_role'],str) or result['group_role'] not in ROLES:raise ValueError('Vælg en gyldig gruppefunktion.')
    if type(result['pioneer']) is not bool:raise ValueError('Pioner skal være Ja eller Nej.')
    if result['group_role'] and not result['group']:raise ValueError('Angiv tjenestegruppe før gruppefunktion.')
    return result


def validate_groups(people):
    roles={}
    for p in people:
        if not p.get('group_role'):continue
        key=(norm(p.get('group')),p['group_role'])
        if key in roles:raise ValueError('Der er flere med samme gruppefunktion i tjenestegruppen. Ret valget før gemning.')
        roles[key]=p.get('id')


class PublisherIndex:
    """One locked import uses the same domain checks without repeated SQL scans."""
    def __init__(self,people):
        self.names={};self.functions={}
        for person in people:self.add(person)

    def keys(self,person):
        return [name.casefold() for name in names(person)],(norm(person.get('group')),person.get('group_role'))

    def add(self,person):
        person_names,function=self.keys(person)
        for name in person_names:self.names.setdefault(name,set()).add(person['id'])
        if function[1]:self.functions.setdefault(function,set()).add(person['id'])

    def remove(self,person):
        person_names,function=self.keys(person)
        for name in person_names:self.names.get(name,set()).discard(person['id'])
        self.functions.get(function,set()).discard(person['id'])

    def check(self,person):
        person_names,function=self.keys(person)
        for name in person_names:
            if self.names.get(name,set())-{person['id']}:raise ValueError('Navnet findes allerede. Vælg den eksisterende forkynder.')
        if function[1] and self.functions.get(function,set())-{person['id']}:
            raise ValueError('Der er flere med samme gruppefunktion i tjenestegruppen. Ret valget før gemning.')


def save(store,data):
    from store import new_id
    old=store.get('publishers',data.get('id')) if data.get('id') else None
    if data.get('id') and not old:raise ValueError('Posten er ændret eller slettet. Opdater siden.')
    person=normalized(data,old or {'id':new_id()})
    index=getattr(store,'_publisher_index',None)
    if index is None:index=PublisherIndex(store.all('publishers'))
    index.check(person)
    store.put('publishers',person)
    if old:index.remove(old)
    index.add(person)
    return {'id':person['id']}


def merge(store, data, *, preview=False):
    """Retain one identity and atomically redirect its duplicate's allocations."""
    from admin_store import signature
    target_id, source_id = data.get('target_id'), data.get('source_id')
    if not isinstance(target_id, str) or not isinstance(source_id, str) or target_id == source_id:
        raise ValueError('Vælg to forskellige forkyndere.')
    target = store.require('publishers', target_id)
    source = store.require('publishers', source_id)
    person = normalized({'name': data.get('name')}, target)
    retained = names(target) + names(source)
    person['aliases'] = names({'name': person['name'], 'aliases': retained})[1:]
    others = [p for p in store.all('publishers') if p['id'] not in (target_id, source_id)]
    PublisherIndex(others).check(person)
    loans = [loan for loan in store.all('loans') + store.all('loans', deleted=True)
             if loan.get('publisher_id') in (target_id, source_id)]
    expected = signature([target, source, person, sorted(loans, key=lambda loan: loan['id'])])
    result = {'id': target_id, 'name': person['name'], 'target_name': target['name'],
              'source_name': source['name'], 'group': person.get('group', ''),
              'group_role': person.get('group_role', ''), 'pioneer': person.get('pioneer', False),
              'expected': expected, 'loans': sum(loan['publisher_id'] == source_id for loan in loans)}
    if preview:
        return result
    if data.get('expected') != expected:
        raise ValueError('Forkyndere eller udleveringer er ændret. Kontrollér sammenlægningen igen.')
    store.put('publishers', person)
    for loan in loans:
        if loan['publisher_id'] != source_id:
            continue
        updated = {key: value for key, value in loan.items() if key not in ('_deleted_at', '_batch')}
        updated['publisher_id'] = target_id
        store.put('loans', updated)
    # The existing undo journal retains the full source row and every changed loan.
    store.workflow_track('publishers', source_id)
    store._dirty_modules.add('publishers')
    store.db.execute('DELETE FROM ' + store.record_table('publishers') + ' WHERE id=?', (source_id,))
    return result
