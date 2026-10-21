"""Real setup preview from a disposable, exclusively fictional local database."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'distrikt' / 'app'))
from store import Store


def fixture():
    polygon = [[10, 55], [10.04, 55], [10.04, 55.04], [10, 55.04]]
    curve = [[9.99, 55.0125], [10.014, 55.0125], [10.014, 55.0135], [10.023, 55.0135], [10.023, 55.0125], [10.05, 55.0125]]
    addresses = [{'id': 'fiction-' + str(i), 'entity': 'address', 'road': 'Fiktiv husvej', 'number': str(i + 1), 'postcode': '9999',
                  'lng': 10.002 + (i % 10) * .003, 'lat': 55.002 + (i // 10) * .003, 'count': 1} for i in range(80)]
    roads = [{'id': 'fiction-road-' + str(i), 'entity': 'road', 'name': 'Fiktiv Forgrenet vej', 'points': points}
             for i, points in enumerate((curve[:3], curve[2:4], curve[3:], [curve[2], [10.016, 55.0145]]))]
    with tempfile.TemporaryDirectory() as folder:
        store = Store(folder)
        try:
            store.mutate('geo.main.save', {'points': polygon})
            store.mutate('geo.import', {'records': addresses + roads, 'source': 'Fiktiv test', 'label': 'Fiktivt vejnet'})
            plan = store.mutate('setup.preview', {'target': 40, 'numbering': 'hundreds', 'start': 100, 'block': 100,
                                                'areas': [{'name': 'Fiktivt prøveområde', 'kind': 'By'}]})
            state = store.state()
            state['version'] = 'fictional'
            state['settings'].update(congregation='Fiktiv menighed', onboarding={'completed': True})
            assert not state['cards'] and len(plan['cards']) == 2 and plan['visits'] == 80
            assert all('Fiktiv Forgrenet vej' in c['warning'] for c in plan['cards'])
            return {'state': state, 'geo': store.geo_state(), 'plan': plan}
        finally:
            store.close()


if __name__ == '__main__':
    print(json.dumps(fixture(), ensure_ascii=False))
