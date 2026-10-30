"""Private, short-lived edit bases for the unfinished profile workflow.

Not connected to HTTP. The caller must authenticate and authorize every read
and write, and supply an opaque, server-owned session identifier. Snapshots
must never be created from a value submitted by the browser.
"""
from copy import deepcopy
import secrets
import threading
import time
from contextlib import contextmanager


class EditSnapshots:
    def __init__(self, *, ttl=1800, capacity=1024, clock=time.monotonic):
        if ttl <= 0 or capacity < 1:
            raise ValueError('Invalid snapshot limits')
        self.ttl, self.capacity, self.clock = ttl, capacity, clock
        self._lock = threading.RLock()
        self._items = {}

    def _expire(self, now):
        for key, item in list(self._items.items()):
            if item['until'] <= now and not item['busy']:
                del self._items[key]

    def create(self, session, module, ident, record):
        if not all(isinstance(x, str) and x for x in (session, module, ident)):
            raise ValueError('Session and record identity required')
        if not isinstance(record, dict) or record.get('id') != ident:
            raise ValueError('Matching server record required')
        with self._lock:
            now = self.clock()
            self._expire(now)
            if len(self._items) >= self.capacity:
                raise ValueError('Too many active edit snapshots')
            token = secrets.token_urlsafe(32)
            self._items[token] = {'session':session, 'module':module, 'id':ident,
                                  'record':deepcopy(record), 'until':now+self.ttl, 'busy':False}
            return token

    @contextmanager
    def claim(self, token, session, module, ident):
        """Claim once; a failed transaction may retry while the base is valid."""
        with self._lock:
            self._expire(self.clock())
            item = self._items.get(token)
            if not item or item['busy'] or (item['session'],item['module'],item['id']) != (session,module,ident):
                raise ValueError('Edit snapshot is unavailable')
            item['busy'] = True
            record = deepcopy(item['record'])
        try:
            yield record
        except BaseException:
            with self._lock:
                if self._items.get(token) is item:
                    item['busy'] = False
                    self._expire(self.clock())
            raise
        else:
            with self._lock:
                if self._items.get(token) is item:
                    del self._items[token]

    def revoke_session(self, session):
        with self._lock:
            for token, item in list(self._items.items()):
                if item['session'] == session:
                    del self._items[token]
