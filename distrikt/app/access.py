"""Private LAN/VPN access; independent of Home Assistant and Nabu Casa."""
import hashlib
import hmac
import ipaddress
import json
import os
import secrets
import threading
import time
from http.cookies import SimpleCookie
from pathlib import Path
from remembered_sessions import RememberedSessions, REMEMBER_LIFETIME

PRIVATE=[ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','127.0.0.0/8','fc00::/7','::1/128')]

def private_client(address):
    try:
        ip=ipaddress.ip_address(address)
        return address!='172.30.32.2' and any(ip in net for net in PRIVATE)
    except ValueError:return False

def write_private(path,value):
    path=Path(path)
    tmp=path.with_name(path.name+'.'+secrets.token_hex(8)+'.tmp')
    try:
        fd=os.open(str(tmp),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        try:tmp.unlink()
        except FileNotFoundError:pass

class Access:
    def __init__(self,root,password=None):
        self.cookie_name='distrikt_beta_session' if os.environ.get('LTM_CHANNEL')=='beta' else 'distrikt_session'
        self.path=Path(root)/'access.json';self.sessions={};self.attempts={};self.lock=threading.RLock()
        self.remembered=RememberedSessions(root,'access-beta' if os.environ.get('LTM_CHANNEL')=='beta' else 'access')
        self.secret=json.loads(self.path.read_text()) if self.path.exists() else None
        if password is not None:
            if len(password)<12:raise ValueError('Vælg en adgangskode med mindst 12 tegn i HA-konfigurationen.')
            if not self.secret or not self.verify(password):
                salt=secrets.token_hex(24)
                self.secret={'salt':salt,'hash':self.hash(password,salt)};write_private(self.path,self.secret)
        if not self.secret:raise ValueError('LAN-adgang kræver en adgangskode. Brug DISTRIKT_PASSWORD ved første opstart.')
    @staticmethod
    def hash(password,salt):return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),240000).hex()
    def verify(self,password):return isinstance(password,str) and len(password)<=1024 and hmac.compare_digest(self.hash(password,self.secret['salt']),self.secret['hash'])
    def _credential_id(self):
        return hashlib.sha256((self.secret['salt']+self.secret['hash']).encode()).hexdigest()
    def login(self,password,ip,remember=False):
        if type(remember) is not bool:raise ValueError('Invalid remember option')
        with self.lock:
            now=time.monotonic();attempts=[t for t in self.attempts.get(ip,[]) if t>now-300]
            if len(attempts)>=8:raise ValueError('For mange forsøg. Vent fem minutter.')
            attempts.append(now);self.attempts[ip]=attempts
            if not self.verify(password):raise ValueError('Forkert adgangskode.')
            self.attempts.pop(ip,None)
            self.sessions={k:v for k,v in self.sessions.items() if v>now}
            if len(self.sessions)>=100:self.sessions.pop(next(iter(self.sessions)))
            token=secrets.token_urlsafe(40)
            if remember:self.remembered.issue(token,'shared',self._credential_id())
            self.sessions[token]=now+(REMEMBER_LIFETIME if remember else 12*3600)
            return token
    def valid(self,cookie):
        token=self.cookie(cookie)
        with self.lock:
            now=time.monotonic()
            if self.sessions.get(token,0)>now:return True
            self.sessions.pop(token,None)
            record=self.remembered.get(token)
            if not record or record['user']!='shared' or not hmac.compare_digest(record['credential'],self._credential_id()):return False
            remaining=record['until']-time.time()
            if remaining<=0:return False
            self.sessions[token]=now+remaining
            return True
    def logout(self,cookie):
        with self.lock:
            token=self.cookie(cookie)
            self.remembered.revoke(token)
            self.sessions.pop(token,None)
    def cookie(self,value):
        try:
            cookies=SimpleCookie();cookies.load(value or '');return cookies[self.cookie_name].value if self.cookie_name in cookies else ''
        except Exception:return ''

LOGIN='''<!doctype html><html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><script src="/theme.js"></script><title>LTM · Log ind</title><link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="/theme.css"><script src="/login.js" defer></script></head><body class="loginPage"><main><section class="panel"><h1>Local Territory Manager</h1><p data-ui="Privat adgang · hjemmenetværk og VPN">Privat adgang · hjemmenetværk og VPN</p><label for="loginLanguage" data-ui="Sprog">Sprog</label><select id="loginLanguage"><option value="da">Dansk</option><option value="en">English</option></select><h2 id="loginHeading" data-ui="Log ind">Log ind</h2><form id="loginForm" aria-labelledby="loginHeading"><label for="loginPassword" data-ui="Adgangskode">Adgangskode</label><input id="loginPassword" aria-describedby="loginError" name="password" type="password" autocomplete="current-password" maxlength="1024" required autofocus><label class="check" for="rememberLogin"><input id="rememberLogin" type="checkbox"> <span data-ui="Forbliv logget på i 7 dage">Forbliv logget på i 7 dage</span></label><p id="loginError" class="formError" role="alert"></p><button class="primary" type="submit" data-ui="Log ind">Log ind</button></form></section></main></body></html>'''

if os.environ.get('LTM_CHANNEL')=='beta':
    LOGIN=LOGIN.replace('<script src="/theme.js"></script><title>LTM · Log ind</title>','<title>LTM Beta · Log ind</title>').replace('<h1>Local Territory Manager</h1>','<h1>Local Territory Manager · Beta</h1>')
