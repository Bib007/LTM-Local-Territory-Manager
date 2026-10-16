"""Local administrative operations on existing data files, always transactional."""
import hashlib
import json
import re
from datetime import date

def signature(items):
    return hashlib.sha256(json.dumps(items,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

class AdminStore:
    def bulk_fields(self,data):
        fields={}
        if data.get('area_id','__keep__')!='__keep__':
            area=data.get('area_id') or ''
            if area and (area=='config' or not self.get('settings',area)):raise ValueError('Området findes ikke.')
            fields['area_id']=area
        if data.get('kind','__keep__')!='__keep__':
            kind=data.get('kind')
            if kind not in ('By','Land','Ukendt'):raise ValueError('Vælg By, Land eller Ukendt.')
            fields['kind']=kind
        return fields

    def bulk_numbers(self,data):
        raw=data.get('numbers','')
        if not isinstance(raw,str) or len(raw)>20000:raise ValueError('Indsæt højst 500 kortnumre.')
        numbers=[n for n in re.split(r'[\s,;]+',raw.strip()) if n]
        if not numbers or len(numbers)>500:raise ValueError('Indsæt mellem 1 og 500 kortnumre.')
        if any(len(n)>30 for n in numbers):raise ValueError('Et kortnummer må højst have 30 tegn.')
        seen=set();duplicates=[]
        existing={c['number'].casefold() for c in self.all('cards')+self.all('cards',deleted=True)}
        for n in numbers:
            key=n.casefold()
            if key in seen or key in existing:duplicates.append(n)
            seen.add(key)
        return numbers,duplicates

    def bulk_cards(self,data):
        ids=data.get('ids')
        if not isinstance(ids,list) or not 1<=len(ids)<=1000 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):raise ValueError('Vælg 1–1.000 forskellige kort.')
        return [self.require('cards',i) for i in ids]

    def loan_correction(self,data):
        from store import valid_day
        loan=self.require('loans',data.get('id'));publisher=self.require('publishers',data.get('publisher_id'))
        day=valid_day(data.get('assigned'))
        if loan.get('cycle_start',loan['assigned'])!=loan['assigned'] and day>loan['cycle_start']:raise ValueError('Udleveringsdatoen må ikke ligge efter starten på en senere gennemgang.')
        events=sorted([e for e in self.all('completions') if e.get('loan_id')==loan['id']],key=lambda e:e['date'])
        if events and day>events[0]['date']:raise ValueError('Udleveringsdatoen må ikke ligge efter første gennemgang.')
        if loan.get('returned') and day>loan['returned']:raise ValueError('Udleveringsdatoen må ikke ligge efter afleveringen.')
        others=[l for l in self.all('loans') if l['card_id']==loan['card_id'] and l['id']!=loan['id']]
        end=loan.get('returned') or date.today().isoformat()
        if day!=loan['assigned'] and any(day<(l.get('returned') or date.today().isoformat()) and l['assigned']<end for l in others):raise ValueError('Datoen overlapper en anden udlevering af samme kort.')
        return loan,publisher,day,events,signature([loan,events,others])

    def admin_mutate(self,action,data):
        if action in ('card.bulk.preview','card.bulk.create'):
            numbers,duplicates=self.bulk_numbers(data);fields=self.bulk_fields(data)
            if action.endswith('preview'):return {'numbers':numbers,'duplicates':duplicates,'count':len(numbers)}
            if duplicates:raise ValueError('Listen indeholder eksisterende eller gentagne kortnumre. Ingen kort er oprettet.')
            ids=[self._mutate('card.save',dict(fields,number=n,temporary=True))['id'] for n in numbers]
            return {'ids':ids,'count':len(ids)}
        if action in ('card.bulk.edit.preview','card.bulk.edit'):
            cards=self.bulk_cards(data);fields=self.bulk_fields(data)
            if not fields:raise ValueError('Vælg et område eller en distriktstype, der skal ændres.')
            expected=signature(cards)
            changes=[{'id':c['id'],'number':c['number'],'before':{k:c.get(k,'') for k in fields},'after':fields} for c in cards if any(c.get(k,'')!=v for k,v in fields.items())]
            if action.endswith('preview'):return {'changes':changes,'selected':len(cards),'expected':expected}
            if data.get('expected')!=expected:raise ValueError('Kortene er ændret siden forhåndsvisningen. Kontrollér masseændringen igen.')
            for c in cards:self._mutate('card.save',dict(c,**fields))
            return {'count':len(changes)}
        if action in ('loan.correct.preview','loan.correct'):
            loan,publisher,day,events,expected=self.loan_correction(data)
            if action.endswith('preview'):return {'expected':expected,'card_number':self.require('cards',loan['card_id'])['number'],'before':{'assigned':loan['assigned'],'publisher_id':loan['publisher_id']},'after':{'assigned':day,'publisher_id':publisher['id']},'completions':len(events),'returned':loan.get('returned')}
            if data.get('expected')!=expected:raise ValueError('Udleveringen er ændret siden forhåndsvisningen. Kontrollér rettelsen igen.')
            previous=loan['assigned'];loan=dict(loan,assigned=day,publisher_id=publisher['id'])
            # Keep later cycles even if their completion history was cleaned up.
            # Only the original allocation date and its original cycle change.
            if events and events[0].get('assigned')==previous:
                self.put('completions',dict(events[0],assigned=day))
            if loan.get('cycle_start',previous)==previous:loan['cycle_start']=day
            self.put('loans',loan)
            return {'id':loan['id'],'completions':len(events)}
        raise ValueError('Ukendt administrativ handling.')

    def storage_info(self):
        from store import MODULES
        with self.lock:
            files=[{'module':m,'bytes':(self.root/(name+'.sqlite3')).stat().st_size} for m,name in MODULES.items()]
            categories={};postcodes={}
            for row in self.db.execute('SELECT payload FROM geo.records WHERE deleted_at IS NULL'):
                payload=row['payload'];record=json.loads(payload);size=len(payload.encode('utf8'));entity=record.get('entity','other')
                category=categories.setdefault(entity,{'count':0,'bytes':0});category['count']+=1;category['bytes']+=size
                if entity=='address':
                    p=postcodes.setdefault(record.get('postcode',''),{'postcode':record.get('postcode',''),'count':0,'bytes':0});p['count']+=1;p['bytes']+=size
            page_size=self.db.execute('PRAGMA geo.page_size').fetchone()[0];free=self.db.execute('PRAGMA geo.freelist_count').fetchone()[0]
            return {'files':files,'total_bytes':sum(f['bytes'] for f in files),'geo_bytes':next(f['bytes'] for f in files if f['module']=='geo'),'reusable_bytes':page_size*free,'categories':categories,'postcodes':sorted(postcodes.values(),key=lambda p:p['postcode'])}
