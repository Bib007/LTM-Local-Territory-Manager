"""Explicit conflict choices through domain validation and atomic evidence."""
from copy import deepcopy
from datetime import datetime,timezone
from concurrent_edits import _equal,_value
from profile_edits import ReviewedMutation,capture,SAVE
from profile_policy import mutation
from profile_workspace import EDIT,VIEWS
from profile_recovery import validated


def account_record(row):
    value=deepcopy(row)
    value['credential']={k:value.pop(k,None) for k in ('salt','hash','iterations')}
    return value


def command(row,current):
    module,field=row['module'],row['field']
    actions={'cards':'card.save','publishers':'publisher.save','notes':'note.save','ib':'ib.save','visits':'visit.save'}
    action=actions.get(module)
    if module=='settings':action='settings.save' if current.get('id')=='config' else 'area.save'
    if module=='cards' and field in ('map_color','geo_polygon','address_ids','polygon'):
        action={'map_color':'card.color','geo_polygon':'geo.boundary','address_ids':'geo.assign','polygon':'map.outline'}[field]
    if not action or field not in SAVE[action][1]:return None
    data=deepcopy(current)
    if action.startswith(('card.color','geo.','map.')):data['card_id']=current['id']
    return action,data


class ResolutionWrite(ReviewedMutation):
    def __init__(self,base,actor,ident,choice):
        super().__init__(base,actor);self.ident,self.choice=ident,choice

    def finish(self,store,touched):
        super().finish(store,touched)
        row=store.require('settings',self.ident)
        row.update(resolved=True,reviewed_by=self.actor,reviewed_at=datetime.now(timezone.utc).isoformat(),selected=self.choice)
        store.put('settings',row)


class ProfileResolutions:
    def __init__(self,runtime):self.runtime=runtime

    def list(self,token):
        r=self.runtime
        with r.accounts.authorized_session(token) as user,r.server.store.lock:
            rows=r.workspace.conflicts(token)
            if 'users.manage' in user['permissions']:rows+=r.accounts.reviews(token)
            r.bases.limit_session(token)
            result=[]
            for row in rows[:100]:
                item=deepcopy(row);account=row['module'] in ('users','roles')
                current=(r.accounts.data[row['module']].get(row['record_id']) if account else r.server.store.get(row['module'],row['record_id']))
                writable=('users.manage' in user['permissions'] if account else EDIT.get(row['module']) in user['permissions'])
                item['can_ack']=writable
                item['can_choose']=bool(writable and current and (account or command(row,current)))
                if item['can_choose']:
                    value=_value(account_record(current) if account and row['module']=='users' else current,row['field'])
                    item['review_snapshot']=r.bases.create(token,'review',row['id'],{'id':row['id'],'current':value})
                result.append(item)
            return result

    def resolve(self,token,data):
        r=self.runtime;store=r.server.store;ident=data.get('id');choice=data.get('choice')
        if choice not in ('saved','incoming'):raise ValueError('Vælg en af de to gemte rettelser.')
        with r.accounts.authorized_session(token) as user,store.lock,r.bases.claim(data.get('review_snapshot'),token,'review',ident) as observed:
            if ident.startswith('account-review-'):
                r.accounts._admin(token)
                accounts=r.accounts._copy();row=next((v for v in accounts.get('reviews',[]) if v['id']==ident),None)
                if not row or row['resolved']:raise ValueError('Rettelsen er allerede gennemgået. Opdater oversigten.')
                current=accounts[row['module']].get(row['record_id'])
                if not current:raise ValueError('Brugeren eller rollen findes ikke længere.')
                view=account_record(current) if row['module']=='users' else current
                if not _equal(_value(view,row['field']),observed['current']):raise ValueError('Oplysningen er ændret igen. Åbn gennemgangen, og vælg ud fra den aktuelle værdi.')
                selected=row[choice]
                if not selected['present']:raise ValueError('Denne oplysning kan ikke fjernes. Ret den i sin formular.')
                if row['field']=='credential':current.update(deepcopy(selected['value']))
                else:current[row['field']]=deepcopy(selected['value'])
                row.update(resolved=True,reviewed_by=user['id'],reviewed_at=datetime.now(timezone.utc).isoformat(),selected=choice)
                validated(accounts);r.accounts._require_admin_remaining(accounts);r.accounts._write(accounts)
                if row['module']=='users' and row['field'] in ('credential','disabled'):
                    r.accounts.sessions={k:v for k,v in r.accounts.sessions.items() if v['user']!=row['record_id']}
                return
            row=store.get('settings',ident)
            if not row or row.get('entity')!='edit-conflict' or row.get('resolved'):raise ValueError('Rettelsen er allerede gennemgået. Opdater oversigten.')
            if row['module'] not in VIEWS or VIEWS[row['module']][0] not in user['permissions'] or EDIT.get(row['module']) not in user['permissions']:raise PermissionError()
            current=store.require(row['module'],row['record_id'])
            if not _equal(_value(current,row['field']),observed['current']):raise ValueError('Oplysningen er ændret igen. Åbn gennemgangen, og vælg ud fra den aktuelle værdi.')
            spec=command(row,current)
            if spec is None:raise ValueError('Denne oplysning skal ændres i sin almindelige formular.')
            action,values=spec;selected=row[choice]
            if not selected['present']:raise ValueError('Denne oplysning skal ændres i sin almindelige formular.')
            values[row['field']]=deepcopy(selected['value'])
            if action in ('geo.boundary','geo.assign'):values['polygon']=values.pop('geo_polygon',[])
            if action=='map.outline':values['points']=values.pop('polygon',[])
            mutation(user,action,values,store)
            review=ResolutionWrite(capture(store),user['id'],ident,choice)
            store.mutate(action,values,review=review)
