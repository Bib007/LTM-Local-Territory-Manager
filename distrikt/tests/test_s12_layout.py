"""Synthetic S-12 template settings: no real congregation data."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store

def preset():
    return {k:{'x':0.0,'y':0.0,'scale':1.0} for k in ('title','number','streets','qr')}

class S12LayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Store(self.tmp.name)
        self.profile={'orientation':'landscape','paper':'a4','mode':'full',
                      'width':146,'height':94,'x':0,'y':0,
                      's12_layout':{'da':preset(),'en':preset()}}
    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()
    def save(self):
        return self.store.mutate('print.profile.save',{'side':'front','profile':self.profile})
    def test_language_presets_are_retained_in_private_backup_ready_settings(self):
        self.profile['s12_layout']['da']['title']['x']=1.5
        self.profile['s12_layout']['en']['number']['y']=-1.5
        self.save()
        stored=self.store.require('settings','config')['print_profiles']['front']
        self.assertEqual(stored['s12_layout']['da']['title']['x'],1.5)
        self.assertEqual(stored['s12_layout']['en']['number']['y'],-1.5)
        self.assertEqual(self.store.state()['settings']['print_profiles']['front']['s12_layout'],stored['s12_layout'])
        self.assertNotIn('s12_layout',self.store.require('settings','config').get('print_profiles',{}).get('back',{}))
    def test_reject_out_of_bounds_nonfinite_and_qr_resizing(self):
        for field,dimension,value in [('title','x',2.1),('streets','scale',1.06),('qr','scale',1.01),('number','y',float('nan'))]:
            self.profile['s12_layout']['da'][field][dimension]=value
            with self.assertRaises(ValueError):
                self.save()
            self.profile['s12_layout']['da'][field][dimension]=1.0 if dimension=='scale' else 0.0
        self.assertNotIn('print_profiles',self.store.require('settings','config'))
    def test_legacy_front_profile_still_works(self):
        self.profile.pop('s12_layout')
        self.save()
        self.assertNotIn('s12_layout',self.store.require('settings','config')['print_profiles']['front'])

if __name__=='__main__':unittest.main()
