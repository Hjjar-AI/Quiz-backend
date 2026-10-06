"""Identify assessed content without changing model versions or schema."""

import hashlib
import json


KNOWLEDGE_CONTENT_FIELDS = (
    'learning_objective', 'canonical_answer', 'key_facts', 'misconceptions',
)


def knowledge_learning_content(obj):
    return {field: getattr(obj, field) for field in KNOWLEDGE_CONTENT_FIELDS}


def question_learning_fingerprint(question):
    content = {
        'question': question.question, 'choices': question.choices,
        'correct_answer': question.correct_answer,
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
    UserQuestionAttempt.objects.using(using).filter(question_id__in=question_ids).delete()
