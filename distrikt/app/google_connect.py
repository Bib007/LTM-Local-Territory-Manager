#!/usr/bin/env python3
"""One-time desktop OAuth with PKCE. Credentials never pass through ChatGPT."""
import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCOPE='https://www.googleapis.com/auth/drive.file'

def main():
    p=argparse.ArgumentParser();p.add_argument('--client');p.add_argument('--output');args=p.parse_args()
    source=args.client
    if not source:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root=tk.Tk();root.withdraw();source=filedialog.askopenfilename(title='Vælg OAuth-klientfilen hentet fra Google Cloud',filetypes=[('Google-klient','*.json')]);root.destroy()
        except Exception:source=input('Træk Google-klientens JSON-fil ind i dette vindue, og tryk Enter: ').strip().strip('"\'')
    if not source:raise ValueError('Ingen Google-klientfil valgt.')
    value=json.loads(Path(source).expanduser().read_text());client=value.get('installed',{})
    if not client.get('client_id','').endswith('.apps.googleusercontent.com') or not client.get('client_secret'):raise ValueError('Opret en OAuth-klient af typen Desktop app, og vælg dens JSON-fil.')
    state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(64)
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    result={}
    class Callback(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            parsed=urllib.parse.urlsplit(self.path);query=urllib.parse.parse_qs(parsed.query)
            good=parsed.path=='/callback' and secrets.compare_digest(query.get('state',[''])[0],state)
            if good:
                if query.get('code'):result['code']=query['code'][0]
                else:result['error']='Google-login blev annulleret eller afvist.'
            message='Du kan lukke fanen og gå tilbage til Google-guiden.' if good else 'Ukendt anmodning.'
            data=('<!doctype html><meta charset="utf-8"><title>Distrikt</title><p>'+message+'</p>').encode()
            self.send_response(200 if good else 400);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    server=HTTPServer(('127.0.0.1',0),Callback);server.timeout=1
    redirect='http://127.0.0.1:%s/callback'%server.server_port
    params={'client_id':client['client_id'],'redirect_uri':redirect,'response_type':'code','scope':SCOPE,'access_type':'offline','prompt':'consent','state':state,'code_challenge':challenge,'code_challenge_method':'S256'}
    print('Logger ind på Google i din browser. Vælg den nye konto til distriktskortene.')
    webbrowser.open('https://accounts.google.com/o/oauth2/v2/auth?'+urllib.parse.urlencode(params))
    deadline=time.monotonic()+600
    try:
        while not result and time.monotonic()<deadline:server.handle_request()
    finally:server.server_close()
    if not result or result.get('error'):raise ValueError(result.get('error','Login udløb. Kør guiden igen.'))
    body=urllib.parse.urlencode({'client_id':client['client_id'],'client_secret':client['client_secret'],'code':result['code'],'code_verifier':verifier,'redirect_uri':redirect,'grant_type':'authorization_code'}).encode()
    with urllib.request.urlopen(urllib.request.Request('https://oauth2.googleapis.com/token',body,{'Content-Type':'application/x-www-form-urlencoded'}),timeout=30) as response:tokens=json.load(response)
    if not tokens.get('refresh_token'):raise ValueError('Google gav ikke varig adgang. Kør guiden igen og godkend adgangen.')
    output=Path(args.output).expanduser() if args.output else Path.home()/'Downloads'/'Distrikt-Google-forbindelse.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    content={k:client[k] for k in ('client_id','client_secret')};content['refresh_token']=tokens['refresh_token']
    fd=os.open(str(output),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:json.dump(content,f)
    os.chmod(output,0o600)
    print('Forbindelsesfilen er gemt her: '+str(output))
    print('Åbn Distrikt → Indstillinger → Deling og QR, og vælg filen. Slet derefter filen fra Downloads. Del den aldrig med andre eller med AI.')

if __name__=='__main__':
    try:main()
    except Exception as error:
        print('Forbindelsen blev ikke oprettet. '+(str(error) if isinstance(error,ValueError) else 'Kontrollér klientfil, internet og Google Cloud-opsætning.'),file=sys.stderr);sys.exit(1)
