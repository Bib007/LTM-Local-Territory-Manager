"""Disposable, time-bounded S-13 reader. No uploads or persistence of source files."""
import io
import json
import sys
from pathlib import Path

def read(raw):
    sys.path.insert(0,str(Path(__file__).with_name('vendor_py')))
    sys.path.insert(0,str(Path(__file__).with_name('vendor_py')/'pypdf-6.10.0.zip'))
    import pypdf
    from pypdf import filters
    filters.ZLIB_MAX_OUTPUT_LENGTH=8000000
    reader=pypdf.PdfReader(io.BytesIO(raw),strict=True)
    if reader.is_encrypted:raise ValueError('Fjern PDF-adgangskoden, eller brug CSV-skabelonen.')
    if not 1<=len(reader.pages)<=20:raise ValueError('Brug højst 20 S-13-sider ad gangen.')
    folder=Path(__file__).resolve().parents[1]/'templates'
    template=json.loads((folder/'S-13-fields.json').read_text());fields=template['fields'];rows=[];records=[]
    background=(folder/'S-13-background.jpg').read_bytes()
    for page_number,page in enumerate(reader.pages,1):
        if page.rotation or abs(float(page.mediabox.width)-template['width'])>1 or abs(float(page.mediabox.height)-template['height'])>1:
            raise ValueError('PDF-layoutet genkendes ikke. Brug den originale S-13 eller CSV-skabelonen.')
        values={}
        for ref in page.get('/Annots',[]):
            widget=ref.get_object();name=widget.get('/T');value=widget.get('/V','')
            if name in fields:values[str(name)]=str(value)
        if not any(k.endswith('.number') for k in values):
            # Flattened LTM S-13 only: the embedded original image and transform
            # are known. Other layouts must not be guessed from nearby dates.
            resources=page.get('/Resources',{}).get_object();objects=resources.get('/XObject',{}).get_object()
            if not any(getattr(ref.get_object(),'_data',None)==background for ref in objects.values()):
                raise ValueError('Ingen understøttede S-13-felter fundet. Scanninger, fotos og andre PDF-layouts indtastes i CSV-skabelonen.')
            position=None
            def visitor(op,args,cm,tm):
                nonlocal position
                if op==b'BT':position=None
                if op==b'Td':position=[float(args[0]),float(args[1])]
                if op!=b'Tj' or position is None:return
                value=args[0].original_bytes.decode('cp1252').strip()
                if not value:return
                x=(position[0]*cm[0]+position[1]*cm[2]+cm[4]-template['width']*.06)/.88
                baseline=(position[0]*cm[1]+position[1]*cm[3]+cm[5]-template['height']*.06)/.88
                y=template['height']-baseline
                for key,(left,top,right,bottom) in fields.items():
                    if key.startswith('row_') and left<=x<right and top<=y<=bottom:
                        values[key]=(values.get(key,'')+' '+value).strip();break
            page.extract_text(visitor_operand_before=visitor)
        found=False
        for i in range(1,21):
            prefix=f'row_{i:02d}.';number=values.get(prefix+'number','').strip()
            if number.endswith(' forts.'):number=number[:-7].strip()
            previous=values.get(prefix+'previous_completed','').strip()
            if previous:rows.append([number,previous]);records.append([number,previous,'','','']);found=True
            for j in range(1,5):
                person,assigned,completed=[values.get(prefix+f'assignment_{j}.'+key,'').strip() for key in ('person','assigned','completed')]
                if not any((person,assigned,completed)):continue
                found=True
                if completed:rows.append([number,completed])
                # A date without a name or allocation is a standalone completion.
                records.append([number,'',person,assigned,completed] if person or assigned else [number,completed,'','',''])
        if not found:raise ValueError('En PDF-side har ingen aflæste udleveringer eller gennemgange. Kontrollér siden, og brug CSV-skabelonen.')
    return {'rows':rows,'records':records}

if __name__=='__main__':
    try:
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(384*1024*1024,384*1024*1024))
            resource.setrlimit(resource.RLIMIT_CPU,(10,10))
        except (ImportError,ValueError,OSError):pass
        raw=sys.stdin.buffer.read(2000001)
        if len(raw)>2000000 or not raw.startswith(b'%PDF-'):raise ValueError('PDF-filen kunne ikke læses.')
        result=read(raw)
    except ValueError as error:result={'error':str(error)}
    except Exception:result={'error':'PDF-filen kunne ikke aflæses lokalt. Brug CSV-skabelonen.'}
    sys.stdout.write(json.dumps(result,ensure_ascii=True))
