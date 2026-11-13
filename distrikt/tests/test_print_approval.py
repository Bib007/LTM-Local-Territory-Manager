"""Batch approval is atomic and bound to the physical print content."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import tempfile
import unittest
from unittest.mock import patch
from store import Store
from profile_policy import mutation

class PrintApprovalTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.s=Store(self.folder.name)
        self.ids=[self.s.mutate('card.save',{'number':str(i),'temporary':True})['id'] for i in (101,102)]
        with self.s.transaction():
            for ident in self.ids:
                c=self.s.require('cards',ident);c.update(front_revision=True,back_revision=True);self.s.put('cards',c)
    def tearDown(self):self.s.close();self.folder.cleanup()
    def entries(self,sides=('front','back')):
        return [{'card_id':c['id'],'side':side,'token':c[side+'_print_token']} for c in self.s.state()['cards'] for side in sides]
    def test_380_cards_share_one_print_context_and_keep_unchanged_tokens(self):
        with self.s.transaction():
            for index in range(380):
                ident='fictional-'+str(index)
                self.s.put('cards',{'id':ident,'number':str(index+1000),'addresses':[{'road':'Prøvevej','numbers':'1–9','count':5}],
                    'front_revision':True,'back_revision':True})
                self.s.put('ib',{'id':'ib-'+ident,'card_id':ident,'road':'Prøvevej','number':'3'})
                self.s.put('maps',{'id':'map-'+ident,'card_id':ident,'image':'fictional image '*1000})
        with patch.object(self.s,'all',wraps=self.s.all) as reads:
            snapshot=self.s.state()
        self.assertEqual(sum(c.args[0]=='maps' for c in reads.call_args_list),1)
        self.assertEqual(sum(c.args[0]=='ib' and not c.kwargs.get('deleted') for c in reads.call_args_list),1)
        entries=[{'card_id':c['id'],'side':side,'token':c[side+'_print_token']} for c in snapshot['cards'] if c['id'].startswith('fictional-') for side in ('front','back')]
        self.assertEqual(len(entries),760)
        # Tokens from the previous version are still valid for unchanged content.
        from hashlib import sha256
        for side in ('front','back'):
            c=self.s.require('cards','fictional-0')
            fields=('id','number','name','area_id','addresses','geo_addresses','address_ids','temporary','geo_polygon') if side=='front' else ('id','number')
            content={k:c.get(k) for k in fields}
            if side=='back':content['ib']=[self.s.require('ib','ib-fictional-0')]
            else:content.update(area_name='',links=[])
            import json
            self.assertEqual(self.s.print_token(c,side),sha256(json.dumps(content,sort_keys=True,ensure_ascii=False).encode()).hexdigest())
        with patch.object(self.s,'all',wraps=self.s.all) as reads:
            self.assertEqual(self.s.mutate('revision.approve_many',{'entries':entries})['approved'],760)
        self.assertEqual(sum(c.args[0]=='maps' for c in reads.call_args_list),1)
        self.assertEqual(sum(c.args[0]=='ib' and not c.kwargs.get('deleted') for c in reads.call_args_list),1)
        self.assertTrue(all(not self.s.require('cards',e['card_id'])[e['side']+'_revision'] for e in entries))

    def test_both_sides_approve_atomically_and_repeat_is_idempotent(self):
        entries=self.entries();result=self.s.mutate('revision.approve_many',{'entries':entries})
        self.assertEqual(result['approved'],4)
        for c in self.s.state()['cards']:
            for side in ('front','back'):self.assertFalse(c[side+'_revision']);self.assertTrue(c[side+'_approved'])
        revision=self.s.revision
        self.assertEqual(self.s.mutate('revision.approve_many',{'entries':entries})['approved'],0)
        self.assertEqual(self.s.revision,revision)
    def test_stale_front_rejects_entire_batch(self):
        entries=self.entries();c=self.s.require('cards',self.ids[-1]);self.s.mutate('card.save',dict(c,name='Ændret efter print'))
        with self.assertRaisesRegex(ValueError,'Printgrundlaget'):self.s.mutate('revision.approve_many',{'entries':entries})
        self.assertTrue(all(c['front_revision'] and c['back_revision'] for c in self.s.state()['cards']))
    def test_back_change_blocks_back_but_not_front(self):
        entries=self.entries()
        with self.s.transaction():self.s.put('ib',{'id':'fictional','card_id':self.ids[0],'road':'Prøvevej','number':'2','date_text':'november'})
        front=[e for e in entries if e['side']=='front'];back=[e for e in entries if e['side']=='back']
        with self.assertRaisesRegex(ValueError,'Printgrundlaget'):self.s.mutate('revision.approve_many',{'entries':back})
        self.assertEqual(self.s.mutate('revision.approve_many',{'entries':front})['approved'],2)
    def test_invalid_and_duplicate_selections_leave_cards_unchanged(self):
        e=self.entries()[0]
        for entries in ([],None,[e,e],[dict(e,side='both')],[dict(e,token='incorrect')]):
            with self.assertRaises(ValueError):self.s.mutate('revision.approve_many',{'entries':entries})
        self.assertTrue(self.s.require('cards',self.ids[0])['front_revision'])
    def test_permissions_require_ib_visibility_only_for_backs(self):
        user={'id':'fictional','permissions':{'cards.view','cards.edit'}}
        with self.assertRaises(PermissionError):
            mutation(user,'revision.approve_many',{'entries':self.entries(('front',))},self.s)
        user['permissions']={'cards.view','print.approve'}
        mutation(user,'revision.approve_many',{'entries':self.entries(('front',))},self.s)
        with self.assertRaises(PermissionError):mutation(user,'revision.approve_many',{'entries':self.entries(('back',))},self.s)
        user['permissions'].add('ib.view');mutation(user,'revision.approve_many',{'entries':self.entries()},self.s)
    def test_saved_profile_does_not_invalidate_printed_content(self):
        entries=self.entries();self.s.mutate('print.profile.save',{'side':'front','profile':{'orientation':'landscape','paper':'a4','mode':'full','width':146,'height':94,'x':0,'y':0}})
        self.assertEqual(self.s.mutate('revision.approve_many',{'entries':entries})['approved'],4)
