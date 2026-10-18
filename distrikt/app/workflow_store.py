"""Local workflow tools. Activity stores summaries only; undo payloads stay in RAM."""
import copy
import json
import time
import uuid
from geography import enclosing_outline, street_rows
from admin_store import signature


class WorkflowStore:
    def workflow_init(self):
        self.revision=uuid.uuid4().hex
        self._geo_cache=None
        self._info_cache=None
        self._setup_previews={}
        self._undo=None
        self._tracking=None
        self._dirty_modules=set()

    def workflow_track(self,module,ident):
        if self._tracking is not None and (module,ident) not in self._tracking:
            row=self.db.execute('SELECT id,payload,deleted_at,batch FROM '+self.alias(module)+'.records WHERE id=?',(ident,)).fetchone()
            self._tracking[module,ident]=tuple(row) if row else None

    def activity(self,limit=200):
        with self.lock:
            return sorted([r for r in self.all('notes') if r.get('entity')=='activity'],key=lambda r:r['at'],reverse=True)[:limit]

    def workflow_mutate(self,action,data):
        from store import clean_text, now
        if action=='filter.save':
            config=dict(self.require('settings','config'));views=list(config.get('saved_views',[]))
            name=clean_text(data.get('name'),60,True)
            allowed={'query','area','status','kind','page','addressTab','addressPostcode','filters'}
            raw=data.get('view')
            if not isinstance(raw,dict) or len(json.dumps(raw))>4000:raise ValueError('Ugyldig filtervisning.')
            view={k:v for k,v in raw.items() if k in allowed}
            views=[v for v in views if v['name']!=name]
            if len(views)>=30:raise ValueError('Der kan gemmes højst 30 visninger.')
            views.append({'id':uuid.uuid4().hex,'name':name,'view':view});config['saved_views']=views;self.put('settings',config);return {}
        if action=='filter.delete':
            config=dict(self.require('settings','config'));config['saved_views']=[v for v in config.get('saved_views',[]) if v['id']!=data.get('id')];self.put('settings',config);return {}
        if action=='backup.record':
            config=dict(self.require('settings','config'));config['last_backup']=now();self.put('settings',config);return {}
        if action=='workflow.undo':
            entry=self._undo
            if not entry or entry['until']<time.monotonic() or entry['revision']!=self.revision:raise ValueError('Fortryd er udløbet, eller data er ændret siden handlingen.')
            for (module,ident),row in entry['rows'].items():
                self._dirty_modules.add(module)
                self.workflow_track(module,ident)
                self.db.execute('DELETE FROM '+self.alias(module)+'.records WHERE id=?',(ident,))
                if row:self.db.execute('INSERT INTO '+self.alias(module)+'.records(id,payload,deleted_at,batch) VALUES(?,?,?,?)',row)
            return {'undone':entry['action']}
        if action in ('card.restructure.preview','card.restructure.apply'):
            return self.restructure(action,data)
        if action=='note.task':
            n=self.require('notes',data.get('id'))
            if n.get('entity')=='activity':raise ValueError('Vælg en opgave.')
            n['task']=True;n['resolved']=False;self.put('notes',n);return {'id':n['id']}
        if action=='address.change.review':
            self._dirty_modules.add('geo')
            pending=self.require('geo',data.get('id'))
            if pending.get('entity')!='address_change':raise ValueError('Vælg en adresseændring.')
            if data.get('decision') not in ('accept','reject'):raise ValueError('Vælg godkend eller afvis.')
            if data['decision']=='accept':
                after=pending['after'];current=self.get('geo',after['id'])
                if current!=pending.get('before'):raise ValueError('Adressen er ændret. Genindlæs kontrollen.')
                self.put('geo',after)
                self.db.execute('UPDATE geo.records SET deleted_at=NULL,batch=NULL WHERE id=?',(after['id'],))
            self.db.execute('DELETE FROM geo.records WHERE id=?',(pending['id'],));return {}
        raise ValueError('Ukendt arbejdsgang.')

    def restructure(self,action,data):
        from store import clean_text,now
        mode=data.get('mode');ids=data.get('ids',[])
        if mode not in ('split','merge') or not isinstance(ids,list) or len(set(ids))!=len(ids):raise ValueError('Vælg opdel eller sammenlæg.')
        if (mode=='split' and len(ids)!=1) or (mode=='merge' and not 2<=len(ids)<=20):raise ValueError('Vælg ét kort til opdeling eller 2–20 til sammenlægning.')
        cards=[self.require('cards',i) for i in ids]
        if any(self.active_loan(c['id']) for c in cards):raise ValueError('Aflever kortene før opdeling eller sammenlægning.')
        if any(c.get('archived') or c.get('temporary') for c in cards):raise ValueError('Vælg færdige aktive kort med adresser.')
        number=clean_text(data.get('number'),30,True)
        if any(c['number'].casefold()==number.casefold() for c in self.all('cards')+self.all('cards',deleted=True)):raise ValueError('Det nye kortnummer findes allerede.')
        members=[]
        for c in cards:
            rows=c.get('geo_addresses') or [self.require('geo',i) for i in c.get('address_ids',[])]
            if not rows:raise ValueError('Kortet skal have geografisk valgte adresser før opdeling/sammenlægning.')
            members.extend(rows)
        if len({a['id'] for a in members})!=len(members):raise ValueError('Kortene indeholder dublerede adresser. Ret kortkontrollen først.')
        moving=set(data.get('address_ids',[])) if mode=='split' else {a['id'] for a in members}
        if not moving or not moving<{a['id'] for a in members} and mode=='split':raise ValueError('Vælg nogle, men ikke alle, adresser til det nye kort.')
        if not moving<={a['id'] for a in members}:raise ValueError('Adressevalget er ikke på kortet.')
        chosen=[a for a in members if a['id'] in moving]
        ib=self.all('ib');notes=[n for n in self.all('notes') if n.get('card_id') in ids]
        # Text-only IB may refer to several units. Never guess which new card owns it.
        if mode=='split' and any(i['card_id'] in ids and not i.get('address_id') for i in ib):raise ValueError('IB uden adressekobling skal knyttes til kortets adresseliste før opdeling.')
        expected=signature([cards,ib,notes])
        result={'expected':expected,'mode':mode,'numbers':[c['number'] for c in cards],'number':number,'moving':len(chosen),'remaining':len(members)-len(chosen),'warning':'Historik bevares på de oprindelige kort. Nye kort får ingen opdigtet gennemgang. Grænser er forslag og skal kontrolleres. Forsider og IB-bagsider skal genprintes.'}
        if action.endswith('preview'):return result
        if data.get('expected')!=expected or data.get('confirm')!='ÆNDR KORT':raise ValueError('Kontrollér forhåndsvisningen og skriv ÆNDR KORT for at bekræfte.')
        source=cards[0];ident=self._mutate('card.save',dict(number=number,name=clean_text(data.get('name'),100),area_id=source.get('area_id',''),kind=source.get('kind','Ukendt'),temporary=True))['id']
        def assign(c,addresses):
            c.update(address_ids=[a['id'] for a in addresses],geo_addresses=addresses,addresses=street_rows(addresses),geo_polygon=enclosing_outline([[a['lng'],a['lat']] for a in addresses]),geo_outline_source='suggestion',temporary=False,front_revision=True,back_revision=True)
            self.put('cards',c)
        assign(self.require('cards',ident),chosen)
        if mode=='split':assign(source,[a for a in members if a['id'] not in moving])
        else:
            for c in cards:
                c.update(archived=True,in_folder=False,replaced_by=ident)
                self.put('cards',c)
        for i in ib:
            if i['card_id'] in ids and (mode=='merge' or i.get('address_id') in moving):i['card_id']=ident;self.put('ib',i)
        if mode=='merge':
            for n in notes:n['card_id']=ident;self.put('notes',n)
        self.put('notes',{'id':uuid.uuid4().hex,'card_id':ident,'date':now()[:10],'created':now(),'text':'Kontrollér den foreslåede grænse og genprint efter '+('opdeling' if mode=='split' else 'sammenlægning')+'. Historik: kort '+', '.join(c['number'] for c in cards)+'.','task':True,'resolved':False})
        return {'id':ident,'count':len(chosen)}
