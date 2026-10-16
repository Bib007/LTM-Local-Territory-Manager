"""Local user workflows, independent print settings and atomic new-person issue."""
import sys
import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store,MODULES

class WorkflowTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def card(self):return self.s.mutate('card.save',{'number':'120','temporary':True})['id']
    def profile(self,side='front'):
        return {'orientation':'landscape' if side=='front' else 'portrait','paper':'cut','mode':'data','width':146 if side=='front' else 94,'height':94 if side=='front' else 146,'x':1.5,'y':-2}
    def test_print_profiles_are_independent_persistent_and_keep_private_records(self):
        c=self.card();l=self.s.mutate('loan.issue',{'card_id':c,'publisher_name':'Fiktiv person','initial':True,'date':date.today().isoformat()})['id']
        self.s.mutate('ib.save',{'card_id':c,'road':'Eksempelvej','number':'1','date':date.today().isoformat()})
        before={m:self.s.all(m) for m in ['cards','publishers','loans','ib']}
        for side in ['front','back']:self.s.mutate('print.profile.save',{'side':side,'profile':self.profile(side)})
        self.s.close();self.s=Store(self.tmp.name)
        self.assertEqual(self.s.get('settings','config')['print_profiles']['front']['width'],146)
        self.assertEqual(self.s.get('settings','config')['print_profiles']['back']['width'],94)
        self.assertEqual({m:self.s.all(m) for m in before},before)
        self.assertEqual(self.s.active_loan(c)['id'],l)
        self.assertEqual(len(list(Path(self.tmp.name).glob('*.sqlite3'))),len(MODULES))
    def test_invalid_profile_rolls_back_and_cannot_inject_print_css(self):
        cfg=self.s.get('settings','config')
        for key,value in [('width',float('nan')),('height',400),('x','0; color:red'),('paper','external'),('orientation','portrait')]:
            profile=self.profile();profile[key]=value
            with self.assertRaises(ValueError):self.s.mutate('print.profile.save',{'side':'front','profile':profile})
            self.assertEqual(self.s.get('settings','config'),cfg)
    def test_settings_changes_preserve_saved_profiles(self):
        self.s.mutate('print.profile.save',{'side':'front','profile':self.profile()})
        self.s.mutate('settings.save',{'folder_minimum':10,'rural_minimum':2,'rural_mode':'manual','congregation':'Test'})
        self.assertEqual(self.s.get('settings','config')['print_profiles']['front']['x'],1.5)
    def test_known_completion_changes_no_placement_and_keeps_latest_when_backdated(self):
        c=self.card();self.s.mutate('folder.set',{'ids':[c],'in_folder':True})
        day=date.today().isoformat();self.s.mutate('completion.record',{'card_id':c,'date':day})
        self.s.mutate('completion.record',{'card_id':c,'date':'2000-01-01'})
        self.assertEqual(self.s.get('cards',c)['last_completed'],day);self.assertTrue(self.s.get('cards',c)['in_folder'])
        self.assertEqual(len(self.s.all('completions')),2);self.assertEqual(self.s.all('loans'),[])
        with self.assertRaises(ValueError):self.s.mutate('completion.record',{'card_id':c,'date':day})
    def test_active_card_uses_loan_completion_instead_of_unrelated_manual_event(self):
        c=self.card();self.s.mutate('loan.issue',{'card_id':c,'publisher_name':'Testperson','initial':True,'date':date.today().isoformat()})
        with self.assertRaises(ValueError):self.s.mutate('completion.record',{'card_id':c,'date':date.today().isoformat()})
        self.assertEqual(self.s.all('completions'),[])
    def test_geographic_card_rejects_manual_list_drift_but_keeps_metadata_editable(self):
        from test_geography import address
        self.s.mutate('geo.import',{'records':[address('a1'),address('a2','3')],'source':'Test','label':'Fiktive adresser'})
        c=self.s.mutate('geo.assign',{'number':'120','address_ids':['a1']})['id']
        before=self.s.get('cards',c)
        edited=dict(before,addresses=[dict(before['addresses'][0],count=12)])
        with self.assertRaises(ValueError):self.s.mutate('card.save',edited)
        self.assertEqual(self.s.get('cards',c),before)
        self.s.mutate('card.save',dict(before,name='Ny lokal beskrivelse'))
        self.assertEqual(self.s.get('cards',c)['address_ids'],['a1'])
        self.s.mutate('geo.assign',{'card_id':c,'address_ids':['a1','a2']})
        self.assertEqual(self.s.get('cards',c)['addresses'][0]['count'],2)
        self.assertEqual(self.s.geo_state()['status']['a2']['card_id'],c)

    def test_person_and_issue_commit_together_and_name_reuses_existing(self):
        c=self.card();future=(date.today()+timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):self.s.mutate('loan.issue',{'card_id':c,'publisher_name':'Skal rulles tilbage','initial':True,'date':future})
        self.assertEqual(self.s.all('publishers'),[]);self.assertEqual(self.s.all('loans'),[])
        pid=self.s.mutate('publisher.save',{'name':'Testperson'})['id']
        l=self.s.mutate('loan.issue',{'card_id':c,'publisher_name':'  TESTPERSON  ','initial':True,'date':date.today().isoformat()})['id']
        self.assertEqual(self.s.get('loans',l)['publisher_id'],pid);self.assertEqual(len(self.s.all('publishers')),1)

if __name__=='__main__':unittest.main()
