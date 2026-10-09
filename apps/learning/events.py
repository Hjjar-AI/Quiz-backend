"""Transactional learning evidence shared by every completion path.

Callers hold the learner lock and supply a durable source identity. Historical
events survive content/history deletion; only matching content feeds live SRS.
"""
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.questions.models import Question
from .models import LearningEvent, UserQuestionAttempt, QuestionExposure, LearningDay
from .evidence import question_learning_fingerprint, with_locked_learning_content
from .confidence import normalize_confidence
from .mastery import attempt_mastery_score
from .srs_service import _apply_review


def replay_question(user, question, fingerprint, latest_event=None):
    """Replay in occurrence order, so delayed uploads cannot reverse chronology."""
    stored = UserQuestionAttempt.objects.filter(user=user, question=question).first()
    if stored is not None and latest_event is not None and latest_event.occurred_at >= stored.last_answered_at:
        before = attempt_mastery_score(stored)
        due = bool(stored.attempts and stored.next_due and latest_event.occurred_at >= stored.next_due)
        _apply_review(stored, latest_event.is_correct, latest_event.confidence_score,
                      error_reason=latest_event.error_reason, now=latest_event.occurred_at)
        stored.save()
        latest_event.spaced_credit = due
        latest_event.mastery_delta = attempt_mastery_score(stored) - before
        latest_event.save(update_fields=['spaced_credit', 'mastery_delta'])
        return
    state = UserQuestionAttempt(user=user, question=question)
    changes = []
    for event in LearningEvent.objects.filter(
        user=user, question=question, fingerprint=fingerprint, current_content=True,
    ).order_by('occurred_at', 'received_at', 'pk'):
        before = attempt_mastery_score(state) if state.attempts else 0.0
        due = bool(state.attempts and state.next_due and event.occurred_at >= state.next_due)
        _apply_review(state, event.is_correct, event.confidence_score,
                      error_reason=event.error_reason, now=event.occurred_at)
        event.spaced_credit = due
        event.mastery_delta = attempt_mastery_score(state) - before
        changes.append(event)
    if not changes:
        return
    if stored is not None:
        state.pk = stored.pk
        state._state.adding = False
    state.save()
    LearningEvent.objects.bulk_update(changes, ['spaced_credit', 'mastery_delta'])


def record_events(user, results, source_key, occurred_at=None):
    now = timezone.now()
    occurred_at = occurred_at or now
    answered = [row for row in results if row.get('user_answer') is not None and row.get('question_id')]
    questions = {q.pk: q for q in with_locked_learning_content(
        Question.objects.select_for_update().filter(
            pk__in=[row['question_id'] for row in answered],
        ).order_by('pk'))}
    created_results = []
    for result in answered:
        qid = result['question_id']
        question = questions.get(qid)
        fingerprint = result.get('learning_fingerprint') or ''
        current = question_learning_fingerprint(question) if question else None
        matches = bool(fingerprint and fingerprint == current)
        event_time = parse_datetime(result['answered_at']) if result.get('answered_at') else occurred_at
        event_time = min(event_time or occurred_at, now)
        event, created = LearningEvent.objects.get_or_create(
            user=user, source_key=source_key, original_question_id=qid,
            defaults={
                'question': question, 'fingerprint': fingerprint,
                'occurred_at': event_time, 'received_at': now,
                'category_id_snapshot': result.get('category_id'),
                'concept_id_snapshot': result.get('knowledge_object_id'),
                'tag_names': result.get('tag_names') or [],
                'is_correct': bool(result.get('is_correct')),
                'confidence_score': normalize_confidence(result.get('confidence_score', 3)),
                'error_reason': result.get('error_reason'), 'current_content': matches,
            },
        )
        if not created:
            continue
        created_results.append({**result, '_occurred_at': event_time})
        day, _ = LearningDay.objects.get_or_create(user=user, date=timezone.localdate(event_time))
        day.questions_answered += 1
        day.save(update_fields=['questions_answered'])
        if not matches:
            continue
        if question.stats_fingerprint != current:
            question.times_answered = question.times_correct = 0
            question.stats_fingerprint = current
        question.times_answered += 1
        question.times_correct += int(event.is_correct)
        # These counters do not change assessed content; avoid save-hook recursion.
        Question.objects.filter(pk=qid).update(
            times_answered=question.times_answered, times_correct=question.times_correct,
            stats_fingerprint=current,
        )
        exposure, _ = QuestionExposure.objects.get_or_create(
            user=user, question=question, fingerprint=current)
        exposure.answered += 1
        exposure.last_answered_at = max(filter(None, [exposure.last_answered_at, event_time]))
        exposure.save(update_fields=['answered', 'last_answered_at'])
        replay_question(user, question, current, latest_event=event)
    return created_results


def learning_streaks(user):
    """Compute on local occurrence days; late uploads may bridge an old gap."""
    days = list(LearningDay.objects.filter(user=user, questions_answered__gt=0).order_by('date').values_list('date', flat=True))
    current = longest = run = 0
    previous = None
    for day in days:
        run = run + 1 if previous and (day - previous).days == 1 else 1
        longest = max(longest, run)
        previous = day
    if days and (timezone.localdate() - days[-1]).days <= 1:
        current = run
    return {'last_study_date': days[-1] if days else None,
            'current_streak': current, 'longest_streak': longest}
