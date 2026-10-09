"""Runtime model invariants shared by admin and ordinary ORM saves.

Bulk writes and QuerySet.update bypass save(); their callers must validate
explicitly. These guards do not replace database constraints.
"""

import math
from numbers import Integral, Real

from django.core.exceptions import ValidationError
from django.db import router, transaction


def require(condition, field, message):
    if not condition:
        raise ValidationError({field: message})


def validate_counts(instance, *fields):
    for field in fields:
        value = getattr(instance, field)
        require(
            isinstance(value, Integral) and not isinstance(value, bool) and value >= 0,
            field,
            'Must be a nonnegative integer.',
        )


def validate_percentage(instance, field):
    value = getattr(instance, field)
    require(
        isinstance(value, Real) and not isinstance(value, bool)
        and math.isfinite(value) and 0 <= value <= 100,
        field,
        'Must be a finite percentage between 0 and 100.',
    )


def validate_result_counts(instance):
    validate_counts(instance, 'total_questions', 'answered_count', 'correct_count')
    require(
        instance.correct_count <= instance.answered_count <= instance.total_questions,
        'correct_count',
        'Counts must satisfy correct <= answered <= total.',
    )
    validate_percentage(instance, 'accuracy')


class InvariantValidationMixin:
    """Expose field errors to forms and preserve ValueError for service callers."""

    def clean(self):
        super().clean()
        self.validate_invariants()

    def invariants_saved(self, previous, saved):
        """Optional transactional hook for dependent learning evidence."""

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        using = using or router.db_for_write(type(self), instance=self)
        if update_fields is not None:
            update_fields = frozenset(update_fields)
            if not update_fields:
                return
        elif not force_insert and self._state.db == using and self.get_deferred_fields():
            # Django treats deferred saves as partial updates too.
            update_fields = frozenset(
                field.attname for field in self._meta.concrete_fields
                if not field.primary_key and field.attname not in self.get_deferred_fields()
            )
        with transaction.atomic(using=using):
            previous = None
            if self.pk is not None:
                previous = type(self)._base_manager.using(using).select_for_update().filter(
                    pk=self.pk,
                ).first()
            saved = self
            if previous is not None and update_fields is not None:
                # Validate the values that will actually be persisted, not
                # unsaved companion changes on the caller's instance.
                from copy import copy
                saved = copy(previous)
                saved._state = copy(previous._state)
                saved._state.fields_cache = {}
                for name in update_fields:
                    field = self._meta.get_field(name)
                    setattr(saved, field.attname, getattr(self, field.attname))
            try:
                saved.validate_invariants()
            except ValidationError as exc:
                raise ValueError('; '.join(exc.messages)) from exc
            result = super().save(
                force_insert=force_insert, force_update=force_update,
                using=using, update_fields=update_fields,
            )
            self.invariants_saved(previous, saved)
            return result


class RevisionedSaveMixin:
    revision_fields = ()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        using = using or router.db_for_write(type(self), instance=self)
        if update_fields is not None and not update_fields:
            return
        with transaction.atomic(using=using):
            previous = type(self).objects.using(using).select_for_update().filter(pk=self.pk).first() if self.pk else None
            fields = set(update_fields) if update_fields is not None else None
            changed = previous is not None and any(
                (fields is None or field in fields) and getattr(previous, field) != getattr(self, field)
                for field in self.revision_fields)
            self.version = (previous.version + int(changed)) if previous else 1
            if fields is not None:
                fields.add('version')
            return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=fields)
