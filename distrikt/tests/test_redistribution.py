"""Explicit transfer/interim lifecycle with only temporary fictional records."""
import copy
from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from portable import snapshot,Restores
from redistribution import planning_date
from test_geography import address


class RedistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=Store(self.tmp.name);self.addCleanup(lambda:self.s.close())
        area=self.s.mutate('area.save',{'name':'Fictional area'})['id']
        records=[address('s'+str(i),str(i+1),lng=10+i*.001) for i in range(4)]+[address('t'+str(i),str(i+101),lng=10.02+i*.001) for i in range(2)]
        self.s.mutate('geo.import',{'records':records,'source':'Fictional','label':'Fictional local data'})
        self.source=self.s.mutate('geo.assign',{'number':'101','address_ids':['s0','s1','s2','s3']})['id']
        self.target=self.s.mutate('geo.assign',{'number':'102','address_ids':['t0','t1']})['id']
        for ident,day in [(self.source,'2026-03-02'),(self.target,'2026-01-02')]:
            c=self.s.require('cards',ident);self.s.mutate('card.save',{**c,'area_id':area})
            self.s.mutate('completion.record',{'card_id':ident,'date':day})
        self.data={'mode':'transfer','ids':[self.source,self.target],'address_ids':['s0','s1'],'number':'102'}

    def put(self,module,item):
        with self.s.transaction():self.s.put(module,item)

    def records(self):return {m:copy.deepcopy(self.s.all(m)) for m in ('cards','loans','completions','ib','notes')}
    def preview(self,data=None):return self.s.mutate('card.restructure.preview',data or self.data)
    def apply(self,data=None,preview=None):
        data=data or self.data;preview=preview or self.preview(data)
        return self.s.mutate('card.restructure.apply',{**data,'expected':preview['expected'],'confirm':'ÆNDR KORT'})

    def test_preview_is_read_only_and_transfer_preserves_actual_history_and_note_owner(self):
        owner='user-'+'a'*32
        note=self.s.mutate('note.save',{'card_id':self.source,'text':'Fictional assigned work','assignee_id':owner,'assignee_before':None})['id']
        ib=self.s.mutate('ib.save',{'card_id':self.source,'address_id':'s0','date':'2026-01-01'})['id']
        before=self.records();revision=self.s.revision;p=self.preview()
        self.assertEqual(self.records(),before);self.assertEqual(self.s.revision,revision)
        self.assertEqual(p['reference_date'],'2026-03-02');self.assertEqual((p['source_visits'],p['target_visits']),(2,4))
        self.apply(preview=p)
        source=self.s.require('cards',self.source);target=self.s.require('cards',self.target)
        self.assertEqual(source['address_ids'],['s2','s3']);self.assertEqual(set(target['address_ids']),{'s0','s1','t0','t1'})
        self.assertEqual(target['last_completed'],'2026-01-02');self.assertEqual(planning_date(target),'2026-03-02')
        self.assertEqual(self.s.all('completions'),before['completions']);self.assertEqual(self.s.require('ib',ib)['card_id'],self.target)
        self.assertEqual(self.s.require('notes',note)['card_id'],self.source);self.assertEqual(self.s.require('notes',note)['assignee_id'],owner)
        self.assertTrue(source['front_revision'] and source['back_revision'] and target['front_revision'] and target['back_revision'])
        self.assertTrue(any('print' in n['text'].lower() for n in self.s.all('notes') if n.get('card_id')==self.target))

    def test_intent_and_all_relevant_data_are_bound_to_confirmation(self):
        p=self.preview();before=self.records()
        for change in [{'address_ids':['s0']},{'mode':'interim','number':'103'},{'ids':[self.target,self.source]}]:
            with self.assertRaises(ValueError):self.apply({**self.data,**change},p)
            self.assertEqual(self.records(),before)
        self.s.mutate('note.save',{'card_id':self.target,'text':'New fictional note'})
        with self.assertRaises(ValueError):self.apply(preview=p)
        self.assertEqual(self.s.require('cards',self.source)['address_ids'],['s0','s1','s2','s3'])

    def test_duplicate_apply_and_wrong_confirmation_do_not_repeat_the_move(self):
        p=self.preview()
        with self.assertRaises(ValueError):self.s.mutate('card.restructure.apply',{**self.data,'expected':p['expected'],'confirm':'yes'})
        self.apply(preview=p);after=self.records()
        with self.assertRaises(ValueError):self.apply(preview=p)
        self.assertEqual(self.records(),after)

    def test_both_cards_must_still_be_in_box_at_apply(self):
        for ident in (self.source,self.target):
            p=self.preview();self.s.mutate('folder.set',{'ids':[ident],'in_folder':True})
            with self.assertRaises(ValueError):self.apply(preview=p)
            self.s.mutate('folder.set',{'ids':[ident],'in_folder':False})
        p=self.preview();self.s.mutate('loan.issue',{'card_id':self.target,'publisher_name':'Fictional person','initial':True,'date':date.today().isoformat()})
        with self.assertRaises(ValueError):self.apply(preview=p)

    def test_interim_card_can_be_issued_returned_and_finalized_without_faking_history(self):
        data={**self.data,'mode':'interim','number':'103','name':'Fictional batch'}
        target_before=copy.deepcopy(self.s.require('cards',self.target));stage=self.apply(data)['id']
        interim=self.s.require('cards',stage)
        self.assertEqual(self.s.require('cards',self.target),target_before)
        self.assertIsNone(interim['last_completed']);self.assertIn('Interim',interim['name']);self.assertEqual(interim['interim_transfer']['status'],'pending')
        finish={'mode':'finalize','ids':[stage,self.target],'address_ids':['s0','s1'],'number':'102'}
        loan=self.s.mutate('loan.issue',{'card_id':stage,'publisher_name':'Fictional interim reader','initial':True,'date':date.today().isoformat()})['id']
        with self.assertRaises(ValueError):self.preview(finish)
        self.s.mutate('loan.finish',{'id':loan,'date':date.today().isoformat(),'complete':True,'retain':True})
        with self.assertRaises(ValueError):self.preview(finish)
        self.s.mutate('loan.finish',{'id':loan,'date':date.today().isoformat(),'complete':False,'retain':False})
        history=copy.deepcopy(self.s.all('completions'));loans=copy.deepcopy(self.s.all('loans'))
        self.apply(finish)
        interim=self.s.require('cards',stage);target=self.s.require('cards',self.target)
        self.assertTrue(interim['archived']);self.assertEqual(interim['replaced_by'],self.target);self.assertEqual(interim['interim_transfer']['status'],'finalized')
        self.assertEqual(self.s.all('completions'),history);self.assertEqual(self.s.all('loans'),loans)
        self.assertEqual(target['last_completed'],'2026-01-02');self.assertEqual(planning_date(target),date.today().isoformat())
        self.assertEqual(self.s.geo_state()['status']['s0']['card_id'],self.target)

    def test_pending_interim_cannot_be_split_merged_or_silently_retargeted(self):
        stage=self.apply({**self.data,'mode':'interim','number':'103'})['id']
        for payload in [{'mode':'split','ids':[stage],'address_ids':['s0'],'number':'104'}, {'mode':'merge','ids':[self.target,self.source],'number':'104'}, {'mode':'finalize','ids':[stage,self.source],'address_ids':['s0','s1']}]:
            with self.assertRaises(ValueError):self.preview(payload)

    def test_ambiguous_ib_duplicate_membership_and_changed_geo_are_rejected(self):
        ib=self.s.mutate('ib.save',{'card_id':self.source,'road':'Fictional road','number':'99','date':'2026-01-01'})['id']
        with self.assertRaisesRegex(ValueError,'adressekobling'):self.preview()
        self.s.mutate('delete',{'module':'ib','id':ib})
        other=self.s.mutate('card.save',{'number':'104','temporary':True})['id'];c=self.s.require('cards',other);c['address_ids']=['s0'];self.put('cards',c)
        with self.assertRaises(ValueError):self.preview()
        self.s.mutate('delete',{'module':'cards','id':other})
        a=self.s.require('geo','s0');a['count']=2;self.put('geo',a)
        with self.assertRaisesRegex(ValueError,'Adressedata'):self.preview()

    def test_transfer_rollback_covers_cards_ib_and_followup_tasks(self):
        before=self.records();revision=self.s.revision;original=self.s.put
        def fail(module,item):
            if module=='notes' and item.get('entity')!='activity':raise RuntimeError('Fictional write failure')
            return original(module,item)
        with patch.object(self.s,'put',side_effect=fail):
            with self.assertRaises(RuntimeError):self.apply()
        self.assertEqual(self.records(),before);self.assertEqual(self.s.revision,revision)

    def test_reference_and_pending_workflow_survive_local_backup(self):
        stage=self.apply({**self.data,'mode':'interim','number':'103'})['id']
        payload=snapshot(self.s,'1.12.4');restores=Restores(self.s,'1.12.4');preview=restores.preview(payload);restores.apply(preview['token'])
        self.assertEqual(self.s.require('cards',stage)['interim_transfer']['target_id'],self.target)
        self.apply({'mode':'finalize','ids':[stage,self.target],'address_ids':['s0','s1']})
        self.assertEqual(planning_date(self.s.require('cards',self.target)),'2026-03-02')

    def test_reference_is_ignored_after_unrelated_membership_changes(self):
        self.apply();card=self.s.require('cards',self.target)
        self.assertEqual(planning_date(card),'2026-03-02')
        card['address_ids']=card['address_ids'][:-1]
        self.assertEqual(planning_date(card),'2026-01-02')

    def test_whole_source_invalid_types_and_unknown_counts_never_move(self):
        for selected in [[],['s0']*2,['s0','s1','s2','s3'],['outside'],[{}]]:
            with self.assertRaises(ValueError):self.preview({**self.data,'address_ids':selected})
        c=self.s.require('cards',self.source);c['addresses'][0]['count_unknown']=True;self.put('cards',c)
        with self.assertRaises(ValueError):self.preview()


if __name__=='__main__':unittest.main()
