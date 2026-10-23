"""Local Datafordeler credentials and explicit connectivity checks. No private records."""
import hashlib
import http.client
import os
import tempfile
import json
import re
import socket
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from access import write_private
from postcode import SourceTimeout, SourceLimit, SourceTransient, SourceUnavailable

BASE='https://graphql.datafordeler.dk/DAR/v3'
MAX_SCHEMA=8*1024*1024

def reject_graphql(result,query):
    """Classify provider failures without returning messages, values or paths."""
    errors=result.get('errors') if isinstance(result,dict) else None
    if not isinstance(errors,list) or not errors:
        raise ValueError('Datafordeleren returnerede et ufuldstændigt svar (GQL-RESULT). Ingen adresser fra opslaget er gemt.') from None
    known=[];categories=[];fields=[]
    allowed_fields={'id_lokalId','status','position','crs','dimension','wkt','nodes','pageInfo','hasNextPage','endCursor','first','after','where','virkningstid','registreringstid','husnummer','navngivenVej','adgangspunkt','postnummer','postnr','navn','vejnavn','adressebetegnelse','etagebetegnelse','doerbetegnelse','husnummertekst','vejnavnebeliggenhed_vejnavnelinje'}
    for error in errors:
        if not isinstance(error,dict):categories.append('GQL-REJECTED');continue
        message=error.get('message');message=message.casefold() if isinstance(message,str) else ''
        ext=error.get('extensions');code=ext.get('code') if isinstance(ext,dict) else None
        if isinstance(code,str) and (re.fullmatch(r'HC\d{4}',code) or code in ('GRAPHQL_VALIDATION_FAILED','GRAPHQL_PARSE_FAILED','AUTH_NOT_AUTHORIZED','AUTH_NOT_AUTHENTICATED','INTERNAL_SERVER_ERROR')):known.append(code)
        if code=='HC0047' or 'max graphql request size reached' in message or 'maximum allowed cost' in message:categories.append('GQL-LIMIT')
        elif code in ('AUTH_NOT_AUTHORIZED','AUTH_NOT_AUTHENTICATED') or 'not authorized' in message or 'not authorised' in message:categories.append('GQL-ACCESS')
        elif code in ('GRAPHQL_VALIDATION_FAILED','GRAPHQL_PARSE_FAILED') or any(s in message for s in ('does not exist','is not defined','unknown field','unknown argument','syntax error','cannot query field')):categories.append('GQL-SCHEMA')
        else:categories.append('GQL-REJECTED')
        for field in re.findall(r'(?:field|argument)\s+[\x22\x27`]?([a-z_][a-z0-9_]*)',message):
            original=next((f for f in allowed_fields if f.casefold()==field),None)
            if original:fields.append(original)
    entity=next(iter(re.findall(r'\b(DAR_(?:Adressepunkt|Adresse|Husnummer|NavngivenVej|Postnummer))\s*\(',query)),'DAR')
    category=next((c for c in categories if c!='GQL-LIMIT'),'GQL-LIMIT' if categories else 'GQL-REJECTED')
    detail=' · '.join([category,entity]+sorted(set(known))[:3]+sorted(set(fields))[:2])
    if categories and all(c=='GQL-LIMIT' for c in categories):raise SourceLimit('Datafordelerens størrelsesgrænse er nået ('+detail+'). Opslaget skal gøres mindre.') from None
    prefix={'GQL-SCHEMA':'Datafordeleren afviste forespørgslens felter eller filtre','GQL-ACCESS':'Datafordeleren afviste adgang til selve dataopslaget'}.get(category,'Datafordeleren afviste forespørgslen')
    raise ValueError(prefix+' ('+detail+'). Ingen adresser fra opslaget er gemt.') from None

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args):return None

class Datafordeler:
    def __init__(self,root):
        self.path=Path(root)/'datafordeler-auth.json'
        self.cache=Path(root)/'datafordeler'
        self.lock=threading.RLock()

    def _auth(self):
        return json.loads(self.path.read_text()) if self.path.exists() else {}

    def status(self):
        with self.lock:
            auth=self._auth()
            return {'configured':bool(auth.get('api_key')),'checked_at':auth.get('checked_at'),
                    'schema_sha256':auth.get('schema_sha256'),'import_ready':bool(auth.get('api_key'))}

    def _request(self,key,suffix='',query=None,*,return_graphql_errors=False):
        url=BASE+suffix+'?'+urllib.parse.urlencode({'apiKey':key})
        payload=json.dumps({'query':query}).encode() if query is not None else None
        headers={'User-Agent':'LTMLocal','Accept':'application/json' if query else 'text/plain'}
        if payload is not None:headers['Content-Type']='application/json'
        request=urllib.request.Request(url,data=payload,headers=headers)
        try:
            with urllib.request.build_opener(NoRedirect()).open(request,timeout=20) as response:
                raw=response.read(MAX_SCHEMA+1)
            if len(raw)>MAX_SCHEMA:raise ValueError('Datafordeleren gav et for stort svar. Nøglen er ikke ændret.')
            return raw
        except urllib.error.HTTPError as error:
            if error.code in (408,504):raise SourceTimeout('Datafordeleren svarede ikke inden for tidsgrænsen. Prøv et mindre område eller fortsæt senere.') from None
            if error.code in (401,403):raise ValueError('Datafordeleren afviste nøglen. Kontrollér API-key på dit IT-system. En ny nøgle kan være op til 15 minutter om at blive aktiv. Ventetid er kun én mulig årsag. Prøv forbindelsen igen, når der er gået 15 minutter.') from None
            if error.code in (429,500,502,503):
                message='Datafordeleren er midlertidigt utilgængelig (HTTP '+str(error.code)+'). Prøv igen senere.'
                cooldown=error.headers.get('Retry-After','') if error.headers else ''
                if cooldown and (not cooldown.isdigit() or int(cooldown)>60):raise SourceUnavailable(message) from None
                delay=max(60 if error.code==429 else 0,int(cooldown) if cooldown else 0)
                raise SourceTransient(message,delay) from None
            if query is not None and error.code in (400,422):
                try:body=json.loads(error.read(MAX_SCHEMA+1))
                except (ValueError,OSError):body=None
                if isinstance(body,dict) and body.get('errors'):
                    if return_graphql_errors:return json.dumps(body).encode()
                    reject_graphql(body,query)
            raise ValueError('Datafordeleren svarede med HTTP '+str(error.code)+'. Prøv igen senere.') from None
        except (OSError,TimeoutError,http.client.HTTPException) as error:
            if isinstance(error,TimeoutError) or isinstance(getattr(error,'reason',None),TimeoutError):
                raise SourceTimeout('Datafordeleren svarede ikke inden for tidsgrænsen. Prøv et mindre område eller fortsæt senere.') from None
            cause=getattr(error,'reason',error)
            if isinstance(cause,ssl.SSLCertVerificationError):
                raise SourceUnavailable('Datafordelerens sikre forbindelse kunne ikke bekræftes (NET-TLS). Kontrollér serverens dato og netværksopsætning. Den gemte nøgle er ikke ændret.') from None
            code='NET-DNS' if isinstance(cause,socket.gaierror) else 'NET-RESET' if isinstance(cause,(ConnectionResetError,ConnectionAbortedError,BrokenPipeError,http.client.IncompleteRead,http.client.RemoteDisconnected)) else 'NET-CONNECTION'
            raise SourceTransient('Forbindelsen til Datafordeleren mislykkedes ('+code+'). Den gemte nøgle er ikke ændret.') from None

    def _check(self,key):
        schema=self._request(key,'/schema')
        try:
            text=schema.decode('utf-8')
            if not re.search(r'\btype\s+\w+',text) or not all(name in text for name in ('DAR_Adresse','DAR_Husnummer','DAR_Postnummer')):
                raise ValueError('Datafordeleren returnerede ikke det forventede DAR v3-skema.')
            probe=json.loads(self._request(key,query='query { __typename }'))
            if probe.get('errors') or not isinstance(probe.get('data',{}).get('__typename'),str) or not probe['data']['__typename']:
                raise ValueError('Datafordelerens GraphQL-forbindelse kunne ikke bekræftes.')
        except (UnicodeError,json.JSONDecodeError,AttributeError):
            raise ValueError('Datafordeleren returnerede et ukendt svar. Nøglen er ikke ændret.') from None
        return schema

    def query(self,query):
        """Internal DAR query transport; never return raw provider errors."""
        if not isinstance(query,str) or not query.strip() or len(query)>100000:
            raise ValueError('Ugyldig DAR-forespørgsel.')
        with self.lock:
            key=self._auth().get('api_key')
        if not key:raise ValueError('Gem først din egen API-key.')
        raw=self._request(key,query=query)
        try:
            result=json.loads(raw)
        except (UnicodeError,json.JSONDecodeError):
            raise ValueError('Datafordeleren returnerede ikke et gyldigt GraphQL-svar.') from None
        if not isinstance(result,dict) or result.get('errors') or not isinstance(result.get('data'),dict):reject_graphql(result,query)
        return result

    def connect(self,key):
        if not isinstance(key,str) or not 10<=len(key.strip())<=2000 or any(ord(c)<33 or ord(c)>126 for c in key.strip()):
            raise ValueError('Indsæt den API-key, der blev oprettet til dit IT-system.')
        key=key.strip()
        with self.lock:
            schema=self._check(key)
            digest=hashlib.sha256(schema).hexdigest()
            self.cache.mkdir(mode=0o700,exist_ok=True)
            target=self.cache/('schema-'+digest+'.graphql')
            # Public schema, kept separately from credentials and never in portable backups.
            temporary=None
            try:
                with tempfile.NamedTemporaryFile(dir=self.cache,delete=False) as output:
                    temporary=Path(output.name);output.write(schema)
                os.replace(temporary,target)
            finally:
                if temporary:temporary.unlink(missing_ok=True)
            write_private(self.path,{'api_key':key,'checked_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'schema_sha256':digest})
            return self.status()

    def check(self):
        with self.lock:
            key=self._auth().get('api_key')
            if not key:raise ValueError('Gem først din egen API-key.')
            return self.connect(key)

    def disconnect(self):
        with self.lock:self.path.unlink(missing_ok=True)
        return self.status()
