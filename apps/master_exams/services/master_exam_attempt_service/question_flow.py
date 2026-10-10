# backend/apps/master_exams/services/master_exam_attempt_service/question_flow.py
"""
Current-question lookup, navigation, and unanswered iteration.
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from ...models import MasterExamAttempt
from .helpers import _grace_seconds
from .finish import _force_finish
from apps.questions.models import Question
from apps.questions.payloads import (
    exam_question_payload,
    snapshot_image_url,
    without_translation_explanations,
)
from apps.learning.confidence import normalize_confidence


def _next_unanswered(question_ids, answers):
    answered = set(int(k) for k in answers.keys())
    for qid in question_ids:
        if qid not in answered:
            return qid
    return None


class _ExpiredNavigation(Exception):
    pass


def _locked_active(attempt):
    User.objects.select_for_update().get(pk=attempt.user_id)
    fresh=MasterExamAttempt.objects.select_for_update().filter(pk=attempt.pk).first()
    if fresh is None: raise ValueError('ATTEMPT_NOT_FOUND')
    if fresh.is_complete: raise ValueError('ATTEMPT_ALREADY_COMPLETE')
    if timezone.now() > fresh.deadline_at + timedelta(seconds=_grace_seconds()): raise _ExpiredNavigation()
    return fresh


def current_question(attempt):
    try:
        with transaction.atomic():
            return _current_question_locked(_locked_active(attempt))
    except _ExpiredNavigation:
        _force_finish(attempt)
        raise ValueError('TIME_EXPIRED')


def _current_question_locked(attempt):
    attempt_qids = list(attempt.question_ids or [])
    current_id = attempt.current_question_id
    if current_id is None or current_id not in attempt_qids:
        current_id = _next_unanswered(
            attempt_qids, attempt.answers,
        )
    if current_id is None:
        current_id = attempt_qids[0] if attempt_qids else None

    if current_id is None:
        return None

    try:
        question = (
            Question.objects
            .select_related('case')
            .get(id=current_id)
        )
    except Question.DoesNotExist:
        return None

    payload = exam_question_payload(question)
    snapshot = (attempt.grading_snapshot or {}).get(str(question.id))
    if snapshot:
        payload.update({
            'text': snapshot['question'],
            'choices': snapshot['choices'],
            'translations': snapshot.get('translations') or {},
            'image_url': snapshot_image_url(snapshot),
            'case': (
                {key: snapshot['case'][key] for key in ('id', 'key', 'stem')}
                if snapshot.get('case') else None
            ),
        })
    payload['translations'] = without_translation_explanations(
        payload.get('translations'),
    )
    from apps.learning.exposure import record_presentation
    record_presentation(attempt.user_id, f'master:{attempt.session_id}', question.pk, snapshot)
    saved = attempt.answers.get(str(question.id)) or {}
    return {
        'index': attempt_qids.index(question.id),
        'total': len(attempt_qids),
        'question': payload,
        'saved_slot': saved or None, 'session_id': attempt.session_id,'current_question_id':attempt.current_question_id,
        'saved_answer': saved.get('answer'),
        'saved_confidence': normalize_confidence(saved.get('confidence', 3)),
    }


def goto_question(attempt, question_id, *, expected_current, session_id):
    try:
        with transaction.atomic():
            fresh=_locked_active(attempt)
            if fresh.session_id != session_id: raise ValueError('ATTEMPT_PROGRESS_CHANGED')
            if question_id not in (fresh.question_ids or []): raise ValueError('QUESTION_NOT_IN_EXAM')
            if fresh.current_question_id != expected_current:
                if fresh.current_question_id == question_id: return fresh
                raise ValueError('ATTEMPT_PROGRESS_CHANGED')
            fresh.current_question_id=question_id
            fresh.save(update_fields=['current_question_id'])
            return fresh
    except _ExpiredNavigation:
        _force_finish(attempt)
        raise ValueError('TIME_EXPIRED')
