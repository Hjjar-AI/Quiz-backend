"""Focused database-backed API cases for the current Android contracts.

Run only with the isolated tests.test_settings overlay. Standard test-schema
initialization is required; no application database or deployed server is used.
SQLite verifies persisted outcomes here, not production row-lock concurrency.
"""
import json

from django.conf import settings
from rest_framework.test import APIClient

from apps.exams.models import ExamSession
from apps.users.models import User
from tests.base import CacheClearingTestCase
from tests.factories import make_admin, make_category, make_exam_session, make_question, make_tag, make_user


class AndroidAuthPersistenceTests(CacheClearingTestCase):
    password = 'account-password-1234'

    def setUp(self):
        super().setUp()
        self.alice = make_user('rotate_alice', self.password)
        self.bob = make_user('rotate_bob', self.password)
        self.client = APIClient(enforce_csrf_checks=True)

    def token(self):
        response = self.client.get('/api/v1/auth/csrf/')
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()['data']['token']

    def login(self, user, token):
        response = self.client.post('/api/v1/auth/login/',
            {'username': user.username, 'password': self.password}, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200, response.content)

    def test_login_rotates_csrf_and_only_new_token_can_log_out(self):
        old_token = self.token()
        old_secret = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        self.login(self.alice, old_token)
        self.assertNotEqual(self.client.cookies[settings.CSRF_COOKIE_NAME].value, old_secret)
        rejected = self.client.post('/api/v1/auth/logout/', {}, format='json', HTTP_X_CSRFTOKEN=old_token)
        self.assertEqual(rejected.status_code, 403, rejected.content)
        self.assertEqual(rejected.json()['details']['reason'], 'CSRF_FAILED')
        self.assertEqual(self.client.get('/api/v1/auth/me/').json()['data']['id'], self.alice.pk)
        current_token = self.token()
        logged_out = self.client.post('/api/v1/auth/logout/', {}, format='json', HTTP_X_CSRFTOKEN=current_token)
        self.assertEqual(logged_out.status_code, 200, logged_out.content)
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 401)

    def test_switching_accounts_invalidates_previous_server_session(self):
        self.login(self.alice, self.token())
        stale = APIClient(enforce_csrf_checks=True)
        stale.cookies[settings.SESSION_COOKIE_NAME] = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.login(self.bob, self.token())
        current = self.client.get('/api/v1/auth/me/')
        self.assertEqual(current.status_code, 200, current.content)
        self.assertEqual(current.json()['data']['id'], self.bob.pk)
        self.assertEqual(stale.get('/api/v1/auth/me/').status_code, 401)


class AndroidDiscardPersistenceTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.owner = make_user('discard_owner')
        self.other = make_user('discard_other')
        self.owned = make_exam_session(self.owner)
        self.foreign = make_exam_session(self.other)
        self.client = APIClient()
        self.client.force_login(self.owner)

    def test_query_discard_deletes_only_caller_session(self):
        response = self.client.delete('/api/v1/study/discard/',
            QUERY_STRING=f'session_id={self.owned.session_id}')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['data']['deleted_count'], 1)
        self.assertFalse(ExamSession.objects.filter(pk=self.owned.pk).exists())
        self.assertTrue(ExamSession.objects.filter(pk=self.foreign.pk).exists())

    def test_foreign_session_query_does_not_delete_other_user_progress(self):
        response = self.client.delete('/api/v1/study/discard/',
            QUERY_STRING=f'session_id={self.foreign.session_id}')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['data']['deleted_count'], 0)
        self.assertTrue(ExamSession.objects.filter(pk=self.owned.pk).exists())
        self.assertTrue(ExamSession.objects.filter(pk=self.foreign.pk).exists())

    def test_current_vue_body_discard_persists_same_owner_scope(self):
        response = self.client.delete('/api/v1/study/discard/',
            {'session_id': self.owned.session_id}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(ExamSession.objects.filter(pk=self.owned.pk).exists())
        self.assertTrue(ExamSession.objects.filter(pk=self.foreign.pk).exists())


class AndroidUserDeletePersistenceTests(CacheClearingTestCase):
    password = 'operator-password-1234'

    def setUp(self):
        super().setUp()
        self.operator = make_user('delete_operator', self.password, capabilities={'admin.users': True})
        self.target = make_user('delete_target')
        self.client = APIClient()
        self.client.force_login(self.operator)

    def delete(self, target=None, password=None):
        target = target or self.target
        return self.client.post(f'/api/v1/auth/admin/users/{target.pk}/delete/',
            {'admin_password': self.password if password is None else password}, format='json')

    def test_password_authorized_post_removes_real_user(self):
        response = self.delete()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(User.objects.filter(pk=self.target.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.operator.pk).exists())

    def test_incorrect_password_keeps_target_unchanged(self):
        response = self.delete(password='incorrect-password')
        self.assertEqual(response.status_code, 403, response.content)
        self.assertTrue(User.objects.filter(pk=self.target.pk).exists())

    def test_self_deletion_is_rejected_with_real_capability_holder(self):
        response = self.delete(target=self.operator)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(response.json()['details']['reason'], 'SELF_DELETE_FORBIDDEN')
        self.assertTrue(User.objects.filter(pk=self.operator.pk).exists())

    def test_last_admin_cannot_be_deleted_by_non_admin_operator(self):
        last_admin = make_admin('only_admin')
        response = self.delete(target=last_admin)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(response.json()['details']['reason'], 'LAST_ADMIN_DELETE_FORBIDDEN')
        self.assertTrue(User.objects.filter(pk=last_admin.pk, is_active=True).exists())

    def test_question_owner_cannot_be_deleted_and_question_is_retained(self):
        question = make_question(owner=self.target)
        response = self.delete()
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()['details']['reason'], 'USER_HAS_QUESTIONS')
        question.refresh_from_db()
        self.assertEqual(question.owned_by_id, self.target.pk)
        self.assertTrue(User.objects.filter(pk=self.target.pk).exists())


class AndroidFilterPersistenceTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user('filter_reader', capabilities={
            'tests.start': True, 'tests.download_full_bank': True, 'admin.database': True})
        self.category = make_category('Selected category')
        other_category = make_category('Other category')
        self.tag = make_tag('Mood, anxiety')
        self.selected = make_question(owner=self.user, category=self.category,
            question='Exact comma tag question', source_document='Shared source')
        self.selected.tags.add(self.tag)
        split = make_question(owner=self.user, category=self.category,
            question='Separate comma components', source_document='Shared source')
        split.tags.add(make_tag('Mood'), make_tag('anxiety'))
        other = make_question(owner=self.user, category=other_category,
            question='Wrong category', source_document='Shared source')
        other.tags.add(self.tag)
        self.client = APIClient()
        self.client.force_login(self.user)

    def query(self):
        return {'category_ids': json.dumps([self.category.pk]),
                'tags_filter': json.dumps([self.tag.name]), 'source_document': 'Shared source'}

    def test_question_list_availability_and_offline_catalog_agree_on_exact_filter(self):
        listed = self.client.get('/api/v1/questions/', self.query())
        count = self.client.get('/api/v1/questions/available-count/', self.query())
        catalog = self.client.get('/api/v1/exam/offline/catalog/', self.query())
        for response in (listed, count, catalog):
            self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual([row['id'] for row in listed.json()['data']['items']], [self.selected.pk])
        self.assertEqual(count.json()['data']['count'], 1)
        self.assertEqual(catalog.json()['data']['question_ids'], [self.selected.pk])
        self.assertEqual(catalog.json()['data']['selection']['tags'], [self.tag.name])

    def test_study_start_body_retains_exact_tag_and_category_selection(self):
        response = self.client.post('/api/v1/study/start/study/', {
            'limit': 20, 'category_ids': [self.category.pk], 'tags_filter': [self.tag.name],
            'source_document': 'Shared source'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        session = ExamSession.objects.get(session_id=response.json()['data']['session_id'], user=self.user)
        self.assertEqual(session.question_ids, [self.selected.pk])

    def test_json_export_filters_rows_without_splitting_tag_name(self):
        response = self.client.post('/api/v1/database/export/json/', {'filters': {
            'category_ids': [self.category.pk], 'tags_filter': [self.tag.name]}}, format='json')
        self.assertEqual(response.status_code, 200)
        # Django's test-client iterator closes the response while suppressing
        # request_finished connection cleanup inside TestCase's outer atomic.
        # Closing it again would close PostgreSQL's active test transaction.
        exported = json.loads(b''.join(response.streaming_content))
        self.assertTrue(response.closed)
        self.assertEqual([item['uuid'] for item in exported], [str(self.selected.uuid)])
