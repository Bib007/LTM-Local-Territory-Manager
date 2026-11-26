"""Local OCR boundaries, cleanup and cancellation; invented pixels/text only."""
import base64
import json
import os
import struct
import sys
import tempfile
import time
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import photo_ocr as ocr


def png(width=1,height=1):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\xff\xff\xff'))+chunk(b'IEND',b'')


class FakeProcess:
    def __init__(self,args,**kw):
        self.args=args;self.returncode=0;self.killed=False
        assert 'shell' not in kw
        assert kw['env']['OMP_THREAD_LIMIT']=='1'
        self.source=Path(args[1]);self.directory=self.source.parent
        assert self.source.is_file()
        Path(args[2]+'.txt').write_text('Fiktivvej 8 - 24.10.2026',encoding='utf-8')
    def poll(self):return self.returncode
    def kill(self):self.killed=True;self.returncode=-1
    def wait(self):return self.returncode


class PhotoOCRTests(unittest.TestCase):
    def wait(self,service,ident):
        until=time.monotonic()+3
        while time.monotonic()<until:
            result=service.status(ident)
            if result['status']!='running':return result
            time.sleep(.01)
        self.fail('OCR test did not finish')
    def test_rejects_invalid_oversize_corrupt_and_trailing_data(self):
        for raw in [b'',b'not an image',png(4001,1),png(3000,3000),png()[:-1],png()+b'extra']:
            with self.assertRaises(ValueError):ocr.validate_png(base64.b64encode(raw).decode())
        self.assertEqual(ocr.validate_png(base64.b64encode(png()).decode()),png())
        for bad in [None,False,'***','a'*(8000001)]:
            with self.assertRaises(ValueError):ocr.validate_png(bad)
    def test_missing_engine_is_explicit_and_does_not_create_job(self):
        service=ocr.PhotoOCR()
        with patch.object(ocr,'engine_path',return_value=None):
            self.assertFalse(service.available()['available'])
            with self.assertRaises(ValueError):service.start({'png':base64.b64encode(png()).decode()})
        self.assertEqual(service.jobs,{})
    def test_recognition_has_fixed_args_private_temp_cleanup_and_ram_only_result(self):
        service=ocr.PhotoOCR();processes=[]
        def create(*a,**kw):
            process=FakeProcess(*a,**kw);processes.append(process);return process
        with patch.object(ocr,'engine_path',return_value='FICTIONAL_ENGINE'),patch.object(service,'available',return_value={'available':True,'languages':['dan','eng']}),patch.object(ocr.subprocess,'Popen',side_effect=create):
            ident=service.start({'png':base64.b64encode(png()).decode(),'name':'../../not-used'})['id'];result=self.wait(service,ident)
            self.assertEqual(result['status'],'done');self.assertEqual(result['text'],'Fiktivvej 8 - 24.10.2026')
            self.assertEqual(processes[0].args[3:],['-l','dan+eng','--psm','6']);self.assertFalse(processes[0].directory.exists())
            service.cancel(ident)
            self.assertNotIn(ident,service.jobs)
            with self.assertRaises(ValueError):service.status(ident)
    def test_cancel_kills_process_before_removing_temporary_directory_and_releases_slot(self):
        service=ocr.PhotoOCR();processes=[]
        class Slow(FakeProcess):
            def __init__(self,*a,**kw):super().__init__(*a,**kw);self.returncode=None
            def kill(self):self.assert_source=self.source.exists();super().kill()
        def create(*a,**kw):p=Slow(*a,**kw);processes.append(p);return p
        with patch.object(ocr,'engine_path',return_value='FICTIONAL_ENGINE'),patch.object(service,'available',return_value={'available':True,'languages':['eng']}),patch.object(ocr.subprocess,'Popen',side_effect=create):
            ident=service.start({'png':base64.b64encode(png()).decode()})['id']
            until=time.monotonic()+2
            while not processes and time.monotonic()<until:time.sleep(.01)
            with self.assertRaises(ValueError):service.start({'png':base64.b64encode(png()).decode()})
            service.cancel(ident);self.assertTrue(processes[0].killed);self.assertTrue(processes[0].assert_source);self.assertFalse(processes[0].directory.exists());self.assertIsNone(service.active)
    def test_shutdown_waits_for_active_process_and_temp_cleanup(self):
        service=ocr.PhotoOCR();processes=[]
        class Slow(FakeProcess):
            def __init__(self,*a,**kw):super().__init__(*a,**kw);self.returncode=None
        def create(*a,**kw):p=Slow(*a,**kw);processes.append(p);return p
        with patch.object(ocr,'engine_path',return_value='FICTIONAL_ENGINE'),patch.object(service,'available',return_value={'available':True,'languages':['eng']}),patch.object(ocr.subprocess,'Popen',side_effect=create):
            service.start({'png':base64.b64encode(png()).decode()})
            until=time.monotonic()+2
            while not processes and time.monotonic()<until:time.sleep(.01)
            service.close();self.assertTrue(processes[0].killed);self.assertFalse(processes[0].directory.exists());self.assertFalse(service.jobs);self.assertIsNone(service.active)

    def test_timeout_and_errors_do_not_leak_native_diagnostics_or_paths(self):
        service=ocr.PhotoOCR()
        with patch.object(ocr,'engine_path',return_value='FICTIONAL_ENGINE'),patch.object(service,'available',return_value={'available':True,'languages':['eng']}),patch.object(ocr.subprocess,'Popen',side_effect=OSError('/private/example NEVER_SHOW')):
            result=self.wait(service,service.start({'png':base64.b64encode(png()).decode()})['id']);self.assertEqual(result['status'],'error');self.assertNotIn('NEVER_SHOW',json.dumps(result));self.assertEqual(result['text'],'')
    def test_timeout_kills_engine_and_removes_its_files(self):
        service=ocr.PhotoOCR();processes=[]
        class Slow(FakeProcess):
            def __init__(self,*a,**kw):super().__init__(*a,**kw);self.returncode=None
        def create(*a,**kw):p=Slow(*a,**kw);processes.append(p);return p
        with patch.object(ocr,'engine_path',return_value='FICTIONAL_ENGINE'),patch.object(service,'available',return_value={'available':True,'languages':['eng']}),patch.object(ocr.subprocess,'Popen',side_effect=create),patch.object(ocr,'TIMEOUT',-.1):
            ident=service.start({'png':base64.b64encode(png()).decode()})['id'];result=self.wait(service,ident)
            self.assertEqual(result['status'],'error');self.assertIn('lang tid',result['error']);self.assertEqual(result['text'],'');self.assertTrue(processes[0].killed);self.assertFalse(processes[0].directory.exists());service.cancel(ident)

    def test_result_expiry_and_close_forget_text(self):
        service=ocr.PhotoOCR();service.jobs={'fake':{'until':0,'text':'FICTIONAL_TEXT'}}
        with self.assertRaises(ValueError):service.status('fake')
        service.close();self.assertEqual(service.jobs,{})

if __name__=='__main__':unittest.main()
