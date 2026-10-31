"""Three-way reconciliation for the future profile workflow.

This module is not connected to any endpoint. Callers must obtain `base` from a
server-held, session-bound snapshot, validate field permissions and save the
merged record and its conflict notices in one transaction. Never put private
values or session tokens in logs.
"""
from copy import deepcopy
import json
import uuid
from datetime import datetime, timezone


def _value(record,field):
    return {'present':field in record,'value':deepcopy(record[field]) if field in record else None}


def _equal(a,b):
    # JSON boolean and number values must remain distinct (True != 1).
    return json.dumps(a,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')) == json.dumps(b,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))


def reconcile(base,current,proposed,editable_fields):
    """Return a merge and conflicts for explicitly authorized top-level fields.

    A conflict keeps all three values, including explicit missing vs null. The
    incoming save becomes the current value, matching LTM's current behavior;
    callers must persist the conflict before reporting the save as successful.
    Lists and nested objects are deliberately treated as single values.
    """
    if not all(isinstance(item,dict) for item in (base,current,proposed)):
        raise ValueError('Record snapshots must be objects')
    if not isinstance(editable_fields,(tuple,list,set,frozenset)) or not all(isinstance(k,str) and k and not k.startswith('_') for k in editable_fields):
        raise ValueError('An explicit list of editable fields is required')
    fields=sorted(set(editable_fields));merged=deepcopy(current);conflicts=[]
    for field in fields:
        original=_value(base,field);saved=_value(current,field);incoming=_value(proposed,field)
        if _equal(original,incoming):continue
        if not _equal(original,saved) and not _equal(saved,incoming):
            conflicts.append({'field':field,'base':original,'saved':saved,'incoming':incoming})
        if incoming['present']:merged[field]=deepcopy(incoming['value'])
        else:merged.pop(field,None)
    return {'record':merged,'conflicts':conflicts}


def commit_reviewed(store,module,ident,base,proposed,editable_fields,actor_id,apply_record):
    """Prototype: save one merged record and all notices in one existing transaction.

    This is intentionally not wired to an API. The future integration MUST
    authenticate the caller, verify a session-bound server snapshot, authorize
    each field and supply the regular domain validation/write path as callback.
    Conflict notices are ordinary local settings records so existing backups do
    not acquire a new, incompatible SQLite table. They can contain private data.
    """
    if module not in ('cards','notes','publishers','ib') or not isinstance(ident,str) or not ident:
        raise ValueError('Unsupported record')
    if not isinstance(actor_id,str) or not actor_id or len(actor_id)>100:
        raise ValueError('An authenticated actor is required')
    if not callable(apply_record) or not isinstance(base,dict) or not isinstance(proposed,dict) or base.get('id')!=ident or proposed.get('id')!=ident:
        raise ValueError('A validated record and matching snapshot are required')
    with store.transaction():
        current=store.require(module,ident)
        result=reconcile(base,current,proposed,editable_fields)
        if _equal(current,result['record']) and not result['conflicts']:
            return {'id':ident,'conflicts':0,'changed':False}
        # The callback must enforce the domain's normal validation and side effects.
        apply_record(store,deepcopy(result['record']))
        actual=store.require(module,ident)
        for field in editable_fields:
            if not _equal(_value(actual,field),_value(result['record'],field)):
                raise ValueError('The validated write did not preserve the reviewed change')
        for conflict in result['conflicts']:
            store.put('settings',{'id':'edit-conflict:'+uuid.uuid4().hex,'entity':'edit-conflict',
                'module':module,'record_id':ident,'incoming_actor_id':actor_id,
                'at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'field':conflict['field'],'base':conflict['base'],'saved':conflict['saved'],
                'incoming':conflict['incoming'],'resolved':False})
    return {'id':ident,'conflicts':len(result['conflicts']),'changed':True}
