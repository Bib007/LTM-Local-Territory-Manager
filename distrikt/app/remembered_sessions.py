"""Opt-in, restart-safe login leases. Only token digests are stored on disk.

The caller's account/access lock serializes mutations. Ordinary sessions are
never written; remembered sessions use a private, channel-specific file.
"""
import hashlib
import json
import time
from pathlib import Path

REMEMBER_LIFETIME = 7 * 24 * 60 * 60
MAX_REMEMBERED = 100


class RememberedSessions:
    def __init__(self, root, channel, clock=time.time):
        self.path = Path(root) / ('login-remembered-' + channel + '.json')
        self.clock = clock
        try:
            value = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(value, dict):
                raise ValueError('Invalid remembered session records')
            self.records = {
                key: record for key, record in value.items()
                if isinstance(key, str) and len(key) == 64
                and isinstance(record, dict)
                and isinstance(record.get('until'), (int, float))
                and type(record.get('until')) is not bool
                and isinstance(record.get('user'), str)
                and isinstance(record.get('credential'), str)
            }
        except FileNotFoundError:
            self.records = {}
        except (ValueError, OSError, UnicodeError):
            # Corrupt or unreadable state must never grant access.
            self.records = {}

    @staticmethod
    def _key(token):
        if not isinstance(token, str) or not 1 <= len(token) <= 256:
            return ''
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def get(self, token):
        record = self.records.get(self._key(token))
        return record if record and record['until'] > self.clock() else None

    def _replace(self, records):
        # Commit to the private file first: a failed revoke cannot be reported
        # as a successful logout and then resurrect a session on restart.
        from access import write_private
        write_private(self.path, records)
        self.records = records

    def issue(self, token, user, credential):
        now = self.clock()
        records = {key: value for key, value in self.records.items() if value['until'] > now}
        while len(records) >= MAX_REMEMBERED:
            del records[min(records, key=lambda key: records[key]['until'])]
        until = now + REMEMBER_LIFETIME
        records[self._key(token)] = {'user': user, 'credential': credential, 'until': until}
        self._replace(records)
        return until

    def revoke(self, token):
        key = self._key(token)
        if key in self.records:
            records = dict(self.records)
            del records[key]
            self._replace(records)

    def revoke_user(self, user):
        if any(row['user'] == user for row in self.records.values()):
            self._replace({key: row for key, row in self.records.items() if row['user'] != user})

    def clear(self):
        if self.records:
            self._replace({})
