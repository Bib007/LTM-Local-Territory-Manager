import sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from portable import snapshot,Restores
from sharing import fingerprint


class WorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
 def tearDown(self):self.s.close();self.temp.cleanup()
 def card(self,number='1'):
  return self.s.mutate('card.save',{'number':number,'temporary':True})['id']
 def geo_card(self,number='1',offset=0):
  records=[{'entity':'address','id':number+'a'+str(i),'road':'Fiktiv vej '+number,'number':str(i),'postcode':'9999','lng':10+offset+i*.001,'lat':55+i*.001,'count':1} for i in range(1,5)]
  self.s.mutate('geo.import',{'records':records,'source':'DAR / Datafordeleren','label':'Fiktiv test'})
  c=self.s.mutate('geo.assign',{'number':number,'address_ids':[a['id'] for a in records]})['id'];return c,records
 def test_general_notes_tasks_and_private_activity(self):
  n=self.s.mutate('note.save',{'text':'Fiktiv generel opgave','task':True})['id']
  self.assertIsNone(self.s.get('notes',n)['card_id'])
  self.s.mutate('note.resolve',{'id':n,'resolved':True});self.assertTrue(self.s.get('notes',n)['resolved'])
  self.assertEqual(len(self.s.state()['notes']),1);self.assertTrue(self.s.activity());self.assertNotIn('Fiktiv generel',str(self.s.activity()))
 def test_note_to_task_keeps_text(self):
  c=self.card();n=self.s.mutate('note.save',{'card_id':c,'text':'Fiktiv note'})['id']
  self.s.mutate('note.task',{'id':n});self.assertTrue(self.s.get('notes',n)['task'])
 def test_cross_tab_revision_rejection_is_paused_until_profiles(self):
  rev=self.s.revision;c=self.card()
  self.s.mutate('card.save',{'id':c,'number':'99','temporary':True,'_revision':rev})
  self.assertEqual(self.s.get('cards',c)['number'],'99')
 def test_undo_folder_then_redo_not_available(self):
  c=self.card();self.s.mutate('folder.set',{'ids':[c],'in_folder':True});self.assertTrue(self.s.state()['undo_available'])
  self.s.mutate('workflow.undo',{});self.assertFalse(self.s.get('cards',c)['in_folder']);self.assertFalse(self.s.state()['undo_available'])
 def test_undo_loan_finish_restores_loan_completion_and_note(self):
  c=self.card();p=self.s.mutate('publisher.save',{'name':'Fiktiv person'})['id'];l=self.s.mutate('loan.issue',{'card_id':c,'publisher_id':p,'initial':True,'date':'2026-01-01'})['id']
  self.s.mutate('loan.finish',{'id':l,'complete':True,'date':'2026-02-01','note':'Fiktiv rettelse'})
  self.s.mutate('workflow.undo',{});self.assertIsNone(self.s.get('loans',l)['returned']);self.assertEqual(self.s.all('completions'),[]);self.assertEqual(self.s.state()['notes'],[])
 def test_undo_expires_and_does_not_store_ib_values_in_activity(self):
  c=self.card();self.s.mutate('ib.save',{'card_id':c,'road':'PRIVATE_STREET','number':'PRIVATE_NUMBER','date':'2026-01-01'})
  self.assertNotIn('PRIVATE',str(self.s.activity()));self.s._undo['until']=time.monotonic()-1
  with self.assertRaises(ValueError):self.s.mutate('workflow.undo',{})
 def test_saved_filters_persist_and_do_not_become_areas(self):
  self.s.mutate('filter.save',{'name':'Landkort','view':{'page':'Distrikter','kind':'Land','status':'Kort i kassen'}})
  self.assertEqual(self.s.state()['areas'],[]);self.assertEqual(self.s.state()['settings']['saved_views'][0]['name'],'Landkort')
 def test_geo_cache_reused_and_invalidated(self):
  c,records=self.geo_card();one=self.s.geo_state();two=self.s.geo_state();self.assertIs(one,two)
  self.s.mutate('card.color',{'card_id':c,'map_color':'#112233'});self.assertIsNot(one,self.s.geo_state())
 def test_new_changed_retired_addresses_need_review(self):
  c,records=self.geo_card();changed=dict(records[0],lng=10.9);new=dict(records[0],id='new-one',number='99');r=[changed,records[1],records[2],new]
  self.s.mutate('geo.import',{'records':r,'source':'DAR / Datafordeleren','label':'Opdatering','complete_road':{'road':records[0]['road'],'postcode':'9999'},'review_changes':True})
  changes=self.s.geo_state()['changes'];self.assertEqual({a['kind'] for a in changes},{'new','changed','retired'})
  self.assertNotEqual(self.s.get('geo',records[0]['id'])['lng'],10.9);self.assertIsNone(self.s.get('geo','new-one'));self.assertFalse(self.s.get('geo',records[3]['id']).get('retired',False))
  item=next(a for a in changes if a['kind']=='changed');self.s.mutate('address.change.review',{'id':item['id'],'decision':'accept'})
  self.assertEqual(self.s.get('geo',records[0]['id'])['lng'],10.9);self.assertNotEqual(self.s.get('cards',c)['geo_addresses'][0]['lng'],10.9)
 def test_split_requires_preview_confirmation_and_preserves_ib_and_history(self):
  c,records=self.geo_card();self.s.mutate('completion.record',{'card_id':c,'date':'2026-01-01'});self.s.mutate('ib.save',{'card_id':c,'address_id':records[0]['id'],'date':'2026-01-01'})
  payload={'mode':'split','ids':[c],'number':'2','address_ids':[records[0]['id'],records[1]['id']]};p=self.s.mutate('card.restructure.preview',payload)
  with self.assertRaises(ValueError):self.s.mutate('card.restructure.apply',dict(payload,expected=p['expected'],confirm='yes'))
  new=self.s.mutate('card.restructure.apply',dict(payload,expected=p['expected'],confirm='ÆNDR KORT'))['id']
  self.assertEqual(len(self.s.get('cards',c)['address_ids']),2);self.assertEqual(self.s.all('ib')[0]['card_id'],new);self.assertEqual(self.s.all('completions')[0]['card_id'],c);self.assertIsNone(self.s.get('cards',new)['last_completed'])
 def test_split_refuses_unlinked_ib(self):
  c,r=self.geo_card();self.s.mutate('ib.save',{'card_id':c,'road':'Fiktiv vej','number':'1','date':'2026-01-01'})
  with self.assertRaisesRegex(ValueError,'adressekobling'):self.s.mutate('card.restructure.preview',{'mode':'split','ids':[c],'number':'2','address_ids':[r[0]['id']]})
 def test_merge_archives_sources_without_stealing_history(self):
  a,ra=self.geo_card('1');b,rb=self.geo_card('2',.02);self.s.mutate('completion.record',{'card_id':a,'date':'2026-01-01'})
  oldfp=fingerprint(self.s,self.s.get('cards',a));data={'mode':'merge','ids':[a,b],'number':'3'};p=self.s.mutate('card.restructure.preview',data)
  new=self.s.mutate('card.restructure.apply',dict(data,expected=p['expected'],confirm='ÆNDR KORT'))['id'];state=self.s.state()
  self.assertEqual([c['id'] for c in state['cards']],[new]);self.assertEqual(len(state['archived_cards']),2);self.assertNotEqual(oldfp,fingerprint(self.s,self.s.get('cards',a)))
  self.assertEqual(len(self.s.get('cards',new)['address_ids']),8);self.assertEqual(self.s.all('completions')[0]['card_id'],a)
  self.assertEqual(self.s.geo_state()['status'][ra[0]['id']]['card_id'],new)
 def test_restructure_refuses_outstanding_loans(self):
  c,r=self.geo_card();self.s.mutate('loan.issue',{'card_id':c,'publisher_name':'Fiktiv','date':'2026-01-01','initial':True})
  with self.assertRaisesRegex(ValueError,'Aflever'):self.s.mutate('card.restructure.preview',{'mode':'split','ids':[c],'number':'2','address_ids':[r[0]['id']]})
 def test_general_notes_activity_and_filters_backup_restore(self):
  self.s.mutate('note.save',{'text':'Fiktiv generel opgave','task':True});data=snapshot(self.s,'1.10.0');restore=Restores(self.s,'1.10.0');p=restore.preview(data);restore.apply(p['token']);self.assertEqual(len(self.s.state()['notes']),1);self.assertTrue(self.s.activity())
 def test_note_changes_keep_geographic_cache_but_reject_updates_clear_it(self):
  c,r=self.geo_card();one=self.s.geo_state();self.s.mutate('note.save',{'text':'Generel note'});self.assertIs(one,self.s.geo_state())
  self.s.mutate('geo.import',{'records':[dict(r[0],lng=10.9)],'label':'Opdatering','source':'DAR / Datafordeleren','review_changes':True});self.assertEqual(len(self.s.geo_state()['changes']),1)
  self.s.mutate('address.change.review',{'id':'change:'+r[0]['id'],'decision':'reject'});self.assertEqual(self.s.geo_state()['changes'],[])
 def test_original_s13_has_standalone_completion_and_archived_history(self):
  from pdf_export import allocation_rows
  c=self.card();self.s.mutate('completion.record',{'card_id':c,'date':'2026-10-01'});state=self.s.state();rows=allocation_rows(state,2027)
  self.assertEqual(rows[0]['allocations'][0],{'person':'','assigned':None,'completed':'2026-10-01'})
  state['archived_cards']=state['cards'];state['cards']=[];self.assertEqual(allocation_rows(state,2027),rows)
