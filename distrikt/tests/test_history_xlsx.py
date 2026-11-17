"""Fictional five-period XLSX imports; no live territory data."""
import base64
import io
import sys
import tempfile
import unittest
import zipfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from store import Store
from portable import digest
from history_xlsx import WIDE_HEADERS, template_xlsx, _cell, xlsx_records
from history_import import csv_text
from card_import import read_rows


def workbook(values, *, formula=False):
    """Edit only a fictional template example using standard XLSX XML."""
    source = template_xlsx()
    with zipfile.ZipFile(io.BytesIO(source)) as archive:
        parts = {path: archive.read(path) for path in archive.namelist()}
    path = 'xl/worksheets/sheet1.xml'
    xml = parts[path].decode('utf-8')
    beginning = xml.index('<row r="5"')
    end = xml.index('</row>', beginning) + len('</row>')
    cells = ''.join(_cell(i + 1, 5, value, 6) for i, value in enumerate(values))
    if formula:
        cells = cells.replace(_cell(3, 5, values[2], 6),
                              '<c r="C5" s="6"><f>1+1</f><v>2</v></c>')
    xml = xml[:beginning] + '<row r="5" ht="26" customHeight="1">' + cells + '</row>' + xml[end:]
    parts[path] = xml.encode('utf-8')
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, raw in parts.items():
            archive.writestr(name, raw)
    return stream.getvalue()


class HistoryXlsxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.card = self.store.mutate('card.save', {'number': 'FIK-001'})['id']

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def ago(self, days):
        return (date.today() - timedelta(days=days)).isoformat()

    def pairs(self, flags=('Ja', 'Nej', 'Ja', 'Nej', 'Ja')):
        fields = ['FIK-001']
        for i, (start, end) in enumerate(((500, 480), (400, 380), (300, 280),
                                          (200, 180), (100, 80))):
            fields.extend(['Fiktiv Forkynder %s' % (i + 1),
                           self.ago(start), self.ago(end), flags[i]])
        return fields

    def preview_xlsx(self, raw):
        return self.store.mutate('setup.history-import.preview',
                                 {'name': 'fiktiv-historik.xlsx',
                                  'content': base64.b64encode(raw).decode('ascii')})

    def preview_csv(self, rows):
        return self.store.mutate('setup.history-import.preview',
                                 {'name': 'fiktiv-historik.csv',
                                  'content': csv_text(rows, WIDE_HEADERS)})

    def apply(self, result):
        return self.store.mutate('setup.history-import.apply',
                                 {'token': result['token'], 'confirm': 'IMPORTÉR HISTORIK'})

    def test_template_is_readable_with_exact_10_dates_and_fictional_example(self):
        raw = template_xlsx()
        self.assertEqual(len([h for h in WIDE_HEADERS if h.startswith(('udleveret', 'indleveret'))]), 10)
        self.assertLess(len(raw), 2000000)
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(raw)))
        rows = read_rows({'name': 'example.xlsx', 'content': base64.b64encode(raw).decode()},
                         sheet_name='Historik', column_cells=True)
        self.assertEqual([str(v).casefold() for v in next(v for line, v in rows if line == 4)], WIDE_HEADERS)
        self.assertEqual(next(v for line, v in rows if line == 5)[0], 'FIK-001')
        self.assertEqual([line for line, _ in xlsx_records(
            {'name': 'example.xlsx', 'content': base64.b64encode(raw).decode()})], [5])

    def test_five_periods_do_not_invent_three_unmarked_completions(self):
        raw = workbook(self.pairs())
        before, revision = digest(self.store), self.store.revision
        with patch('urllib.request.urlopen', side_effect=AssertionError('network not permitted')):
            preview = self.preview_xlsx(raw)
        self.assertEqual((digest(self.store), self.store.revision), (before, revision))
        self.assertEqual((preview['count'], preview['loan_count'],
                          preview['publisher_count'], preview['errors']), (3, 5, 5, 0))
        self.assertEqual([(r['line'], r['period'], r['status']) for r in preview['rows']],
                         [(5, i, 'ready') for i in range(1, 6)])
        self.assertEqual([r['completion_requested'] for r in preview['rows']],
                         [True, False, True, False, True])
        applied = self.apply(preview)
        self.assertEqual((applied['count'], applied['loans']), (3, 5))
        self.assertEqual(len(self.store.all('loans')), 5)
        self.assertEqual(len(self.store.all('completions')), 3)
        self.assertEqual(self.store.require('cards', self.card)['last_completed'], self.ago(80))
        self.assertEqual({e['date'] for e in self.store.all('completions')},
                         {self.ago(n) for n in (480, 280, 80)})
        self.assertTrue(all(e['visits_unknown'] and e['visits'] == 0
                            for e in self.store.all('completions')))
        after = digest(self.store)
        duplicate = self.preview_xlsx(raw)
        self.assertEqual((duplicate['count'], duplicate['loan_count'],
                          duplicate['errors']), (0, 0, 0))
        self.assertEqual([r['status'] for r in duplicate['rows']], ['duplicate'] * 5)
        with self.assertRaises(ValueError):
            self.apply(duplicate)
        self.assertEqual(digest(self.store), after)

    def test_return_without_explicit_yes_does_not_link_known_completion(self):
        completion = self.ago(80)
        self.store.mutate('completion.record', {'card_id': self.card, 'date': completion})
        old = self.store.all('completions')[0]
        row = ['FIK-001', 'Fiktiv Person', self.ago(100), completion, 'Nej'] + [''] * 16
        self.apply(self.preview_xlsx(workbook(row)))
        self.assertEqual(self.store.all('completions')[0], old)
        self.assertIsNone(self.store.all('completions')[0].get('loan_id'))

    def test_blank_return_does_not_create_completion_and_stays_active(self):
        row = ['FIK-001', 'Fiktiv Person', self.ago(100), '', ''] + [''] * 16
        preview = self.preview_xlsx(workbook(row))
        self.assertEqual((preview['count'], preview['loan_count'], preview['errors']), (0, 1, 0))
        self.apply(preview)
        self.assertEqual(len(self.store.all('completions')), 0)
        self.assertEqual(self.store.active_loan(self.card)['assigned'], self.ago(100))

    def test_excel_cell_formula_rejected_on_physical_line_and_period(self):
        before = digest(self.store)
        p = self.preview_xlsx(workbook(self.pairs(), formula=True))
        self.assertEqual(p['rows'][0]['line'], 5)
        self.assertEqual(p['rows'][0]['period'], 1)
        self.assertEqual(p['rows'][0]['status'], 'error')
        self.assertIn('Formler', p['rows'][0]['message'])
        with self.assertRaisesRegex(ValueError, 'Ret alle fejl'):
            self.apply(p)
        self.assertEqual(digest(self.store), before)

    def test_validation_rejects_reversed_order_overlap_missing_name_and_unproven_completion(self):
        wrong_order = self.pairs()
        wrong_order[6] = self.ago(600)  # Period 2 issue before period 1 issue.
        p = self.preview_csv([wrong_order])
        self.assertEqual(p['rows'][1]['status'], 'error')
        self.assertIn('datoorden', p['rows'][1]['message'])
        overlap = self.pairs()
        overlap[6] = self.ago(490)  # Period 2 begins before period 1 is returned.
        p = self.preview_csv([overlap])
        self.assertEqual(p['rows'][1]['status'], 'error')
        self.assertIn('overlapper', p['rows'][1]['message'])
        missing_name = ['FIK-001', '', self.ago(40), self.ago(20), 'Nej'] + [''] * 16
        p = self.preview_csv([missing_name])
        self.assertEqual(p['errors'], 1)
        self.assertIn('forkyndernavnet', p['rows'][0]['message'])
        unsupported = ['FIK-001', 'Fiktiv', self.ago(40), '', 'Ja'] + [''] * 16
        p = self.preview_csv([unsupported])
        self.assertEqual(p['errors'], 1)
        self.assertIn('kræver en indleveringsdato', p['rows'][0]['message'])

    def test_duplicate_card_rows_and_unknown_cards_block_all_writes(self):
        row = ['FIK-001', 'Fiktiv', self.ago(30), '', 'Nej'] + [''] * 16
        before = digest(self.store)
        p = self.preview_csv([row, row])
        self.assertEqual((p['rows'][1]['line'], p['rows'][1]['status']), (3, 'error'))
        self.assertIn('én række pr. kort', p['rows'][1]['message'])
        with self.assertRaises(ValueError):
            self.apply(p)
        unknown = ['FIK-999'] + row[1:]
        p = self.preview_csv([row, unknown])
        self.assertEqual(p['errors'], 1)
        self.assertEqual(digest(self.store), before)

    def test_xlsx_to_preview_csv_roundtrip_keeps_no_completion_flags(self):
        raw = workbook(self.pairs())
        original = self.preview_xlsx(raw)
        rerun = self.store.mutate('setup.history-import.preview',
                                  {'name': 'roundtrip.csv', 'content': original['csv']})
        self.assertEqual((original['count'], original['loan_count'], original['errors']),
                         (rerun['count'], rerun['loan_count'], rerun['errors']))
        self.assertEqual([r['completion_requested'] for r in rerun['rows']],
                         [True, False, True, False, True])


if __name__ == '__main__':
    unittest.main()
