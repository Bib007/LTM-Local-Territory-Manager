import base64
import io
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from sharing import Publications,Drive,SCOPE,fingerprint,public_members,png_bytes

def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
def png(extra=False):
    raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2200,1560,8,6,0,0,0))
    if extra:raw+=chunk(b'tEXt',b'note\0PRIVATE_METADATA')
    return raw+chunk(b'IDAT',zlib.compress((b'\x00'+b'\xff'*8800)*1560))+chunk(b'IEND',b'')
class FakeDrive:
    def __init__(self):self.uploads=[];self.withdrawals=[];self.fail=False
    def connected(self):return True
    def status(self):return {'connected':True,'account':'fake@example.invalid'}
    def upload(self,data,file_id=None):
        if self.fail:raise ValueError('Simuleret netfejl')
        self.uploads.append((data,file_id));return file_id or 'TEST_FILE_12345'
    def share(self,file_id):return 'https://drive.google.com/file/d/'+file_id+'/view'
    def unshare(self,file_id):
        if self.fail:raise ValueError('Simuleret netfejl')
        self.withdrawals.append(file_id)
class SharingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.png=png();cls.url='data:image/png;base64,'+base64.b64encode(cls.png).decode()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name);self.c=self.s.mutate('card.save',{'number':'120','temporary':True})['id']
        a=[{'id':'a1','road':'Fiktiv vej','number':'1','lng':10,'lat':55,'count':1},{'id':'a2','road':'Fiktiv vej','number':'3','lng':10.01,'lat':55.01,'count':1}]
        with self.s.transaction():
            c=self.s.get('cards',self.c);c.update(geo_addresses=a,geo_polygon=[[10,55],[10.02,55],[10.02,55.02]]);self.s.put('cards',c)
        self.p=Publications(self.s);self.p.drive=FakeDrive()
    def tearDown(self):self.s.close();self.temp.cleanup()
    def enqueue(self):return self.p.enqueue({'card_id':self.c,'fingerprint':self.p.prepare(self.c)['fingerprint'],'png':self.url})
    def row(self):return self.s.get('maps',self.p.key(self.c))
    def test_only_public_recipe_not_ib_names_or_notes(self):
        self.s.mutate('ib.save',{'card_id':self.c,'address_id':'a2','road':'Fiktiv vej','number':'3','date':'2026-01-01'})
        self.s.mutate('publisher.save',{'name':'PRIVATE_PUBLISHER'})
        with self.s.transaction():self.s.put('notes',{'id':'n1','card_id':self.c,'text':'PRIVATE_NOTE'})
        recipe=self.p.prepare(self.c);self.assertEqual([a['number'] for a in recipe['members']],['1']);self.assertNotIn('PRIVATE',json.dumps(recipe));self.assertNotIn('ib',recipe)
    def test_publish_queue_stable_file_and_qr(self):
        self.enqueue();self.assertEqual(self.row()['status'],'queued');self.p.process_one();first=self.row();self.assertEqual(first['status'],'published')
        self.assertEqual(self.p.drive.uploads[0][0],self.png);self.assertNotIn('queued_png',first)
        svg=self.p.qr(self.c);self.assertIn(b'viewBox',svg);self.assertIn(b'<path',svg)
        self.enqueue();self.p.process_one();self.assertEqual(self.row()['url'],first['url']);self.assertEqual(self.p.drive.uploads[-1][1],first['file_id'])
    def test_queue_survives_restart(self):
        self.enqueue();self.s.close();self.s=Store(self.temp.name);new=Publications(self.s);new.drive=FakeDrive();new.process_one();self.assertEqual(self.row()['status'],'published')
    def test_metadata_is_stripped_from_png(self):self.assertEqual(png_bytes('data:image/png;base64,'+base64.b64encode(png(True)).decode()),self.png)
    def test_rejects_bad_png_and_stale_fingerprint(self):
        for value in ['not image','data:image/png;base64,AAAA']:
            with self.assertRaises(ValueError):self.p.enqueue({'card_id':self.c,'fingerprint':self.p.prepare(self.c)['fingerprint'],'png':value})
        with self.assertRaises(ValueError):self.p.enqueue({'card_id':self.c,'fingerprint':'stale','png':self.url})
        self.assertIsNone(self.row())
    def test_bounded_retries_then_manual_retry(self):
        self.enqueue();self.p.drive.fail=True
        for i in range(5):
            with self.s.transaction():r=self.row();r['next_try']=0;self.s.put('maps',r)
            self.p.process_one()
        self.assertEqual(self.row()['status'],'failed');self.p.drive.fail=False;self.p.retry(self.c);self.p.process_one();self.assertEqual(self.row()['status'],'published')
    def test_new_ib_invalidates_pending_and_published_images(self):
        self.enqueue();self.p.process_one();self.s.mutate('ib.save',{'card_id':self.c,'road':'Fiktiv vej','number':'3','date':'2026-01-01'})
        self.assertTrue(self.p.status()['cards'][0]['outdated']);self.p.process_one();self.assertEqual(self.row()['status'],'review');self.assertEqual(self.row()['url'],'');self.assertEqual(len(self.p.drive.withdrawals),1)
        self.p.process_one();self.assertEqual(len(self.p.drive.withdrawals),1)
    def test_no_upload_of_changed_queued_image(self):
        self.enqueue();self.s.mutate('card.color',{'card_id':self.c,'map_color':'#ff00ff'});self.p.process_one();self.assertEqual(self.row()['status'],'review');self.assertEqual(self.p.drive.uploads,[])
    def test_failed_withdrawal_is_visible_and_bounded(self):
        self.enqueue();self.p.process_one();self.s.mutate('card.color',{'card_id':self.c,'map_color':'#ff00ff'});self.p.drive.fail=True
        for i in range(5):
            with self.s.transaction():r=self.row();r['next_try']=0;self.s.put('maps',r)
            self.p.process_one()
        self.assertEqual(self.row()['status'],'withdraw_failed');self.assertTrue(self.row()['url'])
    def test_private_withdraw_and_no_image_in_state(self):
        self.enqueue();self.assertEqual(self.s.state()['maps'],[]);self.assertNotIn('queued_png',json.dumps(self.p.status()))
        self.p.process_one();self.p.withdraw(self.c);self.assertEqual(self.row()['status'],'private');self.assertEqual(self.row()['url'],'')
        with self.assertRaises(ValueError):self.p.qr(self.c)
    def test_disconnect_never_silently_deletes_remote_files(self):
        drive=Drive(self.temp.name);drive.path.write_text('{"refresh_token":"PRIVATE"}')
        with patch('sharing.request',side_effect=AssertionError('no network')):drive.disconnect()
        self.assertFalse(drive.connected())
    def test_failed_oauth_does_not_replace_existing_credentials(self):
        drive=Drive(self.temp.name);drive.path.write_text('{"refresh_token":"OLD_PRIVATE"}')
        with patch('sharing.request',side_effect=ValueError('fake auth failure')):
            with self.assertRaises(ValueError):drive.connect({'client_id':'test.apps.googleusercontent.com','client_secret':'TEST','refresh_token':'NEW'})
        self.assertIn('OLD_PRIVATE',drive.path.read_text())
    def test_api_upload_reuses_existing_file_and_minimum_permissions(self):
        d=Drive(self.temp.name);calls=[]
        def api(path,data=None,method=None,content_type=None,upload=False):
            calls.append((path,data,method,content_type,upload))
            if 'permissions?' in path:return {'permissions':[]}
            if 'fields=id,webViewLink' in path:return {'id':'FILE123','webViewLink':'https://drive.google.com/file/d/FILE123/view','resourceKey':'secretkey'}
            return {'id':'FILE123'}
        d.api=api;ident=d.upload(self.png,'FILE123');self.assertEqual(ident,'FILE123');self.assertTrue(calls[0][-1]);self.assertIn('uploadType=media',calls[0][0]);self.assertEqual(calls[0][1],self.png)
        self.assertIn('resourcekey=secretkey',d.share(ident));permission=[c[1] for c in calls if c[2]=='POST'][0];self.assertEqual(permission,{'type':'anyone','role':'reader','allowFileDiscovery':False})
    def test_credential_file_not_readable_by_http(self):
        # Static routing is an explicit allow-list; the dedicated file is not an asset.
        server=(Path(__file__).resolve().parents[1]/'app'/'server.py').read_text();self.assertNotIn("path=='/drive-auth.json'",server)

    def test_front_links_only_for_current_publications_and_revision_once(self):
        self.assertEqual(self.p.front_links(),[])
        self.enqueue();self.p.process_one();link=self.row()['url']
        self.assertEqual(self.p.front_links(),[{'card_id':self.c,'url':link}])
        self.assertTrue(self.s.get('cards',self.c)['front_revision'])
        self.s.mutate('revision.approve',{'card_id':self.c,'side':'front'})
        self.enqueue();self.p.process_one()
        self.assertFalse(self.s.get('cards',self.c)['front_revision'])
        self.s.mutate('card.color',{'card_id':self.c,'map_color':'#112233'})
        self.assertEqual(self.p.front_links(),[])
        with self.assertRaises(ValueError):self.p.qr(self.c,require_current=True)
    def test_upgrade_existing_publication_marks_front_once(self):
        self.enqueue();self.p.process_one()
        with self.s.transaction():
            row=self.row();row.pop('front_url');self.s.put('maps',row)
            c=self.s.get('cards',self.c);c['front_revision']=False;self.s.put('cards',c)
        Publications(self.s)
        self.assertTrue(self.s.get('cards',self.c)['front_revision'])
        self.s.mutate('revision.approve',{'card_id':self.c,'side':'front'})
        Publications(self.s)
        self.assertFalse(self.s.get('cards',self.c)['front_revision'])
    def test_public_name_is_in_recipe_and_invalidates_changed_name(self):
        with self.s.transaction():
            c=self.s.get('cards',self.c);c['name']='Fiktivt bykort';self.s.put('cards',c)
        recipe=self.p.prepare(self.c);self.assertEqual(recipe['card']['name'],'Fiktivt bykort')
        with self.s.transaction():
            c['name']='Nyt kortnavn';self.s.put('cards',c)
        with self.assertRaises(ValueError):self.p.enqueue({'card_id':self.c,'fingerprint':recipe['fingerprint'],'png':self.url})
    def test_layout_upgrade_keeps_existing_link_and_requires_refresh(self):
        self.enqueue();self.p.process_one();link=self.row()['url']
        with self.s.transaction():
            c=self.s.get('cards',self.c);row=self.row();row['fingerprint']=fingerprint(self.s,c,legacy=True);self.s.put('maps',row)
        upgraded=Publications(self.s)
        self.assertEqual(upgraded.front_links(),[{'card_id':self.c,'url':link}])
        self.assertTrue(self.row()['render_refresh']);self.assertFalse(upgraded.status()['cards'][0]['outdated'])
        self.enqueue();self.assertFalse(self.row()['render_refresh'])
    def test_legacy_migration_does_not_bypass_address_changes(self):
        self.enqueue();self.p.process_one()
        with self.s.transaction():
            c=self.s.get('cards',self.c);row=self.row();row['fingerprint']=fingerprint(self.s,c,legacy=True);self.s.put('maps',row)
            c['geo_addresses'].pop();self.s.put('cards',c)
        self.assertEqual(Publications(self.s).front_links(),[])
