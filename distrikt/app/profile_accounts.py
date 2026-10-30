"""Isolated local prototype for accounts, configurable roles and recent sessions.

Not connected to LTM's login or HTTP routes. The migration, authorization of
every endpoint, restore behavior and recovery of administrator access remain
to be designed and verified before use in the application.
"""
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
import unicodedata
import uuid
from pathlib import Path

from access import write_private

PERMISSIONS=frozenset(('cards.view','cards.edit','loans.manage','publishers.manage',
    'ib.view','ib.edit','history.view','settings.manage','users.manage','activity.view','presence.view'))
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
    def __init__(self,root,clock=time.monotonic):
        self.root=Path(root);self.path=self.root/'profiles.json';self.clock=clock
        self.lock=threading.RLock();self.sessions={};self.attempts={};self.account_attempts={}
        self.data=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {'users':{},'roles':{}}

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

    def save_role(self,token,name,permissions,ident=None):
        with self.lock:
            self._admin(token);name=_name(name)
            if not isinstance(permissions,list) or any(p not in PERMISSIONS for p in permissions):raise ValueError('Unknown permission')
            data=self._copy()
            if ident is not None and ident not in data['roles']:raise ValueError('Role not found')
            ident=ident or 'role-'+uuid.uuid4().hex
            if ident not in data['roles'] and any(r['name'].casefold()==name.casefold() for r in data['roles'].values()):raise ValueError('Role name already exists')
            if any(r['id']!=ident and r['name'].casefold()==name.casefold() for r in data['roles'].values()):raise ValueError('Role name already exists')
            data['roles'][ident]={'id':ident,'name':name,'permissions':sorted(set(permissions))}
            self._require_admin_remaining(data);self._write(data);return ident

    def save_user(self,token,name,roles,ident=None,disabled=False,password=None):
        with self.lock:
            self._admin(token);name=_name(name);data=self._copy();roles=self._role_list(data,roles)
            if type(disabled) is not bool:raise ValueError('Invalid account status')
            if ident is not None and ident not in data['users']:raise ValueError('Account not found')
            ident=ident or 'user-'+uuid.uuid4().hex;old=data['users'].get(ident)
            if any(u['id']!=ident and u['name'].casefold()==name.casefold() for u in data['users'].values()):raise ValueError('Account name already exists')
            if not old and password is None:raise ValueError('Choose an initial password')
            credential=_credential(password) if password is not None else {k:old[k] for k in ('salt','hash','iterations')}
            data['users'][ident]={'id':ident,'name':name,'roles':roles,'disabled':disabled,**credential}
            self._require_admin_remaining(data);self._write(data)
            if disabled or password is not None:self.sessions={k:v for k,v in self.sessions.items() if v['user']!=ident}
            return ident

    def overview(self,token):
        with self.lock:
            self._admin(token);data=self._copy()
            users=[{k:u[k] for k in ('id','name','roles','disabled')} for u in data['users'].values()]
            return {'users':users,'roles':list(data['roles'].values())}

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
