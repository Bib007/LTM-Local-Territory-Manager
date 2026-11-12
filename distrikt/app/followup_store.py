"""Persistent, reversible dismissal of non-critical territory-overlap follow-ups.

Stored as settings entity records, so existing SQLite, backup and restore formats
remain compatible. This is separate from address 'Se bort fra' records.
"""
import hashlib
import json
import re
import uuid


class FollowupStore:
    @staticmethod
    def followup_identity(key):
        try:
            parts = json.loads(key) if isinstance(key, str) and len(key) <= 300 else None
        except (ValueError, TypeError):
            parts = None
        if (not isinstance(parts, list) or len(parts) != 4
                or parts[:2] != ['checks', 'overlap']
                or not all(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value)
                           for value in parts[2:])
                or parts[2] >= parts[3]):
            raise ValueError('Kun kortoverlap kan markeres Se bort fra. Andre opfølgninger skal behandles.')
        return json.dumps(parts, ensure_ascii=False, separators=(',', ':'))

    @staticmethod
    def followup_record_id(key):
        return 'followup-ignore:' + hashlib.sha256(key.encode('utf-8')).hexdigest()

    def followup_mutate(self, data):
        from store import now
        key = self.followup_identity(data.get('key'))
        for card_id in json.loads(key)[2:]:
            card = self.get('cards', card_id)
            if not card or card.get('archived'):
                raise ValueError('Et af kortene findes ikke længere. Opdater opfølgningerne.')
        ignored = data.get('ignored')
        if type(ignored) is not bool:
            raise ValueError('Vælg Se bort fra eller Genaktivér.')
        expected = data.get('expected_token')
        if not isinstance(expected, str) or len(expected) > 64:
            raise ValueError('Opfølgningen er ændret. Opdater oversigten.')
        ident = self.followup_record_id(key)
        original = self.get('settings', ident)
        current_token = original.get('token', '') if original else ''
        if expected != current_token:
            raise ValueError('Opfølgningen er ændret af en anden bruger. Opdater oversigten.')
        if bool(original and original.get('ignored')) == ignored:
            raise ValueError('Opfølgningen har allerede den valgte status. Opdater oversigten.')
        event = {
            'ignored': ignored,
            'at': now(),
            'actor_id': data.get('_actor_id') or None,
            'actor_name': data.get('_actor_name') or 'Fælles login / system',
        }
        item = {
            'id': ident, 'entity': 'followup_ignore', 'key': key,
            'ignored': ignored, 'token': uuid.uuid4().hex,
            'history': [*(original.get('history') or []), event] if original else [event],
        }
        self.put('settings', item)
        return {'key': key, 'ignored': ignored}
