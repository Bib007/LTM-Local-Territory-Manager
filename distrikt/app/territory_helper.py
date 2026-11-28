"""One-time, read-only Territory Helper import for the local desktop beta."""
import base64
import hashlib
import json
import re
import secrets
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from geography import valid_polygon


API = 'https://www.territoryhelper.com/api'
CALLBACK = '/territory-helper-return'
MAX_RESPONSE = 2 * 1024 * 1024
UNAVAILABLE = 'Login hos Territory Helper kræver et registreret klient-id og en lokal returadresse.'
EXPIRED = 'Login hos Territory Helper er udløbet. Start importen igen.'
UNREADABLE = 'Territory Helper returnerede et ugyldigt svar.'
UNSUPPORTED = 'Kortet har ingen understøttet polygongrænse i Danmark.'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(path, fields, method='GET'):
    request = Request(API + path + '?' + urlencode(fields),
                      data=b'' if method == 'POST' else None,
                      method=method, headers={'Accept': 'application/json'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=8) as response:
            raw = response.read(MAX_RESPONSE + 1)
    except HTTPError as error:
        error.close()
        message = ('Territory Helper afviste adgang til menigheden eller kortet.'
                   if error.code in (401, 403) else 'Territory Helper afviste forespørgslen.')
        raise ValueError(message) from None
    except (URLError, OSError):
        raise ValueError('Der kunne ikke oprettes forbindelse til Territory Helper.') from None
    if len(raw) > MAX_RESPONSE:
        raise ValueError(UNREADABLE)
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError(UNREADABLE) from None


def read_polygon(value):
    # The API describes Boundary as a JSON array. Accept coordinate objects
    # and numeric pairs only when their order is unambiguous within Denmark.
    try:
        raw = json.loads(value)
        if not isinstance(raw, list) or not 3 <= len(raw) <= 5001:
            raise ValueError()
        if isinstance(raw[0], dict):
            points = []
            for item in raw:
                item = {key.lower(): part for key, part in item.items()}
                points.append([item.get('lng', item.get('lon', item.get('longitude'))),
                               item.get('lat', item.get('latitude'))])
        else:
            points = raw
            if len(points[0]) == 2 and 54 <= points[0][0] <= 58.5:
                points = [[lat, lng] for lng, lat in raw]
        if any(not isinstance(p, list) or len(p) != 2 or
               any(type(part) not in (float, int) for part in p) for p in points):
            raise ValueError()
        if points[0] == points[-1]:
            points = points[:-1]
        return valid_polygon(points, limit=5000)
    except (ValueError, TypeError, AttributeError, IndexError, OverflowError, RecursionError):
        raise ValueError(UNSUPPORTED) from None


class TerritoryHelperImport:
    def __init__(self, client_id, redirect_uri):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.lock = threading.Lock()
        self.pending = {}

    def begin(self, owner, number, congregation):
        if not self.client_id:
            raise ValueError(UNAVAILABLE)
        if not isinstance(number, str) or not 1 <= len(number.strip()) <= 10:
            raise ValueError('Indtast et Territory Helper-kortnummer på højst 10 tegn.')
        if not isinstance(congregation, str) or not re.fullmatch(r'[1-9][0-9]{0,9}', congregation):
            raise ValueError('Indtast et gyldigt menigheds-id fra Territory Helper.')
        verifier, state = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
        now = time.monotonic()
        with self.lock:
            self.pending = {key: value for key, value in self.pending.items() if value[1] > now}
            if len(self.pending) >= 16 and owner not in self.pending:
                raise ValueError('Der er for mange igangværende Territory Helper-login. Prøv igen om lidt.')
            self.pending[owner] = (state, now + 300, verifier, number.strip(), congregation)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        query = urlencode({'client_id': self.client_id, 'redirect_uri': self.redirect_uri,
                           'response_type': 'code', 'state': state, 'code_challenge': challenge,
                           'code_challenge_method': 'S256'})
        return {'authorize_url': API + '/authpkce?' + query, 'state': state}

    def claim(self, owner, state, code):
        if not isinstance(state, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', state):
            raise ValueError(EXPIRED)
        if not isinstance(code, str) or not 1 <= len(code) <= 4096 or not code.isascii():
            raise ValueError(EXPIRED)
        with self.lock:
            pending = self.pending.get(owner)
            if not pending or pending[1] <= time.monotonic() or not secrets.compare_digest(pending[0], state):
                raise ValueError(EXPIRED)
            del self.pending[owner]
        _, _, verifier, number, congregation = pending
        return code, verifier, number, congregation

    def preview(self, work):
        code, verifier, number, congregation = work
        token = request_json('/oauth/token', {'grant_type': 'authorization_code', 'code': code,
                             'redirect_uri': self.redirect_uri, 'client_id': self.client_id,
                             'code_verifier': verifier}, method='POST')
        access = token.get('access_token') if isinstance(token, dict) else None
        if not isinstance(access, str) or not 1 <= len(access) <= 4096:
            raise ValueError(UNREADABLE)
        rows = request_json('/territories', {'access_token': access, 'territory_number': number,
                                             'congregation_id': congregation})
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError(UNREADABLE)
        matches = [row for row in rows if row.get('Number') == number
                   and str(row.get('CongregationId')) == congregation]
        if len(matches) != 1:
            raise ValueError('Territory Helper skal returnere præcis ét kort med det angivne nummer.')
        card = matches[0]
        if card.get('ShapeType') != 'polygon':
            raise ValueError(UNSUPPORTED)
        label = card.get('Label')
        return {'number': number, 'name': label.strip()[:100] if isinstance(label, str) else '',
                'polygon': read_polygon(card.get('Boundary'))}
