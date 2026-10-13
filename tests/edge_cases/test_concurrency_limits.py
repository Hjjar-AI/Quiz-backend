"""Real PostgreSQL races with independent connections and bounded worker counts."""
import json
import threading
import time
import uuid
from collections import Counter
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.db import connection, connections, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.exceptions import RevisionConflict
from apps.core.revisions import settings_revision
from apps.exams.services.exam_service import SessionProgressConflict
from apps.exams.models import ExamSession, TestHistory, OfflineCompletion
from apps.exams.services import ExamService
from apps.feedback.models import Bookmark, QuestionFlag
from apps.feedback.services import FeedbackService
from apps.groups.services import GroupService
from apps.learning.evidence import question_learning_fingerprint
from apps.learning.exposure import record_presentation
from apps.learning.models import LearningEvent, UserQuestionAttempt, LearningDay, QuestionExposure, OfflineQuestionGrant
from apps.master_exams.models import MasterExam, MasterExamQuestion, MasterExamAttempt
from apps.master_exams.services import MasterExamAttemptService, MasterExamService
from apps.planning.models import StudyPlannerDay
from apps.planning.services import StudyPlannerService
from apps.questions.models import Question, ClinicalCase, Category
from apps.questions.services import QuestionService, ImportService
from apps.users.models import User
from tests.factories import make_user, make_admin, make_question, make_case


class PostgreSQLConcurrencyLimitsTests(TransactionTestCase):
    """Counts are probes, not advertised HTTP capacity or universal maxima."""

    def setUp(self):
        super().setUp()
        if connection.vendor != 'postgresql':
            self.skipTest('This matrix requires PostgreSQL row locks and session timeouts.')
        cache.clear()
        self.user = make_user('race_user')
        self.question = make_question(owner=self.user, choices=['A', 'B'])

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def race(self, actions, *, label=None):
        barrier = threading.Barrier(len(actions))
        results = [None] * len(actions)
        elapsed = [0.0] * len(actions)

        def worker(index, action):
            try:
                connections.close_all()
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '5s'")
                    cursor.execute("SET statement_timeout = '10s'")
                barrier.wait(timeout=15)
                started = time.monotonic()
                try:
                    results[index] = ('ok', action())
                except Exception as exc:
                    results[index] = ('error', exc)
                finally:
                    elapsed[index] = time.monotonic() - started
            except Exception as exc:
                results[index] = ('error', exc)
                barrier.abort()
            finally:
                connections.close_all()

        started = time.monotonic()
        threads = [threading.Thread(target=worker, args=(i, action), daemon=True)
                   for i, action in enumerate(actions)]
        for thread in threads:
            thread.start()
        deadline = started + 30
        for thread in threads:
            thread.join(timeout=max(0, deadline - time.monotonic()))
        self.assertFalse(any(thread.is_alive() for thread in threads), 'Worker exceeded test deadline')
        counts = Counter(type(value).__name__ if status == 'error' else 'ok'
                         for status, value in results)
        ordered = sorted(elapsed)
        print('CONCURRENCY_RESULT ' + json.dumps({
            'scenario': label or self._testMethodName, 'workers': len(actions),
            'outcomes': dict(counts), 'wall_seconds': round(time.monotonic() - started, 4),
            'operation_p50_seconds': round(ordered[len(ordered) // 2], 4),
            'operation_max_seconds': round(max(elapsed), 4),
        }), flush=True)
        return results

    def all_ok(self, results):
        self.assertEqual([type(value).__name__ for status, value in results if status == 'error'], [])

    def one_conflict(self, results, error_type):
        self.assertEqual(sum(status == 'ok' for status, _ in results), 1)
        rejected = [value for status, value in results if status == 'error']
        self.assertEqual(len(rejected), 1)
        self.assertIsInstance(rejected[0], error_type)

    def api(self, user, method, path, data=None):
        client = APIClient()
        client.force_authenticate(user=user)
        response = getattr(client, method)(path, data=data, format='json')
        return response.status_code, response.json()

    def master(self):
        now = timezone.now()
        exam = MasterExam.objects.create(name='Race exam', primary_attending=self.user,
            opens_at=now-timedelta(hours=1), closes_at=now+timedelta(hours=2),
            duration_minutes=60, stored_status='published')
        exam.audience_users.add(self.user)
        MasterExamQuestion.objects.create(master_exam=exam, question=self.question, order=1)
        return exam

    def event_result(self):
        return {'question_id': self.question.pk, 'user_answer': 1, 'is_correct': True,
                'confidence_score': 3, 'learning_fingerprint': question_learning_fingerprint(self.question)}

    def record(self, source, user=None):
        user = user or self.user
        with transaction.atomic():
            ExamService.record_completion_side_effects(user, [self.event_result()], source_key=source)

    def test_master_start_four_retries_reuse_one_attempt(self):
        exam = self.master()
        results = self.race([lambda: MasterExamAttemptService.start(self.user, exam).pk] * 4)
        self.all_ok(results)
        self.assertEqual(len({value for _, value in results}), 1)
        self.assertEqual(MasterExamAttempt.objects.count(), 1)

    def test_master_identical_answers_keep_one_slot_and_timestamp(self):
        attempt = MasterExamAttemptService.start(self.user, self.master())
        def answer():
            saved = MasterExamAttemptService.submit_answer(attempt, self.question.pk, 1,
                        expected_slot=None, session_id=attempt.session_id)
            return saved.answers[str(self.question.pk)]['answered_at']
        results = self.race([answer] * 4)
        self.all_ok(results)
        self.assertEqual(len({value for _, value in results}), 1)

    def test_master_different_answers_from_same_baseline_conflict(self):
        attempt = MasterExamAttemptService.start(self.user, self.master())
        results = self.race([lambda a=a: MasterExamAttemptService.submit_answer(
            attempt, self.question.pk, a, expected_slot=None, session_id=attempt.session_id).pk
            for a in (1, 2)])
        self.one_conflict(results, ValueError)
        self.assertEqual(next(value for status, value in results if status == 'error').args,
                         ('ATTEMPT_PROGRESS_CHANGED',))

    def test_master_finish_sixteen_retries_record_learning_once(self):
        attempt = MasterExamAttemptService.start(self.user, self.master())
        MasterExamAttemptService.submit_answer(attempt, self.question.pk, 1,
            expected_slot=None, session_id=attempt.session_id)
        results = self.race([lambda: MasterExamAttemptService.finish(attempt).pk] * 16)
        self.all_ok(results)
        self.assertEqual(LearningEvent.objects.count(), 1)
        self.assertEqual(UserQuestionAttempt.objects.get().attempts, 1)
        self.assertEqual(StudyPlannerDay.objects.get().questions_answered, 1)

    def test_master_answer_racing_finish_has_no_partial_learning(self):
        attempt = MasterExamAttemptService.start(self.user, self.master())
        results = self.race([
            lambda: MasterExamAttemptService.submit_answer(attempt, self.question.pk, 1,
                expected_slot=None, session_id=attempt.session_id).pk,
            lambda: MasterExamAttemptService.finish(attempt).pk])
        attempt.refresh_from_db()
        self.assertTrue(attempt.is_complete)
        rejected = [value for status, value in results if status == 'error']
        if rejected:
            self.assertEqual(len(rejected), 1)
            self.assertIsInstance(rejected[0], ValueError)
            self.assertEqual(str(rejected[0]), 'ATTEMPT_ALREADY_COMPLETE')
        count = len(attempt.answers)
        self.assertEqual(LearningEvent.objects.count(), count)
        self.assertEqual(attempt.correct_count, count)

    def test_ordinary_start_four_retries_leave_one_session(self):
        results = self.race([lambda: ExamService.start_session(self.user, 'study', [self.question.pk]).pk] * 4)
        self.all_ok(results)
        # Ordinary start replaces the previous session; it is not a receipt-backed retry.
        self.assertEqual(ExamSession.objects.filter(user=self.user, mode='study').count(), 1)

    def test_ordinary_different_answers_from_same_baseline_conflict(self):
        session = ExamService.start_session(self.user, 'study', [self.question.pk])
        empty = {'answer': None, 'confidence': None, 'pre_answer': None, 'error_reason': None}
        results = self.race([lambda a=a: ExamService.submit_answer(session, a, 'same',
            expected_index=0, expected_slot=empty) for a in (1, 2)])
        self.one_conflict(results, SessionProgressConflict)

    def test_ordinary_finish_four_retries_create_one_history(self):
        session = ExamService.start_session(self.user, 'exam', [self.question.pk])
        ExamService.submit_answer(session, 1, 'same')
        results = self.race([lambda: ExamService.finish_session(session, self.user)] * 4)
        self.assertEqual(sum(status == 'ok' for status, _ in results), 1)
        for status, value in results:
            if status == 'error':
                self.assertIsInstance(value, ValueError)
        self.assertEqual(TestHistory.objects.count(), 1)
        self.assertEqual(LearningEvent.objects.count(), 1)
        self.assertEqual(UserQuestionAttempt.objects.get().attempts, 1)

    def test_question_same_revision_has_one_winner(self):
        results = self.race([lambda text=text: QuestionService.update_question(self.question.pk,
            {'question': text, 'expected_version': self.question.version}, self.user)
            for text in ('Writer A?', 'Writer B?')])
        self.one_conflict(results, ValueError)
        self.assertEqual(str(next(value for status, value in results if status == 'error')),
                         'Question was modified by another user')
        self.question.refresh_from_db()
        self.assertEqual(self.question.version, 2)

    def test_planner_same_revision_has_one_winner(self):
        planner = StudyPlannerService.get_or_create_planner(self.user)
        results = self.race([lambda target=target: StudyPlannerService.update_planner(
            self.user, target, [], [], timezone.localdate(), None,
            expected_version=planner.version, expected_id=planner.pk) for target in (20, 30)])
        self.one_conflict(results, RevisionConflict)
        planner.refresh_from_db()
        self.assertGreater(planner.version, 1)

    def test_group_same_revision_has_one_winner(self):
        group = GroupService.create_group('Race group', '', self.user.username)
        results = self.race([lambda name=name: GroupService.update_group(group,
            name=name, expected_version=group.version) for name in ('Group A', 'Group B')])
        self.one_conflict(results, RevisionConflict)

    def test_master_composition_same_revision_has_one_winner(self):
        exam = self.master()
        exam.stored_status = 'draft'
        exam.opens_at = timezone.now() + timedelta(hours=1)
        exam.save()
        questions = [make_question(owner=self.user) for _ in range(2)]
        results = self.race([lambda q=q: MasterExamService.add_questions(exam, [q.pk],
            expected_version=exam.version) for q in questions])
        self.one_conflict(results, ValueError)
        self.assertEqual(exam.exam_questions.count(), 2)

    def test_question_creation_receipt_four_retries_create_once(self):
        payload = {'operation_id': str(uuid.uuid4()), 'question': 'Receipt question?',
                   'choices': ['A', 'B'], 'correct_answer': 1}
        results = self.race([lambda: self.api(self.user, 'post', '/api/v1/questions/', payload)] * 4)
        self.all_ok(results)
        self.assertTrue(all(value[0] in (200, 201) for _, value in results))
        self.assertEqual(len({value[1]['data']['id'] for _, value in results}), 1)
        self.assertEqual(Question.objects.count(), 2)

    def test_question_creation_changed_body_same_receipt_conflicts(self):
        identity = str(uuid.uuid4())
        payloads = [{'operation_id': identity, 'question': text,
                     'choices': ['A', 'B'], 'correct_answer': 1} for text in ('Receipt A?', 'Receipt B?')]
        results = self.race([lambda body=body: self.api(self.user, 'post', '/api/v1/questions/', body)
                             for body in payloads])
        self.all_ok(results)
        self.assertEqual(sorted(value[0] for _, value in results), [201, 409])

    def test_category_creation_receipt_four_retries_create_once(self):
        actor = make_user('category_moderator', role='moderator')
        payload = {'operation_id': str(uuid.uuid4()), 'name': 'Receipt category'}
        results = self.race([lambda: self.api(actor, 'post', '/api/v1/questions/categories/create/', payload)] * 4)
        self.all_ok(results)
        self.assertTrue(all(value[0] in (200, 201) for _, value in results))
        self.assertEqual(Category.objects.filter(name='Receipt category').count(), 1)

    def test_bookmark_set_sixteen_retries_keeps_one_row(self):
        results = self.race([lambda: FeedbackService.set_bookmark(self.user.pk, self.question.pk, True)] * 16)
        self.all_ok(results)
        self.assertEqual(Bookmark.objects.count(), 1)

    def test_bookmark_two_legacy_toggles_reverse_each_other(self):
        results = self.race([lambda: FeedbackService.toggle_bookmark(self.user.pk, self.question.pk)] * 2)
        self.all_ok(results)
        self.assertEqual(sorted(value for _, value in results), [False, True])
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_flag_four_retries_create_one_open_flag(self):
        results = self.race([lambda: FeedbackService.flag_question(self.user.pk, self.question.pk, 'Race flag')] * 4)
        self.all_ok(results)
        self.assertEqual(sum(value for _, value in results), 1)
        self.assertEqual(QuestionFlag.objects.count(), 1)

    def test_learning_duplicate_source_sixteen_retries_credit_once(self):
        results = self.race([lambda: self.record('race:duplicate')] * 16)
        self.all_ok(results)
        self.assertEqual(LearningEvent.objects.count(), 1)
        self.assertEqual(LearningDay.objects.get().questions_answered, 1)
        self.assertEqual(StudyPlannerDay.objects.get().questions_answered, 1)
        self.question.refresh_from_db()
        self.assertEqual(self.question.times_answered, 1)

    def test_learning_distinct_sources_bounded_load_has_no_lost_counts(self):
        total = 0
        for workers in (2, 4, 8, 16):
            results = self.race([lambda source=f'race:{workers}:{i}': self.record(source)
                                 for i in range(workers)], label=f'learning_same_user_{workers}')
            self.all_ok(results)
            total += workers
            self.assertEqual(UserQuestionAttempt.objects.get().attempts, total)
            self.assertEqual(LearningDay.objects.get().questions_answered, total)
            self.assertEqual(StudyPlannerDay.objects.get().questions_answered, total)
        self.assertEqual(LearningEvent.objects.count(), total)
        self.question.refresh_from_db()
        self.assertEqual(self.question.times_answered, total)

    def test_learning_sixteen_users_sharing_question_have_no_lost_stats(self):
        users = [make_user() for _ in range(16)]
        results = self.race([lambda u=u: self.record(f'race:user:{u.pk}', user=u) for u in users])
        self.all_ok(results)
        self.assertEqual(LearningEvent.objects.count(), 16)
        self.assertEqual(UserQuestionAttempt.objects.count(), 16)
        self.question.refresh_from_db()
        self.assertEqual(self.question.times_answered, 16)

    def test_presentation_four_retries_credit_once(self):
        snapshot = {'learning_fingerprint': question_learning_fingerprint(self.question)}
        results = self.race([lambda: record_presentation(self.user.pk, 'race:presentation', self.question.pk, snapshot)] * 4)
        self.all_ok(results)
        self.assertEqual(QuestionExposure.objects.get().presented, 1)

    @override_settings(OFFLINE_SELECTED_QUESTION_LIMIT=2)
    def test_offline_selected_quota_cannot_be_overrun_by_four_packs(self):
        questions = [make_question(owner=self.user) for _ in range(4)]
        results = self.race([lambda q=q: self.api(self.user, 'post', '/api/v1/exam/offline/packs/',
            {'question_ids': [q.pk], 'full_bank': False}) for q in questions])
        self.all_ok(results)
        self.assertEqual(sorted(value[0] for _, value in results), [200, 200, 403, 403])
        self.assertEqual(OfflineQuestionGrant.objects.count(), 2)

    def offline_body(self):
        status, body = self.api(self.user, 'post', '/api/v1/exam/offline/packs/',
                               {'question_ids': [self.question.pk]})
        self.assertEqual(status, 200)
        return {'completion_id': str(uuid.uuid4()), 'token': body['data']['token'],
                'answers': [{'question_id': self.question.pk, 'answer': 1, 'confidence': 3}],
                'time_spent': 10}

    def test_offline_completion_four_retries_create_one_history_and_receipt(self):
        body = self.offline_body()
        results = self.race([lambda: self.api(self.user, 'post', '/api/v1/exam/offline/completions/', body)] * 4)
        self.all_ok(results)
        self.assertTrue(all(value[0] == 200 for _, value in results))
        self.assertEqual(OfflineCompletion.objects.count(), 1)
        self.assertEqual(TestHistory.objects.count(), 1)
        self.assertEqual(LearningEvent.objects.count(), 1)
        self.assertEqual(UserQuestionAttempt.objects.get().attempts, 1)

    def test_offline_changed_completion_same_identity_conflicts(self):
        body = self.offline_body()
        changed = {**body, 'answers': [{'question_id': self.question.pk, 'answer': 2, 'confidence': 3}]}
        results = self.race([lambda data=data: self.api(self.user, 'post', '/api/v1/exam/offline/completions/', data)
                             for data in (body, changed)])
        self.all_ok(results)
        self.assertEqual(sorted(value[0] for _, value in results), [200, 409])
        self.assertEqual(TestHistory.objects.count(), 1)

    def test_runtime_settings_same_revision_has_one_winner(self):
        actor = make_admin('settings_admin')
        baseline = settings_revision('_runtime_settings_revision')
        results = self.race([lambda days=days: self.api(actor, 'post', '/api/v1/admin/settings/',
            {'default_expiry_days': days, 'expected_version': baseline}) for days in (20, 30)])
        self.all_ok(results)
        self.assertEqual(sorted(value[0] for _, value in results), [200, 409])

    def test_tag_tree_same_revision_has_one_winner(self):
        from tests.factories import make_tag
        actor = make_user('tag_moderator', role='moderator')
        make_tag('race_tag')
        baseline = settings_revision('_tag_hierarchy_lock')
        results = self.race([lambda name=name: self.api(actor, 'post', '/api/v1/questions/admin/tags/race_tag/rename/',
            {'new_name': name, 'expected_version': baseline}) for name in ('tag_a', 'tag_b')])
        self.all_ok(results)
        self.assertEqual(sorted(value[0] for _, value in results), [200, 409])

    def test_throttle_one_per_minute_is_approximate_under_competing_cache_reads(self):
        # Deliberately coordinate the non-atomic cache read/write window.
        # This tests DRF's algorithm, not real Memcached/Redis integration.
        from apps.core.throttles import _UserScopedThrottle
        gate = threading.Barrier(2)
        class ReadTogetherCache:
            def get(self, key, default=None):
                history = cache.get(key, default)
                gate.wait(timeout=5)
                return history
            def set(self, *args, **kwargs):
                return cache.set(*args, **kwargs)
        class ProbeThrottle(_UserScopedThrottle):
            scope = 'concurrency_probe'
            rate = '1/min'
        request = SimpleNamespace(user=self.user)
        def allow():
            throttle = ProbeThrottle()
            throttle.cache = ReadTogetherCache()
            return throttle.allow_request(request, None)
        results = self.race([allow] * 2)
        self.all_ok(results)
        self.assertEqual([value for _, value in results], [True, True])
        self.assertFalse(ProbeThrottle().allow_request(request, None))

    def test_duplicate_state_imports_preserve_one_uuid_and_advance_local_revision(self):
        from tests.questions.test_state_import import _envelope, _q_entry, _upload
        identity = str(uuid.uuid4())
        payload = _envelope([_q_entry(identity)])
        with patch('apps.questions.services.importing.state_import.entrypoint.verify_upload_mime', return_value=None):
            results = self.race([lambda: ImportService.import_state(
                _upload(payload), self.user.username, conflict_strategy='use_imported')] * 2)
        self.all_ok(results)
        self.assertTrue(all('error' not in value for _, value in results))
        self.assertEqual(Question.objects.filter(uuid=identity).count(), 1)
        self.assertGreaterEqual(Question.objects.get(uuid=identity).version, 2)

    def test_reciprocal_tag_reparenting_cannot_create_cycle(self):
        from tests.factories import make_tag
        tags = [make_tag('cycle_a'), make_tag('cycle_b')]
        def reparent(child, parent):
            child = type(child).objects.get(pk=child.pk)
            child.parent_id = parent.pk
            child.save()
        results = self.race([lambda child=child, parent=parent: reparent(child, parent)
                             for child, parent in (tags, tags[::-1])])
        self.assertEqual(sum(status == 'ok' for status, _ in results), 1)
        rejected = next(value for status, value in results if status == 'error')
        from django.core.exceptions import ValidationError
        self.assertIsInstance(rejected, (ValueError, ValidationError))
        for tag in tags:
            tag.refresh_from_db()
        self.assertFalse(tags[0].parent_id == tags[1].pk and tags[1].parent_id == tags[0].pk)

    def test_group_membership_four_retries_create_one_pair(self):
        group = GroupService.create_group('Membership race', '', self.user.username)
        results = self.race([lambda: GroupService.add_members(group, [self.user.pk])] * 4)
        self.all_ok(results)
        self.assertEqual(group.memberships.count(), 1)

    @override_settings(MASTER_EXAM_MAX_QUESTIONS=2)
    def test_master_question_cap_remains_bounded_with_competing_appends(self):
        exam = self.master()
        exam.stored_status = 'draft'
        exam.opens_at = timezone.now() + timedelta(hours=1)
        exam.save()
        questions = [make_question(owner=self.user) for _ in range(4)]
        results = self.race([lambda q=q: MasterExamService.add_questions(exam, [q.pk]) for q in questions])
        self.assertEqual(sum(status == 'ok' for status, _ in results), 1)
        for status, value in results:
            if status == 'error':
                self.assertIsInstance(value, ValueError)
        self.assertEqual(exam.exam_questions.count(), 2)

    def test_parent_content_edit_racing_completion_keeps_history_but_invalidates_stats(self):
        case = make_case(stem='Original stem')
        self.question.case = case
        self.question.save()
        result = self.event_result()
        def learn():
            with transaction.atomic():
                ExamService.record_completion_side_effects(self.user, [result], source_key='race:parent')
        def edit():
            fresh = ClinicalCase.objects.get(pk=case.pk)
            fresh.stem = 'Revised stem'
            fresh.save()
        results = self.race([learn, edit])
        self.all_ok(results)
        self.question.refresh_from_db()
        self.assertEqual(LearningEvent.objects.count(), 1)
        self.assertEqual(self.question.times_answered, 0)
        self.assertEqual(UserQuestionAttempt.objects.count(), 0)

    def test_last_active_admin_cannot_be_removed_by_cross_deactivation(self):
        admins = [make_admin(password='race-admin-password') for _ in range(2)]
        results = self.race([lambda actor=actor, target=target: self.api(actor, 'post',
            f'/api/v1/auth/admin/users/{target.pk}/active/',
            {'is_active': False, 'admin_password': 'race-admin-password'})
            for actor, target in (admins, admins[::-1])])
        self.all_ok(results)
        self.assertEqual(sorted(value[0] for _, value in results), [200, 400])
        self.assertEqual(User.objects.filter(role='admin', is_active=True).count(), 1)

    def test_lock_timeout_rolls_back_and_independent_user_can_write(self):
        locked = threading.Event()
        release = threading.Event()
        errors = []
        def holder():
            try:
                with transaction.atomic():
                    User.objects.select_for_update().get(pk=self.user.pk)
                    locked.set()
                    if not release.wait(timeout=10):
                        raise TimeoutError('Lock holder deadline')
            except Exception as exc:
                errors.append(exc)
            finally:
                connections.close_all()
        thread = threading.Thread(target=holder, daemon=True)
        thread.start()
        try:
            self.assertTrue(locked.wait(timeout=5))
            other = make_user()
            def blocked():
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '200ms'")
                return FeedbackService.set_bookmark(self.user.pk, self.question.pk, True)
            results = self.race([blocked, lambda: FeedbackService.set_bookmark(other.pk, self.question.pk, True)])
            self.assertEqual(sum(status == 'ok' for status, _ in results), 1)
            exc = next(value for status, value in results if status == 'error')
            self.assertEqual(getattr(exc.__cause__, 'sqlstate', None), '55P03')
            self.assertFalse(Bookmark.objects.filter(user=self.user).exists())
            self.assertTrue(Bookmark.objects.filter(user=other).exists())
        finally:
            release.set()
            thread.join(timeout=10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        FeedbackService.set_bookmark(self.user.pk, self.question.pk, True)
        self.assertEqual(Bookmark.objects.count(), 2)
