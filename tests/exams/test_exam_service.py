# tests/exams/test_exam_service.py
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APIClient

from apps.exams.models import ExamSession, TestHistory
from apps.exams.services import ExamService
from apps.learning.models import UserQuestionAttempt
from tests.base import CacheClearingTestCase
from tests.factories import make_user, make_question, make_tag


class StartSessionTests(CacheClearingTestCase):
    def test_start_creates_session(self):
        u = make_user()
        q = make_question(owner=u)
        s = ExamService.start_session(u, 'study', [q.id])
        self.assertEqual(s.user, u)
        self.assertEqual(s.mode, 'study')
        self.assertEqual(s.question_ids, [q.id])
        self.assertTrue(s.is_active)

    def test_start_deletes_previous_active_same_mode(self):
        u = make_user()
        q = make_question(owner=u)
        first = ExamService.start_session(u, 'study', [q.id])
        ExamService.start_session(u, 'study', [q.id])
        self.assertFalse(
            ExamSession.objects.filter(pk=first.pk).exists()
        )

    def test_start_preserves_other_mode(self):
        u = make_user()
        q = make_question(owner=u)
        exam_s = ExamService.start_session(u, 'exam', [q.id])
        ExamService.start_session(u, 'study', [q.id])
        self.assertTrue(
            ExamSession.objects.filter(pk=exam_s.pk).exists()
        )


    def test_long_display_labels_round_trip_all_session_modes(self):
        user = make_user()
        questions = [make_question(owner=user) for _ in range(2)]
        ids = [q.id for q in questions]
        for mode in ('study', 'exam', 'recall'):
            for label in ('Cardiology, ' * 20, 'طب القلب، ' * 20):
                with self.subTest(mode=mode, label=label):
                    session = ExamService.start_session(user, mode, ids, tag=label)
                    session.refresh_from_db()
                    self.assertEqual(session.tag, label[:99] + '…')
                    self.assertEqual(session.question_ids, ids)
                    ExamService.finish_session(session, user)
                    history = TestHistory.objects.get(source_session_id=session.session_id)
                    self.assertEqual(history.tag, session.tag)
                    self.assertEqual(history.total_questions, len(ids))

    def test_label_at_storage_boundary_is_preserved(self):
        user = make_user()
        question = make_question(owner=user)
        for label in (None, '', 'طب القلب', 'x' * 100):
            with self.subTest(label=label):
                session = ExamService.start_session(user, 'study', [question.id], tag=label)
                session.refresh_from_db()
                self.assertEqual(session.tag, label)


class SessionLabelAPITests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.client = APIClient()
        self.client.force_login(self.user)

    def test_long_multitag_label_keeps_complete_question_filter(self):
        names = [f'Medical specialty number {index}' for index in range(8)]
        questions = []
        for name in names:
            question = make_question(owner=self.user)
            question.tags.add(make_tag(name))
            questions.append(question)
        excluded = make_question(owner=self.user)
        label = ', '.join(names)
        for mode in ('study', 'exam', 'recall'):
            with self.subTest(mode=mode):
                response = self.client.post(
                    f'/api/v1/{mode}/start/{mode}/',
                    {'session_label': label, 'tags_filter': names, 'limit': 20},
                    format='json',
                )
                self.assertEqual(response.status_code, 200, response.data)
                data = response.data['data']
                self.assertEqual(data['tag'], label[:99] + '…')
                self.assertCountEqual(data['question_ids'], [q.id for q in questions])
                self.assertNotIn(excluded.id, data['question_ids'])

    def test_nontext_label_returns_400_and_preserves_existing_session(self):
        question = make_question(owner=self.user)
        session = ExamService.start_session(self.user, 'study', [question.id])
        response = self.client.post(
            '/api/v1/study/start/study/',
            {'question_ids': [question.id], 'session_label': ['invalid']},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(ExamSession.objects.filter(pk=session.pk).exists())


class SubmitAnswerTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.u = make_user()
        self.q = make_question(owner=self.u, choices=['A', 'B', 'C'])
        self.s = ExamService.start_session(self.u, 'study', [self.q.id])

    def test_answer_above_choice_count_is_rejected(self):
        with self.assertRaises(ValueError):
            ExamService.submit_answer(self.s, 4, 'next')

    def test_answer_zero_is_rejected(self):
        with self.assertRaises(ValueError):
            ExamService.submit_answer(self.s, 0, 'next')

    def test_answer_persists_and_advances(self):
        ExamService.submit_answer(self.s, 1, 'next')
        self.s.refresh_from_db()
        self.assertEqual(self.s.answers['0']['answer'], 1)
        self.assertEqual(self.s.current_index, 1)

    def test_recall_requires_pre_answer_before_choice(self):
        session = ExamService.start_session(
            self.u, 'recall', [self.q.id],
        )
        with self.assertRaises(ValueError):
            ExamService.submit_answer(session, 1, 'same')

    def test_recall_pre_answer_reveals_choices_without_marking_answered(self):
        session = ExamService.start_session(
            self.u, 'recall', [self.q.id],
        )
        hidden = ExamService.get_question(session, 0)
        self.assertTrue(hidden['question']['choices_hidden'])
        self.assertEqual(hidden['question']['choices'], [])

        ExamService.submit_answer(
            session, None, 'same', pre_answer='My recalled answer',
        )
        session.refresh_from_db()
        revealed = ExamService.get_question(session, 0)

        self.assertFalse(revealed['question']['choices_hidden'])
        self.assertEqual(revealed['question']['choices'], ['A', 'B', 'C'])
        self.assertEqual(revealed['saved_pre_answer'], 'My recalled answer')
        self.assertIsNone(revealed['saved_answer'])

    def test_numeric_confidence_is_stored(self):
        ExamService.submit_answer(self.s, 1, 'same', confidence=2)
        self.s.refresh_from_db()
        self.assertEqual(self.s.answers['0']['confidence'], 2)


class FinishSessionTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.u = make_user()
        self.q = make_question(owner=self.u, choices=['A', 'B'], correct_answer=1)

    def test_finish_writes_history_and_deletes_session(self):
        s = ExamService.start_session(self.u, 'study', [self.q.id])
        ExamService.submit_answer(s, 1, 'next')
        result = ExamService.finish_session(s, self.u)

        self.assertEqual(result['correct_count'], 1)
        self.assertEqual(result['total_questions'], 1)
        self.assertFalse(ExamSession.objects.filter(pk=s.pk).exists())
        self.assertEqual(TestHistory.objects.count(), 1)

    def test_finish_updates_question_stats(self):
        s = ExamService.start_session(self.u, 'study', [self.q.id])
        ExamService.submit_answer(s, 1, 'next')
        ExamService.finish_session(s, self.u)
        self.q.refresh_from_db()
        self.assertEqual(self.q.times_answered, 1)
        self.assertEqual(self.q.times_correct, 1)

    def test_finish_records_srs_attempts(self):
        s = ExamService.start_session(self.u, 'study', [self.q.id])
        ExamService.submit_answer(s, 1, 'next')
        ExamService.finish_session(s, self.u)
        a = UserQuestionAttempt.objects.get(user=self.u, question=self.q)
        self.assertEqual(a.attempts, 1)
        self.assertTrue(a.ever_correct)

    def test_finish_twice_raises(self):
        s = ExamService.start_session(self.u, 'study', [self.q.id])
        ExamService.submit_answer(s, 1, 'next')
        ExamService.finish_session(s, self.u)
        with self.assertRaises(ValueError):
            ExamService.finish_session(s, self.u)

    def test_finish_does_not_double_count_on_second_call(self):
        s = ExamService.start_session(self.u, 'study', [self.q.id])
        ExamService.submit_answer(s, 1, 'next')
        ExamService.finish_session(s, self.u)
        try:
            ExamService.finish_session(s, self.u)
        except ValueError:
            pass
        self.q.refresh_from_db()
        self.assertEqual(self.q.times_answered, 1)
        self.assertEqual(TestHistory.objects.count(), 1)


class PauseResumeTests(CacheClearingTestCase):
    def test_pause_accumulates_time(self):
        u = make_user()
        q = make_question(owner=u)
        s = ExamService.start_session(u, 'study', [q.id])
        s.started_at = timezone.now() - timedelta(seconds=60)
        s.save()
        ExamService.pause_session(s)
        s.refresh_from_db()
        self.assertFalse(s.is_active)
        self.assertGreaterEqual(s.accumulated_time, 60)

    def test_resume_sets_active_and_resets_started_at(self):
        u = make_user()
        q = make_question(owner=u)
        s = ExamService.start_session(u, 'study', [q.id])
        ExamService.pause_session(s)
        ExamService.resume_session(s)
        s.refresh_from_db()
        self.assertTrue(s.is_active)
