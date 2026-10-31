#!/usr/bin/env python3
"""Reproducible program-only ZIP. No user database folder is ever opened."""
from pathlib import Path
import argparse
import hashlib
import json
import posixpath
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'distrikt'
REQUIRED=('S-12-original.pdf','S-12-source.png','S-13-background.jpg','S-13-fields.json','S-13-fillable.pdf')
PDF_DEPENDENCIES=('pypdf-6.21.4.zip','PYPDF-LICENSE','PYPDF.md','typing_extensions.py','TYPING-EXTENSIONS-LICENSE')
BLOCKED_SUFFIXES=('.sqlite','.sqlite3','.db','.pyc','.log','.tmp')
BLOCKED_NAMES={'drive-auth.json','datafordeler-auth.json','access.json','run.json','launcher.json','profiles.json','profiles.tmp'}
ROOT_DOCS=('repository.yaml','README.md','docs/README.en.md','LICENSE','docs/CHANGELOG.md','docs/planning/ROADMAP.md','.github/CONTRIBUTING.md','docs/CONTRIBUTING.en.md','docs/planning/KOREPLAN.md','docs/help/Dette-skal-hjaelpes-manuelt.md','docs/help/Dette-skal-hjaelpes-manuelt.en.md')
BRAND_FILES=('mark.svg','logo-light.svg','logo-dark.svg','README.md')
SCREENSHOT_FILES=('overblik.png','udlevering.png','distriktskort.png','deling.png')

def account_backup(raw):
    if not raw.lstrip().startswith(b'{'):return False
    try:value=json.loads(raw)
    except (ValueError,UnicodeError):return False
    return isinstance(value,dict) and (value.get('format')=='ltm-account-backup' or
        isinstance(value.get('users'),dict) and isinstance(value.get('roles'),dict)
        and any(isinstance(u,dict) and 'hash' in u for u in value['users'].values()))

def version():
    value=re.search(r"^VERSION='([^']+)'",(SRC/'app/server.py').read_text(),re.M).group(1)
    config=(SRC/'config.yaml').read_text()
    if f'version: "{value}"' not in config:raise ValueError('Server and HA versions differ.')
    return value

def files():
    for dependency in PDF_DEPENDENCIES:
        if not (SRC/'app/vendor_py'/dependency).is_file():raise ValueError('Release incomplete: missing local PDF dependency: '+dependency)
    missing=[n for n in REQUIRED if not (SRC/'templates'/n).is_file()]
    if missing:raise ValueError('Release incomplete: missing blank form assets: '+', '.join(missing))
    if not (SRC/'app'/'kort-import-skabelon.xlsx').is_file():raise ValueError('Release incomplete: missing Excel import template.')
    result={}
    for section in ('app','templates','tests','translations'):
        for p in sorted((SRC/section).rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts:continue
            if p.is_symlink():raise ValueError('Symlink not allowed in release: '+str(p))
            if p.suffix in BLOCKED_SUFFIXES or p.name in BLOCKED_NAMES or p.name.startswith('accounts-before-restore-'):raise ValueError('Private/runtime file in source tree: '+str(p))
            if account_backup(p.read_bytes()):raise ValueError('Private account backup in source tree: '+str(p))
            relative=p.relative_to(SRC).as_posix()
            if any(part.startswith('.') for part in p.relative_to(SRC).parts):continue
            result['Distrikt-lokal/'+relative]=(p.read_bytes(),0o644)
            if section in ('app','templates','translations'):result['Home-Assistant/distrikt/'+relative]=(p.read_bytes(),0o644)
    for p in sorted(SRC.iterdir()):
        if p.is_file() and p.suffix in ('.cmd','.command','.sh','.md') and p.name!='run.sh':
            result['Distrikt-lokal/'+p.name]=(p.read_bytes(),0o755 if p.suffix in ('.command','.sh') else 0o644)
    for n in ('Dockerfile','config.yaml','run.sh','DOCS.md','README.md','CHANGELOG.md','icon.png','logo.png'):
        p=SRC/n;result['Home-Assistant/distrikt/'+n]=(p.read_bytes(),0o755 if n=='run.sh' else 0o644)
    for n in ROOT_DOCS:
        p=ROOT/n
        if not p.is_file():raise ValueError('Missing release document: '+n)
        result[n]=(p.read_bytes(),0o644)
    # HA reads its app-folder changelog; docs/ holds the matching project copy.
    # Reject drift before either the portable or beta package can be published.
    changelog=result['docs/CHANGELOG.md'][0]
    if result['Home-Assistant/distrikt/CHANGELOG.md'][0]!=changelog:
        raise ValueError('Project and HA changelogs differ. Sync distrikt/CHANGELOG.md from docs/CHANGELOG.md.')
    newest=re.search(r'^##[ \t]+([^\s]+)',changelog.decode('utf-8'),re.M)
    if not newest or newest.group(1)!=version():
        raise ValueError('Changelog must list the current version first.')
    for n in BRAND_FILES:
        p=ROOT/'assets'/'brand'/n
        if not p.is_file() or p.is_symlink():raise ValueError('Missing/unsafe brand asset: '+n)
        result['assets/brand/'+n]=(p.read_bytes(),0o644)
    for name in SCREENSHOT_FILES:
        p=ROOT/'assets'/'screenshots'/name
        if not p.is_file() or p.is_symlink():raise ValueError('Missing/unsafe public screenshot: '+name)
        result['assets/screenshots/'+name]=(p.read_bytes(),0o644)
    for p in sorted((ROOT/'docs').rglob('*.md')):
        if p.is_symlink():raise ValueError('Unsafe documentation symlink: '+str(p))
        result[p.relative_to(ROOT).as_posix()]=(p.read_bytes(),0o644)
    p=ROOT/'demo'/'README.md'
    if not p.is_file() or p.is_symlink():raise ValueError('Missing/unsafe demo guide.')
    result['demo/README.md']=(p.read_bytes(),0o644)
    # Shared guides use repository paths; portable copies use the desktop folder.
    for name,(raw,mode) in list(result.items()):
        if name in ROOT_DOCS or name.startswith('docs/'):
            if name.endswith('.md'):
                def portable_link(match):
                    target=match.group(1)
                    if target.startswith(('#','/')) or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):return match.group(0)
                    dest,separator,anchor=target.partition('#')
                    resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),dest))
                    if not resolved.startswith('distrikt/'):return match.group(0)
                    resolved='Distrikt-lokal/'+resolved[len('distrikt/'):]
                    return ']('+posixpath.relpath(resolved,posixpath.dirname(name) or '.')+(separator+anchor if separator else '')
                text=re.sub(r'\]\(([^)\s]+)',portable_link,raw.decode())
                result[name]=(text.encode(),mode)
    p=ROOT/'scripts'/'Opdater-Home-Assistant-Mac.command';result['scripts/'+p.name]=(p.read_bytes(),0o755)
    prefix='Home-Assistant/distrikt/'
    manifest=''.join(hashlib.sha256(raw).hexdigest()+'  '+name[len(prefix):]+'\n' for name,(raw,_) in sorted(result.items()) if name.startswith(prefix))
    result['Home-Assistant/SHA256SUMS.txt']=(manifest.encode(),0o644)
    result['START-HER.txt']=(('Local Territory Manager '+version()+'\n\nLæs README.md eller docs/INSTALL.md. Engelsk: docs/README.en.md.\nMac/Windows/Linux: se docs/SELF-HOSTING.md for den nye Start-LTM-guide i Distrikt-lokal. Python installeres separat. De gamle Start-Distrikt-filer er bevaret til eksisterende lokal brug.\nHA: tilføj repositoryet fra README, og installer gennem HA. Ved flytning af en eksisterende lokal app: følg installationsguiden, og tag privat backup først.\nDatabaser og login medfølger ikke.\n').encode(),0o644)
    validate_links(result)
    return result

def validate_links(entries):
    """All relative Markdown destinations must exist inside the archive."""
    for name,(raw,_) in entries.items():
        if not name.endswith('.md'):continue
        for target in re.findall(r'\]\(([^)\s]+)',raw.decode('utf-8')):
            target=target.split('#',1)[0]
            if not target or ':' in target or target.startswith('/'):continue
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),target))
            if resolved not in entries and not any(n.startswith(resolved.rstrip('/')+'/') for n in entries):
                raise ValueError('Broken packaged guide link: '+name+' -> '+target)

def build(output):
    entries=files();output.mkdir(parents=True,exist_ok=True);path=output/('LTM-v'+version()+'.zip')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,(raw,mode) in sorted(entries.items()):
            item=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));item.create_system=3;item.external_attr=(0o100000|mode)<<16;item.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(item,raw)
    digest=hashlib.sha256(path.read_bytes()).hexdigest();(output/(path.name+'.sha256')).write_text(digest+'  '+path.name+'\n')
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():raise ValueError('ZIP CRC failed.')
        if any(n.endswith(BLOCKED_SUFFIXES) for n in archive.namelist()):raise ValueError('Runtime data in archive.')
    print(json.dumps({'file':str(path),'sha256':digest,'files':len(entries),'bytes':path.stat().st_size}))
    return path

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'dist');args=parser.parse_args();build(args.output)
