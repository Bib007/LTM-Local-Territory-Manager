"""Account backup validation and local-console administrator recovery."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
from profile_accounts import ProfileAccounts,PERMISSIONS,_name
from access import write_private

MAX_ACCOUNT_BACKUP=16*1024*1024

def validated(data):
    if not isinstance(data,dict) or set(data)-{'reviews','permission_schema'}!={'users','roles'}:raise ValueError('Ugyldig kontobackup.')
    if 'permission_schema' in data and (type(data['permission_schema']) is not int or data['permission_schema']!=2):raise ValueError('Ukendt rettighedsformat.')
    if 'reviews' in data:
        reviews=data['reviews']
        if not isinstance(reviews,list) or len(reviews)>5000:raise ValueError('Ugyldige kontorettelser.')
        for row in reviews:
            if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not re.fullmatch(r'account-review-[a-f0-9]{32}',row['id']):raise ValueError('Ugyldig kontorettelse.')
            if row.get('module') not in ('users','roles') or row.get('field') not in ('name','roles','disabled','credential','permissions') or type(row.get('resolved')) is not bool:raise ValueError('Ugyldig kontorettelse.')
            for key in ('base','saved','incoming'):
                if not isinstance(row.get(key),dict) or set(row[key])!={'present','value'} or type(row[key]['present']) is not bool:raise ValueError('Ugyldig kontorettelse.')
    if not all(isinstance(data[k],dict) and 0<len(data[k])<=1000 for k in ('users','roles')):raise ValueError('Ugyldig kontobackup.')
    names=set()
    for ident,role in data['roles'].items():
        if not isinstance(ident,str) or not re.fullmatch(r'role-[a-f0-9]{32}',ident):raise ValueError('Ugyldig rolle.')
        if set(role)!={'id','name','permissions'} or role['id']!=ident or _name(role['name'])!=role['name']:raise ValueError('Ugyldig rolle.')
        if role['name'].casefold() in names:raise ValueError('Dubleret rollenavn.')
        names.add(role['name'].casefold())
        if not isinstance(role['permissions'],list) or any(p not in PERMISSIONS for p in role['permissions']):raise ValueError('Ukendt rettighed.')
    names=set();admin=False
    for ident,user in data['users'].items():
        if not isinstance(ident,str) or not re.fullmatch(r'user-[a-f0-9]{32}',ident):raise ValueError('Ugyldig bruger.')
        if set(user)-{'onboarded'}!={'id','name','roles','disabled','salt','hash','iterations'} or user['id']!=ident or _name(user['name'])!=user['name']:raise ValueError('Ugyldig bruger.')
        if 'onboarded' in user and type(user['onboarded']) is not bool:raise ValueError('Ugyldig introduktionsstatus.')
        if user['name'].casefold() in names:raise ValueError('Dubleret brugernavn.')
        names.add(user['name'].casefold())
        if type(user['disabled']) is not bool or not isinstance(user['roles'],list) or not user['roles'] or any(r not in data['roles'] for r in user['roles']):raise ValueError('Ugyldige brugerroller.')
        if not isinstance(user['salt'],str) or not re.fullmatch(r'[a-f0-9]{48}',user['salt']) or not isinstance(user['hash'],str) or not re.fullmatch(r'[a-f0-9]{64}',user['hash']):raise ValueError('Ugyldig adgangskodehash.')
        if type(user['iterations']) is not int or not 100000<=user['iterations']<=2000000:raise ValueError('Ugyldig arbejdsfaktor.')
        admin |= not user['disabled'] and any('users.manage' in data['roles'][r]['permissions'] for r in user['roles'])
    if not admin:raise ValueError('Kontobackup mangler en aktiv administrator.')
    return data

def backup_value(accounts):
    with accounts.lock:
        value={'format':'ltm-account-backup','schema':1,'accounts':validated(accounts._copy())}
        if len(json.dumps(value).encode())>MAX_ACCOUNT_BACKUP:raise ValueError('Kontobackup er for stor.')
        return value

def parsed_backup(value):
    if not isinstance(value,dict) or value.get('format')!='ltm-account-backup' or value.get('schema')!=1:raise ValueError('Ukendt kontobackup.')
    return validated(value.get('accounts'))

def export_accounts(accounts,path):
    with accounts.lock:
        value=backup_value(accounts)
        destination=Path(path).expanduser().resolve()
        if destination.exists():raise ValueError('Vælg et nyt filnavn; en eksisterende fil overskrives ikke.')
        # Open exclusively and privately, including the first write.
        fd=os.open(str(destination),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False)
        return destination

def restore_accounts(accounts,path):
    path=Path(path).expanduser().resolve()
    if path.stat().st_size>MAX_ACCOUNT_BACKUP:raise ValueError('Kontobackup er for stor.')
    value=json.loads(path.read_text(encoding='utf-8'))
    return restore_value(accounts,parsed_backup(value))

def restore_value(accounts,data):
    data=validated(data)
    with accounts.lock:
        if accounts.data['users']:
            import secrets
            export_accounts(accounts,accounts.root/('accounts-before-restore-'+secrets.token_hex(8)+'.json'))
        accounts._write(data);accounts.sessions.clear()

def main():
    parser=argparse.ArgumentParser(description='Lokal gendannelse af LTM-konti. Stop LTM først.')
    parser.add_argument('--data-dir',required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--recover-admin',action='store_true');group.add_argument('--backup');group.add_argument('--restore')
    args=parser.parse_args()
    from server import acquire_lock
    root=Path(args.data_dir).expanduser().resolve()
    if not root.is_dir():raise ValueError('Vælg installationens eksisterende datamappe.')
    lock=acquire_lock(root/'app.lock')
    if lock is None:raise ValueError('Stop LTM før kontogendannelse eller kontobackup.')
    try:
        try:accounts=ProfileAccounts(root)
        except (json.JSONDecodeError,UnicodeError):
            if not args.restore:raise ValueError('Kontofilen er beskadiget. Gendan en separat kontobackup.') from None
            import secrets
            saved=root/('accounts-before-restore-raw-'+secrets.token_hex(8)+'.json')
            fd=os.open(str(saved),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write((root/'profiles.json').read_bytes())
            accounts=ProfileAccounts(root,load=False)
        if args.backup:
            export_accounts(accounts,args.backup);print('Separat kontobackup er gemt. Den indeholder adgangskodehashes; opbevar den privat og lokalt.')
        elif args.restore:
            if input('Erstat konti og roller? Skriv GENDAN KONTI: ')!='GENDAN KONTI':raise ValueError('Annulleret.')
            restore_accounts(accounts,args.restore);print('Konti og roller er gendannet. Alle skal logge ind igen. Distriktsdata er bevaret.')
        else:
            name=input('Administratorens brugernavn: ');password=getpass.getpass('Ny adgangskode (mindst 12 tegn): ')
            if password!=getpass.getpass('Gentag adgangskode: '):raise ValueError('Adgangskoderne er forskellige.')
            accounts.recover_admin(name,password);print('Administratoradgangen er gendannet. Distriktsdata er bevaret.')
    finally:lock.close()

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,TypeError,KeyError) as error:raise SystemExit(str(error))
