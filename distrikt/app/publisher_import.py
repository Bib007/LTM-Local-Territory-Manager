"""Reviewed local group-list import; all affected publishers commit together."""
from collections import defaultdict
from copy import deepcopy
from card_import import read_rows,norm
from publisher_data import normalized,validate_groups,ROLES,PublisherIndex

HEADERS=['navn','tjenestegruppe','gruppefunktion','pioner']
FIELDS=['name','group','group_role','pioneer']
ALIASES=dict(zip(HEADERS,FIELDS));ALIASES.update(dict(zip(FIELDS,FIELDS)))


def template_csv():return ('\ufeff'+';'.join(HEADERS)+'\r\n').encode('utf-8')


def template_xlsx():
    from ib_import import template_xlsx as blank
    return blank(headers=HEADERS,sheet_name='Forkyndere')


def preview(store,data):
    source=read_rows(data,sheet_name='Forkyndere')
    if not source:raise ValueError('Gruppelisten mangler kolonneoverskrifter.')
    fields=[ALIASES.get(norm(h)) for h in source[0][1]]
    if not fields or any(not f for f in fields) or len(set(fields))!=len(fields) or 'name' not in fields:
        raise ValueError('Brug gruppeskabelonens kolonner: navn, tjenestegruppe, gruppefunktion og pioner.')
    current=store.all('publishers');by_name=defaultdict(list)
    for person in current:by_name[norm(person['name'])].append(person)
    rows=[];seen=set();proposed={p['id']:deepcopy(p) for p in current}
    role_names={norm(label):key for key,label in ROLES.items()};role_names.update({key:key for key in ROLES});role_names['forkynder']=''
    for line,values in source[1:]:
        if len(rows)>=5000:raise ValueError('Gruppelisten må højst indeholde 5.000 linjer.')
        row={'line':line,'status':'error'}
        try:
            if len(values)>len(fields) and any(str(v).strip() for v in values[len(fields):]):raise ValueError('Linjen har flere værdier end kolonneoverskrifter.')
            v={f:str(value).strip() for f,value in zip(fields,list(values)+['']*len(fields))}
            name=norm(v['name'])
            if not name:raise ValueError('Navn mangler.')
            if name in seen:raise ValueError('Navnet er gentaget i filen. Behold kun én linje pr. forkynder.')
            seen.add(name);matches=by_name.get(name,[])
            if len(matches)>1:raise ValueError('Navnet matcher flere eksisterende forkyndere. Ret navnene i registeret først.')
            old=matches[0] if matches else None
            # Omitted columns preserve existing values; a present blank clears.
            values={'name':v['name']}
            if 'group' in fields:values['group']=v['group']
            if 'group_role' in fields:
                role=norm(v['group_role'])
                if role not in role_names:raise ValueError('Gruppefunktion skal være Gruppetilsynsmand, Assistent eller stå tomt.')
                values['group_role']=role_names[role]
            if 'pioneer' in fields:
                value=norm(v['pioneer'])
                if value not in ('','ja','nej','yes','no','true','false','1','0'):raise ValueError('Pioner skal være Ja eller Nej.')
                values['pioneer']=value in ('ja','yes','true','1')
            person={k:v for k,v in normalized(values,old).items() if k in FIELDS or k=='id'}
            if old:
                person['id']=old['id']
                status='existing' if all(person.get(f) == normalized({'name':old['name']},old).get(f) for f in FIELDS) else 'update'
                proposed[old['id']]=person
            else:
                status='new';proposed['new:'+str(line)]=person
            row.update(status=status,record=person,before={f:old.get(f) for f in FIELDS} if old else None)
        except (ValueError,TypeError) as error:row['error']=str(error)
        rows.append(row)
    if not rows:raise ValueError('Gruppelisten indeholder ingen forkyndere. Udfyld skabelonen først.')
    errors=[]
    try:validate_groups(proposed.values())
    except ValueError as error:errors.append(str(error))
    payload={'rows':rows,'errors':errors,**{key:sum(r['status']==key for r in rows) for key in ('new','update','existing')},'invalid':sum(r['status']=='error' for r in rows)}
    return dict(payload,token=store.setup_remember('publishers',payload))


def apply(store,data):
    if data.get('confirm')!='IMPORTÉR GRUPPER':raise ValueError('Skriv IMPORTÉR GRUPPER for at fortsætte.')
    plan=store.setup_require_preview(data,'publishers')
    if plan['invalid'] or plan['errors']:raise ValueError('Ret alle fejl i gruppelisten, og lav en ny forhåndsvisning.')
    changed=[r['record'] for r in plan['rows'] if r['status'] in ('new','update')]
    # Clear functions inside this same transaction before assigning a swap.
    # Domain validation still runs on every final write and the final group set.
    previous=getattr(store,'_publisher_index',None)
    store._publisher_index=PublisherIndex(store.all('publishers'))
    try:
        for person in changed:
            if person.get('id'):
                old=store.require('publishers',person['id'])
                if old.get('group_role'):store._mutate('publisher.save',{**old,'group_role':''})
        for person in changed:store._mutate('publisher.save',person)
        validate_groups(store.all('publishers'))
    finally:store._publisher_index=previous
    return {'new':plan['new'],'update':plan['update'],'existing':plan['existing']}
