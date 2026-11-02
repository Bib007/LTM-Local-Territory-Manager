"""Explicit, atomic movement of known address units between returned cards."""
import math
import uuid
from copy import deepcopy
from datetime import date
from admin_store import signature
from geography import enclosing_outline, street_rows


def planning_date(card):
    """An inherited scheduling reference is never a completion event."""
    ref=card.get('planning_reference') or {}
    inherited=ref.get('date') if isinstance(ref,dict) and ref and ref.get('membership')==sorted(card.get('address_ids') or []) else None
    valid=[]
    for day in (card.get('last_completed'),inherited):
        if not isinstance(day,str) or len(day)!=10:continue
        try:date.fromisoformat(day)
        except ValueError:continue
        valid.append(day)
    return max(valid,default=None)


def redistribute(store,action,data):
    from store import clean_text,now,valid_day
    mode=data.get('mode');ids=data.get('ids')
    if mode not in ('transfer','interim','finalize') or not isinstance(ids,list) or len(ids)!=2 or not all(isinstance(i,str) for i in ids) or ids[0]==ids[1]:
        raise ValueError('Vælg to forskellige kort til flytningen.')
    source,target=[store.require('cards',i) for i in ids]
    if any(c.get('archived') or c.get('temporary') or c.get('in_folder') or store.active_loan(c['id']) for c in (source,target)):
        raise ValueError('Begge kort skal være færdige, afleverede og ligge i kassen.')
    if not source.get('area_id') or source.get('area_id')!=target.get('area_id') or source.get('kind')!=target.get('kind'):
        raise ValueError('Vælg kort med samme område og type.')
    pending=source.get('interim_transfer') or {}
    if target.get('interim_transfer') or (pending and mode!='finalize'):
        raise ValueError('Afslut den midlertidige flytning først.')
    if mode=='finalize' and (pending.get('status')!='pending' or pending.get('target_id')!=target['id'] or sorted(source.get('address_ids') or [])!=pending.get('address_ids')):
        raise ValueError('Det midlertidige kort eller modtageren er ændret. Kontrollér forløbet igen.')
    geo=[]
    def members(card):
        rows=card.get('geo_addresses');wanted=card.get('address_ids')
        if not isinstance(rows,list) or not isinstance(wanted,list) or not rows or not all(isinstance(i,str) for i in wanted) or not all(isinstance(a,dict) and isinstance(a.get('id'),str) for a in rows) or len(set(wanted))!=len(wanted) or {a.get('id') for a in rows}!=set(wanted) or len(rows)!=len(wanted):
            raise ValueError('Kontrollér kortenes præcise adressevalg før flytning.')
        count=0
        for a in rows:
            current=store.require('geo',a['id']);geo.append(current)
            keys=('id','road','number','floor','door','postcode','lat','lng','count','type','retired')
            if any(a.get(k)!=current.get(k) for k in keys) or current.get('retired'):
                raise ValueError('Adressedata er ændret. Opdater kortet i korteditoren før flytning.')
            if type(a.get('count')) is not int or a['count']<0 or a.get('count_unknown') or any(type(a.get(k)) not in (int,float) or not math.isfinite(a[k]) for k in ('lat','lng')) or not -90<=a['lat']<=90 or not -180<=a['lng']<=180:
                raise ValueError('Kontrollér kortenes præcise adressevalg før flytning.')
            count+=a['count']
        lines=card.get('addresses') or []
        if not lines or any(type(r.get('count')) is not int or r['count']<0 or r.get('count_unknown') for r in lines) or sum(r['count'] for r in lines)!=count:
            raise ValueError('Kontrollér kortenes præcise adressevalg før flytning.')
        return rows,count
    source_rows,source_count=members(source);target_rows,target_count=members(target)
    moving=data.get('address_ids')
    if not isinstance(moving,list) or not moving or len(moving)>10000 or not all(isinstance(i,str) for i in moving) or len(set(moving))!=len(moving):
        raise ValueError('Vælg hele adresseenheder til flytningen.')
    moving=set(moving);source_ids=set(source['address_ids'])
    if not moving<=source_ids or (mode=='finalize' and moving!=source_ids) or (mode!='finalize' and moving==source_ids):
        raise ValueError('Vælg nogle, men ikke alle, adresser. Et midlertidigt kort afsluttes samlet.')
    owners=[{'id':c['id'],'address_ids':c.get('address_ids',[])} for c in store.all('cards') if not c.get('archived') and moving.intersection(c.get('address_ids') or [])]
    if any(o['id']!=source['id'] for o in owners):raise ValueError('Adresserne findes på flere kort. Ret kortkontrollen først.')
    ib=[i for i in store.all('ib') if i.get('card_id') in ids]
    if any(i.get('card_id')==source['id'] and not i.get('address_id') for i in ib):
        raise ValueError('IB uden adressekobling skal knyttes til kortets adresseliste før opdeling.')
    notes=[n for n in store.all('notes') if n.get('card_id') in ids and n.get('entity')!='activity']
    number=clean_text(data.get('number'),30,True) if mode=='interim' else target['number']
    name=clean_text(data.get('name'),50) if mode=='interim' else ''
    if mode=='interim' and any(c['number'].casefold()==number.casefold() for c in store.all('cards')+store.all('cards',deleted=True)):
        raise ValueError('Det nye kortnummer findes allerede.')
    chosen=[deepcopy(a) for a in source_rows if a['id'] in moving]
    remaining=[deepcopy(a) for a in source_rows if a['id'] not in moving]
    moved=sum(a['count'] for a in chosen)
    dates=[d for d in (planning_date(source),planning_date(target),pending.get('reference_date')) if d]
    for day in dates:valid_day(day)
    reference=max(dates,default=None)
    intent={'mode':mode,'ids':ids,'address_ids':sorted(moving),'number':number,'name':name}
    expected=signature([source,target,geo,owners,ib,notes,intent])
    result={'expected':expected,'mode':mode,'numbers':[source['number'],target['number']],'number':number,'moving':len(chosen),'remaining':len(remaining),
            'visits':moved,'source_visits':source_count-moved,'target_visits':target_count+(moved if mode!='interim' else 0),'reference_date':reference}
    if action.endswith('preview'):return result
    if data.get('expected')!=expected or data.get('confirm')!='ÆNDR KORT':
        raise ValueError('Kontrollér forhåndsvisningen og skriv ÆNDR KORT for at bekræfte.')
    stamp=now()
    def assign(card,rows):
        card.update(address_ids=[a['id'] for a in rows],geo_addresses=rows,addresses=street_rows(rows),
                    geo_polygon=enclosing_outline([[a['lng'],a['lat']] for a in rows]),geo_outline_source='suggestion',front_revision=True,back_revision=True)
        store.put('cards',card)
    def task(card,text):
        store.put('notes',{'id':uuid.uuid4().hex,'card_id':card['id'],'date':stamp[:10],'created':stamp,'text':text,'task':True,'resolved':False})
    if mode=='interim':
        ident=store._mutate('card.save',{'number':number,'name':('Interim → '+target['number']+(' · '+name if name else '')),'area_id':source['area_id'],'kind':source['kind'],'temporary':True})['id']
        receiver=store.require('cards',ident);receiver['temporary']=False
        receiver['interim_transfer']={'status':'pending','source_id':source['id'],'target_id':target['id'],'source_number':source['number'],'target_number':target['number'],'address_ids':sorted(moving),'reference_date':reference,'created':stamp}
        assign(receiver,chosen)
        task(receiver,'Interim transfer from card '+source['number']+' to card '+target['number']+'. Print this interim number. After return, explicitly finalize the transfer and print the updated receiving card. No completion is created by moving addresses.')
        task(target,'Pending interim card '+number+': finalize only after return, then print both updated sides with the receiving card number.')
    else:
        receiver=target
        rows=[deepcopy(a) for a in target_rows]+chosen
        receiver['planning_reference']={'date':reference,'membership':sorted(a['id'] for a in rows),'origin_numbers':[source['number'],target['number']],'at':stamp}
        assign(receiver,rows)
        task(receiver,'Addresses received from card '+source['number']+'. Review the boundary and print both updated sides. The latest known date is a planning reference, not a completion event.')
    if mode=='finalize':
        source.update(archived=True,in_folder=False,replaced_by=target['id'],interim_transfer={**pending,'status':'finalized','finalized_at':stamp})
        store.put('cards',source)
    else:
        assign(source,remaining)
        task(source,'Addresses moved to card '+receiver['number']+'. Review the boundary and print both updated sides. Original loan and completion history is retained.')
    for item in ib:
        if item.get('card_id')==source['id'] and item.get('address_id') in moving:
            item['card_id']=receiver['id'];store.put('ib',item)
    return {'id':receiver['id'],'source_id':source['id'],'target_id':target['id'],'mode':mode,'count':len(chosen)}
