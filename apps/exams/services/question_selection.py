"""User-scoped question variety without changing explicit selections or SRS order.

Existing frozen histories/session/attempt IDs are exposure evidence; they do not
prove a screen was viewed. Deleted histories/discarded sessions cannot contribute.
"""
from collections import Counter
import random


def question_exposure_scores(user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return {}, {}
    from ..models import TestHistory, ExamSession
    from apps.master_exams.models import MasterExamAttempt

    counts = Counter()
    latest = {}

    def record(ids, when):
        valid = set()
        for value in ids:
            if isinstance(value, bool) or not (isinstance(value, int) or (isinstance(value, str) and value.isdecimal())):
                continue
            try:
                qid = int(value)
            except (TypeError, ValueError, OverflowError):
                continue
            if qid > 0:
                valid.add(qid)
        stamp = when.timestamp() if when is not None else 0
        for qid in valid:
            counts[qid] += 1
            latest[qid] = max(latest.get(qid, 0), stamp)

    for results, completed in TestHistory.objects.filter(user=user).values_list('results', 'completed_at').iterator(chunk_size=100):
        if isinstance(results, list):
            record([row.get('question_id', row.get('id')) for row in results if isinstance(row, dict)], completed)
    for ids, started in ExamSession.objects.filter(user=user).values_list('question_ids', 'started_at').iterator(chunk_size=100):
        if isinstance(ids, list):
            record(ids, started)
    for ids, started in MasterExamAttempt.objects.filter(user=user).values_list('question_ids', 'started_at').iterator(chunk_size=100):
        if isinstance(ids, list):
            record(ids, started)
    return counts, latest


def select_varied_question_ids(queryset, count, user=None, exposure=None):
    if count <= 0:
        return []
    ids = list(queryset.order_by().values_list('pk', flat=True).distinct())
    counts, latest = exposure if exposure is not None else question_exposure_scores(user)
    random.shuffle(ids)
    # Unseen first; then fewer previous allocations and older exposure. Random ties.
    ids.sort(key=lambda qid: (counts.get(qid, 0), latest.get(qid, 0)))
    selected = ids[:count]
    random.shuffle(selected)
    return selected
