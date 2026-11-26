"""Private, browser-encrypted connection-backup payloads.

The browser encrypts this small payload before it is downloaded. The server
never receives the chosen passphrase and ordinary data/account backups never
include these credentials.
"""
import json
from access import write_private

DRIVE_KEYS=('client_id','client_secret','refresh_token')


def _read(path):
    try:value=json.loads(path.read_text())
    except (OSError,UnicodeError,json.JSONDecodeError):raise ValueError('Forbindelsesoplysningerne kunne ikke læses.') from None
    if not isinstance(value,dict):raise ValueError('Forbindelsesoplysningerne har et ukendt format.')
    return value


def _drive(value):
    if not isinstance(value,dict):raise ValueError('Google-forbindelsen har et ukendt format.')
    result={key:value.get(key) for key in DRIVE_KEYS}
    if any(not isinstance(item,str) or not item or len(item)>8192 for item in result.values()) or not result['client_id'].endswith('.apps.googleusercontent.com'):raise ValueError('Google-forbindelsen har et ukendt format.')
    account=value.get('account','')
    if not isinstance(account,str) or len(account)>320:raise ValueError('Google-forbindelsen har et ukendt format.')
    if account:result['account']=account
    return result


def _datafordeler(value):
    if not isinstance(value,dict):raise ValueError('Datafordeler-forbindelsen har et ukendt format.')
    key=value.get('api_key')
    if not isinstance(key,str) or not 10<=len(key)<=2000 or any(ord(char)<33 or ord(char)>126 for char in key):raise ValueError('Datafordeler-forbindelsen har et ukendt format.')
    result={'api_key':key}
    for name in ('checked_at','schema_sha256'):
        item=value.get(name)
        if isinstance(item,str) and len(item)<=128:result[name]=item
    return result


def export(server):
    """Return credentials only to a connections administrator for local encryption."""
    connections={}
    with server.sharing.lock,server.address_source.lock,server.store.lock:
        if server.sharing.drive.connected():connections['google_drive']=_drive(_read(server.sharing.drive.path))
        if server.address_source.path.exists():connections['datafordeler']=_datafordeler(_read(server.address_source.path))
        token=(server.store.get('geo','config') or {}).get('token','')
        if token:connections['adressevaelger']={'token':token}
    return {'schema':1,'connections':connections}


def restore(server,payload,confirmation):
    if confirmation!='GENDAN FORBINDELSER':raise ValueError('Skriv GENDAN FORBINDELSER for at fortsætte.')
    if not isinstance(payload,dict) or payload.get('schema')!=1 or not isinstance(payload.get('connections'),dict):raise ValueError('Den dekrypterede fil er ikke en gyldig forbindelsesbackup.')
    connections=payload['connections']
    if set(connections)-{'google_drive','datafordeler','adressevaelger'}:raise ValueError('Den dekrypterede fil er ikke en gyldig forbindelsesbackup.')
    drive=_drive(connections['google_drive']) if 'google_drive' in connections else None
    datafordeler=_datafordeler(connections['datafordeler']) if 'datafordeler' in connections else None
    picker=connections.get('adressevaelger')
    if picker is not None:
        if not isinstance(picker,dict) or set(picker)!={'token'} or not isinstance(picker['token'],str) or not 1<=len(picker['token'].strip())<=300:raise ValueError('Adressevælger-forbindelsen har et ukendt format.')
        picker={'token':picker['token'].strip()}
    if not connections:raise ValueError('Forbindelsesbackupen indeholder ingen forbindelser.')
    with server.sharing.lock,server.address_source.lock,server.store.transaction():
        if drive is not None:
            write_private(server.sharing.drive.path,drive);server.sharing.drive.access='';server.sharing.drive.expires=0
        if datafordeler is not None:write_private(server.address_source.path,datafordeler)
        if picker is not None:server.store.put('geo',{'id':'config',**picker})
    return {'restored':sorted(connections)}
