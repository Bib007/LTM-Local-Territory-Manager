import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store

class CardNotesTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
  self.c=self.s.mutate('card.save',{'number':'120','temporary':True})['id']
  self.l=self.s.mutate('loan.issue',{'card_id':self.c,'publisher_name':'Fiktiv person','date':'2026-01-01','initial':True})['id']
 def tearDown(self):self.s.close();self.tmp.cleanup()
 def finish(self,**extra):return self.s.mutate('loan.finish',dict(id=self.l,date='2026-02-01',complete=True,retain=False,**extra))
 def test_finish_note_atomic_local_and_does_not_create_ib(self):
  self.finish(note='Tilføj IB på nr. 42')
  n=self.s.state()['notes'][0];self.assertEqual(n['card_id'],self.c);self.assertEqual(n['loan_id'],self.l);self.assertEqual(n['text'],'Tilføj IB på nr. 42')
  self.assertFalse(n['resolved']);self.assertFalse(self.s.state()['ib']);self.assertFalse(self.s.get('cards',self.c)['in_folder'])
  self.s.close();self.s=Store(self.tmp.name);self.assertEqual(self.s.state()['notes'][0],n)
 def test_invalid_note_rolls_back_finish(self):
  with self.assertRaises(ValueError):self.finish(note='x'*1001)
  self.assertFalse(self.s.get('loans',self.l)['returned']);self.assertFalse(self.s.state()['completions']);self.assertFalse(self.s.state()['notes'])
 def test_retain_multiple_notes_and_return_without_completion(self):
  self.s.mutate('loan.finish',{'id':self.l,'date':'2026-02-01','complete':True,'retain':True,'note':'Første note'})
  self.s.mutate('loan.finish',{'id':self.l,'date':'2026-03-01','complete':False,'retain':False,'note':'Anden note'})
  self.assertEqual(len(self.s.state()['notes']),2);self.assertEqual(len(self.s.state()['completions']),1)
 def test_edit_resolve_reopen_and_delete_restore_with_card(self):
  self.finish(note='Testnote');n=self.s.state()['notes'][0]
  self.s.mutate('note.save',{'id':n['id'],'card_id':self.c,'text':'Rettet note'})
  self.s.mutate('note.resolve',{'id':n['id'],'resolved':True});self.assertTrue(self.s.get('notes',n['id'])['resolved'])
  self.s.mutate('note.resolve',{'id':n['id'],'resolved':False});self.assertFalse(self.s.get('notes',n['id'])['resolved'])
  result=self.s.mutate('delete',{'module':'cards','id':self.c});self.assertFalse(self.s.state()['notes'])
  self.s.mutate('restore',{'batch':result['batch']});self.assertEqual(self.s.state()['notes'][0]['text'],'Rettet note')
 def test_manual_completion_note_and_no_note_no_extra_record(self):
  self.finish();self.assertFalse(self.s.state()['notes'])
  self.s.mutate('completion.record',{'card_id':self.c,'date':'2026-03-01','note':'Tjek husnummer 7'})
  self.assertEqual(len(self.s.state()['notes']),1)
