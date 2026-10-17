"""Read-only DAR road/postcode adapter. Not activated in Downloads yet.

Queries, aliases and joins share one snapshot. No local store or checkpoint is
read or changed here; callers must only import a complete returned result.
"""
import re
from dar_join import join_addresses
from dar_paging import IncompleteResult

SOURCE = 'dar-graphql-v3'


def _ids(rows, field):
    values = []
    for row in rows:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            raise IncompleteResult('DAR-svaret manglede en nødvendig ID-reference.')
        values.append(value)
    return sorted(set(values))


class DarAdapter:
    def __init__(self, query):
        self.query = query

    def _post(self, postcode):
        if not isinstance(postcode, str) or not re.fullmatch(r'\d{4}', postcode):
            raise ValueError('Skriv et firecifret postnummer.')
        posts = self.query.collect('DAR_Postnummer', {'postnr': postcode})
        if len(posts) != 1:
            raise IncompleteResult('Postnummeret kunne ikke findes entydigt i DAR.')
        return posts

    def discover_postcode(self, postcode):
        posts = self._post(postcode)
        houses = self.query.collect('DAR_Husnummer', {'postnummer': posts[0]['id_lokalId']})
        roads = self.query.collect_many('DAR_NavngivenVej', 'id_lokalId',
                                        _ids(houses, 'navngivenVej'), require_all=True)
        for road in roads:
            if not isinstance(road.get('vejnavn'), str) or not road['vejnavn'].strip():
                raise IncompleteResult('Den officielle DAR-vejliste var ufuldstændig.')
        roads.sort(key=lambda row: (row['vejnavn'].casefold(), row['id_lokalId']))
        return {'source': SOURCE, 'snapshot': self.query.snapshot, 'postcode': postcode,
                'name': posts[0].get('navn') or '', 'roads': roads}

    def road(self, road_id, *, postcode=None):
        roads = self.query.collect_many('DAR_NavngivenVej', 'id_lokalId', [road_id], require_all=True)
        filters = {'navngivenVej': road_id}
        posts = self._post(postcode) if postcode is not None else None
        if posts is not None:
            filters['postnummer'] = posts[0]['id_lokalId']
        houses = self.query.collect('DAR_Husnummer', filters)
        addresses = self.query.collect_many('DAR_Adresse', 'husnummer', _ids(houses, 'id_lokalId'))
        # Only points needed by an actual address are requested. A valid house may
        # have no current unit addresses; no artificial dwelling is manufactured.
        needed_houses = set(_ids(addresses, 'husnummer'))
        used = [house for house in houses if house['id_lokalId'] in needed_houses]
        points = self.query.collect_many('DAR_Adressepunkt', 'id_lokalId',
                                         _ids(used, 'adgangspunkt'), require_all=True)
        if posts is None:
            posts = self.query.collect_many('DAR_Postnummer', 'id_lokalId',
                                            _ids(used, 'postnummer'), require_all=True)
        name = roads[0].get('vejnavn')
        if not isinstance(name, str) or not name.strip():
            raise IncompleteResult('DAR-vejen manglede et gyldigt navn.')
        result = join_addresses(addresses, houses, points, roads, posts, postcode=postcode, road=name)
        for address in result:
            address['source'] = 'DAR / Datafordeleren'
        self.query.check_cancel()
        return {'source': SOURCE, 'snapshot': self.query.snapshot, 'road_id': road_id,
                'road': name, 'addresses': result, 'roads': roads}
