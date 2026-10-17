"""Public program source and invented diagnostics only; no user databases."""
import ast
import json
import re
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(APP))
from ui_errors import UIError, error_payload
from store import valid_day
from setup_store import bounded_int


class UIErrorTests(unittest.TestCase):
    def test_original_diagnostic_and_scalar_parameters_are_preserved(self):
        name = 'Historik <fictional> {number} & "quoted"'
        error = UIError('Området {name} findes allerede. Vælg det fra listen.', name=name)
        self.assertIsInstance(error, ValueError)
        self.assertEqual(str(error), 'Området ' + name + ' findes allerede. Vælg det fra listen.')
        self.assertEqual(json.loads(json.dumps(error_payload(error)))['ui_error']['params'], {'name': name})
        self.assertEqual(error_payload(ValueError('Unknown <fictional>')), {'error': 'Unknown <fictional>'})

    def test_date_validation_keeps_its_existing_danish_contract(self):
        for raw, suffix in [('not-a-date', ' skal være en gyldig dato.'), ((date.today()+timedelta(days=1)).isoformat(), ' må ikke ligge i fremtiden.')]:
            with self.assertRaises(UIError) as caught:
                valid_day(raw)
            self.assertEqual(str(caught.exception), 'Dato'+suffix)
            self.assertEqual(error_payload(caught.exception)['ui_error']['params'], {'field': 'Dato'})

    def test_number_validation_keeps_values_and_bounds(self):
        for raw, original in [('fictional', 'Besøg pr. kort skal være et helt tal.'), (0, 'Besøg pr. kort skal være mellem 1 og 1000.')]:
            with self.assertRaises(UIError) as caught:
                bounded_int(raw, 1, 1000, 'Besøg pr. kort')
            self.assertEqual(str(caught.exception), original)
            self.assertEqual(caught.exception.ui_params['label'], 'Besøg pr. kort')
        self.assertEqual(bounded_int(50, 1, 1000, 'Besøg pr. kort'), 50)

    def test_core_error_catalog_and_dynamic_messages_have_explicit_templates(self):
        # Check Python syntax, not line-number snapshots: new core errors must also be localized.
        source=(APP/'i18n.js').read_text(encoding='utf-8').split('english:{',1)[1].split('\n },\n content(',1)[0]
        literals=re.findall(r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')\s*:''', source)
        keys={ast.literal_eval(raw) for raw in literals}
        count=0
        for name in ('store.py','workflow_store.py','admin_store.py','geo_store.py','setup_store.py','portable.py','server.py'):
            for node in ast.walk(ast.parse((APP/name).read_text(encoding='utf-8'))):
                if not isinstance(node, ast.Raise) or not isinstance(node.exc, ast.Call) or not isinstance(node.exc.func, ast.Name) or node.exc.func.id not in ('ValueError','UIError') or not node.exc.args:
                    continue
                key=node.exc.args[0]
                self.assertIsInstance(key, ast.Constant, name+': use an explicit UIError template for parameters')
                self.assertIn(key.value, keys, name+': missing translation for '+str(key.value))
                count+=1
        self.assertGreater(count, 200)


if __name__ == '__main__':
    unittest.main()
