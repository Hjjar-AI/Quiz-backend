# backend/apps/users/signals.py
"""Clean up legacy role-cache entries after model writes commit.

Role resolution reads the database; bulk writes also take effect without signals.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import RoleCapabilities
from .services.permission_service import invalidate_role_capabilities


@receiver(post_save, sender=RoleCapabilities, dispatch_uid='role_caps_save')
def _invalidate_on_save(sender, instance, **kwargs):
    invalidate_role_capabilities(instance.role, using=kwargs.get('using'))


@receiver(post_delete, sender=RoleCapabilities, dispatch_uid='role_caps_delete')
def _invalidate_on_delete(sender, instance, **kwargs):
    invalidate_role_capabilities(instance.role, using=kwargs.get('using'))