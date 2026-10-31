"""Explicit default-deny rules for the real application's profile mode.

Managing users never implies permission to read territory or personal data.
All checks run under the accounts lock, before the Store lock is acquired.
"""
from copy import deepcopy
from profile_accounts import PERMISSIONS

READ_ALL=frozenset(('cards.view','publishers.view','loans.view','ib.view','notes.view',
                    'history.view','geo.view','activity.view','settings.manage'))
WRITE_ALL=frozenset(('cards.edit','publishers.manage','loans.manage','ib.edit','notes.edit',
                     'history.edit','geo.edit','settings.manage'))

GET={
 '/api/state':(), '/api/profiles/session':(), '/api/profiles/conflicts':(),
 '/api/profiles/admin':('users.manage',), '/api/profiles/online':('presence.view',),
 '/api/geo':('cards.view','geo.view'), '/api/geo/job':('geo.view',),
 '/api/geo/suggest':('geo.view',), '/api/map':('cards.view','geo.view'),
 '/api/storage':('settings.manage',), '/api/data-info':('settings.manage',),
 '/api/activity':('activity.view',), '/api/address-source/status':('connections.manage',),
 '/api/share/status':('sharing.manage','cards.view'),
 '/api/share/qr':('sharing.manage','cards.view'), '/card-qr.svg':('sharing.manage','cards.view'),
 '/api/export/s13':('history.view','loans.view','publishers.view','cards.view'),
 '/api/export/backup':READ_ALL|{'backup.export'}, '/api/restore/safety':READ_ALL|{'backup.export'},
 '/api/setup/card-template.xlsx':('cards.edit',), '/api/setup/card-template.csv':('cards.edit',),
 '/api/setup/ib-template.csv':('ib.edit',),
 '/api/photo/status':('ib.view','ib.edit'), '/api/photo/job':('ib.view','ib.edit'),
}
POST={
 '/api/logout':(), '/api/profiles/heartbeat':(),
 '/api/profiles/intro/complete':(),
 '/api/profiles/users/save':('users.manage',), '/api/profiles/roles/save':('users.manage',),
 '/api/profiles/conflicts/acknowledge':(),
 '/api/mutate':(),
 '/api/restore/preview':READ_ALL|WRITE_ALL|{'backup.restore'},
 '/api/restore/apply':READ_ALL|WRITE_ALL|{'backup.restore'},
 '/api/beta/reset':READ_ALL|WRITE_ALL|{'backup.restore'},
 '/api/export/readable/prepare':READ_ALL|{'backup.export'},
 '/api/export/readable/image':READ_ALL|{'backup.export'},
 '/api/export/readable/finish':READ_ALL|{'backup.export'},
 '/api/share/connect':('connections.manage','sharing.manage'),
 '/api/share/disconnect':('connections.manage','sharing.manage'),
 '/api/share/prepare':('sharing.manage','cards.view','geo.view'),
 '/api/share/publish':('sharing.manage','cards.view','geo.view'),
 '/api/share/withdraw':('sharing.manage','cards.view'), '/api/share/retry':('sharing.manage','cards.view'),
 '/api/address-source/connect':('connections.manage',), '/api/address-source/check':('connections.manage',),
 '/api/address-source/diagnose':('connections.manage',), '/api/address-source/disconnect':('connections.manage',),
 '/api/geo/download':('geo.view','geo.edit','connections.manage'), '/api/geo/pause':('geo.edit',),
 '/api/photo/read':('ib.view','ib.edit'), '/api/photo/cancel':('ib.view','ib.edit'),
 '/api/open-data':('settings.manage',), '/api/shutdown':('settings.manage',),
}

def require(permissions,needed):
    if needed is None or not set(needed)<=set(permissions):
        raise PermissionError('Du har ikke rettighed til denne handling.')

def route(permissions,path,post=False):
    require(permissions,(POST if post else GET).get(path))

GROUPS={
 ('cards.view','cards.edit'):'card.save card.color card.bulk.preview card.bulk.create card.bulk.edit.preview card.bulk.edit revision.approve',
 ('cards.view','geo.view','geo.edit','cards.edit'):'geo.assign geo.boundary geo.preview map.save map.outline card.restructure.preview card.restructure.apply',
 ('geo.view','geo.edit','cards.view','ib.view'):'geo.manual geo.type geo.import geo.import_file geo.postcode.save geo.postcode.road geo.main.save geo.main.prune.preview geo.main.prune geo.main.download.save geo.main.download.tile geo.main.import.preview ignore.save address.change.review',
 ('connections.manage',):'geo.token',
 ('cards.view','loans.view','loans.manage'):'folder.set loan.issue loan.finish',
 ('loans.view','loans.manage','publishers.view','publishers.manage'):'loan.correct.preview loan.correct',
 ('publishers.view','publishers.manage'):'publisher.save',
 ('notes.view','notes.edit'):'note.save note.resolve note.task note.complete',
 ('cards.view','history.view','history.edit'):'completion.record',
 ('history.view','history.edit'):'visit.save history.cleanup',
 ('cards.view','ib.view','ib.edit'):'ib.save setup.ib.preview setup.ib.apply',
 ('settings.manage',):'settings.save print.profile.save area.save area.delete filter.save filter.delete setup.onboarding.save setup.onboarding.task setup.defaults',
 ('settings.manage','geo.view','geo.edit','connections.manage'):'address.task.configure',
 ('backup.export',):'backup.record backup.snooze',
 ('cards.view','cards.edit','geo.view'):'setup.card-import.preview setup.card-import.apply',
 ('cards.view','cards.edit','loans.view','loans.manage','history.view','history.edit','publishers.view','publishers.manage'):'setup.history-import.preview setup.history-import.apply',
}
ACTIONS={action:frozenset(rights) for rights,actions in GROUPS.items() for action in actions.split()}
CASCADE=frozenset(('cards.view','cards.edit','loans.view','loans.manage','history.view','history.edit','ib.view','ib.edit','notes.view','notes.edit','geo.view','geo.edit'))
ACTIONS.update({'card.restructure.preview':CASCADE,'card.restructure.apply':CASCADE})
DELETE={'cards':CASCADE,'ib':{'cards.view','ib.view','ib.edit'},
        'notes':{'notes.view','notes.edit'},'visits':{'history.view','history.edit'},
        'loans':{'loans.view','loans.manage'},'completions':{'history.view','history.edit'},
        'ignored':{'geo.view','geo.edit'}}

def mutation(user,action,data,store):
    needed=ACTIONS.get(action)
    if action=='delete':needed=DELETE.get(data.get('module'))
    if action in ('restore','recovery.purge'):needed=READ_ALL|WRITE_ALL|{'backup.restore'}
    if action=='workflow.undo':
        entry=store._undo or {}
        if entry.get('actor_id')!=user['id']:raise PermissionError('Fortryd findes kun for din egen seneste handling.')
        needed=ACTIONS.get(entry.get('action'))
        if needed is not None:
            needed=set(needed)
            extra={'cards':{'cards.view','cards.edit'},'notes':{'notes.view','notes.edit'},
                   'publishers':{'publishers.view','publishers.manage'},'loans':{'loans.view','loans.manage'},
                   'ib':{'ib.view','ib.edit'},'completions':{'history.view','history.edit'},
                   'visits':{'history.view','history.edit'},'settings':{'settings.manage'}}
            for module,_ in entry.get('rows',{}):needed.update(extra.get(module,READ_ALL|WRITE_ALL))
    require(user['permissions'],needed)
    # A write that creates a publisher or note also needs that module's right.
    if action=='loan.issue' and not data.get('publisher_id'):require(user['permissions'],('publishers.view','publishers.manage'))
    if action=='loan.issue':require(user['permissions'],('publishers.view',))
    if action=='loan.finish' and data.get('complete'):require(user['permissions'],('history.view','history.edit'))
    if action=='revision.approve' and data.get('side')=='back':require(user['permissions'],('ib.view',))
    if action in ('loan.finish','completion.record') and data.get('note'):require(user['permissions'],('notes.view','notes.edit'))

CARD_FIELDS=set('id number name kind area_id map_color temporary in_folder archived last_completed created front_revision back_revision front_approved back_approved addresses address_ids geo_addresses imported_addresses geo_polygon geo_outline_source geo_updated polygon'.split())
FIELDS={
 'cards':CARD_FIELDS,'archived_cards':CARD_FIELDS,
 'publishers':{'id','name'},
 'loans':set('id card_id publisher_id assigned cycle_start returned initial'.split()),
 'ib':set('id card_id address_id road number date'.split()),
 'notes':set('id card_id loan_id completion_id text date created resolved resolved_at task recurrence task_history'.split()),
 'completions':set('id card_id loan_id date assigned previous_completed visits'.split()),
 'visits':{'id','date','note'},
}
MODULE_RIGHT={'cards':'cards.view','archived_cards':'cards.view','publishers':'publishers.view',
              'loans':'loans.view','ib':'ib.view','notes':'notes.view','completions':'history.view','visits':'history.view'}
CONFIG_FIELDS=set('id schema congregation folder_minimum rural_mode rural_minimum require_revision folder_minimum_configured print_profiles saved_views last_backup backup_snoozed_until backup_history onboarding'.split())

def state_for(raw,user):
    p=user['permissions'];result={k:deepcopy(raw[k]) for k in ('version','beta','today','revision')}
    for module,right in MODULE_RIGHT.items():
        result[module]=[{k:deepcopy(v) for k,v in row.items() if k in FIELDS[module]} for row in raw[module]] if right in p else []
    result['settings']={k:deepcopy(v) for k,v in raw['settings'].items() if k in CONFIG_FIELDS} if 'settings.manage' in p else {'congregation':'','folder_minimum':0,'rural_minimum':0,'rural_mode':'auto','require_revision':False}
    result['areas']=[{k:deepcopy(v) for k,v in r.items() if k in ('id','name')} for r in raw['areas']] if 'cards.view' in p else []
    result.update(ignored=[],maps=[],recovery=[],public_maps=[],geo_info={},address_task={},backup_last_day=None,undo_available=False)
    if 'geo.view' in p:
        result['geo_info']=deepcopy(raw['geo_info'])
        result['ignored']=[{k:deepcopy(v) for k,v in r.items() if k in ('id','address_id','label','reason','date')} for r in raw['ignored']]
    if {'cards.view','geo.view'}<=p:result['maps']=deepcopy(raw['maps'])
    if 'sharing.manage' in p:result['public_maps']=deepcopy(raw['public_maps'])
    if 'settings.manage' in p:
        result['address_task']=deepcopy(raw['address_task']);result['backup_last_day']=raw['backup_last_day']
    if READ_ALL|WRITE_ALL|{'backup.restore'}<=p:result['recovery']=deepcopy(raw['recovery'])
    result['profile']={'user':{'id':user['id'],'name':user['name'],'onboarded':user['onboarded']},'permissions':sorted(p),'auth_revision':user['revision']}
    return result
