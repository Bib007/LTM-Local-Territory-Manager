"""Portable snapshots and reviewed, transactional restores. No credentials are exported."""
import hashlib
import io
import json
import os
import secrets
import sqlite3
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from store import MODULES

MAX_ARCHIVE=100*1024*1024
MAX_EXPANDED=512*1024*1024
CORE={'settings','cards','publishers','loans','completions','ib','visits','maps','geo','ignored'}

def digest(store):
    h=hashlib.sha256()
    for module in MODULES:
        h.update(module.encode())
        for row in store.db.execute('SELECT id,payload,deleted_at,batch FROM '+store.alias(module)+'.records ORDER BY id'):
            h.update(json.dumps(tuple(row),ensure_ascii=False).encode())
    return h.hexdigest()

def snapshot(store,version):
    out=io.BytesIO()
    with store.lock, tempfile.TemporaryDirectory() as temp:
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for module,name in MODULES.items():
                target=Path(temp)/(name+'.sqlite3')
                db=sqlite3.connect(str(target))
                try:store.db.backup(db,name=store.alias(module))
                finally:db.close()
                z.write(target,target.name)
            z.writestr('manifest.json',json.dumps({'format':'distrikt-backup','schema':1,'version':version,'created':datetime.now(timezone.utc).isoformat(),'databases':list(MODULES.values())}))
            z.writestr('LAES-MIG.txt','Privat sikkerhedskopi af Distrikt. Indeholder IB og personoplysninger. Upload ikke til AI, Drive eller offentlig deling. Google-login og adgangskode følger ikke med.\n')
    return out.getvalue()

class Restores:
    def __init__(self,store,version):self.store=store;self.version=version;self.pending={}
    def preview(self,payload):
        if not payload or len(payload)>MAX_ARCHIVE:raise ValueError('Sikkerhedskopien må højst fylde 100 MB.')
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                files=z.infolist();names=[f.filename for f in files]
                permitted={n+'.sqlite3' for n in MODULES.values()}|{'manifest.json','LAES-MIG.txt'}
                if len(names)!=len(set(names)) or any(n not in permitted for n in names):raise ValueError('ZIP-filen indeholder ukendte eller dublerede filer.')
                if sum(f.file_size for f in files)>MAX_EXPANDED:raise ValueError('Den udpakkede sikkerhedskopi er for stor.')
                if not {MODULES[m]+'.sqlite3' for m in CORE}<=set(names):raise ValueError('Der mangler nødvendige databasefiler. Vælg en samlet Distrikt-sikkerhedskopi.')
                if 'manifest.json' in names:
                    manifest=json.loads(z.read('manifest.json'))
                    if manifest.get('format')!='distrikt-backup' or manifest.get('schema')!=1:raise ValueError('Sikkerhedskopiens format understøttes ikke.')
                rows={};counts={}
                with tempfile.TemporaryDirectory() as temp:
                    for module,name in MODULES.items():
                        filename=name+'.sqlite3';items=[]
                        if filename in names:
                            p=Path(temp)/filename;p.write_bytes(z.read(filename))
                            db=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
                            try:
                                db.execute('PRAGMA trusted_schema=OFF')
                                if db.execute('PRAGMA user_version').fetchone()[0]!=1:raise ValueError('Ukendt databaseversion: '+name)
                                objects=db.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
                                if objects!=[('table','records')]:raise ValueError('Ugyldig databasestruktur: '+name)
                                columns=[r[1] for r in db.execute('PRAGMA table_info(records)')]
                                if columns!=['id','payload','deleted_at','batch']:raise ValueError('Ugyldigt databaseformat: '+name)
                                if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Beskadiget database: '+name)
                                for row in db.execute('SELECT id,payload,deleted_at,batch FROM records'):
                                    item=json.loads(row[1])
                                    if not isinstance(item,dict) or item.get('id')!=row[0]:raise ValueError('Ugyldig post i '+name)
                                    items.append(tuple(row))
                            finally:db.close()
                        rows[module]=items;counts[module]=sum(r[2] is None for r in items)
                settings=[json.loads(r[1]) for r in rows['settings'] if r[0]=='config' and r[2] is None]
                if len(settings)!=1:raise ValueError('Sikkerhedskopien mangler indstillinger.')
                cards={r[0] for r in rows['cards']};publishers={r[0] for r in rows['publishers']}
                for module in ('loans','completions','ib','notes'):
                    for row in rows.get(module,[]):
                        item=json.loads(row[1])
                        if row[2] is None and not (module=='notes' and (item.get('entity')=='activity' or item.get('card_id') is None)) and item.get('card_id') not in cards:raise ValueError('Sikkerhedskopien har historik uden tilhørende kort.')
                        if module=='loans' and row[2] is None and item.get('publisher_id') not in publishers:raise ValueError('Sikkerhedskopien har udlån uden tilhørende forkynder.')
        except (zipfile.BadZipFile,sqlite3.Error,json.JSONDecodeError,RuntimeError,UnicodeError) as exc:
            raise ValueError('Sikkerhedskopien er ugyldig eller beskadiget.') from exc
        # Match the lists shown by Store.state(); retain raw counts for callers
        # that inspect all stored records, including archived cards and activity.
        visible_counts=dict(counts)
        visible_counts['cards']=sum(r[2] is None and not json.loads(r[1]).get('archived') for r in rows['cards'])
        visible_counts['notes']=sum(r[2] is None and json.loads(r[1]).get('entity')!='activity' for r in rows['notes'])
        token=secrets.token_urlsafe(32)
        with self.store.lock:
            self.pending={token:{'rows':rows,'expires':time.monotonic()+600,'digest':digest(self.store)}}
        return {'token':token,'counts':counts,'visible_counts':visible_counts,'warning':'Import erstatter alle lokale registreringer. Der gemmes automatisk en sikkerhedskopi af de nuværende data først. Hvis denne installation allerede har delte kort, skal deres offentlige adgang fjernes under Deling og QR før import.'}
    def apply(self,token):
        with self.store.lock:
            if any(r.get('entity')=='publication' and r.get('file_id') and r.get('status')!='private' for r in self.store.all('maps')):
                raise ValueError('Fjern først offentlig adgang til de nuværende kort under Deling og QR. Derefter kan du importere uden at efterlade delte billeder uden registrering.')
            data=self.pending.get(token)
            if not data or data['expires']<time.monotonic():raise ValueError('Forhåndsvisningen er udløbet. Vælg sikkerhedskopien igen.')
            if digest(self.store)!=data['digest']:raise ValueError('Data er ændret siden forhåndsvisningen. Vælg sikkerhedskopien igen.')
            folder=self.store.root/'backups';folder.mkdir(mode=0o700,exist_ok=True)
            filename='foer-import-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(3)+'.zip'
            target=folder/filename;target.write_bytes(snapshot(self.store,self.version));os.chmod(target,0o600)
            with self.store.transaction():
                self.store._dirty_modules.update(MODULES)
                for module,rows in data['rows'].items():
                    alias=self.store.alias(module)
                    self.store.db.execute('DELETE FROM '+alias+'.records')
                    self.store.db.executemany('INSERT INTO '+alias+'.records(id,payload,deleted_at,batch) VALUES(?,?,?,?)',rows)
                # Never resume public uploads from a different installation or an older backup.
                for item in self.store.all('maps'):
                    if item.get('entity')=='publication':
                        item.update(status='review',error='Kontrollér kortbilledet og publicér igen efter import.')
                        item.pop('queued_png',None);self.store.put('maps',item)
            self.pending.clear()
            return {'ok':True,'safety_backup':filename}

    def reset_beta(self,confirmation,revision):
        """Called only by the beta-gated HTTP route, under the sharing lock."""
        with self.store.lock:
            if confirmation!='NULSTIL BETA':raise ValueError('Skriv NULSTIL BETA for at bekræfte.')
            if revision!=self.store.revision:raise ValueError('Data er ændret. Genindlæs og kontrollér nulstillingen igen.')
            if any(r.get('entity')=='publication' and r.get('file_id') and
                   (r.get('status')!='private' or r.get('possibly_public') or r.get('url'))
                   for r in self.store.all('maps')+self.store.all('maps',deleted=True)):
                raise ValueError('Fjern først offentlig adgang til kortene under Deling og QR. Nulstilling må ikke efterlade offentlige billeder uden registrering.')
            folder=self.store.root/'backups';folder.mkdir(mode=0o700,exist_ok=True)
            filename='foer-beta-nulstilling-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(3)+'.zip'
            target=folder/filename
            target.write_bytes(snapshot(self.store,self.version));os.chmod(target,0o600)
            with self.store.transaction():
                self.store._dirty_modules.update(MODULES)
                for module in MODULES:self.store.db.execute('DELETE FROM '+self.store.alias(module)+'.records')
                self.store.put('settings',{'id':'config','congregation':'','folder_minimum':30,
                    'rural_mode':'auto','rural_minimum':5,'require_revision':False,'schema':1})
            self.store.workflow_init()
            self.pending.clear()
            return {'ok':True,'safety_backup':filename}
