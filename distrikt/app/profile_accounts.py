"""Local accounts, configurable roles and session authorization for LTM."""
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
import unicodedata
import uuid
from copy import deepcopy
from datetime import datetime,timezone
from concurrent_edits import reconcile
from pathlib import Path
from contextlib import contextmanager

from access import write_private

PERMISSIONS=frozenset(('cards.view','cards.edit','loans.manage','publishers.manage',
    'ib.view','ib.edit','history.view','settings.manage','users.manage','activity.view','presence.view',
    'notes.view','notes.edit','publishers.view','loans.view','history.edit',
    'geo.view','geo.edit','backup.export','backup.restore','connections.manage','sharing.manage'))
SESSION_LIFETIME=12*60*60
ONLINE_WINDOW=90
KDF_ITERATIONS=600000


def _name(value):
    if not isinstance(value,str):raise ValueError('A name is required')
    value=unicodedata.normalize('NFKC',value).strip()
    if not value or len(value)>100:raise ValueError('A name is required')
    return value


def _secret(password,salt,iterations):
    return hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),bytes.fromhex(salt),iterations).hex()


def _credential(password):
    if not isinstance(password,str) or not 12<=len(password)<=1024:raise ValueError('Password must contain 12–1024 characters')
    salt=secrets.token_hex(24)
    return {'salt':salt,'hash':_secret(password,salt,KDF_ITERATIONS),'iterations':KDF_ITERATIONS}


class ProfileAccounts:
    def __init__(self,root,clock=time.monotonic,*,load=True):
        self.root=Path(root);self.path=self.root/'profiles.json';self.clock=clock
        self.lock=threading.RLock();self.sessions={};self.attempts={};self.account_attempts={}
        self.data=json.loads(self.path.read_text(encoding='utf-8')) if load and self.path.exists() else {'users':{},'roles':{}}

    def _write(self,data):
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        os.chmod(self.root,0o700)
        write_private(self.path,data)
        self.data=data

    def _copy(self):return json.loads(json.dumps(self.data))

    def _permissions(self,data,user):
        if not user or user.get('disabled'):return set()
        return {p for ident in user['roles'] for p in data['roles'].get(ident,{}).get('permissions',[]) if p in PERMISSIONS}

    def _require_admin_remaining(self,data):
        if not any('users.manage' in self._permissions(data,u) for u in data['users'].values()):
            raise ValueError('At least one active account must manage users')

    def _role_list(self,data,roles):
        if not isinstance(roles,list) or not roles or any(not isinstance(r,str) or r not in data['roles'] for r in roles):
            raise ValueError('Select existing roles')
        return list(dict.fromkeys(roles))

    def _session(self,token):
        session=self.sessions.get(token);now=self.clock()
        if not session or session['expires']<=now:
            self.sessions.pop(token,None);raise PermissionError('Sign in again')
        user=self.data['users'].get(session['user'])
        if not user or user.get('disabled'):
            self.sessions.pop(token,None);raise PermissionError('Sign in again')
        return session,user

    def authorize(self,token,permission):
        with self.lock:
            session,user=self._session(token)
            if permission not in self._permissions(self.data,user):raise PermissionError('Permission denied')
            session['seen']=self.clock()
            return user['id']

    @contextmanager
    def authorized_session(self,token):
        """Hold current session/rights stable through a local data operation.

        Lock order is accounts, then Store. Never acquire this while holding a
        Store lock. Returned values are copies and cannot grant permissions.
        """
        with self.lock:
            session,user=self._session(token)
            session['seen']=self.clock()
            yield {'id':user['id'],'name':user['name'],'onboarded':bool(user.get('onboarded')),
                   'permissions':frozenset(self._permissions(self.data,user))}

    def bootstrap(self,name,password):
        """Caller must first prove control of the existing installation."""
        with self.lock:
            if self.data['users']:raise ValueError('Accounts already exist')
            name=_name(name);cred=_credential(password);data=self._copy()
            role='role-'+uuid.uuid4().hex;ident='user-'+uuid.uuid4().hex
            data['roles'][role]={'id':role,'name':'Administrator','permissions':sorted(PERMISSIONS)}
            data['users'][ident]={'id':ident,'name':name,'roles':[role],'disabled':False,**cred}
            self._write(data);return ident

    def login(self,name,password,client):
        with self.lock:
            if not isinstance(client,str) or not client or len(client)>100:raise ValueError('Invalid client')
            now=self.clock()
            name=unicodedata.normalize('NFKC',name if isinstance(name,str) and len(name)<=100 else '').strip().casefold()
            account=hashlib.sha256(name.encode('utf-8')).hexdigest()
            # Never evict an active rate-limit entry merely because many names
            # or clients were supplied; discard expired entries, then fail closed.
            for bucket,key in ((self.attempts,client),(self.account_attempts,account)):
                if len(bucket)>=1000 and key not in bucket:
                    for old in list(bucket):
                        if not any(t>now-300 for t in bucket[old]):del bucket[old]
                    if len(bucket)>=1000:raise PermissionError('Try again later')
            attempts=[t for t in self.attempts.get(client,[]) if t>now-300]
            account_attempts=[t for t in self.account_attempts.get(account,[]) if t>now-300]
            if len(attempts)>=8 or len(account_attempts)>=8:raise PermissionError('Try again later')
            attempts.append(now);account_attempts.append(now)
            self.attempts[client]=attempts;self.account_attempts[account]=account_attempts
            user=next((u for u in self.data['users'].values() if u['name'].casefold()==name),None)
            # Perform the same KDF for unknown users; do not reveal which part failed.
            salt=user['salt'] if user else '00'*24
            iterations=user['iterations'] if user else KDF_ITERATIONS
            if type(iterations) is not int or not 100000<=iterations<=2000000:raise ValueError('Invalid credential settings')
            actual=_secret(password if isinstance(password,str) and len(password)<=1024 else '',salt,iterations)
            valid=hmac.compare_digest(actual,user['hash'] if user else '00'*32)
            if not user or user.get('disabled') or not valid:raise PermissionError('Incorrect login')
            self.attempts.pop(client,None);self.account_attempts.pop(account,None);token=secrets.token_urlsafe(40)
            self.sessions={k:v for k,v in self.sessions.items() if v['expires']>now}
            if len(self.sessions)>=100:self.sessions.pop(next(iter(self.sessions)))
            self.sessions[token]={'user':user['id'],'expires':now+SESSION_LIFETIME,'seen':now}
            return token

    def logout(self,token):
        with self.lock:self.sessions.pop(token,None)

    def _admin(self,token):self.authorize(token,'users.manage')

    def _review_account(self,data,module,old,proposed,base,actor):
        if base is None or old is None:return proposed
        if base.get('id')!=old['id']:raise ValueError('Åbn brugeren eller rollen igen.')
        def record(row):
            result=deepcopy(row)
            if module=='users':result['credential']={k:result.pop(k) for k in ('salt','hash','iterations')}
            return result
        fields={'name','permissions'} if module=='roles' else {'name','roles','disabled','credential'}
        result=reconcile(record(base),record(old),record(proposed),fields)
        for conflict in result['conflicts']:
            reviews=data.setdefault('reviews',[])
            if len(reviews)>=5000:raise ValueError('Gennemgå de gemte kontorettelser før flere ændringer.')
            reviews.append({'id':'account-review-'+uuid.uuid4().hex,'module':module,'record_id':old['id'],
                'actor_id':actor,'at':datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                **conflict,'resolved':False})
            # Changes to access rights/passwords do not silently win a collision.
            field=conflict['field']
            if field in record(old):result['record'][field]=deepcopy(record(old)[field])
            else:result['record'].pop(field,None)
        merged=result['record']
        if module=='users':merged.update(merged.pop('credential'))
        return merged

    def save_role(self,token,name,permissions,ident=None,*,base=None):
        with self.lock:
            self._admin(token);name=_name(name)
            if not isinstance(permissions,list) or any(p not in PERMISSIONS for p in permissions):raise ValueError('Unknown permission')
            data=self._copy()
            if ident is not None and ident not in data['roles']:raise ValueError('Role not found')
            ident=ident or 'role-'+uuid.uuid4().hex
            if ident not in data['roles'] and any(r['name'].casefold()==name.casefold() for r in data['roles'].values()):raise ValueError('Role name already exists')
            if any(r['id']!=ident and r['name'].casefold()==name.casefold() for r in data['roles'].values()):raise ValueError('Role name already exists')
            proposed={'id':ident,'name':name,'permissions':sorted(set(permissions))}
            data['roles'][ident]=self._review_account(data,'roles',data['roles'].get(ident),proposed,base,self.authorize(token,'users.manage'))
            if any(r['id']!=ident and r['name'].casefold()==data['roles'][ident]['name'].casefold() for r in data['roles'].values()):raise ValueError('Role name already exists')
            self._require_admin_remaining(data);self._write(data);return ident

    def save_user(self,token,name,roles,ident=None,disabled=False,password=None,*,base=None):
        with self.lock:
            self._admin(token);name=_name(name);data=self._copy();roles=self._role_list(data,roles)
            if type(disabled) is not bool:raise ValueError('Invalid account status')
            if ident is not None and ident not in data['users']:raise ValueError('Account not found')
            ident=ident or 'user-'+uuid.uuid4().hex;old=data['users'].get(ident)
            if any(u['id']!=ident and u['name'].casefold()==name.casefold() for u in data['users'].values()):raise ValueError('Account name already exists')
            if not old and password is None:raise ValueError('Choose an initial password')
            credential=_credential(password) if password is not None else {k:old[k] for k in ('salt','hash','iterations')}
            proposed={'id':ident,'name':name,'roles':roles,'disabled':disabled,**credential,
                                  **({'onboarded':old['onboarded']} if old and 'onboarded' in old else {})}
            if old and base is not None and password is None:
                # No password field in the form means the editor did not change
                # the observed credential, even if another admin just reset it.
                proposed.update({k:base[k] for k in ('salt','hash','iterations')})
            data['users'][ident]=self._review_account(data,'users',old,proposed,base,self.authorize(token,'users.manage'))
            if any(u['id']!=ident and u['name'].casefold()==data['users'][ident]['name'].casefold() for u in data['users'].values()):raise ValueError('Account name already exists')
            self._require_admin_remaining(data);self._write(data)
            if disabled or password is not None:self.sessions={k:v for k,v in self.sessions.items() if v['user']!=ident}
            return ident

    def overview(self,token):
        with self.lock:
            self._admin(token);data=self._copy()
            users=[{k:u[k] for k in ('id','name','roles','disabled')} for u in data['users'].values()]
            return {'users':users,'roles':list(data['roles'].values())}

    def reviews(self,token):
        with self.lock:
            self._admin(token);result=[]
            for row in self.data.get('reviews',[]):
                if row.get('resolved'):continue
                item=deepcopy(row)
                current=self.data[item['module']].get(item['record_id'],{})
                item['record_label']=('Bruger ' if item['module']=='users' else 'Rolle ')+current.get('name','')
                item['current']={'present':item['field'] in current,'value':deepcopy(current.get(item['field']))}
                if item['field']=='credential':
                    for key in ('base','saved','incoming','current'):item[key]={'present':True,'value':'Adgangskodeændring (vises ikke)'}
                result.append(item)
            return result

    def acknowledge_review(self,token,ident):
        with self.lock:
            self._admin(token);data=self._copy()
            row=next((r for r in data.get('reviews',[]) if r['id']==ident),None)
            if not row:raise ValueError('Kontorettelsen findes ikke.')
            row.update(resolved=True,reviewed_by=self.authorize(token,'users.manage'),reviewed_at=datetime.now(timezone.utc).isoformat())
            self._write(data)

    def online(self,token):
        with self.lock:
            self.authorize(token,'presence.view');now=self.clock();active={}
            for key in list(self.sessions):
                try:session,user=self._session(key)
                except PermissionError:continue
                if now-session['seen']<=ONLINE_WINDOW:active[user['id']]={'id':user['id'],'name':user['name']}
            return sorted(active.values(),key=lambda u:u['name'].casefold())

    def heartbeat(self,token):
        with self.lock:
            session,_=self._session(token);session['seen']=self.clock()

    def complete_intro(self,token):
        with self.lock:
            _,user=self._session(token)
            data=self._copy();data['users'][user['id']]['onboarded']=True;self._write(data)

    def recover_admin(self,name,password):
        """Local console only, with the application stopped and its file lock held."""
        with self.lock:
            name=_name(name);credential=_credential(password);data=self._copy()
            user=next((u for u in data['users'].values() if u['name'].casefold()==name.casefold()),None)
            ident=user['id'] if user else 'user-'+uuid.uuid4().hex
            role='role-'+uuid.uuid4().hex
            data['roles'][role]={'id':role,'name':'Gendannet administrator '+role[-8:],'permissions':sorted(PERMISSIONS)}
            data['users'][ident]={'id':ident,'name':name,'roles':[role],'disabled':False,**credential}
            self._write(data);self.sessions.clear()
            return ident
