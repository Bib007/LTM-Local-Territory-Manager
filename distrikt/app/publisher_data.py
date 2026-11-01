"""Service functions are territory records, never account permissions."""
from card_import import norm

ROLES={'':'Ingen gruppefunktion','overseer':'Gruppetilsynsmand','assistant':'Assistent'}


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
        return person['name'].casefold(),(norm(person.get('group')),person.get('group_role'))

    def add(self,person):
        name,function=self.keys(person)
        self.names.setdefault(name,set()).add(person['id'])
        if function[1]:self.functions.setdefault(function,set()).add(person['id'])

    def remove(self,person):
        name,function=self.keys(person)
        self.names.get(name,set()).discard(person['id'])
        self.functions.get(function,set()).discard(person['id'])

    def check(self,person):
        name,function=self.keys(person)
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
