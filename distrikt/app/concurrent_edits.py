"""Three-way reconciliation for the future profile workflow.

This module is not connected to any endpoint. Callers must obtain `base` from a
server-held, session-bound snapshot, validate field permissions and save the
merged record and its conflict notices in one transaction. Never put private
values or session tokens in logs.
"""
from copy import deepcopy
import json


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
