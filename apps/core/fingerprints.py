"""Stable JSON hashing; callers explicitly preserve their existing wire encoding."""
import hashlib
import json


def json_fingerprint(value, *, ensure_ascii=True, separators=None):
    options = {'sort_keys': True, 'ensure_ascii': ensure_ascii}
    if separators is not None:
        options['separators'] = separators
    return hashlib.sha256(json.dumps(value, **options).encode('utf-8')).hexdigest()
