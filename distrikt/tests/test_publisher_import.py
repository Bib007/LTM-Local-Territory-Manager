"""Fictional group lists and existing identities; no accounts or external files."""
from copy import deepcopy
import base64
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from card_import import read_rows
from publisher_import import template_xlsx


class PublisherImportTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
    def tearDown(self):self.s.close();self.temp.cleanup()
    def preview(self,text):return self.s.mutate('setup.publisher-import.preview',{'name':'fiktiv.csv','content':text})
    def apply(self,p,confirm='IMPORTÉR GRUPPER'):return self.s.mutate('setup.publisher-import.apply',{'token':p['token'],'confirm':confirm})
    def person(self,name,**values):return self.s.mutate('publisher.save',{'name':name,**values})['id']

    def test_blank_excel_uses_named_text_sheet_and_shared_bounded_parser(self):
        rows=read_rows({'name':'fiktiv.xlsx','content':base64.b64encode(template_xlsx()).decode()},sheet_name='Forkyndere')
        self.assertEqual(rows,[(1,['navn','tjenestegruppe','gruppefunktion','pioner'])])

    def test_reviewed_update_preserves_id_loans_history_and_unlisted_people(self):
        ident=self.person('Fiktiv A');other=self.person('Fiktiv B')
        card=self.s.mutate('card.save',{'number':'F108','temporary':True})['id']
        self.s.mutate('loan.issue',{'card_id':card,'publisher_id':ident,'date':'2026-10-01','initial':True})
        loans=deepcopy(self.s.all('loans'));before=self.s.revision
        plan=self.preview('navn;tjenestegruppe;gruppefunktion;pioner\nFiktiv A;Gruppe 01;Gruppetilsynsmand;Ja\nFiktiv C;Gruppe 01;Assistent;Nej')
        self.assertEqual((plan['new'],plan['update'],plan['invalid']),(1,1,0));self.assertEqual(self.s.revision,before)
        with self.assertRaises(ValueError):self.apply(plan,'IMPORTER')
        self.apply(plan)
        person=self.s.require('publishers',ident);self.assertEqual(person['group'],'Gruppe 01');self.assertTrue(person['pioneer'])
        self.assertEqual(person['group_role'],'overseer');self.assertIsNotNone(self.s.get('publishers',other))
        self.assertEqual(self.s.all('loans'),loans)
        expected=deepcopy(self.s.all('publishers'))
        self.s.close();self.s=Store(self.temp.name)
        self.assertEqual(self.s.all('publishers'),expected)

    def test_duplicates_bad_values_and_conflicting_group_roles_block_whole_file(self):
        for text in [
            'navn;tjenestegruppe;gruppefunktion;pioner\nFiktiv A;G1;Gruppetilsynsmand;Ja\nFiktiv B;G1;Gruppetilsynsmand;Nej',
            'navn;pioner\nFiktiv A;måske',
            'navn\nFiktiv A\nfiktiv a',
            'navn;gruppefunktion\nFiktiv A;Assistent',
        ]:
            with self.subTest(text=text):
                plan=self.preview(text);self.assertTrue(plan['invalid'] or plan['errors'])
                with self.assertRaises(ValueError):self.apply(plan)
                self.assertEqual(self.s.all('publishers'),[])

    def test_imported_function_swap_is_atomic_and_does_not_change_accounts(self):
        a=self.person('Fiktiv A',group='G1',group_role='overseer',pioneer=True)
        b=self.person('Fiktiv B',group='G1',group_role='assistant')
        plan=self.preview('navn;tjenestegruppe;gruppefunktion;pioner\nFiktiv A;G1;Assistent;Ja\nFiktiv B;G1;Gruppetilsynsmand;Nej')
        self.assertEqual(plan['errors'],[]);self.apply(plan)
        self.assertEqual(self.s.require('publishers',a)['group_role'],'assistant')
        self.assertEqual(self.s.require('publishers',b)['group_role'],'overseer')
        self.assertFalse((Path(self.temp.name)/'profiles.json').exists())

    def test_changed_publisher_list_invalidates_approval_but_unrelated_card_does_not(self):
        p=self.preview('navn\nFiktiv A');self.person('Fiktiv B')
        with self.assertRaisesRegex(ValueError,'Forkynderlisten'):self.apply(p)
        p=self.preview('navn\nFiktiv A');self.s.mutate('card.save',{'number':'F108','temporary':True});self.apply(p)
        self.assertEqual(len(self.s.all('publishers')),2)

    def test_absent_columns_preserve_existing_values_and_present_blanks_clear(self):
        ident=self.person('Fiktiv A',group='G1',group_role='assistant',pioneer=True)
        p=self.preview('navn\nFiktiv A');self.assertEqual(p['existing'],1);self.apply(p)
        self.assertTrue(self.s.require('publishers',ident)['pioneer'])
        p=self.preview('navn;tjenestegruppe;gruppefunktion;pioner\nFiktiv A;;;');self.apply(p)
        person=self.s.require('publishers',ident);self.assertEqual(person['group'],'');self.assertFalse(person['pioneer'])

    def test_storage_failure_during_second_final_write_rolls_everything_back(self):
        a=self.person('Fiktiv A',group='G1',group_role='overseer')
        b=self.person('Fiktiv B',group='G1',group_role='assistant')
        plan=self.preview('navn;tjenestegruppe;gruppefunktion\nFiktiv A;G1;Assistent\nFiktiv B;G1;Gruppetilsynsmand')
        before=deepcopy(self.s.all('publishers'));put=self.s.put
        def fail(module,item,*args,**kwargs):
            if module=='publishers' and item['id']==b and item.get('group_role')=='overseer':raise OSError('Fiktiv lagerfejl')
            return put(module,item,*args,**kwargs)
        with patch.object(self.s,'put',side_effect=fail),self.assertRaises(OSError):self.apply(plan)
        self.assertEqual(self.s.all('publishers'),before)

    def test_private_data_backup_restore_preserves_group_fields_and_identity(self):
        from portable import snapshot,Restores
        ident=self.person('Fiktiv A',group='Gruppe 01',group_role='assistant',pioneer=True)
        expected=deepcopy(self.s.require('publishers',ident));raw=snapshot(self.s,'fictional')
        self.s.mutate('publisher.save',{'id':ident,'name':'Fiktiv A','group':'Gruppe 02','group_role':'','pioneer':False})
        restores=Restores(self.s,'fictional');preview=restores.preview(raw);restores.apply(preview['token'])
        self.assertEqual(self.s.require('publishers',ident),expected)

    def test_normal_edits_validate_functions_and_allow_multiple_cards(self):
        ident=self.person('Fiktiv A',group='G1',group_role='overseer')
        with self.assertRaises(ValueError):self.person('Fiktiv B',group='g1',group_role='overseer')
        for value in ['ja',1,{},None]:
            with self.subTest(value=value),self.assertRaises(ValueError):self.person('Fiktiv B',pioneer=value)
        for number in ['F108','F109']:
            card=self.s.mutate('card.save',{'number':number,'temporary':True})['id']
            self.s.mutate('loan.issue',{'card_id':card,'publisher_id':ident,'date':'2026-10-01','initial':True})
        self.assertEqual(len(self.s.all('loans')),2)

if __name__=='__main__':unittest.main()
