# backend/apps/questions/serializers/case_resolver.py
"""
Case-resolution helper used by every write path that can attach a
question to a ClinicalCase.

This lives in its own module (not inside `case.py`) because it is a
write-path helper, not a serializer, and it is imported directly by
non-serializer code:

  • apps/master_exams/services/master_exam_service.py
  • apps/master_exams/views/drafts_views.py
  • apps/questions/services/question_service.py

Keeping it separate makes that cross-module contract visible and
lets the helper be exercised in isolation.
"""

from django.db import transaction
from django.http import Http404
from rest_framework.exceptions import ValidationError

from ..models import ClinicalCase
from ..case_policy import visible_cases


@transaction.atomic
def _resolve_case(case_key, user, *, stem=None, existing_case=None, actor=None):
    """
    Resolve a case_key string to a ClinicalCase instance, creating the
    case on first reference. `case_key` may be None or empty, in which
    case the question is detached (returns None).

    `stem` initializes a newly created case only.
    Existing cases are resolved only when visible to the acting user.
    Their content is never edited here, including a blank shared stem:
    changes use the dedicated authorized, revisioned case editor.

    `existing_case` remains accepted for caller compatibility. Always read
    current state under a lock: the caller's case may have an obsolete stem.
    """
    if case_key is None:
        return None
    key = str(case_key).strip()
    if not key:
        return None

    normalized_stem = None
    if stem:
        normalized_stem = str(stem).strip() or None

    created_by_user = user if getattr(user, 'is_authenticated', False) else None
    actor = user if actor is None else actor
    case = ClinicalCase.objects.select_for_update().filter(key=key).first()
    if case is None:
        case, created = ClinicalCase.objects.get_or_create(
            key=key,
            defaults={'authored_by': created_by_user, 'stem': normalized_stem},
        )
        if created:
            return case
        # get_or_create can return a row inserted by a concurrent writer.
        case = ClinicalCase.objects.select_for_update().get(pk=case.pk)
    if not visible_cases(actor).filter(pk=case.pk).exists():
        raise Http404
    if normalized_stem and normalized_stem != (case.stem or '').strip():
        raise ValidationError({'case_stem': [
            'عدّل نص الحالة المشتركة من محرر الحالة ثم احفظ السؤال / Edit the shared stem in the case editor before saving the question.',
        ]})
    # Holding the parent for an FK link is safe here: no existing linked
    # question locks/save hooks are acquired after this parent lock.
    return case
