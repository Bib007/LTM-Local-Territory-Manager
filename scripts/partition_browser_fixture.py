"""Real setup preview from a disposable, exclusively fictional local database."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'distrikt' / 'app'))
from store import Store


def fixture(kind='road'):
    if kind not in ('road','river','rail'):
        raise ValueError('Unknown fictional fixture')
    polygon = [[10, 55], [10.04, 55], [10.04, 55.04], [10, 55.04]]
    curve = [[9.99, 55.0125], [10.014, 55.0125], [10.014, 55.0135], [10.023, 55.0135], [10.023, 55.0125], [10.05, 55.0125]]
    addresses = [{'id': 'fiction-' + str(i), 'entity': 'address', 'road': 'Fiktiv husvej', 'number': str(i + 1), 'postcode': '9999',
                  'lng': 10.002 + (i % 10) * .003, 'lat': 55.002 + (i // 10) * .003, 'count': 1} for i in range(80)]
    roads = [{'id': 'fiction-road-' + str(i), 'entity': 'road', 'name': 'Fiktiv Forgrenet vej', 'points': points}
             for i, points in enumerate((curve[:3], curve[2:4], curve[3:], [curve[2], [10.016, 55.0145]]))]
    dividers = [] if kind=='road' else [{'id':'fiction-divider','entity':'divider','divider_type':kind,
                  'name':'Fiktivt <vandløb>' if kind=='river' else 'Fiktiv <jernbane>',
                  'points':[[10.0155 if x==10.014 else 10.0245 if x==10.023 else x,55.0165 if y==55.0135 else y] for x,y in curve]}]
    with tempfile.TemporaryDirectory() as folder:
        store = Store(folder)
        try:
            store.mutate('geo.main.save', {'points': polygon})
            store.mutate('geo.import', {'records': addresses + roads + dividers, 'source': 'Fiktiv test', 'label': 'Fiktivt vejnet'})
            plan = store.mutate('setup.preview', {'target': 40, 'numbering': 'hundreds', 'start': 100, 'block': 100,
                                                'areas': [{'name': 'Fiktivt prøveområde', 'kind': 'By'}]})
            state = store.state()
            state['version'] = 'fictional'
            state['settings'].update(congregation='Fiktiv menighed', onboarding={'completed': True})
            assert not state['cards'] and len(plan['cards']) == 2 and plan['visits'] == 80
            assert all(('Fiktiv Forgrenet vej' if kind=='road' else 'Vandløb' if kind=='river' else 'Jernbane') in c['warning'] for c in plan['cards'])
            return {'state': state, 'geo': store.geo_state(), 'plan': plan}
        finally:
            store.close()


if __name__ == '__main__':
    print(json.dumps(fixture(sys.argv[1] if len(sys.argv)>1 else 'road'), ensure_ascii=False))
