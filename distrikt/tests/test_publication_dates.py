"""Approved fictional images and dates, with a local fake Drive transport."""
import base64
from copy import deepcopy
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from store import Store
from sharing import Publications,png_bytes
from publication_dates import dates,date_key,render,rgb_pixels
from portable import snapshot
from test_sharing import FakeDrive,chunk


def plain_png():
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2200,1560,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\xff'*6600)*1560))+chunk(b'IEND',b'')


class PublicationDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.png=plain_png();cls.url='data:image/png;base64,'+base64.b64encode(cls.png).decode()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.s=Store(self.temp.name)
        self.c=self.s.mutate('card.save',{'number':'F106','temporary':True})['id']
        with self.s.transaction():
            card=self.s.require('cards',self.c);card['geo_polygon']=[[10,55],[10.1,55],[10.1,55.1]];self.s.put('cards',card)
        self.person=self.s.mutate('publisher.save',{'name':'PRIVATE_PERSON_NOT_ON_PUBLIC_IMAGE'})['id']
        self.loan=self.s.mutate('loan.issue',{'card_id':self.c,'publisher_id':self.person,'initial':True,'date':'2026-01-01'})['id']
        self.p=Publications(self.s);self.p.drive=FakeDrive()
    def tearDown(self):self.s.close();self.temp.cleanup()
    def row(self):return self.s.require('maps',self.p.key(self.c))
    def approve(self):
        recipe=self.p.prepare(self.c)
        preview=self.p.date_preview({'card_id':self.c,'fingerprint':recipe['fingerprint'],'date_fingerprint':recipe['date_fingerprint'],'png':self.url})
        self.p.enqueue({'card_id':self.c,'render_revision':7,'fingerprint':recipe['fingerprint'],'date_fingerprint':preview['date_fingerprint'],'date_updates':True,'png':preview['png']})
        self.p.process_one();return preview
    def complete(self,day='2026-01-02'):self.s.mutate('loan.finish',{'id':self.s.active_loan(self.c)['id'],'date':day,'complete':True,'retain':True})
    def drain(self,n=5):
        for _ in range(n):self.p.process_one()

    def test_exact_preview_is_idempotent_read_only_and_contains_no_identity(self):
        before=self.s.revision;recipe=self.p.prepare(self.c)
        self.assertNotIn('PRIVATE',str(recipe));self.assertEqual(recipe['dates'],{'completed':None,'assigned':'2026-01-01'})
        data={'card_id':self.c,'fingerprint':recipe['fingerprint'],'date_fingerprint':recipe['date_fingerprint'],'png':self.url}
        preview=self.p.date_preview(data)
        self.assertEqual(self.s.revision,before);self.assertFalse(self.p.images.directory.exists())
        raw=png_bytes(preview['png']);self.assertEqual(render(raw,recipe['dates']),raw)
        self.p.enqueue({**data,'png':preview['png'],'render_revision':7,'date_updates':True});self.p.process_one()
        self.assertEqual(self.p.drive.uploads[0][0],raw)
        with zipfile.ZipFile(io.BytesIO(snapshot(self.s,'fictional'))) as z:self.assertFalse(any('approved-public-images' in n for n in z.namelist()))

    def test_completion_updates_only_dates_on_same_file_after_closing_old_image(self):
        self.approve();before=self.row();initial=deepcopy(self.p.drive.uploads)
        self.complete();self.p.process_one();self.assertEqual(self.row()['status'],'queued')
        self.p.process_one();self.assertTrue(self.p.drive.withdrawals);self.assertEqual(len(self.p.drive.uploads),1)
        self.p.process_one();current=self.row();self.assertEqual(current['file_id'],before['file_id']);self.assertEqual(current['front_url'],before['front_url'])
        self.assertEqual(current['date_values']['completed'],'2026-01-02');self.assertEqual(current['status'],'published')
        self.assertNotEqual(self.p.drive.uploads[-1][0],initial[0][0]);self.assertEqual(self.p.drive.uploads[-1][1],before['file_id'])

    def test_return_without_completion_and_reissue_clear_old_assignment_and_keep_qr(self):
        self.complete();self.approve();link=self.row()['front_url']
        self.s.mutate('loan.finish',{'id':self.loan,'date':'2026-01-03','complete':False});self.drain()
        self.assertEqual(self.row()['date_values'],{'completed':'2026-01-02','assigned':None});self.assertEqual(self.row()['status'],'ready')
        self.s.mutate('loan.issue',{'card_id':self.c,'publisher_id':self.person,'initial':True,'date':'2026-01-04'});self.drain()
        self.assertEqual(self.row()['date_values']['assigned'],'2026-01-04');self.assertEqual(self.row()['front_url'],link);self.assertEqual(self.row()['status'],'published')

    def test_stale_date_approval_is_rejected_before_upload_or_cache_write(self):
        recipe=self.p.prepare(self.c);self.complete()
        with self.assertRaises(ValueError):self.p.enqueue({'card_id':self.c,'render_revision':7,'date_updates':True,'date_fingerprint':recipe['date_fingerprint'],'fingerprint':recipe['fingerprint'],'png':self.url})
        self.assertEqual(self.p.drive.uploads,[]);self.assertFalse(self.p.images.directory.exists())

    def test_missing_cache_fails_closed_and_requires_a_new_approved_image(self):
        self.approve();(self.p.images.directory/(self.row()['approved_image']+'.png')).unlink()
        self.complete();self.drain();self.assertEqual(len(self.p.drive.uploads),1)
        self.assertEqual(self.row()['status'],'review');self.assertEqual(self.row()['url'],'');self.assertTrue(self.row()['date_error'])

    def test_manual_withdrawal_is_not_reopened_by_a_date_change(self):
        self.approve();self.p.withdraw(self.c);self.complete();self.drain()
        self.assertEqual(self.row()['status'],'private');self.assertEqual(len(self.p.drive.uploads),1)

    def test_lost_manual_withdrawal_reply_stops_updates_until_new_owner_approval(self):
        self.approve();self.p.drive.fail=True
        result=self.p.withdraw(self.c)
        self.assertEqual(result['status'],'withdraw_retry');self.assertTrue(self.row()['manual_withdraw'])
        self.complete();self.p.drive.fail=False;self.drain()
        self.assertEqual(self.row()['status'],'private');self.assertEqual(len(self.p.drive.uploads),1)
        self.approve();self.assertFalse(self.row().get('manual_withdraw'));self.assertEqual(self.row()['status'],'published')

    def test_failed_date_upload_keeps_same_file_and_does_not_claim_publication(self):
        self.approve();file_id=self.row()['file_id'];self.complete()
        self.p.process_one();self.p.process_one()
        self.p.drive.fail=True;self.p.process_one()
        self.assertEqual(self.row()['status'],'retry');self.assertFalse(self.row()['url'])
        self.assertEqual(self.row()['file_id'],file_id)
        self.p.drive.fail=False;self.p.retry(self.c);self.drain()
        self.assertEqual(self.row()['status'],'published');self.assertEqual(self.row()['file_id'],file_id)

    def test_boundary_change_requires_new_approval_and_cannot_reuse_cached_map(self):
        self.approve()
        with self.s.transaction():
            c=self.s.require('cards',self.c);c['geo_polygon']=[[10,55],[10.2,55],[10.2,55.2]];self.s.put('cards',c)
        self.complete();self.drain();self.assertEqual(len(self.p.drive.uploads),1);self.assertEqual(self.row()['status'],'review')

    def test_new_completion_during_upload_never_opens_an_old_dated_image(self):
        self.approve();self.complete();self.p.process_one();self.p.process_one()
        original=self.p.drive.upload
        def change(raw,file_id=None):
            result=original(raw,file_id);self.complete('2026-01-03');return result
        shares=len(self.p.drive.shares)
        with patch.object(self.p.drive,'upload',side_effect=change):self.p.process_one()
        self.assertEqual(len(self.p.drive.shares),shares);self.assertEqual(self.row()['status'],'review')
        self.drain();self.assertEqual(self.row()['date_values']['completed'],'2026-01-03');self.assertEqual(self.row()['status'],'published')

    def test_restoring_data_cannot_resume_cached_public_date_updates(self):
        from portable import Restores
        self.approve();raw=snapshot(self.s,'fictional');self.p.withdraw(self.c)
        restores=Restores(self.s,'fictional');preview=restores.preview(raw);restores.apply(preview['token'])
        self.assertEqual(self.row()['status'],'review');self.assertFalse(self.row().get('date_updates'))
        self.complete();self.drain();self.assertEqual(len(self.p.drive.uploads),1);self.assertEqual(len(self.p.drive.shares),1)

    def test_new_ib_requires_approval_instead_of_reusing_the_cached_map(self):
        with self.s.transaction():
            card=self.s.require('cards',self.c)
            card['geo_addresses']=[{'id':'FICT_ADDR','road':'Fiktiv vej','number':'1','postcode':'9999','lng':10,'lat':55,'count':1}]
            self.s.put('cards',card)
        self.approve()
        self.s.mutate('ib.save',{'card_id':self.c,'road':'Fiktiv vej','number':'1','date':'2026-01-02'})
        self.complete();self.drain()
        self.assertEqual(self.row()['status'],'review');self.assertEqual(len(self.p.drive.uploads),1)

    def test_date_patch_keeps_all_other_pixels_and_is_bounded(self):
        original=rgb_pixels(self.png);values={'completed':'2026-01-02','assigned':'2026-01-01'}
        modified=rgb_pixels(render(self.png,values));stride=6601
        for top in [468,568]:
            for y in range(top,top+58):
                start=y*stride+1+1644*3;modified[start:start+502*3]=original[start:start+502*3]
        self.assertEqual(modified,original)
        self.assertEqual(date_key(values),date_key(dict(reversed(list(values.items())))))

if __name__=='__main__':unittest.main()
