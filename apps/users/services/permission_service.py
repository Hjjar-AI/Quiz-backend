# backend/apps/users/services/permission_service.py
"""
Capability resolution for a User.

Resolution order
----------------
1. Unauthenticated or None    → empty set.
2. Role is 'admin'            → all capabilities.
3. Otherwise                  → role defaults from RoleCapabilities,
                                overlaid with per-user overrides.

The `User.capabilities` field is a dict of {capability_string: bool}.
A `True` value grants the capability even if the role does not hold it;
a `False` value revokes it even if the role does. Absent keys inherit
the role default. This is the standard three-state model
(inherit / force-on / force-off).

Caching
-------
Only the request's User instance memoizes resolved capabilities. Shared role
caches can retain revoked grants after a transaction commits or publish grants
that are later rolled back. Role defaults therefore read the database directly.
"""
from django.core.cache import cache
from django.db import transaction

from ..capabilities import CAPABILITIES, DEFAULT_ROLE_CAPABILITIES


def role_capabilities(role):
    """Read current role defaults, falling back only when no row exists."""
    if not role:
        return set()

    # Lazy import to avoid a circular import at module load:
    # permission_service → models → permission_service.
    from ..models import RoleCapabilities

    row = RoleCapabilities.objects.filter(role=role).first()
    if row is None:
        return set(DEFAULT_ROLE_CAPABILITIES.get(role, ()))
    if not isinstance(row.capabilities, list):
        return set()
    # Admin/raw ORM JSON writes must not crash resolution or restore defaults.
    return {cap for cap in row.capabilities if isinstance(cap, str) and cap in CAPABILITIES}


def invalidate_role_capabilities(role=None, *, using=None):
    """Compatibility hook: remove legacy shared entries after a committed write."""
    roles = (role,) if role else tuple(DEFAULT_ROLE_CAPABILITIES)
    transaction.on_commit(
        lambda: cache.delete_many([f'role_caps:{item}' for item in roles]),
        using=using,
    )


def resolve_for_user(user):
    """
    Return the full set of capabilities granted to `user`.

    The returned set is a fresh object; mutating it does not affect
    the cache or the user's stored overrides.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return set()

    # Admin bypass. Admins always hold the entire capability set
    # regardless of any role-default or override entry.
    if user.role == 'admin':
        return set(CAPABILITIES)

    caps = role_capabilities(user.role)

    overrides = getattr(user, 'capabilities', None) or {}
    if overrides:
        for cap, granted in overrides.items():
            # Silently drop overrides for capabilities that no longer
            # exist. A typo or a removed capability should not break
            # resolution for the rest of the set.
            if cap not in CAPABILITIES:
                continue
            if granted:
                caps.add(cap)
            else:
                caps.discard(cap)

    return caps


def resolved_capabilities_for_user(user):
    """
    Memoized variant used by User.resolved_capabilities().

    The memo lives on the User instance, which Django fetches fresh
    per request. This means:
      • Within a request, has_capability() is O(1) after the first call.
      • Across requests, the memo is discarded — never stale.

    If a code path mutates user.capabilities and re-checks within the
    same request, it must clear the memo. See UserCapabilitiesView.put
    for the pattern (delattr).
    """
    cached = getattr(user, '_resolved_caps_cache', None)
    if cached is not None:
        return cached
    caps = resolve_for_user(user)
    user._resolved_caps_cache = caps
    return caps
