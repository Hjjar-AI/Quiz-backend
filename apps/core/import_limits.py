"""Short-lived, account/session-scoped import throttle reauthentication."""
import math
from time import time

IMPORT_UNLOCK_SECONDS = 10 * 60
_SESSION_KEY = '_import_limit_unlock'


def import_unlock_status(request):
    user = getattr(request, 'user', None)
    session = getattr(request, 'session', None)
    grant = session.get(_SESSION_KEY) if session is not None else None
    if not user or not user.is_authenticated or not isinstance(grant, dict):
        return {'active': False, 'expires_at': None, 'expires_in': 0}
    expiry = grant.get('expires_at')
    now = time()
    if (grant.get('user_id') != user.pk or not isinstance(expiry, (int, float))
            or not math.isfinite(expiry) or expiry <= now):
        return {'active': False, 'expires_at': None, 'expires_in': 0}
    return {
        'active': True,
        'expires_at': expiry,
        'expires_in': max(0, math.ceil(expiry - now)),
    }


def unlock_import_limit(request):
    request.session[_SESSION_KEY] = {
        'user_id': request.user.pk,
        'expires_at': time() + IMPORT_UNLOCK_SECONDS,
    }
    return import_unlock_status(request)
