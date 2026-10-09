"""Allocation and first presentation are different durable signals."""
from django.db import transaction
from django.utils import timezone
from apps.users.models import User
from apps.questions.models import Question
from .models import QuestionExposure, QuestionPresentation


def record_allocations(user, snapshots):
    now = timezone.now()
    live = set(Question.objects.filter(pk__in=[int(qid) for qid in snapshots]).values_list('pk', flat=True))
    for key, snapshot in snapshots.items():
        qid = int(key)
        fingerprint = snapshot.get('learning_fingerprint')
        if qid not in live or not fingerprint:
            continue
        exposure, _ = QuestionExposure.objects.get_or_create(user=user, question_id=qid, fingerprint=fingerprint)
        exposure.allocated += 1
        exposure.last_allocated_at = now
        exposure.save(update_fields=['allocated', 'last_allocated_at'])


@transaction.atomic
def record_presentation(user_id, source_key, question_id, snapshot):
    fingerprint = (snapshot or {}).get('learning_fingerprint')
    if not fingerprint:
        return
    User.objects.select_for_update().only('pk').get(pk=user_id)
    if not Question.objects.filter(pk=question_id).exists():
        return
    _, created = QuestionPresentation.objects.get_or_create(
        user_id=user_id, source_key=source_key, question_id=question_id,
        defaults={'fingerprint': fingerprint})
    if created:
        exposure, _ = QuestionExposure.objects.get_or_create(
            user_id=user_id, question_id=question_id, fingerprint=fingerprint)
        exposure.presented += 1
        exposure.last_presented_at = timezone.now()
        exposure.save(update_fields=['presented', 'last_presented_at'])
