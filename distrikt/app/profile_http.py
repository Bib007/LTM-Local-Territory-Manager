"""Loopback-only integration server for the unfinished profile workflow.

Not used by the normal LTM launcher. Accounts must already be initialized by
an authorized owner. No bootstrap endpoint, legacy API or external listener.
"""
import hashlib
import hmac
import json
import secrets
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from profile_accounts import PERMISSIONS
from profile_workspace import ProfileWorkspace
from edit_snapshots import EditSnapshots

COOKIE='ltm_profile_preview'

class ProfilePreviewServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self, accounts, store):
        if not accounts.data['users']:raise ValueError('Initialize accounts through the owner first')
        super().__init__(('127.0.0.1',0),ProfileHandler)
        self.accounts=accounts
        self.workspace=ProfileWorkspace(accounts,store,EditSnapshots())
        self.csrf_secret=secrets.token_bytes(32)
        self.origin='http://127.0.0.1:'+str(self.server_port)
    def csrf(self,token):
        return hmac.new(self.csrf_secret,token.encode(),hashlib.sha256).hexdigest()

class ProfileHandler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def respond(self,status,value,headers=None,kind='application/json'):
        raw=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode()
        self.send_response(status)
        for key,val in {'Content-Type':kind+'; charset=utf-8','Content-Length':str(len(raw)),
                        'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
                        'Referrer-Policy':'no-referrer',
                        'Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",**(headers or {})}.items():
            self.send_header(key,val)
        self.end_headers();self.wfile.write(raw)
    def token(self):
        try:
            cookies=SimpleCookie();cookies.load(self.headers.get('Cookie',''))
            return cookies[COOKIE].value if COOKIE in cookies else ''
        except Exception:return ''
    def dispatch(self,post=False):
        try:
            if self.headers.get('Host')!=self.server.origin.removeprefix('http://'):
                raise PermissionError('Unknown host')
            if self.headers.get('Origin') not in (None,self.server.origin):raise PermissionError('Wrong origin')
            if post and self.headers.get('Origin')!=self.server.origin:raise PermissionError('Origin required')
            path=urlsplit(self.path).path
            if not post and path in ('/','/profile-preview.js','/profile-preview.css'):
                name={'/':'profile-preview.html','/profile-preview.js':'profile-preview.js','/profile-preview.css':'profile-preview.css'}[path]
                kind={'/':'text/html','/profile-preview.js':'text/javascript','/profile-preview.css':'text/css'}[path]
                return self.respond(200,(Path(__file__).parent/name).read_bytes(),kind=kind)
            data={}
            if post:
                if self.headers.get('Content-Type')!='application/json':raise ValueError('JSON required')
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=32768:raise ValueError('Invalid body size')
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict):raise ValueError('Object required')
            if post and path=='/api/profiles/login':
                token=self.server.accounts.login(data.get('name'),data.get('password'),self.client_address[0])
                return self.respond(200,{'ok':True},headers={'Set-Cookie':COOKIE+'='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200'})
            token=self.token()
            with self.server.accounts.authorized_session(token):
                if post and not hmac.compare_digest(self.headers.get('X-LTM-CSRF',''),self.server.csrf(token)):
                    raise PermissionError('Invalid request token')
                if not post:
                    if path=='/api/profiles/session':return self.respond(200,{'csrf':self.server.csrf(token),'overview':self.server.workspace.overview(token)})
                    if path=='/api/profiles/conflicts':return self.respond(200,self.server.workspace.conflicts(token))
                    if path=='/api/profiles/online':return self.respond(200,self.server.accounts.online(token))
                    if path=='/api/profiles/admin':return self.respond(200,{**self.server.accounts.overview(token),'permissions':sorted(PERMISSIONS)})
                else:
                    if path=='/api/profiles/logout':
                        self.server.workspace.snapshots.revoke_session(token);self.server.accounts.logout(token)
                        return self.respond(200,{'ok':True},headers={'Set-Cookie':COOKIE+'=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
                    if path=='/api/profiles/roles/save':
                        ident=self.server.accounts.save_role(token,data.get('name'),data.get('permissions'),data.get('id'))
                        return self.respond(200,{'id':ident})
                    if path=='/api/profiles/users/save':
                        ident=self.server.accounts.save_user(token,data.get('name'),data.get('roles'),data.get('id'),data.get('disabled',False),data.get('password'))
                        return self.respond(200,{'id':ident})
                    if path=='/api/profiles/conflicts/acknowledge':
                        return self.respond(200,{'changed':self.server.workspace.acknowledge_conflict(token,data.get('id'))})
            self.respond(404,{'error':'Ukendt funktion.'})
        except PermissionError:self.respond(403,{'error':'Log ind, eller kontrollér dine rettigheder.'})
        except (ValueError,TypeError,KeyError):self.respond(400,{'error':'Kontrollér oplysningerne. Ændringen kunne ikke udføres.'})
        except Exception:self.respond(500,{'error':'Lokal fejl. Kontrollér resultatet før et nyt forsøg.'})
    def do_GET(self):self.dispatch()
    def do_POST(self):self.dispatch(True)
