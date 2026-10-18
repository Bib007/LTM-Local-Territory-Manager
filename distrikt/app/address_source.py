"""Local Datafordeler credentials and explicit connectivity checks. No private records."""
import hashlib
import http.client
import os
import tempfile
import json
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from access import write_private
from postcode import SourceTimeout

BASE='https://graphql.datafordeler.dk/DAR/v3'
MAX_SCHEMA=8*1024*1024

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

    def _request(self,key,suffix='',query=None):
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
            raise ValueError('Datafordeleren svarede med HTTP '+str(error.code)+'. Prøv igen senere.') from None
        except (OSError,TimeoutError,http.client.HTTPException) as error:
            if isinstance(error,TimeoutError) or isinstance(getattr(error,'reason',None),TimeoutError):
                raise SourceTimeout('Datafordeleren svarede ikke inden for tidsgrænsen. Prøv et mindre område eller fortsæt senere.') from None
            raise ValueError('Forbindelsen til Datafordeleren mislykkedes. Den gemte nøgle er ikke ændret.') from None

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
        if not isinstance(result,dict) or result.get('errors') or not isinstance(result.get('data'),dict):
            raise ValueError('Datafordelerens forespørgsel kunne ikke gennemføres fuldstændigt.')
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
