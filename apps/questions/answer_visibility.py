"""Answer lookup restrictions shared by payload serializers and offline services."""

from rest_framework.exceptions import APIException


class AnswersWithheld(APIException):
    status_code = 409

    def __init__(self):
        super().__init__({
            'detail': 'أكمل الامتحان الجاري قبل عرض مواد الإجابة / Finish the current exam before viewing answer material.',
            'code': 'ANSWERS_WITHHELD',
        })


def require_answers_available(user, question_ids, *, hidden=None, exclude_session_id=None):
    hidden = closed_book_question_ids(user, exclude_session_id=exclude_session_id) if hidden is None else hidden
    if hidden.intersection(question_ids):
        raise AnswersWithheld()


def closed_book_knowledge_object_ids(user, *, request=None):
    """Protect both frozen and current concept links after content edits."""
    from apps.exams.models import ExamSession
    from apps.master_exams.models import MasterExamAttempt
    from .models import Question

    if user is None or not getattr(user, 'is_authenticated', False):
        return set()
    cache_name = '_closed_book_knowledge_object_ids'
    if request is not None and hasattr(request, cache_name):
        return getattr(request, cache_name)
    ids = set()
    question_ids = set()
    sources = (
        ExamSession.objects.filter(user=user, mode='exam'),
        MasterExamAttempt.objects.filter(user=user, is_complete=False),
    )
    for source in sources:
        for row in source.values('question_ids', 'grading_snapshot'):
            question_ids.update(row['question_ids'] or [])
            for snapshot in (row['grading_snapshot'] or {}).values():
                if snapshot.get('knowledge_object_id'):
                    ids.add(snapshot['knowledge_object_id'])
    ids.update(Question.objects.filter(pk__in=question_ids, knowledge_object__isnull=False)
               .values_list('knowledge_object_id', flat=True))
    if request is not None:
        setattr(request, cache_name, ids)
    return ids


def closed_book_question_ids(user, *, request=None, exclude_session_id=None):
    if user is None or not getattr(user, 'is_authenticated', False):
        return set()
    cache_name = '_closed_book_question_ids'
    if request is not None and exclude_session_id is None and hasattr(request, cache_name):
        return getattr(request, cache_name)

    # Lazy imports preserve model import ordering. Paused ordinary exams still
    # withhold lookup answers; only completed master attempts stop withholding.
    from apps.exams.models import ExamSession
    from apps.master_exams.models import MasterExamAttempt

    hidden = set()
    ordinary = ExamSession.objects.filter(user=user, mode='exam')
    if exclude_session_id is not None:
        ordinary = ordinary.exclude(session_id=exclude_session_id)
    for ids in ordinary.values_list('question_ids', flat=True):
        hidden.update(ids or [])
    for ids in MasterExamAttempt.objects.filter(user=user, is_complete=False).values_list('question_ids', flat=True):
        hidden.update(ids or [])
    if request is not None and exclude_session_id is None:
        setattr(request, cache_name, hidden)
    return hidden
