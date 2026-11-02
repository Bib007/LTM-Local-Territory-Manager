"""Aggregate-only status and session-bound, read-only personal guides."""
from calendar import monthrange
from copy import deepcopy
from datetime import date
import uuid

DASHBOARD_LEGACY=frozenset(('cards.view','history.view','loans.view','publishers.view','notes.view','geo.view'))
REPORT_LEGACY=frozenset(('cards.view','history.view','loans.view','publishers.view'))
RELEASE='roles-guides-1'
# Stable feature ids survive a beta -> stable version-name change.
STEPS=(
 {'id':'start','page':'Forside','requires':(), 'title':('Din startside','Your start page'),'text':('Menuen viser de funktioner, dine roller giver adgang til. Du kan altid genåbne din egen guide.','The menu shows the features allowed by your roles. You can always reopen your own guide.')},
 {'id':'status','feature':'summary-status','page':'Forside','requires':('dashboard.view',),'title':('Forsidestatus','Home status'),'text':('Her vises samlede tal for distrikter, gennemgange og udleveret eller hjemme. Oversigtsretten giver ikke adgang til enkeltpersoner eller enkeltsager.','See totals for territories, completions, and assigned or home. Summary access does not grant access to people or individual records.')},
 {'id':'reports','feature':'summary-reports','page':'Rapporter','requires':('reports.view',),'title':('Rapportoversigt','Report summary'),'text':('Sammenlign kalenderår, tjenesteår og seneste 12 måneder. Gennemgange tælles hver gang; distrikter tælles én gang. Detaljer kræver særskilt adgang.','Compare the calendar year, service year and last 12 months. Every completion counts; territories count once. Details require separate access.')},
 {'id':'cards','page':'Distrikter','requires':('cards.view',),'title':('Distriktskort','Territory cards'),'text':('Find og læs dine kort. Indhold og handlinger følger dine aktuelle rettigheder.','Find and read your cards. Content and actions follow your current permissions.')},
 {'id':'desk','page':'Udlevering','requires':('cards.view','loans.view'),'title':('Daglig brug','Daily work'),'text':('Se kortenes udleveringsstatus. Knapper til ændringer kræver de relevante administrationsrettigheder.','See card assignment status. Changes require the relevant management permissions.')},
 {'id':'people','page':'Forkyndere','requires':('publishers.view',),'title':('Forkyndere','Publishers'),'text':('Denne side viser forkyndere. Administration kræver også redigeringsadgang.','This page shows publishers. Management also requires edit access.')},
 {'id':'tasks','page':'Opgaver','requires':('notes.view',),'title':('Opgaver','Tasks'),'text':('Læs opgaver her. Guiden opretter eller ændrer ingen opgaver.','Read tasks here. The guide does not create or change tasks.')},
 {'id':'roles','feature':'personal-guides','page':'Indstillinger','section':'users','requires':('users.manage',),'title':('Brugere og egne roller','Users and custom roles'),'text':('Opret egne roller med tydelige rettigheder. Du kan planlægge en individuel guide til en brugers næste login uden at ændre vedkommendes rettigheder.','Create custom roles with clear permissions. Schedule a personal guide for a user’s next login without changing their permissions.')},
 {'id':'settings','page':'Indstillinger','section':'general','requires':('settings.manage',),'title':('Fælles opsætning','Shared setup'),'text':('Fælles opsætning er adskilt fra din personlige guide. Guiden ændrer ingen indstillinger.','Shared setup is separate from your personal guide. The guide changes no settings.')},
)

def summaries(raw):
    """No raw identifiers/text/addresses leave this projection."""
    today=date.fromisoformat(raw['today']);y=today.year;service=y+1 if today.month>=9 else y
    rolling=date(y-1,today.month,min(today.day,monthrange(y-1,today.month)[1]))
    periods={'calendar':(date(y,1,1),today),'service':(date(service-1,9,1),today),'rolling':(rolling,today)}
    cards=raw['cards'];ids={c['id'] for c in cards};assigned={l['card_id'] for l in raw['loans'] if not l.get('returned') and l['card_id'] in ids}
    result={}
    for kind,(start,end) in periods.items():
        a,b=start.isoformat(),end.isoformat();events=[e for e in raw['completions'] if a<=e.get('date','')<=b]
        done={e['card_id'] for e in events if e['card_id'] in ids}
        done.update(c['id'] for c in cards if a<=(c.get('last_completed') or '')<=b)
        missing=ids-done
        result[kind]={'start':a,'end':b,'completions':len(events),'territories':len(ids),'completed_territories':len(done),'missing':len(missing),'assigned':len(assigned),'home':len(ids-assigned),'missing_assigned':len(missing&assigned),'missing_home':len(missing-assigned)}
    return {'as_of':raw['today'],'revision':raw['revision'],'periods':result}


def guide_valid(value):
    """Strict bounded account-backup contract. No credentials/permissions here."""
    if not isinstance(value,dict) or set(value)-{'schema','completed_steps','seen_features','assigned','completed_assignment','assigned_steps'} or type(value.get('schema')) is not int or value.get('schema')!=1:raise ValueError('Ugyldig personlig guide.')
    for key in ('completed_steps','seen_features','assigned_steps'):
        items=value.get(key,[])
        if not isinstance(items,list) or len(items)>256 or any(not isinstance(v,str) or len(v)>100 for v in items):raise ValueError('Ugyldig personlig guide.')
    assigned=value.get('assigned')
    if assigned is not None:
        if not isinstance(assigned,dict) or set(assigned)!={'id','kind','release'} or assigned['kind'] not in ('intro','news') or assigned['release']!=RELEASE:raise ValueError('Ugyldig guideanmodning.')
        if not isinstance(assigned['id'],str) or len(assigned['id'])!=32 or any(c not in '0123456789abcdef' for c in assigned['id']):raise ValueError('Ugyldig guideanmodning.')
    completed=value.get('completed_assignment','')
    if not isinstance(completed,str) or len(completed)>32:raise ValueError('Ugyldig personlig guide.')
    return value


class GuideAccounts:
    def guide_assign(self,token,ident,kind,expected):
        with self.lock:
            self._admin(token)
            if kind not in ('intro','news'):raise ValueError('Vælg en gyldig guide.')
            old=self.data['users'].get(ident)
            if not old:raise ValueError('Account not found')
            current=old.get('intro',{}).get('assigned')
            if expected!=(current or {}).get('id',''):raise ValueError('Guideplanen er ændret. Åbn brugeren igen.')
            data=self._copy();intro=data['users'][ident].setdefault('intro',{'schema':1})
            intro['assigned']={'id':uuid.uuid4().hex,'kind':kind,'release':RELEASE};intro['assigned_steps']=[]
            self._write(data)
            return deepcopy(intro['assigned'])

    def _guide_run(self,token):
        session,user=self._session(token);intro=user.get('intro',{});p=self._permissions(self.data,user)
        # Assignment was captured at successful login, never from heartbeat.
        assigned=session.get('guide_assignment')
        if not user.get('onboarded'):kind,request='intro','first'
        elif assigned and assigned==intro.get('assigned') and intro.get('completed_assignment')!=assigned['id']:kind,request=assigned['kind'],assigned['id']
        else:kind,request='news','release-'+RELEASE
        run=session.get('guide_run')
        if run and run['kind']=='replay':kind,request='replay',run['request_id']
        if not run or run['request_id']!=request:
            run={'id':uuid.uuid4().hex,'kind':kind,'request_id':request,'done':[]};session['guide_run']=run
        steps=[deepcopy(s) for s in STEPS if set(s['requires'])<=p and (kind!='news' or s.get('feature'))]
        done=intro.get('completed_steps',[]) if request=='first' else intro.get('assigned_steps',[]) if assigned and request==assigned['id'] else run['done']
        steps=[s for s in steps if s['id'] not in done and (kind!='news' or request!='release-'+RELEASE or s['feature'] not in intro.get('seen_features',[]))]
        return session,user,run,steps

    def guide_current(self,token):
        with self.lock:
            _,_,run,steps=self._guide_run(token)
            return {'run_id':run['id'],'request_id':run['request_id'],'kind':run['kind'],'release':RELEASE,'auth_revision':self.generation,'steps':steps}

    def guide_replay(self,token):
        with self.lock:
            session,_=self._session(token);session['guide_run']={'id':uuid.uuid4().hex,'kind':'replay','request_id':uuid.uuid4().hex,'done':[]}
            return self.guide_current(token)

    def guide_progress(self,token,run_id,request_id,step_id):
        with self.lock:
            session,user=self._session(token)
            receipt=session.get('guide_receipts',{}).get(run_id)
            if receipt and receipt['request']==request_id and step_id in receipt['steps']:return self.guide_current(token)
            session,user,run,steps=self._guide_run(token)
            if run_id!=run['id'] or request_id!=run['request_id']:raise ValueError('Guiden er ændret. Åbn guiden igen.')
            if step_id in run['done']:return self.guide_current(token)
            step=next((s for s in steps if s['id']==step_id),None)
            if step is None:raise PermissionError('Du har ikke adgang til dette guidetrin.')
            data=self._copy();target=data['users'][user['id']];intro=target.setdefault('intro',{'schema':1})
            if run['kind']!='replay':
                if request_id=='first':key='completed_steps'
                elif request_id==(intro.get('assigned') or {}).get('id'):key='assigned_steps'
                else:key=None
                if key:intro[key]=sorted(set(intro.get(key,[]))|{step_id})
                if step.get('feature'):intro['seen_features']=sorted(set(intro.get('seen_features',[]))|{step['feature']})
                if len(steps)==1:
                    if request_id=='first':target['onboarded']=True
                    elif request_id==(intro.get('assigned') or {}).get('id'):intro['completed_assignment']=request_id
                self._write(data)
            run['done'].append(step_id)
            receipts=session.setdefault('guide_receipts',{})
            if len(receipts)>=64 and run_id not in receipts:receipts.pop(next(iter(receipts)))
            receipts[run_id]={'request':request_id,'steps':list(run['done'])}
            return self.guide_current(token)
