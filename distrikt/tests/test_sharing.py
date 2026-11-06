import base64
import hashlib
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
from sharing import Publications,Drive,RENDER_REVISION,SCOPE,fingerprint,public_members,public_name,png_bytes

def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
def png(extra=False):
    raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2200,1560,8,6,0,0,0))
    if extra:raw+=chunk(b'tEXt',b'note\0PRIVATE_METADATA')
    return raw+chunk(b'IDAT',zlib.compress((b'\x00'+b'\xff'*8800)*1560))+chunk(b'IEND',b'')
class FakeDrive:
    def __init__(self):self.uploads=[];self.withdrawals=[];self.shares=[];self.fail=False
    def connected(self):return True
    def status(self):return {'connected':True,'account':'fake@example.invalid'}
    def upload(self,data,file_id=None):
        if self.fail:raise ValueError('Simuleret netfejl')
        self.uploads.append((data,file_id));return file_id or 'TEST_FILE_12345'
    def link(self,file_id):return 'https://drive.google.com/file/d/'+file_id+'/view'
    def share(self,file_id):
        if self.fail:raise ValueError('Simuleret netfejl')
        self.shares.append(file_id);return self.link(file_id)
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
        self.publisher=self.s.mutate('publisher.save',{'name':'Fiktiv kortholder'})['id']
        self.loan=self.s.mutate('loan.issue',{'card_id':self.c,'publisher_id':self.publisher,'date':'2026-01-01','initial':True})['id']
    def tearDown(self):self.s.close();self.temp.cleanup()
    def enqueue(self):return self.p.enqueue({'render_revision':6,'card_id':self.c,'fingerprint':self.p.prepare(self.c)['fingerprint'],'png':self.url})
    def enqueue_dates(self):
        recipe=self.p.prepare(self.c)
        return self.p.enqueue({'render_revision':recipe['render_revision'],'card_id':self.c,'fingerprint':recipe['fingerprint'],'date_fingerprint':recipe['date_fingerprint'],'date_updates':True,'png':self.url})
    def row(self):return self.s.get('maps',self.p.key(self.c))
    def finish(self,retain=False):
        return self.s.mutate('loan.finish',{'id':self.loan,'date':'2026-01-02','complete':retain,'retain':retain})
    def issue_again(self):
        self.loan=self.s.mutate('loan.issue',{'card_id':self.c,'publisher_id':self.publisher,'date':'2026-01-03','initial':True})['id']
    def test_google_failure_does_not_block_card_edits_or_issuance(self):
        self.enqueue();self.p.process_one();self.finish()
        self.s.mutate('folder.set',{'ids':[self.c],'in_folder':True})
        revision=self.s.state()['revision'];self.p.drive.fail=True
        self.p.process_one()
        self.assertEqual(self.row()['status'],'access_retry')
        self.assertTrue(self.row()['possibly_public'])
        self.assertNotEqual(self.s.revision,revision,'Exercise a real background status change')
        self.s.mutate('card.save',dict(self.s.get('cards',self.c),name='Opdigtet rettelse',_revision=revision))
        revision=self.s.revision
        # Another failure must not block issuing the card after its local edit.
        self.p.sync_access(self.row())
        result=self.s.mutate('loan.issue',{'card_id':self.c,'publisher_id':self.publisher,
            'date':'2026-01-03','_revision':revision})
        self.assertEqual(self.s.active_loan(self.c)['id'],result['id'])
        self.assertTrue(self.p.status()['cards'][0]['access_pending'])

    def test_upload_before_issue_is_private_but_qr_is_printable(self):
        self.finish();self.enqueue();self.p.process_one()
        row=self.row();self.assertEqual(row['status'],'ready');self.assertEqual(row['url'],'')
        self.assertTrue(row['front_url']);self.assertEqual(self.p.drive.shares,[])
        self.assertIn(b'viewBox',self.p.qr(self.c,require_current=True))
        self.assertEqual(self.p.front_links(),[{'card_id':self.c,'url':row['front_url']}])
        self.issue_again();self.assertTrue(self.p.status()['cards'][0]['access_pending'])
        self.p.process_one();self.assertEqual(self.row()['status'],'published');self.assertEqual(len(self.p.drive.uploads),1)
    def test_return_closes_and_reissue_reopens_same_file_without_reupload(self):
        self.enqueue();self.p.process_one();link=self.row()['url'];svg=self.p.qr(self.c)
        self.finish();pending=self.p.status()['cards'][0]
        self.assertFalse(pending['issued']);self.assertTrue(pending['access_pending'])
        self.p.process_one();self.assertEqual(self.row()['status'],'ready');self.assertEqual(self.row()['url'],'')
        self.assertEqual(self.p.qr(self.c),svg)
        self.issue_again();self.p.process_one()
        self.assertEqual(self.row()['url'],link);self.assertEqual(len(self.p.drive.uploads),1);self.assertEqual(self.p.qr(self.c),svg)
    def test_retained_card_and_undo_before_sync_keep_access_open(self):
        self.enqueue();self.p.process_one();self.finish(retain=True);self.p.process_one()
        self.assertEqual(self.row()['status'],'published');self.assertEqual(self.p.drive.withdrawals,[])
        self.finish();self.s.mutate('workflow.undo',{});self.p.process_one()
        self.assertEqual(self.row()['status'],'published')
    def test_closed_card_is_not_reopened_after_ib_change(self):
        self.enqueue();self.p.process_one();self.finish();self.p.process_one()
        self.s.mutate('ib.save',{'card_id':self.c,'road':'Fiktiv vej','number':'3','date':'2026-01-02'})
        shares=len(self.p.drive.shares);self.issue_again();self.p.process_one()
        self.assertEqual(len(self.p.drive.shares),shares);self.assertEqual(self.p.front_links(),[])
    def test_failed_return_close_is_visible_bounded_and_retryable(self):
        self.enqueue();self.p.process_one();self.finish();self.p.drive.fail=True
        for _ in range(5):
            with self.s.transaction():r=self.row();r['next_try']=0;self.s.put('maps',r)
            self.p.process_one()
        self.assertEqual(self.row()['status'],'access_failed');self.assertTrue(self.row()['url'])
        self.assertTrue(self.p.status()['cards'][0]['access_pending'])
        self.p.drive.fail=False;self.p.retry(self.c);self.p.process_one()
        self.assertEqual(self.row()['status'],'ready');self.assertFalse(self.row()['possibly_public'])
    def test_return_during_share_is_closed_before_success(self):
        share=self.p.drive.share
        def delayed(file_id):
            url=share(file_id);self.finish();return url
        self.p.drive.share=delayed;self.enqueue();self.p.process_one()
        self.assertEqual(self.row()['status'],'ready');self.assertFalse(self.row()['possibly_public'])
        self.assertEqual(self.p.drive.withdrawals,['TEST_FILE_12345'])
    def test_lost_share_response_then_return_still_withdraws(self):
        share=self.p.drive.share
        def lost_response(file_id):share(file_id);raise ValueError('Simuleret tabt svar')
        self.p.drive.share=lost_response;self.enqueue();self.p.process_one()
        self.assertEqual(self.row()['status'],'access_retry');self.assertTrue(self.row()['possibly_public'])
        self.finish();self.p.process_one() # A new target bypasses the old retry delay.
        self.assertEqual(self.row()['status'],'ready');self.assertFalse(self.row()['possibly_public'])
    def test_manual_only_front_is_publicly_prepared_without_inventing_geography(self):
        c=self.s.mutate('card.save',{'number':'F125','name':'Fiktivt manuelt kort','temporary':False,'addresses':[
            {'road':'Sikker Prøvevej','numbers':'2–8','count':0,'count_unknown':True},
            {'road':'Sikker Sti','numbers':'hele vejen','count':4}]})['id']
        recipe=self.p.prepare(c)
        self.assertTrue(recipe['geography_missing']);self.assertEqual(recipe['members'],[])
        self.assertEqual(recipe['manual_front_rows'],[
            {'road':'Sikker Prøvevej','numbers':'2–8','count':None,'count_unknown':True},
            {'road':'Sikker Sti','numbers':'hele vejen','count':4,'count_unknown':False}])
        self.assertNotIn('geo_polygon',recipe['card']);self.assertNotIn('addresses',recipe['card'])
        self.assertNotIn('publisher',json.dumps(recipe));self.assertNotIn('private',json.dumps(recipe).lower())

    def test_polygon_card_fingerprint_keeps_pre_manual_front_shape(self):
        c_id=self.s.mutate('card.save',{'number':'F128','name':'Fiktivt polygonkort','temporary':False,'addresses':[
            {'road':'Kun manuel linje','numbers':'1–5','count':0,'count_unknown':True}]})['id']
        with self.s.transaction():
            c=self.s.get('cards',c_id);c['geo_polygon']=[[10,55],[10.01,55],[10.01,55.01]];self.s.put('cards',c)
        c=self.s.get('cards',c_id)
        previous={'number':c['number'],'color':c.get('map_color','#477596'),'polygon':c.get('geo_polygon',[]),
                  'members':sorted(public_members(self.s,c),key=lambda a:a['id']),'name':public_name(self.s,c)}
        expected=hashlib.sha256(json.dumps(previous,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(fingerprint(self.s,c),expected)
        self.assertEqual(self.p.prepare(c_id)['manual_front_rows'],[])

    def test_manual_rows_are_conservatively_filtered_against_ib_and_fingerprinted(self):
        c=self.s.mutate('card.save',{'number':'F126','name':'Fiktiv filtrering','temporary':False,'addresses':[
            {'road':'Prøvevej','numbers':'7','count':2},
            {'road':'Prøvevej','numbers':'8','count':1},
            {'road':'Prøvevej','numbers':'7–9','count':0,'count_unknown':True},
            {'road':'Sikker Sti','numbers':'hele vejen','count':0,'count_unknown':True}]})['id']
        with self.s.transaction():self.s.put('ib',{'id':'fictional-ib','card_id':c,'road':'Prøvevej','number':'7 1 tv','date':'2026-01-01'})
        recipe=self.p.prepare(c)
        self.assertTrue(recipe['manual_ib_withheld'])
        self.assertEqual([(r['road'],r['numbers']) for r in recipe['manual_front_rows']],
            [('Prøvevej','8'),('Sikker Sti','hele vejen')])
        before=recipe['fingerprint']
        self.s.mutate('card.save',{'id':c,'number':'F126','name':'Fiktiv filtrering','temporary':False,'addresses':[
            {'road':'Prøvevej','numbers':'7','count':2},
            {'road':'Prøvevej','numbers':'8','count':1},
            {'road':'Prøvevej','numbers':'7–9','count':2},
            {'road':'Sikker Sti','numbers':'hele vejen','count':0,'count_unknown':True}]})
        self.assertNotEqual(before,self.p.prepare(c)['fingerprint'],'Even withheld row count certainty is fingerprinted')
        before=self.p.prepare(c)['fingerprint']
        self.s.mutate('card.save',{'id':c,'number':'F126','name':'Fiktiv filtrering','temporary':False,'addresses':[
            {'road':'Prøvevej','numbers':'9','count':1},
            {'road':'Sikker Sti','numbers':'hele vejen','count':0,'count_unknown':True}]})
        self.assertNotEqual(before,self.p.prepare(c)['fingerprint'])

    def test_manual_only_preview_fingerprint_change_rejects_stale_approval(self):
        c=self.s.mutate('card.save',{'number':'F127','temporary':False,'addresses':[{'road':'Fiktiv vej','numbers':'1','count':1}]})['id']
        old=self.p.prepare(c)['fingerprint']
        self.s.mutate('card.save',{'id':c,'number':'F127','temporary':False,'addresses':[{'road':'Fiktiv vej','numbers':'2','count':1}]})
        with self.assertRaisesRegex(ValueError,'Kortet er ændret'):
            self.p.enqueue({'render_revision':7,'card_id':c,'fingerprint':old,'date_updates':True,'date_fingerprint':self.p.prepare(c)['date_fingerprint'],'png':self.url})

    def test_private_manual_withdrawal_does_not_auto_reopen(self):
        self.enqueue();self.p.process_one();self.p.withdraw(self.c)
        count=len(self.p.drive.shares);self.finish();self.issue_again();self.p.process_one()
        self.assertEqual(self.row()['status'],'private');self.assertEqual(len(self.p.drive.shares),count)
    def test_restart_reconciles_return_without_browser(self):
        self.enqueue();self.p.process_one();self.finish()
        other=Publications(self.s);other.drive=self.p.drive;other.process_one()
        self.assertEqual(self.row()['status'],'ready')
    def test_disconnected_return_stays_pending_until_reconnected(self):
        self.enqueue();self.p.process_one();self.finish()
        self.p.drive.connected=lambda:False
        self.p.process_one();self.assertTrue(self.p.status()['cards'][0]['access_pending'])
        self.assertEqual(self.row()['status'],'published')
        self.p.drive.connected=lambda:True
        self.p.process_one();self.assertEqual(self.row()['status'],'ready')
    def test_card_deleted_during_share_never_finishes_public(self):
        share=self.p.drive.share
        def deleted(file_id):
            url=share(file_id);self.s.mutate('delete',{'module':'cards','id':self.c});return url
        self.p.drive.share=deleted;self.enqueue();self.p.process_one()
        self.assertEqual(self.row()['status'],'review');self.assertFalse(self.row()['possibly_public'])
        self.assertEqual(self.row()['url'],'')
    def test_return_closes_old_image_while_replacement_upload_is_delayed(self):
        self.enqueue();self.p.process_one();self.enqueue()
        with self.s.transaction():
            row=self.row();row.update(status='retry',next_try=10**12);self.s.put('maps',row)
        self.finish();self.p.process_one()
        self.assertEqual(self.row()['url'],'');self.assertEqual(self.row()['status'],'retry')
        self.assertTrue(self.row()['queued_png']);self.assertEqual(len(self.p.drive.uploads),1)
    def test_queued_withdraw_failure_keeps_png_and_manual_retry_only_closes(self):
        self.enqueue();self.p.process_one();self.enqueue();self.finish();self.p.drive.fail=True
        self.p.process_one();self.assertTrue(self.row()['close_error']);self.assertTrue(self.row()['queued_png'])
        self.assertTrue(self.p.status()['cards'][0]['close_pending'])
        self.p.drive.fail=False;self.p.retry(self.c);self.p.process_one()
        self.assertEqual(self.row()['url'],'');self.assertTrue(self.row()['queued_png'])
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
            if 'fields=id,webViewLink' in path:return {'id':'FILE123','webViewLink':'https://drive.google.com/file/d/FILE123/view','resourceKey':'secretkey' if any(c[2]=='POST' for c in calls) else ''}
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
    def test_public_saved_points_include_house_number_but_never_ib_metadata(self):
        before=self.p.prepare(self.c)
        with self.s.transaction():
            self.s.put('ib',{'id':'fictional-ib','card_id':self.c,'address_id':'a2',
                'road':'Fiktiv vej','number':'3','note':'PRIVATE_IB_NOTE','status':'PRIVATE_IB_STATUS'})
        recipe=self.p.prepare(self.c)
        members=recipe['members']
        self.assertEqual([a['id'] for a in members],['a1','a2'])
        self.assertNotIn('saved_point',members[0])
        self.assertTrue(members[1]['saved_point'])
        self.assertEqual(members[1]['number'],'3')
        self.assertEqual(members[1]['count'],1)
        self.assertNotIn('floor',members[1])
        self.assertNotIn('door',members[1])
        self.assertNotIn('postcode',members[1])
        self.assertNotIn('PRIVATE_IB_',json.dumps(recipe))
        self.assertNotEqual(before['fingerprint'],recipe['fingerprint'])
        self.assertEqual(recipe['render_revision'],RENDER_REVISION)

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
        self.enqueue_dates();self.assertFalse(self.row()['render_refresh'])
    def test_old_layout_keeps_qr_and_access_until_owner_approves_new_image(self):
        recipe=self.p.prepare(self.c)
        self.p.enqueue({'card_id':self.c,'fingerprint':recipe['fingerprint'],'png':self.url,
            'render_revision':7,'date_updates':True,'date_fingerprint':recipe['date_fingerprint']})
        self.p.process_one();before=self.row();link=before['front_url'];uploads=len(self.p.drive.uploads)
        upgraded=Publications(self.s)
        self.assertTrue(upgraded.status()['cards'][0]['render_refresh'])
        self.assertEqual(upgraded.front_links(),[{'card_id':self.c,'url':link}])
        self.assertEqual(self.row()['file_id'],before['file_id'])
        self.assertEqual(self.row()['status'],'published')
        self.assertEqual(len(self.p.drive.uploads),uploads)
        self.assertEqual(self.p.prepare(self.c)['render_revision'],RENDER_REVISION)
        self.enqueue_dates();self.p.process_one()
        self.assertEqual(self.row()['front_url'],link)
        self.assertEqual(self.row()['render_revision'],RENDER_REVISION)
        self.assertFalse(Publications(self.s).status()['cards'][0]['render_refresh'])
    def test_previous_layout_keeps_link_without_automatic_upload(self):
        self.p.enqueue({'card_id':self.c,'fingerprint':self.p.prepare(self.c)['fingerprint'],'png':self.url,'render_revision':5})
        self.p.process_one();before=self.row();uploads=len(self.p.drive.uploads)
        upgraded=Publications(self.s)
        self.assertTrue(upgraded.status()['cards'][0]['render_refresh'])
        self.assertEqual(upgraded.front_links(),[{'card_id':self.c,'url':before['front_url']}])
        self.assertEqual(self.row()['render_revision'],5)
        self.assertEqual(len(self.p.drive.uploads),uploads)
        self.assertEqual(self.row()['status'],'published')
    def test_unknown_stored_layout_metadata_is_preserved_and_requests_review(self):
        self.enqueue();self.p.process_one()
        with self.s.transaction():
            row=self.row();row['render_revision']='future-layout';self.s.put('maps',row)
        upgraded=Publications(self.s)
        self.assertTrue(upgraded.status()['cards'][0]['render_refresh'])
        self.assertEqual(self.row()['render_revision'],'future-layout')
        self.assertTrue(upgraded.front_links())

    def test_unknown_layout_revision_is_rejected_without_writes(self):
        for revision in ('6',True,0,RENDER_REVISION+1):
            with self.subTest(revision=revision),self.assertRaises(ValueError):
                self.p.enqueue({'card_id':self.c,'fingerprint':self.p.prepare(self.c)['fingerprint'],'png':self.url,'render_revision':revision})
        self.assertIsNone(self.row())

    def test_legacy_migration_does_not_bypass_address_changes(self):
        self.enqueue();self.p.process_one()
        with self.s.transaction():
            c=self.s.get('cards',self.c);row=self.row();row['fingerprint']=fingerprint(self.s,c,legacy=True);self.s.put('maps',row)
            c['geo_addresses'].pop();self.s.put('cards',c)
        self.assertEqual(Publications(self.s).front_links(),[])
