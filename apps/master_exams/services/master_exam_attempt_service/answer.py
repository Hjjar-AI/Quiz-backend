# backend/apps/master_exams/services/master_exam_attempt_service/answer.py
"""
Save one answer into an attempt.

CONCURRENCY
-----------
Wrapped in a `select_for_update()` transaction. Without the lock,
two concurrent submissions on the same attempt (a double-click, a
network retry, two tabs) would both read the same `answers` JSONField
and both write their own version with
`save(update_fields=['answers', 'current_question_id'])` — the second
write silently clobbering the first. The row lock serializes the
read-modify-write so the second submission sees the first one's
result before applying its own mutation.

The time check runs after acquiring the lock. A request may wait for
the lock beyond its deadline. Timeout completion runs after leaving
the answer transaction so raising TIME_EXPIRED cannot roll it back.

The view for master exams already prevents most concurrent traffic —
`masterExamAttemptStore.js` maintains a per-question `_pendingAnswers`
map on the client. The lock here closes the door on the cases the
client cannot control: another tab, another device, a retried
request after a slow response.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.questions.models import Question
from apps.questions.payloads import resolve_choice_ceiling
from apps.learning.confidence import normalize_confidence

from ...models import MasterExamAttempt
from .helpers import _grace_seconds, _last_answer_tolerance_seconds
from .question_flow import _next_unanswered
from .finish import _force_finish


def submit_answer(attempt, question_id, answer, confidence=3, error_reason=None, *, expected_slot, session_id):
    grace = timedelta(seconds=_grace_seconds())
    tolerance = timedelta(seconds=_last_answer_tolerance_seconds())
    try:
        return _submit_answer_locked(
            attempt, question_id, answer, confidence, error_reason, grace + tolerance, expected_slot, session_id,
        )
    except _AnswerTimeExpired:
        _force_finish(attempt, reason='timeout')
        raise ValueError('TIME_EXPIRED')


class _AnswerTimeExpired(Exception):
    """Leave the answer transaction before committing timeout completion."""


def _submit_answer_locked(attempt, question_id, answer, confidence, error_reason, allowance, expected_slot, session_id):
    with transaction.atomic():
        locked = (
            MasterExamAttempt.objects
            .select_for_update()
            .filter(pk=attempt.pk)
            .first()
        )
        if locked is None:
            raise ValueError('ATTEMPT_NOT_FOUND')

        if locked.session_id != session_id:
            raise ValueError('ATTEMPT_PROGRESS_CHANGED')

        # Re-check complete under the lock: the sweeper (or a
        # concurrent finish from another tab) may have completed the
        # attempt between the pre-lock read and lock acquisition.
        if locked.is_complete:
            raise ValueError('ATTEMPT_ALREADY_COMPLETE')

        now = timezone.now()
        if locked.deadline_at is not None and now > locked.deadline_at + allowance:
            raise _AnswerTimeExpired
        if isinstance(answer, bool) or not isinstance(answer, int) or answer < 1:
            raise ValueError('إجابة غير صالحة. يجب أن تكون رقماً موجباً')

        attempt_qids = list(locked.question_ids or [])
        if question_id not in attempt_qids:
            raise ValueError('QUESTION_NOT_IN_ATTEMPT')

        # Choice ceiling — shared with ExamService.submit_answer in
        # apps/exams via `resolve_choice_ceiling`, so the fallback order
        # (snapshot choices → live question choices) cannot drift between
        # the two graders.
        #
        # LAZY QUESTION FETCH (perf — preserved from the pre-refactor
        # version)
        # -----------------------------------------------------------------
        # The live `Question` row is only consulted when the frozen
        # snapshot does not itself carry a `choices` list. In practice,
        # every attempt created after the snapshot column landed has a
        # full snapshot, so this branch never fires and we skip an
        # indexed read on the hot answer-submission path.
        #
        # The first draft of this refactor fetched the question
        # unconditionally, which added one DB round-trip per submission
        # for a value `resolve_choice_ceiling` would have found in the
        # snapshot anyway. Do not hoist the fetch above the guard.
        snapshot = (locked.grading_snapshot or {}).get(str(question_id))
        question = None
        if not snapshot or snapshot.get('choices') is None:
            question = Question.objects.filter(id=question_id).only('choices').first()
        max_choice = resolve_choice_ceiling(snapshot, question)
        if max_choice is not None and answer > max_choice:
            raise ValueError(
                f'إجابة غير صالحة. هذا السؤال يحتوي على {max_choice} خيارات فقط'
            )

        actual = (locked.answers or {}).get(str(question_id))
        if actual != expected_slot:
            if actual and actual.get('answer') == answer and normalize_confidence(actual.get('confidence',3)) == normalize_confidence(confidence) and actual.get('error_reason') == error_reason:
                return locked
            raise ValueError('ATTEMPT_PROGRESS_CHANGED')
        new_answers = dict(locked.answers or {})
        new_answers[str(question_id)] = {
            'answer': answer,
            'confidence': normalize_confidence(confidence),
            'answered_at': now.isoformat(),
            'error_reason': error_reason,
        }
        locked.answers = new_answers

        next_id = _next_unanswered(attempt_qids, new_answers)
        locked.current_question_id = next_id or question_id
        locked.save(update_fields=['answers', 'current_question_id'])

        return locked
