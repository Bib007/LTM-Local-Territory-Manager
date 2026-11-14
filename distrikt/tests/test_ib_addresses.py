"""Exact local IB selection; fictional cards/units in temporary databases."""
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store

class IBAddressTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
        records=[dict(id='unit-a',entity='address',road='Eksempelvej',number='42B',floor='1',door='tv',postcode='9999',lng=10,lat=55,count=1),dict(id='unit-b',entity='address',road='Eksempelvej',number='42B',floor='1',door='th',postcode='9999',lng=10,lat=55,count=1),dict(id='neighbor',entity='address',road='Anden vej',number='9',postcode='9999',lng=10.01,lat=55.01,count=1)]
        self.s.mutate('geo.import',{'records':records,'source':'Fiktive testdata'})
        self.c=self.s.mutate('geo.assign',{'address_ids':['unit-a','unit-b'],'number':'120'})['id']
        self.s.mutate('revision.approve',{'card_id':self.c,'side':'front'})
        self.s.mutate('revision.approve',{'card_id':self.c,'side':'back'})
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def save(self,**extra):
        payload={'card_id':self.c,'address_id':'unit-a','road':'Wrong input ignored','number':'999','date':date.today().isoformat()};payload.update(extra)
        return self.s.mutate('ib.save',payload)
    def test_exact_apartment_canonicalized_without_changing_counts_or_front(self):
        before=self.s.get('cards',self.c);result=self.save();ib=self.s.get('ib',result['id']);after=self.s.get('cards',self.c)
        self.assertEqual(ib['address_id'],'unit-a');self.assertEqual(ib['road'],'Eksempelvej');self.assertEqual(ib['number'],'42B, 1 tv')
        self.assertEqual(before['addresses'],after['addresses']);self.assertEqual(before['geo_addresses'],after['geo_addresses'])
        self.assertFalse(after['front_revision']);self.assertTrue(after['back_revision'])
        self.s.close();self.s=Store(self.tmp.name);self.assertEqual(self.s.get('ib',result['id']),ib)
        self.assertEqual(len(list(Path(self.tmp.name).glob('*.sqlite3'))),11)
    def test_foreign_address_and_duplicate_are_rejected_atomically(self):
        before=self.s.get('cards',self.c)
        with self.assertRaisesRegex(ValueError,'ikke på'):self.save(address_id='neighbor')
        self.assertEqual(self.s.all('ib'),[]);self.assertEqual(self.s.get('cards',self.c),before)
        result=self.save()
        with self.assertRaisesRegex(ValueError,'allerede'):self.save()
        self.save(id=result['id']);self.assertEqual(len(self.s.all('ib')),1)
        self.save(address_id='unit-b');self.assertEqual(len(self.s.all('ib')),2)
    def test_manual_edit_clears_old_binding_and_temporary_cards_remain_supported(self):
        result=self.save()
        self.save(id=result['id'],address_id='',road='Eksempelvej',number='42B')
        self.assertNotIn('address_id',self.s.get('ib',result['id']))
        temporary=self.s.mutate('card.save',{'number':'584','temporary':True})['id']
        ib=self.s.mutate('ib.save',{'card_id':temporary,'road':'Fysisk kortvej','number':'1A','date':date.today().isoformat()})['id']
        self.assertEqual(self.s.get('ib',ib)['number'],'1A')

class IBBulkSuggestionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.addCleanup(self.store.close)
        records = [
            dict(id=ident, road='Prøvevej', number=number, postcode='9999', lng=10, lat=55, **unit)
            for ident, number, unit in [
                ('house', '1A', {}), ('other-house', '2', {}),
                ('left', '3', {'floor': 'st', 'door': 'tv'}),
                ('right', '3', {'floor': 'st', 'door': 'th'}),
                ('retired', '4', {}), ('outside', '5', {}),
            ]
        ]
        self.store.mutate('geo.import', {'records': records, 'source': 'DAR / Datafordeleren'})
        self.card = self.store.mutate('geo.assign', {'number': '303', 'address_ids': [
            'house', 'other-house', 'left', 'right', 'retired',
        ]})['id']
        row = self.store.get('geo', 'retired')
        row['retired'] = True
        with self.store.transaction():
            self.store.put('geo', row)

    def manual(self, number, **extra):
        return self.store.mutate('ib.save', {'card_id': self.card, 'road': 'prøvevej',
            'number': number, 'date_text': 'marts 2024', **extra})['id']

    def preview(self):
        return self.store.mutate('ib.bulk.preview', {'card_id': self.card})

    def apply(self, plan, selected):
        return self.store.mutate('ib.bulk.apply', {
            'card_id': self.card, 'expected': plan['expected'], 'selected': selected,
        })

    def test_apply_selected_side_by_side_and_undo(self):
        house = self.manual('1a')
        keep = self.manual('2')
        unit = self.manual('3, st. tv')
        for number in ('3', '4', '5'):
            self.manual(number)
        for side in ('front', 'back'):
            self.store.mutate('revision.approve', {'card_id': self.card, 'side': side})
        revision = self.store.revision
        plan = self.preview()
        self.assertEqual(self.store.revision, revision)
        selected = {row['id']: row for row in plan['rows'] if row['selectable']}
        self.assertEqual(set(selected), {house, keep, unit})
        self.assertEqual(selected[house]['before'], 'prøvevej 1a')
        self.assertEqual(selected[house]['after'], 'Prøvevej 1A · 9999')
        kept_item = self.store.get('ib', keep)
        self.assertEqual(self.apply(plan, [house, unit]), {'count': 2})
        linked = self.store.get('ib', unit)
        self.assertEqual((linked['number'], linked['address_id'], linked['date_text']),
                         ('3, st tv', 'left', 'marts 2024'))
        self.assertEqual(self.store.get('ib', keep), kept_item)
        self.assertTrue(self.store.get('cards', self.card)['back_revision'])
        self.assertFalse(self.store.get('cards', self.card)['front_revision'])
        self.store.mutate('workflow.undo', {})
        self.assertNotIn('address_id', self.store.get('ib', unit))
        self.assertFalse(self.store.get('cards', self.card)['back_revision'])

    def test_stale_and_unapproved_rows_cannot_change_anything(self):
        chosen = self.manual('1a')
        unknown = self.manual('5')
        plan = self.preview()
        with self.assertRaisesRegex(ValueError, 'gyldigt DAR'):
            self.apply(plan, [chosen, unknown])
        self.manual('2')
        with self.assertRaisesRegex(ValueError, 'ændret'):
            self.apply(plan, [chosen])
        self.assertNotIn('address_id', self.store.get('ib', chosen))

    def test_matching_one_unit_respects_existing_registration_and_postcode(self):
        self.store.mutate('ib.save', {'card_id': self.card, 'address_id': 'house', 'date_text': '2024'})
        self.manual(' 1 a')
        self.manual('2', postcode='9998')
        self.manual('3 st tv')
        self.manual('3, st tv')
        self.assertFalse(any(row['selectable'] for row in self.preview()['rows']))

if __name__=='__main__':unittest.main()
