"""Two public dates on an approved image. No identities, IB or external fonts."""
from datetime import date
import base64
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import zlib

@lru_cache(maxsize=1)
def date_font():
    value=json.loads((Path(__file__).parent/'vendor_fonts/date-glyphs.json').read_text())
    if value.get('format')!=1 or set(value.get('glyphs',{}))!=set('0123456789.-'):raise ValueError('Datotegnenes lokale skrifttype er ugyldig.')
    glyphs={}
    for char,glyph in value['glyphs'].items():
        width,height,advance=glyph['width'],glyph['height'],glyph['advance']
        if type(width) is not int or not 1<=width<=64 or height!=58 or type(advance) not in (int,float) or not 0<advance<=40:raise ValueError('Datotegnenes lokale skrifttype er ugyldig.')
        decoder=zlib.decompressobj();alpha=decoder.decompress(base64.b64decode(glyph['alpha'],validate=True),width*height+1)
        if len(alpha)!=width*height or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:raise ValueError('Datotegnenes lokale skrifttype er ugyldig.')
        glyphs[char]=(width,height,advance,alpha)
    return glyphs


def dates(store,card):
    loan=store.active_loan(card['id'])
    return {'completed':card.get('last_completed') or None,'assigned':loan.get('assigned') if loan else None}


def date_key(values):return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def date_text(value):
    if not value:return '-'
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',value):raise ValueError('Ugyldig offentlig kortdato.')
    try:date.fromisoformat(value)
    except ValueError:raise ValueError('Ugyldig offentlig kortdato.') from None
    return value[8:10]+'.'+value[5:7]+'.'+value[:4]


def png_idat(raw):
    """Return the concatenated image data of an already validated PNG."""
    packed=[];pos=8
    while pos<len(raw):
        n=struct.unpack('>I',raw[pos:pos+4])[0]
        if raw[pos+4:pos+8]==b'IDAT':packed.append(raw[pos+8:pos+8+n])
        pos+=12+n
    return b''.join(packed)


def rgb_pixels(raw):
    """Decode only an already validated 2200x1560 RGB/RGBA image."""
    width,height=2200,1560;channels=4 if raw[25]==6 else 3
    stride=width*channels;limit=height*(stride+1)
    decoder=zlib.decompressobj();pixels=decoder.decompress(png_idat(raw),limit+1)
    if len(pixels)!=limit or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:raise ValueError('Ugyldige PNG-pixels.')
    result=bytearray();previous=bytearray(stride)
    for y in range(height):
        offset=y*(stride+1);kind=pixels[offset];row=bytearray(pixels[offset+1:offset+stride+1])
        if kind:
            for x in range(stride):
                left=row[x-channels] if x>=channels else 0;above=previous[x];diagonal=previous[x-channels] if x>=channels else 0
                if kind==1:predict=left
                elif kind==2:predict=above
                elif kind==3:predict=(left+above)//2
                elif kind==4:
                    p=left+above-diagonal;a,b,c=abs(p-left),abs(p-above),abs(p-diagonal)
                    predict=left if a<=b and a<=c else above if b<=c else diagonal
                else:raise ValueError('Ukendt PNG-filter.')
                row[x]=(row[x]+predict)&255
        result.append(0)
        if channels==3:result.extend(row)
        else:
            for x in range(0,stride,4):
                alpha=row[x+3];result.extend((row[x+j]*alpha+255*(255-alpha)+127)//255 for j in range(3))
        previous=row
    return result


def render(raw,values):
    # The approved layout reserves these two rectangles for date values only.
    pixels=rgb_pixels(raw);stride=1+2200*3
    def fill(x,y,w,h,color):
        band=bytes(color)*w
        for row in range(y,y+h):
            start=row*stride+1+x*3;pixels[start:start+w*3]=band
    for name,top in [('completed',468),('assigned',568)]:
        fill(1644,top,502,58,(255,255,255))
        left=1652.0
        for char in date_text(values[name]):
            width,height,advance,alpha=date_font()[char]
            for y in range(height):
                for x in range(width):
                    opacity=alpha[y*width+x]
                    if not opacity:continue
                    start=(top+y)*stride+1+(round(left)+x)*3
                    for channel,color in enumerate((22,60,87)):
                        pixels[start+channel]=(color*opacity+pixels[start+channel]*(255-opacity)+127)//255
            left+=advance
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    result=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2200,1560,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b'')
    if len(result)>8*1024*1024:raise ValueError('PNG-billedet er ugyldigt eller for stort.')
    return result


class ApprovedImages:
    """Private, disposable image cache; absent from database/account backups."""
    def __init__(self,root):self.directory=Path(root)/'.approved-public-images'

    def save(self,raw):
        key=hashlib.sha256(raw).hexdigest()
        self.directory.mkdir(mode=0o700,exist_ok=True)
        if self.directory.is_symlink():raise ValueError('Kortbilledets lokale cache er ugyldig.')
        os.chmod(self.directory,0o700)
        temporary=self.directory/(key+'.'+os.urandom(8).hex()+'.tmp')
        try:
            with temporary.open('xb') as stream:
                os.chmod(temporary,0o600);stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,self.directory/(key+'.png'))
        finally:temporary.unlink(missing_ok=True)
        return key

    def load(self,key):
        if not isinstance(key,str) or not re.fullmatch(r'[a-f0-9]{64}',key):raise ValueError('Kortbilledets lokale cache mangler.')
        path=self.directory/(key+'.png')
        if self.directory.is_symlink() or path.is_symlink() or path.stat().st_size>8*1024*1024:raise ValueError('Kortbilledets lokale cache er ugyldig.')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=key:raise ValueError('Kortbilledets lokale cache er beskadiget.')
        return raw


    def prune(self,referenced):
        if not self.directory.exists() or self.directory.is_symlink():return
        for path in self.directory.iterdir():
            if not path.is_symlink() and re.fullmatch(r'[a-f0-9]{64}\.png',path.name) and path.stem not in referenced:
                path.unlink(missing_ok=True)
