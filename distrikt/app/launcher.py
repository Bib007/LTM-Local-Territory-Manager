"""Shared interactive desktop/server start. Settings and credentials stay outside the ZIP."""
import argparse
import getpass
import ipaddress
import json
import os
import sys
import warnings
from pathlib import Path

import server
from access import Access, write_private


def paths(root=None):
    beta='-beta' if '-beta.' in server.VERSION else ''
    base=Path(root) if root else server.DEFAULT_DATA.parent
    return {'config':base/('Distrikt'+beta+'-start')/'launcher.json',
            'local':base/('Distrikt'+beta),'server':base/('Distrikt'+beta+'-server')}


def validate(config):
    if not isinstance(config,dict) or config.get('mode') not in ('local','server'):
        raise ValueError('Vælg lokal brug eller server.')
    if config['mode']=='local':return {'mode':'local'}
    host=str(config.get('host','')).strip()
    try:ip=ipaddress.IPv4Address(host)
    except ValueError:raise ValueError('Skriv computerens private IPv4-adresse, uden http:// eller port.') from None
    if not any(ip in ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16')):
        raise ValueError('Brug en privat IPv4-adresse på hjemmenetværket.')
    port=config.get('port')
    if type(port) is not int or not 1024<=port<=65535:raise ValueError('Vælg en port mellem 1024 og 65535.')
    return {'mode':'server','host':host,'port':port}


def configure(input_fn=None):
    input_fn=input_fn or input
    print('\n1 · Kun på denne computer\n2 · Server til hjemmenetværk og egen VPN\n0 · Afbryd')
    choice=input_fn('Vælg: ').strip()
    if choice=='0':return None
    if choice=='1':return {'mode':'local'}
    if choice!='2':raise ValueError('Vælg 1, 2 eller 0.')
    host=input_fn('Computerens faste private IPv4-adresse: ').strip()
    default=8788 if '-beta.' in server.VERSION else 8787
    raw=input_fn('Port ['+str(default)+']: ').strip()
    try:port=int(raw or str(default))
    except ValueError:raise ValueError('Porten skal være et tal.') from None
    return validate({'mode':'server','host':host,'port':port})


def secret_prompt(label):
    with warnings.catch_warnings():
        warnings.simplefilter('error',getpass.GetPassWarning)
        try:return getpass.getpass(label)
        except getpass.GetPassWarning:raise ValueError('Åbn startguiden i et terminalvindue, så adgangskoden kan indtastes skjult.') from None


def prepare_password(data,password_fn=None):
    password_fn=password_fn or secret_prompt
    if (data/'access.json').exists():return
    print('Vælg serverens login. Koden vises ikke, mens du skriver.')
    password=password_fn('Adgangskode (mindst 12 tegn): ')
    if not 12<=len(password)<=1024:raise ValueError('Vælg en adgangskode med 12–1024 tegn.')
    if password!=password_fn('Gentag adgangskoden: '):raise ValueError('Adgangskoderne er ikke ens.')
    data.mkdir(parents=True,exist_ok=True,mode=0o700)
    Access(data,password)  # Only the existing salted hash format is saved.


def launch(config,locations,no_browser=False):
    config=validate(config)
    # This wizard uses its own saved hash; no inherited HA password may rotate it.
    os.environ.pop('DISTRIKT_PASSWORD',None)
    if '-beta.' in server.VERSION:os.environ['LTM_CHANNEL']='beta'
    data=locations[config['mode']]
    print('Private data: '+str(data))
    if config['mode']=='local':
        args=['--data-dir',str(data)]
        if no_browser:args.append('--no-browser')
        server.main(args)
    else:
        info=server.running(data)
        url='http://'+config['host']+':'+str(config['port'])
        if info:
            if info.get('public_url')!=url:raise ValueError('En server kører allerede med andre netværksvalg. Stop den med Ctrl+C i dens vindue, før du ændrer adresse eller port.')
            print('Serveren kører allerede: '+url)
            return
        prepare_password(data)
        print('Åbn '+url+' på hjemmenetværket eller via egen VPN.')
        print('Lad dette vindue stå åbent. Stop serveren med Ctrl+C. Browseren åbnes ikke automatisk.')
        server.main(['--serve','--lan','--access-host',config['host'],'--bind',config['host'],
                     '--port',str(config['port']),'--data-dir',str(data),'--no-browser'])


def main(argv=None):
    parser=argparse.ArgumentParser(description='LTM · lokal app eller privat server')
    parser.add_argument('--root',type=Path,help='Separat rodmappe til startindstillinger og data')
    parser.add_argument('--configure',action='store_true',help='Vælg lokal brug eller server igen')
    parser.add_argument('--no-browser',action='store_true',help='Åbn ikke browser ved lokal start')
    args=parser.parse_args(argv);locations=paths(args.root);path=locations['config']
    print('LTM '+server.VERSION+' · startguide')
    config=None
    if path.exists() and not args.configure:
        try:config=validate(json.loads(path.read_text(encoding='utf-8')))
        except (ValueError,TypeError):raise ValueError('Startindstillingerne kunne ikke læses. Start med --configure for at vælge igen. Dine data er bevaret.') from None
    if config is None:
        print('Lokal brug og server har hver sin datamappe. Flyt via appens backup, hvis det ønskes.')
        config=configure()
        if config is None:return
        if config['mode']=='server':prepare_password(locations['server'])
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        write_private(path,validate(config))
    launch(config,locations,args.no_browser)


if __name__=='__main__':
    try:main()
    except (EOFError,KeyboardInterrupt):print('\nStart afbrudt. Gemte data er bevaret.')
    except Exception as error:print('LTM: '+str(error),file=sys.stderr);sys.exit(1)
