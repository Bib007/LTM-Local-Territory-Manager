"""Fictional, offline checks for the publicly reviewed Drive address-list pages."""
import io
import re
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app/vendor_py/pypdf-6.21.4.zip'))

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))

from pdf_export import shared_card_pdf
from public_address_list import address_entries, address_pages
from test_sharing import png


class DriveAddressListTests(unittest.TestCase):
    def test_sorting_and_private_fields_are_not_serialized(self):
        entries = address_entries([
            {'road': 'Testvej', 'postcode': '7000', 'number': '12',
             'floor': '2', 'door': 'th', 'note': 'PRIVATE_IB_NOTE'},
            {'road': 'Testvej', 'postcode': '7000', 'number': '3'},
            {'road': 'Anden vej', 'postcode': '6000', 'number': '1'},
        ])
        self.assertEqual([(e['road'], e['label']) for e in entries],
                         [('Anden vej', '1'), ('Testvej', '3'), ('Testvej', '12, 2. th')])
        self.assertNotIn('PRIVATE_IB_NOTE', str(entries))
        self.assertNotIn('note', entries[0])

    def test_many_addresses_continue_after_page_three_and_remain_searchable(self):
        members = [{'road': 'Fiktiv vej', 'postcode': '7000', 'number': str(i)}
                   for i in range(1, 161)]
        members.append({'road': 'Anden vej', 'postcode': '7100',
                        'number': '4A', 'floor': 'st', 'door': 'tv'})
        entries = address_entries(members)
        pdf = shared_card_pdf(png(), png(), address_list=entries,
                              number='F101', name='Fiktivt byområde')
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf))
        self.assertGreater(len(reader.pages), 3)
        self.assertEqual([len(p.images) for p in reader.pages[:3]], [1, 1, 0])
        self.assertTrue(all(not p.images for p in reader.pages[2:]))
        text = '\n'.join((p.extract_text() or '') for p in reader.pages[2:])
        self.assertIn('ADRESSELISTE', text)
        self.assertIn('F101', text)
        self.assertIn('4A, st. tv', text)
        self.assertIn('160', text)
        self.assertIn('161 adresser', text)
        self.assertNotIn('PRIVATE_IB_', text)

    def test_manual_ranges_are_kept_verbatim_and_long_lines_wrap(self):
        number_range = '9' * 2500
        rows = address_entries([], [
            {'road': 'Lang fiktiv vej', 'numbers': number_range},
            {'road': 'Kort vej', 'numbers': '2–8'},
        ])
        self.assertEqual(len(rows), 2)
        pages = address_pages(rows, 'M1', 'Manuelt kort')
        self.assertGreaterEqual(len(pages), 2)
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(shared_card_pdf(png(), png(),
                                 address_list=rows, number='M1', name='Manuelt kort')))
        text = '\n'.join((p.extract_text() or '') for p in reader.pages[2:])
        self.assertIn('2–8', text)
        self.assertGreaterEqual(sum(len(x) for x in re.findall(r'9+', text)), 2500)
        self.assertIn('Manuelle nummerintervaller', text)

    def test_empty_list_still_has_a_third_page(self):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(shared_card_pdf(png(), png(),
                              address_list=[], number='T0', name='Fiktivt tomt kort')))
        self.assertEqual(len(reader.pages), 3)
        self.assertIn('Ingen adresser', reader.pages[2].extract_text())


if __name__ == '__main__':
    unittest.main()
