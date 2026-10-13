"""Answer lookup restrictions shared by payload serializers and offline services."""


def closed_book_question_ids(user, *, request=None):
    if user is None or not getattr(user, 'is_authenticated', False):
        return set()
    cache_name = '_closed_book_question_ids'
    if request is not None and hasattr(request, cache_name):
        return getattr(request, cache_name)

    # Lazy imports preserve model import ordering. Paused ordinary exams still
    # withhold lookup answers; only completed master attempts stop withholding.
    from apps.exams.models import ExamSession
    from apps.master_exams.models import MasterExamAttempt

    hidden = set()
    for ids in ExamSession.objects.filter(user=user, mode='exam').values_list('question_ids', flat=True):
        hidden.update(ids or [])
    for ids in MasterExamAttempt.objects.filter(user=user, is_complete=False).values_list('question_ids', flat=True):
        hidden.update(ids or [])
    if request is not None:
        setattr(request, cache_name, hidden)
    return hidden
