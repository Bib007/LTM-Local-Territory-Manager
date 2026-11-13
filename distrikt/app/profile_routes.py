"""Profile integration for the normal HTTP server; no anonymous bootstrap."""
from contextlib import contextmanager
from http.cookies import SimpleCookie
import hashlib
import hmac
import json
import threading
import time
from urllib.parse import urlsplit
from profile_accounts import PERMISSIONS
from profile_policy import route,mutation,state_for
from profile_edits import ReviewedMutation,capture
from edit_snapshots import EditSnapshots
from profile_workspace import ProfileWorkspace

ERRORS={
 'A name is required':'Udfyld et navn på højst 100 tegn.',
 'Password must contain 12–1024 characters':'Adgangskoden skal være mellem 12 og 1.024 tegn.',
 'At least one active account must manage users':'Den sidste aktive brugeradministrator kan ikke fjernes.',
 'Select existing roles':'Vælg mindst én eksisterende rolle.',
 'Unknown permission':'Vælg gyldige rettigheder fra listen.',
 'Role not found':'Rollen findes ikke længere. Åbn brugeradministrationen igen.',
 'Account not found':'Brugeren findes ikke længere. Åbn brugeradministrationen igen.',
 'Role name already exists':'Der findes allerede en rolle med det navn.',
 'Account name already exists':'Der findes allerede en bruger med det navn.',
 'Choose an initial password':'Vælg en adgangskode til den nye bruger.',
 'Accounts already exist':'Profiler er allerede aktiveret. Log ind med din individuelle konto.',
 'Edit snapshot is unavailable':'Redigeringens udgangspunkt er udløbet eller ikke længere tilgængeligt. Kopiér eventuelt din tekst, og åbn redigeringen igen.',
 'Too many active edit snapshots':'Der er ikke plads til flere aktive redigeringer. Afslut nogle åbne faner, eller prøv igen senere.',
}

def profile_error(error):
    return ValueError(ERRORS[str(error)]) if str(error) in ERRORS else error

class ProfileRuntime:
    def __init__(self,server,accounts):
        self.server=server;self.accounts=accounts
        self.cookie='ltm_profiles_beta' if server.beta else 'ltm_profiles'
        self.bases=EditSnapshots(capacity=512)
        self.workspace=ProfileWorkspace(accounts,server.store,self.bases)
        from profile_resolutions import ProfileResolutions
        self.reviews=ProfileResolutions(self)

    @property
    def enabled(self):return bool(self.accounts.data['users'])

    def token(self,cookie):
        try:
            value=SimpleCookie();value.load(cookie or '')
            return value[self.cookie].value if self.cookie in value else ''
        except Exception:return ''

    def csrf(self,token):
        return hmac.new(self.server.token.encode(),token.encode(),hashlib.sha256).hexdigest()

    def valid(self,cookie):
        try:
            with self.accounts.authorized_session(self.token(cookie)):return True
        except PermissionError:return False

    def cookie_header(self,token):
        return self.cookie+'='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age='+('43200' if token else '0')

    def authors(self,items):
        # Resolve legacy IDs only to known accounts; never guess an author.
        with self.accounts.lock:
            return [{**item,**({'actor_name':self.accounts.data['users'][item['actor_id']]['name']} if not item.get('actor_name') and item.get('actor_id') in self.accounts.data['users'] else {})} for item in items]

    def state(self,token,raw):
        with self.accounts.authorized_session(token) as user,self.server.store.lock:
            result=state_for(raw,user)
            result['recovery']=self.authors(result.get('recovery',[]))
            permissions=user['permissions']
            if 'reports.view' in permissions:
                result['report_congregation']=raw['settings'].get('congregation','')
            if {'reports.view','cards.view','geo.view'}<=permissions:
                totals=self.server.store.boundary_report()
                result['boundary_report']=None if totals is None else {
                    key:value for key,value in totals.items() if key!='ib' or 'ib.view' in permissions
                }
            if {'users.manage','notes.view'}<=user['permissions']:
                result['task_users']=[{'id':u['id'],'name':u['name']} for u in self.accounts.data['users'].values() if not u.get('disabled')]
            from profile_policy import MODULE_RIGHT
            modules={m for m,right in MODULE_RIGHT.items() if right in user['permissions']}
            if 'settings.manage' in user['permissions']:modules.add('settings')
            if {'geo.view','cards.view'}<=user['permissions']:modules.add('maps')
            self.bases.limit_session(token)
            result['profile']['snapshot']=self.bases.create(token,'workspace','workspace',capture(self.server.store,modules))
            result['profile']['conflicts']=len(self.workspace.conflicts(token))+(len(self.accounts.reviews(token)) if 'users.manage' in user['permissions'] else 0)
            from profile_policy import ACTIONS
            if ACTIONS['history.cleanup']<=permissions:
                result['history_cleanup_cutoff']=self.server.store.history_cutoff()
            result['undo_available']=False
            if raw['undo_available']:
                try:
                    mutation(user,'workflow.undo',{},self.server.store)
                except PermissionError:
                    pass
                else:
                    result['undo_available']=True
            return result

    def mutate(self,token,user,action,data,snapshot):
        store=self.server.store
        with store.lock:
            mutation(user,action,data,store)
            if action=='note.save' and data.get('assignee_id'):
                owner=self.accounts.data['users'].get(data['assignee_id']) if isinstance(data['assignee_id'],str) else None
                current=store.get('notes',data.get('id')) or {}
                if (not owner or owner.get('disabled')) and data['assignee_id']!=current.get('assignee_id'):
                    raise ValueError('Vælg en aktiv bruger som ansvarshavende.')
            if action.endswith('.preview'):return store.mutate(action,data),None
            with self.bases.claim(snapshot,token,'workspace','workspace') as base:
                reserved=[]
                protected=self.bases.is_protected(snapshot,token)
                def reserve(observed):reserved.append(self.bases.create(token,'workspace','workspace',observed,protected=protected))
                reviewed=ReviewedMutation(base,user['id'],reserve)
                reviewed.actor_name=user['name']
                try:result=store.mutate(action,data,review=reviewed)
                except BaseException:
                    for key in reserved:self.bases.discard(key,token)
                    raise
                return result,reserved[0]

class ProfileRoutes:
    def profile_token(self):return self.server.profiles.token(self.headers.get('Cookie'))

    @contextmanager
    def profile_scope(self,post=False):
        self.profile_user=None
        if not self.allowed(public=True):yield False;return
        runtime=self.server.profiles;handed=False
        try:
            # Accounts -> jobs/sharing -> Store. Keep rights stable through writes.
            with runtime.accounts.lock:
                if not runtime.enabled:handed=True;yield True;return
                path=urlsplit(self.path).path
                # The desktop updater owns the private run.json secret, but has
                # no browser session. Keep its stop channel local and distinct
                # from profile CSRF tokens; never allow it on the LAN/HA server.
                if (post and path=='/api/shutdown' and not self.server.access
                        and self.client_address[0]=='127.0.0.1'
                        and hmac.compare_digest(self.headers.get('X-Distrikt-Token',''),self.server.token)):
                    self.send({'ok':True})
                    threading.Thread(target=self.server.shutdown,daemon=True).start()
                    yield False;return
                if post and path=='/api/login':
                    self.profile_login();yield False;return
                protected=path.startswith('/api/') and path!='/api/ping' or path=='/card-qr.svg'
                if not post and not protected:handed=True;yield True;return
                token=self.profile_token()
                try:
                    with runtime.accounts.authorized_session(token) as user:self.profile_user=user
                except PermissionError:
                    self.send({'error':'Log ind igen på den lokale adresse.'},status=401);yield False;return
                if (post or path.startswith('/api/')) and not hmac.compare_digest(self.headers.get('X-Distrikt-Token',''),runtime.csrf(token)):
                    raise PermissionError()
                route(self.profile_user['permissions'],path,post)
                handed=True;yield True
        except PermissionError:
            self.send({'error':'Du har ikke rettighed til denne handling.'},status=403)
            if not handed:yield False

    def profile_login(self):
        try:
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError()
            length=int(self.headers.get('Content-Length',0))
            if not 0<length<4096:raise ValueError()
            data=json.loads(self.rfile.read(length))
            token=self.server.accounts.login(data.get('name'),data.get('password'),self.client_address[0])
            self.send({'ok':True},headers={'Set-Cookie':self.server.profiles.cookie_header(token)})
        except (ValueError,TypeError,AttributeError,PermissionError):
            self.send({'error':'Forkert brugernavn eller adgangskode. Vent fem minutter efter gentagne forsøg.'},status=401)

    def profile_get(self,path):
        if not self.server.profiles.enabled:return False
        runtime=self.server.profiles;token=self.profile_token()
        if path=='/api/profiles/guide':
            self.send(self.server.accounts.guide_current(token));return True
        if path=='/api/profiles/backup':
            from profile_recovery import backup_value
            self.send(backup_value(self.server.accounts),headers={'Content-Disposition':'attachment; filename="LTM-kontobackup.json"'});return True
        if path=='/api/profiles/session':
            self.send({'user':{k:v for k,v in self.profile_user.items() if k!='permissions'},'permissions':sorted(self.profile_user['permissions']),'enabled':True});return True
        if path=='/api/profiles/admin':
            from copy import deepcopy
            runtime.bases.limit_session(token)
            edit=runtime.bases.create(token,'accounts','accounts',{'id':'accounts','data':deepcopy(self.server.accounts.data)})
            self.send({**self.server.accounts.overview(token),'permissions':sorted(PERMISSIONS),'edit_snapshot':edit});return True
        if path=='/api/profiles/online':self.send(self.server.accounts.online(token));return True
        if path=='/api/profiles/conflicts':
            self.send(runtime.reviews.list(token));return True
        return False

    def profile_post(self,path,data):
        runtime=self.server.profiles;token=self.profile_token()
        if path=='/api/profiles/activate':
            if runtime.enabled:raise PermissionError()
            if data.get('confirmation')!='AKTIVÉR PROFILER':raise ValueError('Skriv AKTIVÉR PROFILER for at bekræfte.')
            self.server.accounts.bootstrap(data.get('name'),data.get('password'))
            self.send({'ok':True,'login_required':True});return True
        if not runtime.enabled:return False
        if path=='/api/profiles/edit-base':
            self.send({'snapshot':runtime.bases.fork(data.get('snapshot'),token)});return True
        if path=='/api/profiles/edit-base/release':
            runtime.bases.discard(data.get('snapshot'),token)
            self.send({'ok':True});return True
        if path=='/api/profiles/backup/preview':
            from profile_recovery import parsed_backup
            try:self.server.accounts.confirm_password(token,data.get('password'),self.client_address[0])
            except PermissionError:raise ValueError('Adgangskoden kunne ikke bekræftes. Kontrollér den, eller vent fem minutter efter gentagne forsøg.') from None
            if len(json.dumps(data.get('backup')).encode())>8*1024*1024:raise ValueError('Vælg en kontobackup på højst 8 MB i appen. Større filer gendannes med det lokale værktøj.')
            backup=parsed_backup(data.get('backup'))
            runtime.bases.limit_session(token)
            snapshot=runtime.bases.create(token,'account-restore','accounts',{'id':'accounts','data':backup,'generation':self.server.accounts.generation,'until':time.monotonic()+300})
            self.send({'snapshot':snapshot,'users':len(backup['users']),'roles':len(backup['roles'])});return True
        if path=='/api/profiles/backup/apply':
            if data.get('confirmation')!='GENDAN KONTI':raise ValueError('Skriv GENDAN KONTI for at bekræfte.')
            from profile_recovery import restore_value
            with runtime.bases.claim(data.get('snapshot'),token,'account-restore','accounts') as snapshot:
                if snapshot['until']<time.monotonic() or snapshot['generation']!=self.server.accounts.generation:raise ValueError('Konti eller roller er ændret, eller forhåndsvisningen er udløbet. Kontrollér filen igen.')
                restore_value(self.server.accounts,snapshot['data'])
                runtime.bases.clear()
                self.send({'ok':True,'login_required':True});return True
        if path=='/api/profiles/conflicts/resolve':
            runtime.reviews.resolve(token,data)
            self.send({'ok':True,'login_required':token not in self.server.accounts.sessions});return True
        if path in ('/api/profiles/roles/save','/api/profiles/users/save'):
            module='roles' if '/roles/' in path else 'users'
            with runtime.bases.claim(data.get('edit_snapshot'),token,'accounts','accounts') as snapshot:
                base=snapshot['data'][module].get(data.get('id'))
                if data.get('id') and base is None:raise ValueError('Åbn brugeren eller rollen igen.')
                if module=='roles':ident=self.server.accounts.save_role(token,data.get('name'),data.get('permissions'),data.get('id'),base=base)
                else:ident=self.server.accounts.save_user(token,data.get('name'),data.get('roles'),data.get('id'),data.get('disabled',False),data.get('password'),base=base)
                self.send({'id':ident});return True
        if path=='/api/profiles/guide/preview':
            from profile_features import STEPS
            from copy import deepcopy
            user=self.server.accounts.data['users'].get(data.get('user_id'))
            if not user:raise ValueError('Account not found')
            rights=self.server.accounts._permissions(self.server.accounts.data,user)
            self.send({'preview':True,'steps':[deepcopy(s) for s in STEPS if set(s['requires'])<=rights]});return True
        if path=='/api/profiles/guide/assign':
            assigned=self.server.accounts.guide_assign(token,data.get('user_id'),data.get('kind'),data.get('expected_assignment'))
            self.send({'ok':True,'assigned':assigned});return True
        if path=='/api/profiles/guide/replay':
            self.send(self.server.accounts.guide_replay(token));return True
        if path=='/api/profiles/guide/progress':
            self.send(self.server.accounts.guide_progress(token,data.get('run_id'),data.get('request_id'),data.get('step_id')));return True
        if path=='/api/profiles/heartbeat':
            self.server.accounts.heartbeat(token)
            status={'ok':True,'permissions':sorted(self.profile_user['permissions']),'auth_revision':self.server.accounts.generation,
                    'conflicts':len(runtime.workspace.conflicts(token))+(len(self.server.accounts.reviews(token)) if 'users.manage' in self.profile_user['permissions'] else 0)}
            if 'notes.view' in self.profile_user['permissions']:
                # Return only this account's count, never other users' task data.
                from profile_features import personal_open_task_count
                from datetime import date
                with self.server.store.lock:
                    status['my_open_tasks']=personal_open_task_count(self.server.store.all('notes'),date.today().isoformat(),self.profile_user['id'])
            self.send(status);return True
        if path=='/api/profiles/intro/complete':
            self.server.accounts.complete_intro(token);self.send({'ok':True});return True
        if path=='/api/profiles/conflicts/acknowledge':
            if str(data.get('id','')).startswith('account-review-'):
                self.server.accounts.acknowledge_review(token,data.get('id'));self.send({'changed':True});return True
            self.send({'changed':runtime.workspace.acknowledge_conflict(token,data.get('id'))});return True
        return False
