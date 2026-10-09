"""Shared optimistic revisions; API callers compare only under row locks."""
from rest_framework import serializers
from .exceptions import RevisionConflict
from .models import Setting


def expected_revision(request):
    raw = request.query_params.get('expected_version') if request.method == 'DELETE' else request.data.get('expected_version')
    return serializers.IntegerField(min_value=1).run_validation(raw)


def check_revision(current, expected):
    if current != expected:
        raise RevisionConflict()



def settings_revision(key, using='default'):
    value = Setting.objects.using(using).filter(key=key).values_list('value', flat=True).first()
    return int(value) if value and value.isdecimal() else 1


def lock_revision(key, using='default'):
    Setting.objects.using(using).get_or_create(key=key, defaults={'value': '1'})
    row = Setting.objects.using(using).select_for_update().get(key=key)
    return int(row.value) if row.value and row.value.isdecimal() else 1


def bump_revision(key, using='default'):
    revision = lock_revision(key, using) + 1
    Setting.objects.using(using).filter(key=key).update(value=str(revision))
    return revision
