import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from conflict_reviews import pending, acknowledge
from store import Store


class ConflictReviewTests(unittest.TestCase):
    def test_permissions_acknowledgement_and_persistence(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            try:
                with store.transaction():
                    store.put('settings',{'id':'fictional-ib','entity':'edit-conflict','module':'ib','saved':{'value':'private fictional value'},'resolved':False})
                    store.put('settings',{'id':'fictional-card','entity':'edit-conflict','module':'cards','resolved':False})
                self.assertEqual([x['id'] for x in pending(store,{'cards'})],['fictional-card'])
                with self.assertRaises(ValueError):acknowledge(store,'fictional-ib',{'cards'},'fictional-user')
                self.assertTrue(acknowledge(store,'fictional-card',{'cards'},'fictional-user'))
                self.assertFalse(acknowledge(store,'fictional-card',{'cards'},'fictional-user'))
                self.assertEqual(pending(store,{'cards'}),[])
                self.assertFalse(store.require('settings','fictional-ib')['resolved'])
            finally:store.close()
            store=Store(root)
            try:self.assertEqual(store.require('settings','fictional-card')['reviewed_by'],'fictional-user')
            finally:store.close()

    def test_requires_explicit_permissions(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            try:
                with self.assertRaises(ValueError):pending(store,None)
                with self.assertRaises(ValueError):acknowledge(store,'missing',None,'x')
            finally:store.close()


if __name__=='__main__':unittest.main()
