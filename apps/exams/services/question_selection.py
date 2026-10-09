"""Version-aware user variety, concept diversity and explicit selection strategies."""
from collections import Counter
import heapq
import random
from django.utils import timezone
from apps.learning.models import QuestionExposure, UserQuestionAttempt
from apps.learning.evidence import question_learning_fingerprint

STRATEGIES = {'coverage', 'balanced', 'review'}


def question_exposure_scores(user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return {}
    return {(e.question_id, e.fingerprint): e for e in QuestionExposure.objects.filter(user=user).iterator()}


def select_varied_question_ids(queryset, count, user=None, exposure=None, strategy='coverage', selected_concepts=None):
    if count <= 0:
        return []
    if strategy not in STRATEGIES:
        raise ValueError('Invalid selection strategy')
    rows = list(queryset.order_by().select_related('knowledge_object', 'case').distinct())
    evidence = exposure if exposure is not None else question_exposure_scores(user)
    attempts = {a.question_id: a for a in UserQuestionAttempt.objects.filter(user=user)} if user else {}
    now = timezone.now()
    concepts = selected_concepts if selected_concepts is not None else Counter()
    heap = []
    by_id = {q.pk: q for q in rows}
    for q in rows:
        version = question_learning_fingerprint(q)
        seen = evidence.get((q.pk, version))
        allocations = seen.allocated if seen else 0
        presentations = max(seen.presented, seen.answered) if seen else 0
        times = [stamp for stamp in (seen.last_presented_at, seen.last_answered_at, seen.last_allocated_at) if stamp] if seen else []
        when = max(times) if times else None
        last = when.timestamp() if when else 0
        attempt = attempts.get(q.pk)
        due = bool(attempt and (attempt.next_due is None or attempt.next_due <= now))
        weak = bool(attempt and (not attempt.last_correct or not attempt.last_confidence))
        # Coverage retains unseen-first. Review favors due/weak evidence; balanced
        # mixes unseen coverage with due reviews, before other repeated practice.
        tier = int(presentations > 0) if strategy == 'coverage' else (
            (0 if due else 1 if weak else 2 if presentations == 0 else 3) if strategy == 'review'
            else (0 if due or presentations == 0 else 1 if weak else 2))
        concept = ('concept', q.knowledge_object_id) if q.knowledge_object_id else ('question', q.pk)
        base = (tier, presentations, allocations)
        heapq.heappush(heap, (base, 0, last, random.random(), q.pk, concept))
    chosen = []
    while heap and len(chosen) < count:
        base, diversity, last, tie, qid, concept = heapq.heappop(heap)
        if diversity != concepts[concept]:
            heapq.heappush(heap, (base, concepts[concept], last, tie, qid, concept))
            continue
        chosen.append(qid)
        concepts[concept] += 1
    return order_case_groups(chosen, by_id)


def order_case_groups(ids, by_id=None):
    from apps.questions.models import Question
    by_id = by_id if by_id is not None else {q.pk: q for q in Question.objects.filter(pk__in=ids)}
    blocks = {}
    for qid in ids:
        q = by_id.get(qid)
        key = ('case', q.case_id) if q and q.case_id else ('question', qid)
        blocks.setdefault(key, []).append(qid)
    groups = list(blocks.values())
    for group in groups:
        group.sort(key=lambda qid: (by_id[qid].case_order or 0, qid) if qid in by_id else (0, qid))
    random.shuffle(groups)
    return [qid for group in groups for qid in group]
