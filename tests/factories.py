# tests/factories.py
"""
Minimal factory helpers for coherent positive fixtures. Explicit inconsistent
values still reach model validation. Core prerequisites include:

  • Question.published must have owned_by (CheckConstraint).
  • User.create_user requires a password and a valid username.
  • Verified questions include verifier and timestamp.
  • Histories/SRS counters and confidence fields agree.

Activity tests use immutable learning evidence rather than history rows.

USERNAME VALIDATION
-------------------
The model's USERNAME_REGEX is `^[a-zA-Z0-9_\\u0600-\\u06FF]{3,50}$`.
That means: no hyphens, no dots, no spaces, at least 3 characters.
A test that calls make_user('flagged-author') or make_admin('the-admin')
fails inside create_user with an Arabic error message that is easy
to misread as an app bug. `_validate_username` catches that earlier
with an English message that names the factory.
"""
import re
from datetime import timedelta

from django.utils import timezone

from apps.users.models import User
from apps.questions.models import (
    Question, Category, Tag, ClinicalCase,
)


_counter = {'n': 0}
_USERNAME_RE = re.compile(r'^[a-zA-Z0-9_\u0600-\u06FF]{3,50}$')


def _next(prefix):
    _counter['n'] += 1
    return f'{prefix}{_counter["n"]}'


def _validate_username(username):
    """
    Fail fast with a clear message when a test passes a username the
    model will reject. The regex is duplicated here on purpose — the
    model's own error message is in Arabic and does not name the
    factory, which makes the failure look like an app bug during a
    test run.
    """
    if not _USERNAME_RE.match(username):
        raise ValueError(
            f'tests.factories: username {username!r} is rejected by '
            f'USERNAME_REGEX. Rules: 3-50 chars, letters/digits/'
            f'underscore only, no hyphens or dots.'
        )


def make_user(username=None, password='test-pw-1234', **kw):
    if username is None:
        username = _next('user')
    _validate_username(username)
    return User.objects.create_user(username=username, password=password, **kw)


def make_admin(username=None, password='test-admin-pw-1234', **kw):
    if username is None:
        username = _next('admin')
    _validate_username(username)
    return User.objects.create_superuser(username=username, password=password, **kw)


def make_stub(username=None):
    if username is None:
        username = _next('stub')
    _validate_username(username)
    return User.objects.create_stub(username)


def make_category(name=None, **kw):
    if name is None:
        name = _next('cat-')
    return Category.objects.create(name=name, **kw)


def make_tag(name=None):
    if name is None:
        name = _next('tag-')
    return Tag.objects.create(name=name)


def make_case(key=None, **kw):
    if key is None:
        key = _next('case-')
    return ClinicalCase.objects.create(key=key, **kw)


def make_question(owner=None, **kw):
    """
    Build a Question.

    `owner` is used as both authored_by and owned_by unless overridden.
    The CheckConstraint on Question requires a published question
    (is_draft=False) to have owned_by set, so we always pass one.
    """
    if owner is None:
        owner = make_user()
    defaults = {
        'question': 'Sample question text?',
        'choices': ['A', 'B', 'C', 'D'],
        'correct_answer': 1,
        'explanation': 'Because.',
        'difficulty': 'medium',
        'authored_by': owner,
        'owned_by': owner,
        'is_draft': False,
    }
    defaults.update(kw)
    if defaults.get('verified'):
        defaults.setdefault('verified_by', owner.username)
        defaults.setdefault('verified_at', timezone.now())
    return Question.objects.create(**defaults)


def make_test_history(user, **kw):
    from apps.exams.models import TestHistory
    defaults = {
        'user': user,
        'mode': 'study',
        'total_questions': 10,
        'correct_count': 7,
        'accuracy': 70.0,
        'time_spent': 300,
        'completed_at': timezone.now(),
    }
    defaults.update(kw)
    defaults.setdefault('answered_count', defaults['total_questions'])
    if 'correct_count' not in kw:
        defaults['correct_count'] = round(defaults['answered_count'] * defaults['accuracy'] / 100)
    return TestHistory.objects.create(**defaults)


def make_attempt(**kw):
    """Build coherent SRS query fixtures; explicit inconsistent fields still fail."""
    from apps.learning.models import UserQuestionAttempt
    defaults = dict(kw)
    wrong = defaults.get('wrong_count', 0)
    correct = defaults.get('ever_correct', defaults.get('last_correct', False))
    defaults.setdefault('attempts', wrong + max(defaults.get('repetitions', 0), int(correct)))
    defaults.setdefault('ever_correct', defaults['attempts'] > wrong)
    defaults.setdefault('last_confidence_score', 3 if defaults.get('last_confidence', True) else 2)
    return UserQuestionAttempt.objects.create(**defaults)


def make_learning_batch(user, total_questions=10, correct_count=None, completed_at=None):
    """Commit answered evidence through the same path as session writers."""
    from django.db import transaction
    from apps.learning.events import record_events, learning_streaks
    from apps.learning.evidence import question_learning_fingerprint
    from apps.planning.services import StudyPlannerService
    correct_count = round(total_questions * .7) if correct_count is None else correct_count
    results = []
    for index in range(total_questions):
        question = make_question(owner=user)
        correct = index < correct_count
        results.append({'question_id': question.pk, 'user_answer': 1 if correct else 2,
                        'is_correct': correct, 'confidence_score': 3,
                        'learning_fingerprint': question_learning_fingerprint(question)})
    with transaction.atomic():
        User.objects.select_for_update().get(pk=user.pk)
        created = record_events(user, results, _next('fixture:'), occurred_at=completed_at)
        StudyPlannerService.record_learning_progress(user, created)
        for field, value in learning_streaks(user).items():
            setattr(user, field, value)
        user.save(update_fields=['current_streak', 'longest_streak', 'last_study_date'])
    return created


def make_exam_session(user, question_ids=None, mode='study', **kw):
    from apps.exams.models import ExamSession
    import uuid
    defaults = {
        'session_id': str(uuid.uuid4()),
        'user': user,
        'mode': mode,
        'question_ids': question_ids or [],
        'answers': {},
        'current_index': 0,
        'is_active': True,
    }
    defaults.update(kw)
    return ExamSession.objects.create(**defaults)
