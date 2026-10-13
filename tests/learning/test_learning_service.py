# tests/learning/test_learning_service.py
from datetime import timedelta

from django.utils import timezone

from apps.learning.models import UserQuestionAttempt
from apps.learning.services import LearningService
from tests.base import CacheClearingTestCase
from tests.factories import make_attempt
from tests.factories import make_user, make_question


class StudyNowQueueTests(CacheClearingTestCase):
    """Queue budgets include planner targets and only due reviews earn priority."""
    def setUp(self):
        super().setUp()
        self.u = make_user()

    # ── Helpers ────────────────────────────────────────────────────
    def _make_srs_only(self, n):
        """
        Questions that are due NOW and nothing else:
          • next_due in the past   → srs_due
          • last_correct=True      → NOT wrong_open
          • ever_correct=True      → NOT wrong_open
          • last_confidence=True   → NOT fragile
        """
        for _ in range(n):
            q = make_question(owner=self.u)
            make_attempt(
                user=self.u, question=q,
                next_due=timezone.now() - timedelta(days=1),
                last_correct=True,
                ever_correct=True,
                last_confidence=True,
            )

    def _make_fragile_only(self, n):
        """
        Questions that are fragile and nothing else:
          • last_correct=True, last_confidence=False → fragile
          • next_due far in the future               → NOT srs_due
          • ever_correct=True                        → NOT wrong_open
        """
        for _ in range(n):
            q = make_question(owner=self.u)
            make_attempt(
                user=self.u, question=q,
                last_correct=True,
                last_confidence=False,
                ever_correct=True,
                next_due=timezone.now() + timedelta(days=30),
            )

    def _make_wrong_open_only(self, n):
        """
        Questions that are wrong-open and nothing else:
          • ever_correct=False, last_correct=False  → wrong_open
          • next_due far in the future              → NOT srs_due
          • last_confidence=True                    → NOT fragile
        """
        for _ in range(n):
            q = make_question(owner=self.u)
            make_attempt(
                user=self.u, question=q,
                ever_correct=False,
                last_correct=False,
                last_confidence=True,
                next_due=timezone.now() + timedelta(days=30),
            )

    def _make_fresh(self, n):
        """Never-attempted public questions."""
        for _ in range(n):
            make_question(owner=self.u)

    # ── Tests ──────────────────────────────────────────────────────

    def test_anonymous_returns_empty_payload(self):
        from django.contrib.auth.models import AnonymousUser
        result = LearningService.study_now_queue(AnonymousUser())
        self.assertEqual(result['question_ids'], [])
        self.assertEqual(result['total'], 0)
        self.assertEqual(
            set(result['breakdown'].keys()),
            {'srs_due', 'planner_targets', 'fragile', 'wrong_open',
             'weak_categories', 'fresh', 'general'},
        )

    def test_brand_new_user_gets_fresh_questions(self):
        self._make_fresh(30)
        result = LearningService.study_now_queue(self.u, limit=10)
        self.assertEqual(result['total'], 10)
        self.assertEqual(result['breakdown']['fresh'], 10)

    def test_empty_question_bank_returns_empty(self):
        result = LearningService.study_now_queue(self.u, limit=10)
        self.assertEqual(result['question_ids'], [])
        self.assertEqual(result['total'], 0)

    def test_srs_due_bucket_fills_its_budget(self):
        self._make_srs_only(15)
        self._make_fresh(20)
        result = LearningService.study_now_queue(self.u, limit=10)
        self.assertEqual(result['breakdown']['srs_due'], 3)
        self.assertEqual(result['breakdown']['fresh'], 7)
        self.assertEqual(result['total'], 10)

    def test_future_fragile_answers_do_not_earn_early_review_priority(self):
        self._make_srs_only(2)
        self._make_fragile_only(20)
        self._make_fresh(20)
        result = LearningService.study_now_queue(self.u, limit=10)
        self.assertEqual(result['breakdown']['srs_due'], 2)
        self.assertEqual(result['breakdown']['fragile'], 0)
        self.assertEqual(result['breakdown']['fresh'], 8)
        self.assertEqual(result['total'], 10)

    def test_future_wrong_answers_do_not_earn_early_review_priority(self):
        self._make_wrong_open_only(20)
        self._make_fresh(20)
        result = LearningService.study_now_queue(self.u, limit=10)
        self.assertEqual(result['breakdown']['srs_due'], 0)
        self.assertEqual(result['breakdown']['wrong_open'], 0)
        self.assertEqual(result['breakdown']['fresh'], 10)
        self.assertEqual(result['total'], 10)

    def test_never_returns_duplicates(self):
        # A question that is BOTH due and fragile — must appear once.
        q = make_question(owner=self.u)
        make_attempt(
            user=self.u, question=q,
            next_due=timezone.now() - timedelta(days=1),
            last_correct=True, last_confidence=False,
        )
        self._make_fresh(20)
        result = LearningService.study_now_queue(self.u, limit=10)
        ids = result['question_ids']
        self.assertEqual(len(ids), len(set(ids)))

    def test_limit_is_clamped_to_200(self):
        self._make_fresh(300)
        result = LearningService.study_now_queue(self.u, limit=1000)
        self.assertLessEqual(result['total'], 200)

    def test_zero_limit_is_clamped_to_one(self):
        """
        The service clamps limit to the range [1, 200]. A limit of 0
        (or any negative value) must produce exactly one question
        when at least one question is visible — not zero, which is
        what an unclamped implementation would produce.

        The previous version of this test asserted `>= 0`, which is
        trivially true for a list length and would still pass if the
        clamp were removed entirely.
        """
        make_question(owner=self.u)
        result = LearningService.study_now_queue(self.u, limit=0)
        self.assertEqual(result['total'], 1)

    def test_negative_limit_is_clamped_to_one(self):
        make_question(owner=self.u)
        result = LearningService.study_now_queue(self.u, limit=-5)
        self.assertEqual(result['total'], 1)

    def test_invalid_limit_uses_default(self):
        self._make_fresh(30)
        result = LearningService.study_now_queue(self.u, limit='garbage')
        self.assertLessEqual(result['total'], 20)
