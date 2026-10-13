# tests/learning/test_srs_service.py
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.learning.models import UserQuestionAttempt
from apps.learning.srs_service import (
    SRSService, _apply_review, _next_interval, EASE_FLOOR,
)
from tests.base import CacheClearingTestCase
from tests.factories import make_attempt
from tests.factories import make_user, make_question


class NextIntervalTests(CacheClearingTestCase):
    def test_first_repetition_is_one_day(self):
        self.assertEqual(_next_interval(1, 0, 2.5), 1)

    def test_second_repetition_is_six_days(self):
        self.assertEqual(_next_interval(2, 1, 2.5), 6)

    def test_third_repetition_multiplies_by_ease(self):
        self.assertEqual(_next_interval(3, 6, 2.5), 15)
        self.assertEqual(_next_interval(3, 6, 3.0), 18)

    def test_interval_never_below_one(self):
        self.assertGreaterEqual(_next_interval(3, 0, 1.3), 1)


class ApplyReviewTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.q = make_question(owner=self.user)

    def _fresh(self):
        return UserQuestionAttempt(user=self.user, question=self.q)

    def test_correct_confident_advances_ladder(self):
        a = self._fresh()
        _apply_review(a, is_correct=True, is_confident=True)
        self.assertEqual(a.attempts, 1)
        self.assertEqual(a.repetitions, 1)
        self.assertEqual(a.interval_days, 1)
        self.assertTrue(a.ever_correct)

    def test_numeric_confidence_score_is_preserved(self):
        a = self._fresh()
        _apply_review(a, is_correct=True, confidence_score=2)
        self.assertEqual(a.last_confidence_score, 2)
        self.assertFalse(a.last_confidence)

    def test_guessing_score_is_preserved(self):
        a = self._fresh()
        _apply_review(a, is_correct=False, confidence_score=1)
        self.assertEqual(a.last_confidence_score, 1)
        self.assertFalse(a.last_confidence)

    def test_wrong_unknown_schedules_ten_minute_relearning(self):
        a = self._fresh()
        a.attempts = 5
        a.ever_correct = a.last_correct = True
        a.repetitions = 5
        a.interval_days = 30
        _apply_review(a, is_correct=False, is_confident=False,
                      error_reason='unknown')
        self.assertEqual(a.repetitions, 0)
        self.assertEqual(a.interval_days, 0)
        self.assertTrue(a.relearning)
        self.assertEqual(a.next_due - a.last_answered_at, timedelta(minutes=10))
        self.assertEqual(a.wrong_count, 1)

    def test_wrong_misread_resets_chain_and_schedules_twelve_hours(self):
        a = self._fresh()
        a.attempts = 3
        a.ever_correct = a.last_correct = True
        a.repetitions = 3
        _apply_review(a, is_correct=False, is_confident=False,
                      error_reason='misread')
        self.assertEqual(a.repetitions, 0)
        self.assertEqual(a.interval_days, 0)
        self.assertTrue(a.relearning)
        self.assertEqual(a.next_due - a.last_answered_at, timedelta(hours=12))

    def test_wrong_confused_resets_chain_and_schedules_six_hours(self):
        a = self._fresh()
        a.attempts = 3
        a.ever_correct = a.last_correct = True
        a.repetitions = 3
        _apply_review(a, is_correct=False, is_confident=False,
                      error_reason='confused')
        self.assertEqual(a.repetitions, 0)
        self.assertEqual(a.interval_days, 0)
        self.assertTrue(a.relearning)
        self.assertEqual(a.next_due - a.last_answered_at, timedelta(hours=6))

    def test_wrong_guessed_resets(self):
        a = self._fresh()
        a.attempts = 4
        a.ever_correct = a.last_correct = True
        a.repetitions = 4
        _apply_review(a, is_correct=False, is_confident=False,
                      error_reason='guessed')
        self.assertEqual(a.repetitions, 0)
        self.assertEqual(a.interval_days, 0)
        self.assertTrue(a.relearning)
        self.assertEqual(a.next_due - a.last_answered_at, timedelta(hours=1))

    def test_ease_factor_has_a_floor(self):
        a = self._fresh()
        a.ease_factor = EASE_FLOOR
        for _ in range(10):
            _apply_review(a, is_correct=False, is_confident=False)
        self.assertGreaterEqual(a.ease_factor, EASE_FLOOR)

    def test_correct_clears_error_reason(self):
        a = self._fresh()
        _apply_review(a, is_correct=False, is_confident=False,
                      error_reason='misread')
        self.assertEqual(a.last_error_reason, 'misread')
        _apply_review(a, is_correct=True, is_confident=True)
        self.assertIsNone(a.last_error_reason)


class RecordLearningEventsTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.q1 = make_question(owner=self.user)
        self.q2 = make_question(owner=self.user)

    def _record(self, source, answered=True):
        from apps.learning.events import record_events
        from apps.learning.evidence import question_learning_fingerprint
        from apps.users.models import User
        results = [{'question_id': q.pk, 'user_answer': 1 if answered else None,
                    'is_correct': True, 'confidence_score': 3,
                    'learning_fingerprint': question_learning_fingerprint(q)}
                   for q in (self.q1, self.q2)]
        with transaction.atomic():
            User.objects.select_for_update().get(pk=self.user.pk)
            return record_events(self.user, results, source)

    def test_creates_rows_for_new_answers(self):
        self.assertEqual(len(self._record('test:first')), 2)
        self.assertEqual(UserQuestionAttempt.objects.count(), 2)

    def test_unanswered_rows_are_skipped(self):
        self.assertEqual(self._record('test:unanswered', answered=False), [])
        self.assertEqual(UserQuestionAttempt.objects.count(), 0)

    def test_new_source_updates_existing(self):
        self._record('test:first')
        self._record('test:second')
        a = UserQuestionAttempt.objects.get(user=self.user, question=self.q1)
        self.assertEqual(a.attempts, 2)
        # Immediate practice does not advance spaced repetitions.
        self.assertEqual(a.repetitions, 1)

    def test_duplicate_source_does_not_double_count(self):
        self._record('test:first')
        self.assertEqual(self._record('test:first'), [])
        a = UserQuestionAttempt.objects.get(user=self.user, question=self.q1)
        self.assertEqual(a.attempts, 1)
        self.q1.refresh_from_db()
        self.assertEqual(self.q1.times_answered, 1)


class DueAndQueryTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.q1 = make_question(owner=self.user)
        self.q2 = make_question(owner=self.user)

    def test_due_includes_past_and_null_next_due(self):
        now = timezone.now()
        make_attempt(
            user=self.user, question=self.q1,
            next_due=now - timedelta(days=1),
        )
        make_attempt(
            user=self.user, question=self.q2,
            next_due=None,
        )
        due = set(SRSService.due_question_ids(self.user))
        self.assertEqual(due, {self.q1.id, self.q2.id})

    def test_due_excludes_future(self):
        make_attempt(
            user=self.user, question=self.q1,
            next_due=timezone.now() + timedelta(days=7),
        )
        self.assertEqual(SRSService.due_question_ids(self.user), [])

    def test_wrong_question_ids_ordered_by_wrong_count(self):
        make_attempt(
            user=self.user, question=self.q1,
            ever_correct=False, wrong_count=1,
        )
        make_attempt(
            user=self.user, question=self.q2,
            ever_correct=False, wrong_count=5,
        )
        wrong = SRSService.wrong_question_ids(self.user)
        self.assertEqual(wrong[0], self.q2.id)

    def test_fragile_question_ids_are_correct_but_not_confident(self):
        make_attempt(
            user=self.user, question=self.q1,
            last_correct=True, last_confidence=False,
        )
        make_attempt(
            user=self.user, question=self.q2,
            last_correct=True, last_confidence=True,
        )
        self.assertEqual(
            SRSService.fragile_question_ids(self.user), [self.q1.id],
        )

    def test_attempt_summary_shape(self):
        make_attempt(
            user=self.user, question=self.q1,
            ever_correct=True, last_correct=True, last_confidence=False,
        )
        summary = SRSService.attempt_summary(self.user)
        self.assertEqual(summary['total_seen'], 1)
        self.assertEqual(summary['ever_correct'], 1)
        self.assertEqual(summary['fragile_correct'], 1)
        self.assertEqual(summary['wrong_open'], 0)
