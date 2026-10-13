"""Learning activity from immutable events, bucketed in Python for portable TZ behavior."""
from datetime import datetime, time
from django.utils import timezone
from apps.learning.models import LearningEvent


def _bucket():
    return {'sources': set(), 'ids': set(), 'concepts': set(), 'questions': 0,
            'correct': 0, 'due_reviews': 0, 'mastery_gain': 0.0}


def _add(bucket, event):
    bucket['sources'].add(event.source_key)
    bucket['ids'].add(event.original_question_id)
    if event.concept_id_snapshot:
        bucket['concepts'].add(event.concept_id_snapshot)
    bucket['questions'] += 1
    bucket['correct'] += int(event.is_correct)
    bucket['due_reviews'] += int(event.spaced_credit)
    bucket['mastery_gain'] += event.mastery_delta


def _public(bucket):
    return {'sessions': len(bucket['sources']), 'questions': bucket['questions'],
            'correct': bucket['correct'], 'unique_questions': len(bucket['ids']),
            'unique_concepts': len(bucket['concepts']), 'due_reviews': bucket['due_reviews'],
            'mastery_gain': round(bucket['mastery_gain'], 1)}


def daily_activity(user_id, first_date):
    start = timezone.make_aware(datetime.combine(first_date, time.min))
    activity = {}
    for event in LearningEvent.objects.filter(user_id=user_id, occurred_at__gte=start).only('source_key', 'occurred_at', 'original_question_id', 'concept_id_snapshot', 'is_correct', 'spaced_credit', 'mastery_delta').iterator():
        day = timezone.localtime(event.occurred_at).date().isoformat()
        _add(activity.setdefault(day, _bucket()), event)
    return {day: _public(bucket) for day, bucket in activity.items()}


def group_activity(user_ids, cutoff):
    activity = {}
    for event in LearningEvent.objects.filter(user_id__in=user_ids, occurred_at__gte=cutoff).only('user_id', 'source_key', 'original_question_id', 'concept_id_snapshot', 'is_correct', 'spaced_credit', 'mastery_delta').iterator():
        _add(activity.setdefault(event.user_id, _bucket()), event)
    result = {}
    for user_id, bucket in activity.items():
        row = _public(bucket)
        row['questions_answered'] = row.pop('questions')
        result[user_id] = row
    return result
