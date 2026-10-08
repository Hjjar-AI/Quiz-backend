"""Serialize structural taxonomy writes across application workers."""

from apps.core.models import Setting


def lock_tag_hierarchy(using='default'):
    """Acquire the shared row lock inside the caller's transaction.

    A single persistent mutex also covers initially disconnected trees;
    locking just the edited tag cannot prevent reciprocal reparenting.
    """
    manager = Setting.objects.using(using)
    manager.get_or_create(key='_tag_hierarchy_lock', defaults={'value': ''})
    manager.select_for_update().get(key='_tag_hierarchy_lock')
