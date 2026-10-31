"""Session-owned bases, domain-validated merges and atomic conflict evidence."""
from copy import deepcopy
from datetime import datetime,timezone
import uuid
from concurrent_edits import reconcile,_equal,_value

SAVE={
 'card.save':('cards',set('number name area_id kind temporary map_color addresses'.split())),
 'publisher.save':('publishers',{'name'}),
 'note.save':('notes',{'text','card_id','recurrence'}),
 'ib.save':('ib',{'address_id','road','number','date'}),
 'area.save':('settings',{'name'}),
 'settings.save':('settings',{'congregation','folder_minimum','rural_minimum','rural_mode','require_revision'}),
 'visit.save':('visits',{'date','note'}),
 'card.color':('cards',{'map_color'}),
 'geo.boundary':('cards',{'geo_polygon'}),
 'map.outline':('cards',{'polygon'}),
}
REVIEW_FIELDS={
 'cards':set('number name area_id kind temporary map_color addresses geo_polygon address_ids geo_addresses imported_addresses polygon in_folder last_completed front_revision back_revision'.split()),
 'publishers':{'name'},'notes':{'text','card_id','recurrence','resolved','task_history'},
 'ib':{'address_id','road','number','date'},
 'visits':{'date','note'},'loans':{'assigned','cycle_start','returned','publisher_id'},
 'settings':set('congregation folder_minimum rural_minimum rural_mode require_revision name print_profiles saved_views'.split()),
 'maps':{'image','name'},
}

def capture(store,modules=None):
    return {'id':'workspace','records':{m:{r['id']:deepcopy(r) for r in store.all(m) if not r.get('entity')} for m in REVIEW_FIELDS if modules is None or m in modules}}

class ReviewedMutation:
    def __init__(self,base,actor,on_precommit=None):
        self.base=base;self.actor=actor;self.observed=deepcopy(base);self.conflicts=[]
        self.on_precommit=on_precommit

    def prepare(self,store,action,data):
        """Normalize in a rolled-back savepoint, then run the actual domain write once.

        Only these ordinary forms replace complete values from a stale form.
        Command operations (issue/return/import etc.) retain their existing
        current-state validation and their concrete approval tokens.
        """
        spec=SAVE.get(action)
        ident='config' if action=='settings.save' else data.get('card_id') if action in ('card.color','geo.boundary','map.outline') else data.get('id')
        if not spec or not ident:return data
        aliases={'geo.boundary':{'polygon':'geo_polygon'},'map.outline':{'points':'polygon'}}.get(action,{})
        draft={aliases.get(k,k):deepcopy(v) for k,v in data.items()}
        module,fields=spec;current=store.require(module,ident)
        original=self.base['records'].get(module,{}).get(ident)
        if original is None:raise ValueError('Åbn redigeringen igen for at hente dens udgangspunkt.')
        def canonical(field,value):
            if field=='recurrence' and isinstance(value,dict):return {k:value.get(k) for k in ('frequency','weekday')}
            if field=='map_color' and isinstance(value,str):return value.lower()
            if field in ('name','number','text','road') and isinstance(value,str):return value.strip()
            if field in ('area_id','address_id','card_id'):return value or None
            return value
        unchanged={f for f in fields if f in draft and _equal(canonical(f,draft[f]),canonical(f,original.get(f)))}
        trial=deepcopy(draft)
        for field in unchanged:
            if field in current:trial[field]=deepcopy(current[field])
            else:trial.pop(field,None)
        tracking=store._tracking;dirty=set(store._dirty_modules)
        store.db.execute('SAVEPOINT profile_normalize')
        try:
            store._tracking=None
            reverse={v:k for k,v in aliases.items()}
            store._mutate(action,{reverse.get(k,k):v for k,v in trial.items()})
            proposed=deepcopy(store.require(module,ident))
        finally:
            store.db.execute('ROLLBACK TO profile_normalize');store.db.execute('RELEASE profile_normalize')
            store._tracking=tracking;store._dirty_modules=dirty
        for field in unchanged:
            if field in original:proposed[field]=deepcopy(original[field])
            else:proposed.pop(field,None)
        reviewed=reconcile(original,current,proposed,fields)
        self.conflicts=[dict(c,module=module,record_id=ident) for c in reviewed['conflicts']]
        # The next base represents what this editor has observed, including
        # unchanged stale fields. It must not pretend a merged field was shown.
        self.observed['records'][module][ident]=proposed
        result=deepcopy(draft)
        for field in fields:
            if field in reviewed['record']:result[field]=deepcopy(reviewed['record'][field])
            else:result.pop(field,None)
        return {reverse.get(k,k):v for k,v in result.items()}

    def finish(self,store,touched):
        already={(c['module'],c['record_id'],c['field']) for c in self.conflicts}
        for (module,ident),previous in touched.items():
            if module not in REVIEW_FIELDS or not previous:continue
            import json
            current=json.loads(previous[1]);incoming=store.get(module,ident)
            original=self.base['records'].get(module,{}).get(ident)
            if original is None or incoming is None or current.get('entity'):continue
            # For domain commands, only fields actually changed by the command
            # are proposals. Unchanged fields cannot reverse an unrelated save.
            fields={f for f in REVIEW_FIELDS[module] if not _equal(_value(current,f),_value(incoming,f))}
            for c in reconcile(original,current,incoming,fields)['conflicts']:
                key=(module,ident,c['field'])
                if key not in already:
                    self.conflicts.append(dict(c,module=module,record_id=ident));already.add(key)
        for c in self.conflicts:
            store.put('settings',{'id':'edit-conflict:'+uuid.uuid4().hex,'entity':'edit-conflict',
                **deepcopy(c),'incoming_actor_id':self.actor,
                'at':datetime.now(timezone.utc).isoformat(timespec='microseconds'),'resolved':False})
        if self.on_precommit:self.on_precommit(self.observed)
