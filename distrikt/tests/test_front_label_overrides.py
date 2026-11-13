"""All data invented: display-only DAR overrides, persistence and conflict protection."""
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))

from store import Store
from geography import street_rows
from front_labels import token
from profile_policy import ACTIONS,require
from portable import snapshot,Restores
from readable_export import tables
from sharing import Publications,fingerprint


def address(ident,road,number,count=1):
    return {'id':'dar:fictional-'+ident,'entity':'address','source':'DAR / Datafordeleren',
            'road':road,'number':number,'postcode':'7000','count':count,
            'type':'Hus','lng':9.76,'lat':55.56,'label':road+' '+number+', 7000'}


class FrontLabelOverrideTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.tmp.name)/'source')
        self.ident=self.store.mutate('card.save',{'number':'F-FAKE-101','temporary':True,'kind':'By'})['id']
        self.members=[address('1','Fiktivvej','2'),address('2','Fiktivvej','4')]
        self.replace_members(self.members)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def replace_members(self,members):
        with self.store.transaction():
            card=self.store.require('cards',self.ident)
            card['geo_addresses']=members
            card['address_ids']=[a['id'] for a in members]
            card['addresses']=street_rows(members)
            card['temporary']=False
            self.store.put('cards',card)

    def view(self):
        return next(c for c in self.store.state()['cards'] if c['id']==self.ident)

    def save(self,road='Ny Fiktivvej',numbers=None,expected=None):
        row=self.view()['front_addresses'][0]
        return self.store.mutate('card.front_labels.save',{
            'card_id':self.ident,'expected_token':expected or token(self.store.require('cards',self.ident)),
            'rows':[{'source_ids':row['source_ids'],'road':road,'numbers':numbers}]})

    def test_dar_is_original_and_custom_print_is_separate(self):
        before=self.view()
        self.assertEqual(before['front_addresses'][0]['road'],'Fiktivvej')
        original_geo=self.store.require('cards',self.ident)['geo_addresses']
        self.save('Egen Vej','2A–8B (lige)')
        card=self.view()
        line=card['front_addresses'][0]
        self.assertEqual(line['road'],'Fiktivvej')
        self.assertEqual(line['extra_road'],'Egen Vej')
        self.assertEqual(line['extra_numbers'],'2A–8B (lige)')
        self.assertEqual(line['numbers'],'2–4 (lige)')
        self.assertEqual(self.store.require('cards',self.ident)['geo_addresses'],original_geo)
        self.assertTrue(card['front_revision'])
        self.assertNotEqual(before['front_print_token'],card['front_print_token'])
        self.save(None,None)
        self.assertEqual(self.view()['front_addresses'][0]['extra_road'],'')
        self.assertEqual(self.view()['front_addresses'][0]['extra_numbers'],'')
        self.assertEqual(self.view()['front_addresses'][0]['road'],'Fiktivvej')
        self.assertEqual(self.store.require('cards',self.ident)['front_line_overrides'],[])

    def test_refresh_and_dar_rename_preserve_manual_overrides(self):
        self.save('Manuelt vejnavn')
        self.replace_members([address('1','Omdøbt DAR-vej','2'),
                              address('2','Omdøbt DAR-vej','4'),
                              address('3','Omdøbt DAR-vej','6')])
        line=self.view()['front_addresses'][0]
        self.assertEqual(line['road'],'Omdøbt DAR-vej')
        self.assertEqual(line['extra_road'],'Manuelt vejnavn')
        self.assertEqual(line['extra_numbers'],'')
        self.store.close()
        self.store=Store(Path(self.tmp.name)/'source')
        self.assertEqual(self.view()['front_addresses'][0]['extra_road'],'Manuelt vejnavn')
        self.assertEqual(self.store.require('cards',self.ident)['front_line_overrides'][0]['dar_road'],'Fiktivvej')

    def test_split_is_pending_not_silently_moved_to_wrong_road(self):
        self.save('Bevar min tekst')
        self.replace_members([address('1','Fiktivvej','2'),address('2','Anden fiktiv vej','4')])
        card=self.view()
        self.assertEqual(card['front_label_unmatched'],1)
        self.assertEqual({r['extra_road'] for r in card['front_addresses']},
                         {''})
        self.assertEqual(len(self.store.require('cards',self.ident)['front_line_overrides']),1)

    def test_unmatched_overrides_require_explicit_reset(self):
        self.save('Fiktiv manuel tekst')
        self.replace_members([address('1','Fiktivvej','2'),address('2','Anden vej','4')])
        card=self.view()
        self.assertEqual(card['front_label_unmatched'],1)
        rows=[{'source_ids':row['source_ids'],'road':None,'numbers':None}
              for row in card['front_addresses']]
        self.store.mutate('card.front_labels.save',{
            'card_id':self.ident,'expected_token':card['front_labels_token'],'rows':rows})
        self.assertEqual(self.view()['front_label_unmatched'],1)
        card=self.view()
        self.store.mutate('card.front_labels.save',{
            'card_id':self.ident,'expected_token':card['front_labels_token'],
            'rows':rows,'clear_unmatched':True})
        self.assertEqual(self.view()['front_label_unmatched'],0)
        self.assertEqual(self.store.require('cards',self.ident)['front_line_overrides'],[])

    def test_stale_save_rejected_and_no_overwrite(self):
        original=self.view()['front_labels_token']
        self.save('Version A',expected=original)
        with self.assertRaisesRegex(ValueError,'ændret'):
            self.save('Version B',expected=original)
        self.assertEqual(self.view()['front_addresses'][0]['extra_road'],'Version A')

    def test_reject_controls_wrong_source_and_excessive_length(self):
        original=self.store.require('cards',self.ident)
        base=self.view()
        for road in ('', 'X'*121,'falsk'+chr(10)+'vej','skjult'+chr(0x202e)+' vej',42):
            with self.subTest(road=repr(road)):
                with self.assertRaises(ValueError):
                    self.save(road)
        with self.assertRaises(ValueError):
            self.store.mutate('card.front_labels.save',{
                'card_id':self.ident,'expected_token':base['front_labels_token'],
                'rows':[{'source_ids':['dar:fictional-UNRELATED'],'road':'X','numbers':None}]})
        self.assertEqual(self.store.require('cards',self.ident),original)

    def test_permission_must_allow_front_text(self):
        required=ACTIONS['card.front_labels.save']
        with self.assertRaises(PermissionError):require({'cards.view'},required)
        require({'cards.view','cards.front_text'},required)

    def test_backup_readable_export_and_public_fingerprint(self):
        before=fingerprint(self.store,self.store.require('cards',self.ident))
        self.save('Eksporteret Fiktivvej','2–4')
        after=fingerprint(self.store,self.store.require('cards',self.ident))
        self.assertNotEqual(before,after,'Manual edits must invalidate previously published cards')
        recipe=Publications(self.store).prepare(self.ident)
        line=recipe['card']['front_addresses'][0]
        self.assertEqual((line['road'],line['numbers']),('Fiktivvej','2–4 (lige)'))
        self.assertEqual((line['extra_road'],line['extra_numbers']),('Eksporteret Fiktivvej','2–4'))
        self.assertNotIn('geo_addresses',recipe['card'])
        archive=tables(self.store.state(),self.store.all('geo'))
        text=archive['CSV/forsidetekster.csv'].decode('utf-8-sig')
        self.assertIn('vist_vej;viste_numre',text)
        self.assertIn('Fiktivvej – Eksporteret Fiktivvej',text)
        self.assertIn('2–4 (lige) – 2–4',text)
        target=Store(Path(self.tmp.name)/'target')
        try:
            restorer=Restores(target,'fictional')
            backup=snapshot(self.store,'fictional')
            self.assertIsInstance(backup,bytes)
            with zipfile.ZipFile(io.BytesIO(backup)) as z:self.assertIn('kort.sqlite3',z.namelist())
            plan=restorer.preview(backup)
            restorer.apply(plan['token'])
            self.assertEqual(target.get('cards',self.ident)['front_line_overrides'],
                             self.store.get('cards',self.ident)['front_line_overrides'])
        finally:target.close()


if __name__=='__main__':unittest.main()
