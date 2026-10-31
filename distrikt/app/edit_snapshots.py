"""Session-bound, bounded in-memory bases for concurrent editing."""
from copy import deepcopy
import secrets
import threading
import time
from contextlib import contextmanager
import json


class EditSnapshots:
    def __init__(self, *, ttl=1800, capacity=1024, clock=time.monotonic, max_bytes=64*1024*1024):
        if ttl <= 0 or capacity < 1:
            raise ValueError('Invalid snapshot limits')
        self.ttl, self.capacity, self.clock = ttl, capacity, clock
        self._lock = threading.RLock()
        self._items = {}
        self.max_bytes=max_bytes

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
            size=len(json.dumps(record,ensure_ascii=False).encode('utf-8'))
            if len(self._items) >= self.capacity or sum(i['size'] for i in self._items.values())+size>self.max_bytes:
                raise ValueError('Too many active edit snapshots')
            token = secrets.token_urlsafe(32)
            self._items[token] = {'session':session, 'module':module, 'id':ident,
                                  'record':deepcopy(record), 'until':now+self.ttl, 'busy':False,'size':size}
            return token

    def discard(self,token,session):
        with self._lock:
            item=self._items.get(token)
            if item and item['session']==session and not item['busy']:del self._items[token]

    def clear(self):
        with self._lock:self._items.clear()

    def limit_session(self,session,keep=16):
        with self._lock:
            old=[key for key,item in self._items.items() if item['session']==session and not item['busy']]
            for key in old[:-keep]:del self._items[key]

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
