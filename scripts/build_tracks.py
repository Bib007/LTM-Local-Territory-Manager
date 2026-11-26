#!/usr/bin/env python3
"""Build reproducible, purpose-specific LTM packages from the common source.

This only prepares release assets. It never reads a user data folder and never
publishes an asset. GitHub's manual release-track workflow owns publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import build_release as release

TRACKS={
    'home-assistant':('Home Assistant','LTM-Home-Assistant'),
    'macos-app':('macOS app','LTM-macOS-app'),
    'macos-server':('macOS server','LTM-macOS-server'),
    'windows-app':('Windows app','LTM-Windows-app'),
    'windows-server':('Windows server','LTM-Windows-server'),
}

_ROOT_FILES=('README.md','README.da.md','LICENSE','repository.yaml','homeassistant/ltm-status.yaml')

def _manifest(entries):
    return ''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n'
                   for name,(raw,_) in sorted(entries.items()))

def _start_here(track):
    title,folder=TRACKS[track]
    if track=='home-assistant':
        return (f'# Local Territory Manager — {title}\n\n'
                'This is the Home Assistant source package from the common LTM version. '
                'Install through the add-on repository; do not copy program files into a running installation. '
                'Keep separate private data and account backups before updating.\n').encode()
    platform='macOS' if track.startswith('macos') else 'Windows'
    purpose='local app' if track.endswith('app') else 'private LAN/VPN server'
    launcher='Start-LTM-App' if track.endswith('app') else 'Start-LTM-Server'
    suffix='.command' if platform=='macOS' else '.cmd'
    return (f'# Local Territory Manager — {title}\n\n'
            f'This is the {platform} {purpose} package from the common LTM version. '
            f'Open `Distrikt/{launcher}{suffix}` after extracting the complete ZIP. '
            'It uses Python 3.9+ and is not yet a native DMG or EXE installer. '
            'Your data and account backups stay outside this program folder.\n').encode()

def _desktop_entries(track,source):
    prefix='Distrikt-lokal/'
    base=TRACKS[track][1]+'/'
    mac=track.startswith('macos')
    role='App' if track.endswith('app') else 'Server'
    suffix='.command' if mac else '.cmd'
    permitted_launchers={'Start-LTM'+suffix,'Start-LTM-'+role+suffix}
    result={}
    for name,(raw,mode) in source.items():
        if name.startswith(prefix):
            relative=name[len(prefix):]
            if relative.startswith(('Start','Stop','Forbind')) and relative not in permitted_launchers:continue
            result[base+'Distrikt/'+relative]=(raw,mode)
        elif name.startswith('docs/') or name in _ROOT_FILES or name.startswith('assets/brand/'):
            result[base+name]=(raw,mode)
    result[base+'START-HERE.md']=(_start_here(track),0o644)
    return result

def _home_assistant_entries(source):
    base=TRACKS['home-assistant'][1]+'/'
    prefix='Home-Assistant/'
    result={}
    for name,(raw,mode) in source.items():
        if name.startswith(prefix):
            result[base+name[len(prefix):]]=(raw,mode)
        elif name.startswith('docs/') or name in _ROOT_FILES or name.startswith('assets/brand/'):
            result[base+name]=(raw,mode)
    result[base+'START-HERE.md']=(_start_here('home-assistant'),0o644)
    return result

def entries(track):
    if track not in TRACKS:raise ValueError('Unknown release track: '+track)
    source=release.files()
    result=_home_assistant_entries(source) if track=='home-assistant' else _desktop_entries(track,source)
    result['SHA256SUMS.txt']=(_manifest(result).encode(),0o644)
    return result

def build(track,output):
    package=TRACKS[track][1]
    output.mkdir(parents=True,exist_ok=True)
    target=output/(package+'-v'+release.version()+'.zip')
    content=entries(track)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,(raw,mode) in sorted(content.items()):
            item=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));item.create_system=3
            item.external_attr=(0o100000|mode)<<16;item.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(item,raw)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip():raise ValueError('Track ZIP CRC failed.')
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    checksum=target.with_suffix('.zip.sha256')
    checksum.write_text(digest+'  '+target.name+'\n')
    result={'track':track,'file':str(target),'sha256':digest,'files':len(content),'bytes':target.stat().st_size}
    print(json.dumps(result));return target

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--track',choices=tuple(TRACKS)+('all',),default='all')
    parser.add_argument('--output',type=Path,default=release.ROOT/'dist')
    args=parser.parse_args()
    if args.track=='all':
        for track in TRACKS:build(track,args.output)
    else:build(args.track,args.output)
