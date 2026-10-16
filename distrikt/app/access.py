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

PRIVATE=[ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','127.0.0.0/8','fc00::/7','::1/128')]

def private_client(address):
    try:
        ip=ipaddress.ip_address(address)
        return address!='172.30.32.2' and any(ip in net for net in PRIVATE)
    except ValueError:return False

def write_private(path,value):
    path=Path(path);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value));os.chmod(tmp,0o600);os.replace(tmp,path)

class Access:
    def __init__(self,root,password=None):
        self.path=Path(root)/'access.json';self.sessions={};self.attempts={};self.lock=threading.RLock()
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
    def login(self,password,ip):
        with self.lock:
            now=time.monotonic();attempts=[t for t in self.attempts.get(ip,[]) if t>now-300]
            if len(attempts)>=8:raise ValueError('For mange forsøg. Vent fem minutter.')
            attempts.append(now);self.attempts[ip]=attempts
            if not self.verify(password):raise ValueError('Forkert adgangskode.')
            self.attempts.pop(ip,None)
            self.sessions={k:v for k,v in self.sessions.items() if v>now}
            if len(self.sessions)>=100:self.sessions.pop(next(iter(self.sessions)))
            token=secrets.token_urlsafe(40);self.sessions[token]=now+12*3600
            return token
    def valid(self,cookie):
        token=self.cookie(cookie)
        with self.lock:return self.sessions.get(token,0)>time.monotonic()
    def logout(self,cookie):
        with self.lock:self.sessions.pop(self.cookie(cookie),None)
    @staticmethod
    def cookie(value):
        try:
            cookies=SimpleCookie();cookies.load(value or '');return cookies['distrikt_session'].value if 'distrikt_session' in cookies else ''
        except Exception:return ''

LOGIN='''<!doctype html><html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Distrikt · Log ind</title><link rel="stylesheet" href="/style.css"><script src="/login.js" defer></script></head><body class="loginPage"><main><section class="panel"><h1>Distrikt</h1><p>Privat adgang · hjemmenetværk og VPN</p><form id="loginForm"><label>Adgangskode</label><input name="password" type="password" autocomplete="current-password" maxlength="1024" required autofocus><p id="loginError" role="alert"></p><button class="primary">Log ind</button></form></section></main></body></html>'''
