"""Identify assessed content without changing model versions or schema."""

import hashlib
import json


KNOWLEDGE_CONTENT_FIELDS = (
    'learning_objective', 'canonical_answer', 'key_facts', 'misconceptions',
)


def with_locked_learning_content(queryset):
    """Lock nullable assessed relations separately, without outer-join locks.

    Evaluate only inside a transaction, after locking the question rows.
    Related rows are locked in a consistent case/knowledge and primary-key order.
    """
    from django.db.models import Prefetch
    from apps.questions.models import ClinicalCase, KnowledgeObject

    return queryset.prefetch_related(
        Prefetch('case', queryset=ClinicalCase.objects.select_for_update().order_by('pk')),
        Prefetch('knowledge_object', queryset=KnowledgeObject.objects.select_for_update().order_by('pk')),
    )


def knowledge_learning_content(obj):
    content = {field: getattr(obj, field) for field in KNOWLEDGE_CONTENT_FIELDS}
    content['translations'] = {
        locale: {field: value.get(field) for field in KNOWLEDGE_CONTENT_FIELDS}
        for locale, value in (obj.translations or {}).items() if isinstance(value, dict)
    }
    return content


def question_learning_fingerprint(question):
    content = {
        'question': question.question, 'choices': question.choices,
        'correct_answer': question.correct_answer,
        'translations': {
            locale: {field: value.get(field) for field in ('question', 'choices')}
            for locale, value in (question.translations or {}).items() if isinstance(value, dict)
        },
        'knowledge_object_id': question.knowledge_object_id,
        'knowledge': (
            knowledge_learning_content(question.knowledge_object)
            if question.knowledge_object_id else None
        ),
        'case_stem': question.case.stem if question.case_id else None,
        'image': question.image.name if question.image else None,
    }
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, ensure_ascii=False).encode('utf-8'),
    ).hexdigest()


def invalidate_question_learning(question_ids, using='default'):
    from .models import UserQuestionAttempt
    from apps.questions.models import Question
    ids = list(question_ids)
    UserQuestionAttempt.objects.using(using).filter(question_id__in=ids).delete()
    Question.objects.using(using).filter(pk__in=ids).update(
        times_answered=0, times_correct=0, stats_fingerprint='',
    )
