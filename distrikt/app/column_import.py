"""W127 draft: explicit positional mapping, no inference, no writes, no networking."""
from card_import import read_rows,ImportCell
from ui_errors import UIError
SCHEMAS={
 'card':[('card','Kortnummer',True),('area','Område',False),('name','Kortnavn',False),('kind','Distriktstype',False),('road','Vejnavn',False),('number','Husnummer / interval',False),('floor','Etage',False),('door','Dør',False),('postcode','Postnummer',False),('type','Adressetype',False),('count','Besøg',False)],
 'ib':[('road','Vejnavn',True),('number','Husnummer / interval',True),('card','Kortnummer',False),('postcode','Postnummer',False),('floor','Etage',False),('door','Dør',False),('date','Dato (ÅÅÅÅ-MM-DD)',False)]}

def schema(kind):
    if kind not in SCHEMAS:raise ValueError('Vælg Kort eller IB.')
    return SCHEMAS[kind]

def load(data):
    if not isinstance(data,dict):raise ValueError('Ugyldigt filvalg.')
    if str(data.get('name','')).lower().endswith('.xlsx'):
        if not isinstance(data.get('sheet'),str) or not data['sheet']:raise ValueError('Vælg XLSX-fane før prøvevisning.')
        rows=read_rows(data,sheet_name=data['sheet'],strict_sheet=True,column_cells=True)
    else:rows=read_rows(data)
    if not rows:raise ValueError('Filen er tom.')
    if any(len(v)>40 for _,v in rows):raise ValueError('Filen må højst indeholde 40 kolonner.')
    rows=[(line,[ImportCell(x,'Et felt er for langt (højst 250 tegn).') if len(x)>250 else x for x in values]) for line,values in rows]
    # Do not reinterpret formula-like CSV strings. They stay inert text, including in preview.
    return rows

def split_rows(data):
    rows=load(data);header=data.get('header_row')
    if header is not None and (type(header) is not int or header<1):raise ValueError('Overskriftsrække skal være et positivt rækkenummer eller fravalgt.')
    width=max(len(values) for _,values in rows)
    if header is None:return rows,['']*width,width
    found=next((values for line,values in rows if line==header),None)
    if found is None:raise ValueError('Den valgte overskriftsrække findes ikke eller er tom.')
    return [(line,values) for line,values in rows if line>header],found+['']*(width-len(found)),width

def describe(data):
    # Metadata discovery reads bounded workbook XML, never follows links.
    if str(data.get('name','')).lower().endswith('.xlsx') and not data.get('sheet'):
        return {'sheets':read_rows(data,list_sheets=True),'needs_sheet':True}
    rows,headers,width=split_rows(data)
    if not rows:raise ValueError('Der er ingen datarækker efter overskriften.')
    kind=data.get('kind');fields=schema(kind)
    return {'fields':[{'key':k,'label':label,'required':required} for k,label,required in fields],
            'columns':[{'index':i,'label':h} for i,h in enumerate(headers)],
            'sample':[{'line':line,'values':v+['']*(width-len(v))} for line,v in rows[:8]],'rows':len(rows),'width':width,
            'issues':[{'line':line,'column':i,'message':x.issue} for line,values in rows[:8] for i,x in enumerate(values) if getattr(x,'issue','')],
            'notice':'Intet er gemt. Alle kolonner starter som Ignorér; vælg hver betydning selv.'}

def normalized_rows(data,kind):
    fields=schema(kind);allowed={k for k,_,_ in fields}
    rows,headers,width=split_rows(data);mapping=data.get('column_map')
    if not isinstance(mapping,list) or len(mapping)!=width:raise ValueError('Vælg et felt eller Ignorér for hver kildekolonne.')
    if any(v is not None and (not isinstance(v,str) or v not in allowed) for v in mapping):raise ValueError('Kolonnevalget indeholder et ukendt felt.')
    selected=[v for v in mapping if v is not None]
    if len(selected)!=len(set(selected)):raise ValueError('Samme importfelt er valgt flere gange. Ret kolonnevalget.')
    missing=[label for k,label,required in fields if required and k not in selected]
    if missing:raise UIError('Obligatoriske felter mangler: {fields}.',fields=', '.join(missing))
    if not rows:raise ValueError('Ingen datarækker er valgt.')
    if len(rows)>(5000 if kind=='ib' else 10000):raise UIError('Importfilen må højst indeholde {count} datarækker.',count=5000 if kind=='ib' else 10000)
    for line,values in rows:
        for i,field in enumerate(mapping):
            if field is not None and i<len(values) and getattr(values[i],'issue',''):
                raise UIError('Række {line}, kolonne {column}: {reason}',line=line,column=i+1,reason=values[i].issue)
    # Canonical header is internal only. Preserve physical source row/CSV record numbers.
    return [(0,selected)]+[(line,[values[i] if i<len(values) else '' for i,v in enumerate(mapping) if v is not None]) for line,values in rows]
