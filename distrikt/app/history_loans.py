"""Plan additive S-13 allocations against the same frozen local revision."""
import uuid

def norm(value):return str(value or '').strip().casefold()
def overlaps(a,b):
    return a['assigned']<(b.get('returned') or '9999-12-31') and b['assigned']<(a.get('returned') or '9999-12-31')

class LoanPreview:
    def __init__(self,store,today,cutoff):
        self.today=today;self.cutoff=cutoff
        self.people={};self.deleted_people={norm(p['name']) for p in store.all('publishers',deleted=True)}
        for person in store.all('publishers'):self.people.setdefault(norm(person['name']),[]).append(person)
        self.existing=store.all('loans');self.by_card={};self.deleted_by_card={}
        for loan in self.existing:self.by_card.setdefault(loan['card_id'],[]).append(loan)
        for loan in store.all('loans',deleted=True):self.deleted_by_card.setdefault(loan['card_id'],[]).append(loan)
        self.completions={};by_loan={}
        for e in store.all('completions'):
            self.completions.setdefault((e['card_id'],e['date']),[]).append(e)
            if e.get('loan_id'):by_loan.setdefault(e['loan_id'],[]).append(e)
        self.recovery={(e['card_id'],e['date']) for e in store.all('completions',deleted=True)}
        self.new_loans=[];self.new_people={};self.links=[];self.events={};self.seen=set();self.known=set();self.claimed=set()
        # Retained-card cycles already stored in one loan are duplicates too.
        for loan in self.existing:
            cycle=loan['assigned']
            for e in sorted(by_loan.get(loan['id'],[]),key=lambda e:e['date']):
                self.known.add((loan['card_id'],loan['publisher_id'],e.get('assigned') or cycle,e['date']));cycle=e['date']
            if not loan.get('returned'):self.known.add((loan['card_id'],loan['publisher_id'],loan.get('cycle_start') or loan['assigned'],None))

    def add(self,row,card,name,assigned,returned):
        if not name or len(name)>100 or any(ord(c)<32 for c in name) or '?' in name or '\ufffd' in name:
            raise ValueError('Ret forkyndernavnet; det mangler eller kunne ikke aflæses entydigt.')
        if not assigned:raise ValueError('Udleveringsdatoen mangler.')
        if assigned>self.today or returned and returned>self.today:raise ValueError('Datoen ligger i fremtiden.')
        if returned and returned<assigned:raise ValueError('Indlevering skal være på eller efter udlevering.')
        row.update(publisher=name,assigned=assigned,returned=returned or '',date=returned or '',loan_state='closed' if returned else 'active')
        if returned and returned<self.cutoff:row.update(status='outside',message='Ældre end to år; medtages ikke.');return
        matches=self.people.get(norm(name),[])
        if len(matches)>1:raise ValueError('Forkyndernavnet er ikke entydigt. Ret navnene i LTM før import.')
        person=matches[0] if matches else None
        if not person and norm(name) in self.deleted_people:raise ValueError('Forkynderen findes i Gendan ved fejl. Gendan personen først.')
        key=(card['id'],person['id'] if person else norm(name),assigned,returned)
        if key in self.seen or key in self.known:
            row.update(status='duplicate',message='Allerede kendt eller gentaget; medtages ikke.');return
        if card.get('archived') and not returned:raise ValueError('Et arkiveret kort kan ikke importeres som aktivt udlån.')
        candidate={'card_id':card['id'],'assigned':assigned,'returned':returned}
        current=self.by_card.get(card['id'],[])
        existing=next((l for l in current if person and l['publisher_id']==person['id'] and l['assigned']==assigned and l.get('returned')==returned),None)
        for old in self.deleted_by_card.get(card['id'],[]):
            if old['card_id']==card['id'] and (overlaps(candidate,old) or old['assigned']==assigned):raise ValueError('Udlånet findes i Gendan ved fejl. Gendan eller fjern det dér først.')
        for old in current:
            if old['card_id']==card['id'] and (not existing or old['id']!=existing['id']) and overlaps(candidate,old):
                raise ValueError('Udlånet overlapper et andet udlån på kortet. Ret eller fjern rækken før import.')
        if not returned and any(not l.get('returned') for l in current):
            raise ValueError('Kortet har allerede et andet aktivt udlån.')
        completion=None
        if returned:
            if (card['id'],returned) in self.recovery:raise ValueError('Gennemgangen findes i Gendan ved fejl. Gendan eller fjern den dér først.')
            matches=self.completions.get((card['id'],returned),[])
            if len(matches)>1 or (card['id'],returned) in self.claimed:raise ValueError('Flere udleveringer har samme gennemgangsdato. Ret rækken før import.')
            completion=matches[0] if matches else None
            if completion and completion.get('loan_id') and (not existing or completion['loan_id']!=existing['id']):
                raise ValueError('Gennemgangsdatoen er knyttet til et andet udlån. Ret rækken før import.')
        if not person:
            person=self.new_people.setdefault(norm(name),{'id':uuid.uuid4().hex,'name':name})
        row.update(publisher=person['name'],publisher_action='existing' if norm(name) in self.people else 'new')
        loan=existing or dict(candidate,id=uuid.uuid4().hex,publisher_id=person['id'],cycle_start=assigned,initial=True,source='history-import')
        if not existing:self.new_loans.append(loan);self.by_card.setdefault(card['id'],[]).append(loan)
        if returned:
            if completion:
                if not completion.get('loan_id'):
                    self.links.append({'id':completion['id'],'loan_id':loan['id'],'assigned':assigned})
                    row['completion_action']='link'
            else:self.events[(card['id'],returned)]={'card_id':card['id'],'date':returned,'loan_id':loan['id'],'assigned':assigned};row['completion_action']='new'
        if returned:self.claimed.add((card['id'],returned))
        self.seen.add(key);row['status']='ready'

    def payload(self):return {'publishers':list(self.new_people.values()),'loans':self.new_loans,'links':self.links}

def apply_loans(store,plan):
    for person in plan['publishers']:store.put('publishers',person)
    for loan in plan['loans']:
        store.put('loans',loan)
        if not loan.get('returned'):
            card=dict(store.require('cards',loan['card_id']));card['in_folder']=False;store.put('cards',card)
    for link in plan['links']:
        entry=dict(store.require('completions',link['id']));entry.update(loan_id=link['loan_id'],assigned=link['assigned']);store.put('completions',entry)
