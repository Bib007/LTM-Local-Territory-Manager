"""Authorized profile overview, server edit bases and conflict review."""
from copy import deepcopy
from conflict_reviews import pending, acknowledge
from profile_edits import REVIEW_FIELDS

# Explicit fields keep new database fields private until reviewed here.
VIEWS = {
    'cards': ('cards.view', ('id','number','name','kind','area_id','map_color','temporary','in_folder','archived')),
    'publishers': ('publishers.view', ('id','name')),
    'loans': ('loans.view', ('id','card_id','publisher_id','assigned','cycle_start','returned','initial')),
    'ib': ('ib.view', ('id','card_id','address_id','road','number','date')),
    'notes': ('notes.view', ('id','card_id','loan_id','text','date','created','resolved','resolved_at','task','recurrence')),
    'completions': ('history.view', ('id','card_id','loan_id','date','previous_completed')),
    'visits': ('history.view', ('id','date','note')),
}
EDIT = {'cards':'cards.edit','publishers':'publishers.manage','ib':'ib.edit','notes':'notes.edit'}
# Only fields supported by the reconciliation prototype can be reviewed here.
CONFLICT_FIELDS = REVIEW_FIELDS
VIEWS.update(visits=('history.view',('id','date','note')),
             settings=('settings.manage',('id','name')),maps=('geo.view',('id','name')))
EDIT.update(visits='history.edit',loans='loans.manage',settings='settings.manage',maps='geo.edit')
NOTICE_FIELDS = ('id','module','record_id','field','at','incoming_actor_id',
                 'base','saved','incoming','resolved')


class ProfileWorkspace:
    def __init__(self, accounts, store, snapshots):
        self.accounts, self.store, self.snapshots = accounts, store, snapshots

    def overview(self, token):
        """A minimal profile overview; denied modules are absent, not counted."""
        with self.accounts.authorized_session(token) as user, self.store.lock:
            result={'user':{'id':user['id'],'name':user['name']},
                    'permissions':sorted(user['permissions']), 'records':{}}
            for module,(permission,fields) in VIEWS.items():
                if permission not in user['permissions']:continue
                result['records'][module]=[
                    {key:deepcopy(row[key]) for key in fields if key in row}
                    for row in self.store.all(module) if not row.get('entity')]
            return result

    def _review_modules(self, permissions):
        return {m for m in CONFLICT_FIELDS if VIEWS[m][0] in permissions}

    def conflicts(self, token):
        with self.accounts.authorized_session(token) as user,self.store.lock:
            rows=pending(self.store,self._review_modules(user['permissions']))
            result=[]
            for row in rows:
                if row.get('field') not in CONFLICT_FIELDS[row['module']]:continue
                value={key:deepcopy(row[key]) for key in NOTICE_FIELDS if key in row}
                current=self.store.get(row['module'],row.get('record_id')) or {}
                if row['module']=='cards':value['record_label']='Kort '+str(current.get('number',''))
                value['current']={'present':row['field'] in current,'value':deepcopy(current.get(row['field']))}
                result.append(value)
            return result

    def acknowledge_conflict(self, token, ident):
        """An explicit acknowledgement; never applied just by reading a page."""
        with self.accounts.authorized_session(token) as user, self.store.lock:
            modules={m for m in self._review_modules(user['permissions']) if EDIT[m] in user['permissions']}
            row=self.store.get('settings',ident)
            if not row or row.get('module') not in modules or row.get('field') not in CONFLICT_FIELDS[row['module']]:
                raise PermissionError('Review unavailable')
            return acknowledge(self.store,ident,modules,user['id'])

    def begin_edit(self, token, module, ident):
        """Issue a base from the database, never from client-submitted values."""
        with self.accounts.authorized_session(token) as user, self.store.lock:
            if module not in EDIT or EDIT[module] not in user['permissions'] or VIEWS[module][0] not in user['permissions']:
                raise PermissionError('Editing unavailable')
            row=self.store.require(module,ident)
            if row.get('entity'):raise PermissionError('Editing unavailable')
            fields=CONFLICT_FIELDS[module]
            base={k:deepcopy(row[k]) for k in fields|{'id'} if k in row}
            snapshot=self.snapshots.create(token,module,ident,base)
            return {'snapshot':snapshot,'record':base}
