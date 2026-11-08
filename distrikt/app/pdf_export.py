"""Small standard-library PDF writer for local S-13 output; no cloud service."""
import math
import re
import json
from pathlib import Path
from resource_paths import templates_dir
from datetime import date

def literal(value):
    return str(value or '').encode('cp1252', 'replace').decode('latin1').replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

def pdf_document(pages, width=595.28, height=841.89, image=None, *, page_images=None):
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
    kids = []
    for source in page_images or ([image] if image else []):
        raw,iw,ih=source[:3]
        png=len(source)>3 and source[3]=='png'
        filter_name='/FlateDecode /DecodeParms << /Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns %s >>'%iw if png else '/DCTDecode'
        objects.append(('<< /Type /XObject /Subtype /Image /Width %s /Height %s /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter %s /Length %s >>\nstream\n'%(iw,ih,filter_name,len(raw))).encode()+raw+b'\nendstream')
    for index,commands in enumerate(pages):
        page_id = len(objects)+1
        content_id = page_id+1
        kids.append('%s 0 R' % page_id)
        image_id=4+index if page_images else (4 if image else None)
        resources='/XObject << /Im1 %s 0 R >>'%image_id if image_id else ''
        objects.append(('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Resources << /Font << /F1 3 0 R >> %s >> /Contents %s 0 R >>' % (width, height, resources,content_id)).encode())
        content = '\n'.join(commands).encode('latin1')
        objects.append(('<< /Length %s >>\nstream\n' % len(content)).encode()+content+b'\nendstream')
    objects[1] = ('<< /Type /Pages /Kids [%s] /Count %s >>' % (' '.join(kids), len(kids))).encode()
    result = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'); offsets=[0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(result)); result.extend(('%s 0 obj\n' % i).encode()+obj+b'\nendobj\n')
    xref=len(result); result.extend(('xref\n0 %s\n0000000000 65535 f \n' % (len(objects)+1)).encode())
    for offset in offsets[1:]: result.extend(('%010d 00000 n \n' % offset).encode())
    result.extend(('trailer\n<< /Size %s /Root 1 0 R >>\nstartxref\n%s\n%%%%EOF\n' % (len(objects)+1,xref)).encode())
    return bytes(result)

def shared_card_pdf(map_png,front_png):
    """Place the two approved raster images on separate landscape PDF pages."""
    import zlib
    from publication_dates import png_idat,rgb_pixels

    width,height=841.89,595.28
    scale=min(width/2200,height/1560)
    w,h=2200*scale,1560*scale
    draw=['q %.3f 0 0 %.3f %.3f %.3f cm /Im1 Do Q'%(w,h,(width-w)/2,(height-h)/2)]
    # Reuse the lossless RGB data directly. Convert RGBA only if a browser
    # generated it, flattening transparency onto white.
    images=[(png_idat(raw) if raw[25]==2 else zlib.compress(rgb_pixels(raw)),
             2200,1560,'png') for raw in (map_png,front_png)]
    return pdf_document([draw,draw],width,height,page_images=images)

def text(x,y,value,size=8,maxchars=None):
    value=str(value or '')
    # Shrink to fit rather than silently drop parts of a publisher name.
    if maxchars and len(value)>maxchars: size=max(1.5, size*maxchars/len(value))
    return 'BT /F1 %.2f Tf %.2f %.2f Td (%s) Tj ET' % (size,x,y,literal(value))

def fmt(day):
    return date.fromisoformat(day).strftime('%d.%m.%y') if day else ''

def allocation_rows(state, year, language='da'):
    start='%s-09-01' % (year-1); end='%s-08-31' % year
    names={p['id']:p['name'] for p in state['publishers']}
    loan_ids={l['id'] for l in state['loans']}
    rows=[]
    for card in sorted(state['cards']+state.get('archived_cards',[]),key=lambda c:[(0,int(part)) if part.isdigit() else (1,part.casefold()) for part in re.split(r'(\d+)',c['number'])]):
        assignments=[]
        for loan in sorted((l for l in state['loans'] if l['card_id']==card['id']),key=lambda l:l['assigned']):
            finished=sorted((e for e in state['completions'] if e.get('loan_id')==loan['id']),key=lambda e:e['date'])
            done=[e['date'] for e in finished]
            cycle=loan['assigned']
            for entry in finished:
                day=entry['date']
                assigned=entry.get('assigned') or cycle
                if assigned<=end and day>=start:
                    assignments.append({'person':names.get(loan['publisher_id'],'—'),'assigned':assigned,'completed':day if day<=end else None})
                cycle=day
            cycle=loan.get('cycle_start',cycle)
            if (not loan.get('returned') or loan['returned']>=start) and cycle<=end:
                # A completed return must not create a phantom second allocation.
                if not (done and loan.get('returned')==done[-1]):
                    assignments.append({'person':names.get(loan['publisher_id'],'—'),'assigned':cycle,'completed':None})
        # A missing assignment does not erase a valid completion or display the removed allocation.
        assignments += [{'person':'','assigned':None,'completed':e['date']} for e in state['completions'] if e['card_id']==card['id'] and e.get('loan_id') not in loan_ids and start<=e['date']<=end]
        assignments.sort(key=lambda a:a['assigned'] or a['completed'] or '')
        dates=[e['date'] for e in state['completions'] if e['card_id']==card['id'] and e['date']<start]
        dates += [e['previous_completed'] for e in state['completions'] if e['card_id']==card['id'] and e.get('previous_completed') and e['previous_completed']<start]
        if card.get('last_completed') and card['last_completed']<start: dates.append(card['last_completed'])
        prev=max(dates,default=None)
        for i in range(max(1,math.ceil(len(assignments)/4))):
            rows.append({'number':card['number']+((' cont.' if language=='en' else ' forts.') if i else ''),'previous':prev,'allocations':assignments[i*4:i*4+4]})
    return rows

def s13_pdf(state,year,language='da'):
    if language not in ('da','en'):raise ValueError('Vælg dansk eller engelsk formular.')
    """Flatten values over the supplied original S-13 image, with safe A4 margins."""
    folder=templates_dir()
    template=json.loads((folder/('S-13-E-fields.json' if language=='en' else 'S-13-fields.json')).read_text())
    width=template['width'];height=template['height'];fields=template['fields']
    rows=allocation_rows(state,year,language);chunks=[rows[i:i+20] for i in range(0,len(rows),20)] or [[]]
    pages=[]
    for chunk in chunks:
        values={'service_year':f'{year-1}/{year}','territory_type':'Hus til hus'}
        for i,row in enumerate(chunk,1):
            prefix=f'row_{i:02d}.'
            values[prefix+'number']=row['number'];values[prefix+'previous_completed']=fmt(row['previous'])
            for j,item in enumerate(row['allocations'],1):
                for key in ('person','assigned','completed'):
                    values[prefix+f'assignment_{j}.'+key]=item[key] if key=='person' else fmt(item[key])
        commands=['q .88 0 0 .88 %.3f %.3f cm'%(width*.06,height*.06),'q %.3f 0 0 %.3f 0 %.3f cm /Im1 Do Q'%(width,template.get('background_height',800.986),template.get('background_y',20.452)),'0 g']
        for name,value in values.items():
            if name not in fields:continue
            x,y,right,bottom=fields[name];size=9 if name in ('service_year','territory_type') else 7
            commands.append(text(x+1,height-y-min(bottom-y-2,10),value,size,maxchars=max(1,int((right-x-2)/(size*.8)))))
        commands.append('Q');pages.append(commands)
    return pdf_document(pages,width,height,image=((folder/('S-13-E-background.jpg' if language=='en' else 'S-13-background.jpg')).read_bytes(),template.get('image_width',926),template.get('image_height',1246)))
