"""Boundary-based review of invented DAR changes; never a live DAR lookup."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from profile_policy import ACTIONS, mutation

POLYGON=[[9.99,54.99],[10.01,54.99],[10.01,55.01],[9.99,55.01]]


class OutsideAddressChangeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Store(self.tmp.name)
        self.store.mutate('geo.main.save',{'points':POLYGON})
    def tearDown(self):
        self.store.close();self.tmp.cleanup()

    @staticmethod
    def address(ident,lng=10,lat=55,label=None):
        row={'id':ident,'entity':'address','road':'Example Road','postcode':'9999',
             'number':ident,'label':label or 'Example Road '+ident,'count':1,'lng':lng,'lat':lat}
        return row

    def change(self,ident,kind,after,before=None):
        item={'id':'change:'+ident,'entity':'address_change','kind':kind,'after':after,
              'before':before,'at':'2026-11-14T12:00:00+00:00'}
        with self.store.transaction():self.store.put('geo',item)
        return item['id']

    def preview(self):
        return self.store.mutate('address.change.outside.preview',{})

    def seed(self):
        return {
          'outside':self.change('outside','new',self.address('out',10.05,label='Example <outside> Road 1')),
          'inside':self.change('inside','new',self.address('inside')),
          'edge':self.change('edge','new',self.address('edge',10.01)),
          'outside_changed':self.change('outside_changed','changed',self.address('newplace',10.06),self.address('oldplace',10.04)),
          'moved_out':self.change('moved_out','changed',self.address('movedout',10.05),self.address('movedin')),
          'unknown_before':self.change('unknown_before','changed',self.address('unknown',10.05),{'id':'old','entity':'address'}),
          'unknown_after':self.change('unknown_after','new',{'id':'bad','entity':'address','label':'Missing coordinates'}),
          'outside_retired':self.change('outside_retired','retired',dict(self.address('retired',10.07),retired=True),self.address('retired',10.07)),
          'inside_retired':self.change('inside_retired','retired',dict(self.address('retired_in'),retired=True),self.address('retired_in')),
        }

    def test_preview_is_read_only_and_classifies_same_street_each_house_by_coordinates(self):
        ids=self.seed()
        before=copy.deepcopy(self.store.all('geo'))
        preview=self.preview()
        self.assertEqual(self.store.all('geo'),before)
        self.assertEqual(preview['count'],3)
        self.assertEqual(preview['protected'],1)
        self.assertEqual(preview['uncertain'],2)
        self.assertEqual(preview['remaining'],6)
        self.assertEqual({x['id'] for x in preview['examples']},{ids['outside'],ids['outside_changed'],ids['outside_retired']})
        self.assertEqual(len(preview['expected']),64)
        self.assertIn('<outside>',preview['examples'][0]['label'])
        # Original addresses, IB, history and card state are not preview targets.
        for key in ('cards','ib','loans','ignored'):self.assertEqual(self.store.all(key),[])

    def test_bulk_rejection_is_atomic_and_keeps_inside_edge_uncertain_and_historical_moves(self):
        ids=self.seed()
        self.store.mutate('geo.manual',{'road':'Example Road','number':'200','postcode':'9999','lng':10.05,'lat':55})
        address=next(a for a in self.store.all('geo') if a.get('entity')=='address')
        card=self.store.mutate('geo.assign',{'number':'F001','address_ids':[address['id']]})['id']
        before=self.store.get('cards',card)
        preview=self.preview()
        with self.assertRaisesRegex(ValueError,'AFVIS UDENFOR'):
            self.store.mutate('address.change.outside.reject',{'expected':preview['expected']})
        result=self.store.mutate('address.change.outside.reject',{'expected':preview['expected'],'confirm':'AFVIS UDENFOR'})
        self.assertEqual(result,{'count':3,'remaining':6})
        self.assertEqual(self.store.get('cards',card),before)
        self.assertIsNotNone(self.store.get('geo',address['id']))
        for key in ('outside','outside_changed','outside_retired'):
            self.assertIsNone(self.store.get('geo',ids[key]))
        for key in ('inside','edge','moved_out','unknown_before','unknown_after','inside_retired'):
            self.assertIsNotNone(self.store.get('geo',ids[key]))
        self.assertEqual(self.store.activity(1)[0]['action'],'address.change.outside.reject')
        with self.assertRaisesRegex(ValueError,'forhåndsvisning'):
            self.store.mutate('address.change.outside.reject',{'expected':preview['expected'],'confirm':'AFVIS UDENFOR'})
        self.store.close();self.store=Store(self.tmp.name)
        self.assertEqual(len([r for r in self.store.all('geo') if r.get('entity')=='address_change']),6)

    def test_changed_boundary_and_pending_additions_invalidate_confirmation(self):
        ids=self.seed();preview=self.preview()
        self.change('late','new',self.address('late',10.06))
        with self.assertRaisesRegex(ValueError,'forhåndsvisning'):
            self.store.mutate('address.change.outside.reject',{'expected':preview['expected'],'confirm':'AFVIS UDENFOR'})
        self.assertIsNotNone(self.store.get('geo',ids['outside']))
        updated=self.preview()
        self.store.mutate('geo.main.save',{'points':[[9.98,54.98],[10.08,54.98],[10.08,55.08],[9.98,55.08]]})
        with self.assertRaisesRegex(ValueError,'forhåndsvisning'):
            self.store.mutate('address.change.outside.reject',{'expected':updated['expected'],'confirm':'AFVIS UDENFOR'})
        self.assertIsNotNone(self.store.get('geo',ids['outside']))

    def test_missing_boundary_rejects_preview_and_write(self):
        with self.store.transaction():self.store.db.execute('DELETE FROM geo.records WHERE id=?',('main-boundary',))
        with self.assertRaisesRegex(ValueError,'samlede distriktsgrænse'):self.preview()
        with self.assertRaisesRegex(ValueError,'samlede distriktsgrænse'):
            self.store.mutate('address.change.outside.reject',{'expected':'any','confirm':'AFVIS UDENFOR'})

    def test_permissions_require_address_review_rights_even_for_preview(self):
        needed={'geo.view','geo.edit','cards.view','ib.view'}
        for action in ('address.change.outside.preview','address.change.outside.reject'):
            self.assertEqual(set(ACTIONS[action]),needed)
            for omitted in needed:
                user={'id':'user','permissions':frozenset(needed-{omitted})}
                with self.assertRaises(PermissionError):mutation(user,action,{},self.store)
            mutation({'id':'editor','permissions':frozenset(needed)},action,{},self.store)


if __name__=='__main__':unittest.main()
