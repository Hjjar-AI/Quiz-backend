"""Current Android/API regression contracts without application DB or schema setup.

Real DRF authentication/dispatch/serializers run here. Destructive services and ORM
boundaries are mocked; these checks do not establish database locking behavior.
"""
import json
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import ANY, Mock, patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from apps.core.api_errors import error_details
from apps.core.authentication import ApiSessionAuthentication
from apps.core.exceptions import RevisionConflict, custom_exception_handler
from apps.core.throttles import AdminPasswordRateThrottle
from apps.core.utils import api_error, api_success, parse_csv_param
from apps.database.serializers import QuestionExportRequestSerializer
from apps.exams.views.offline_views import OfflineCatalogQuery
from apps.exams.views.session_views import DiscardProgressView
from apps.master_exams.views.crud_views import MasterExamDetailView
from apps.users.views.admin_user_views import AdminUserDeleteView
from apps.users.views.auth_views import LoginView


def actor(identifier=1, permitted=True):
    return SimpleNamespace(id=identifier, pk=identifier, is_authenticated=True,
        is_active=True, has_capability=lambda capability: permitted)


class GuardedWrite(APIView):
    authentication_classes = [ApiSessionAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = []
    dispatched = Mock()

    def post(self, request):
        self.dispatched()
        return api_success(data={'saved': True})


@override_settings(ALLOWED_HOSTS=['testserver'], CSRF_TRUSTED_ORIGINS=[])
class TypedCsrfContractTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory(enforce_csrf_checks=True)
        GuardedWrite.dispatched.reset_mock()

    def request(self, *, authenticated=True, token=False, origin=None):
        request = self.factory.post('/api/v1/write/', {'value': 1}, format='json')
        request.user = actor() if authenticated else AnonymousUser()
        if token:
            request.META['HTTP_X_CSRFTOKEN'] = get_token(request)
            request.COOKIES[settings.CSRF_COOKIE_NAME] = request.META['CSRF_COOKIE']
        if origin:
            request.META['HTTP_ORIGIN'] = origin
        return request

    def test_missing_token_is_typed_and_never_dispatches(self):
        response = GuardedWrite.as_view()(self.request())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['details']['reason'], 'CSRF_FAILED')
        GuardedWrite.dispatched.assert_not_called()

    def test_valid_token_dispatches_once(self):
        response = GuardedWrite.as_view()(self.request(token=True))
        self.assertEqual(response.status_code, 200)
        GuardedWrite.dispatched.assert_called_once_with()

    def test_origin_rejection_remains_typed_even_with_valid_token(self):
        response = GuardedWrite.as_view()(self.request(token=True, origin='https://untrusted.invalid'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['details']['reason'], 'CSRF_FAILED')
        GuardedWrite.dispatched.assert_not_called()

    def test_anonymous_login_enforces_csrf_before_checking_credentials(self):
        request = self.request(authenticated=False)
        with patch('apps.users.views.auth_views.AuthenticationService.login_user') as login:
            response = LoginView.as_view(throttle_classes=[])(request)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['details']['reason'], 'CSRF_FAILED')
        login.assert_not_called()

    def test_valid_anonymous_login_token_reaches_credential_check(self):
        request = self.factory.post('/api/v1/auth/login/',
            {'username': 'sample', 'password': 'wrong-password'}, format='json')
        request.user = AnonymousUser()
        request.META['HTTP_X_CSRFTOKEN'] = get_token(request)
        request.COOKIES[settings.CSRF_COOKIE_NAME] = request.META['CSRF_COOKIE']
        with patch('apps.users.views.auth_views.AuthenticationService.login_user', return_value=None) as login:
            response = LoginView.as_view(throttle_classes=[])(request)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['details']['reason'], 'INVALID_CREDENTIALS')
        login.assert_called_once_with('sample', 'wrong-password', ANY)

    def test_permission_message_mentioning_csrf_is_not_a_csrf_rejection(self):
        response = custom_exception_handler(PermissionDenied('CSRF administrator permission required'), {})
        self.assertEqual(response.data['details']['reason'], 'PERMISSION_DENIED')


class ErrorReasonContractTests(SimpleTestCase):
    def test_status_fallbacks_are_stable(self):
        for status, reason in [(400, 'VALIDATION_ERROR'), (401, 'AUTHENTICATION_REQUIRED'),
                (403, 'PERMISSION_DENIED'), (404, 'NOT_FOUND'), (409, 'REQUEST_CONFLICT'),
                (429, 'RATE_LIMITED'), (500, 'SERVER_ERROR')]:
            with self.subTest(status=status):
                self.assertEqual(api_error('message', status).data['details']['reason'], reason)

    def test_semantic_reason_and_fields_survive_without_mutating_input(self):
        original = {'reason': 'SESSION_PAUSED', 'answer': ['Keep this draft']}
        result = error_details(original, 409, reason='REQUEST_CONFLICT')
        self.assertEqual(result, original)
        self.assertIsNot(result, original)

    def test_reason_field_validation_is_retained_separately_from_machine_token(self):
        original = {'reason': ['Required'], 'non_field_errors': ['Check the form']}
        result = error_details(original, 400)
        self.assertEqual(result['reason'], 'VALIDATION_ERROR')
        self.assertEqual(result['non_field_errors'], [['Check the form'], ['Required']])
        self.assertEqual(original['reason'], ['Required'])

    def test_revision_conflict_keeps_distinct_reason_and_status(self):
        response = custom_exception_handler(RevisionConflict(), {})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['details']['reason'], 'REVISION_CONFLICT')


class FilterEncodingContractTests(SimpleTestCase):
    def test_json_array_preserves_comma_and_bracket_tag_names(self):
        tags = ['Mood, anxiety', '[Mood]', 'وسم، عربي']
        self.assertEqual(parse_csv_param(json.dumps(tags, ensure_ascii=False)), tags)

    def test_current_vue_comma_queries_remain_supported(self):
        self.assertEqual(parse_csv_param('1, 2,,3', coerce=int), [1, 2, 3])
        self.assertEqual(parse_csv_param('[Mood]'), ['[Mood]'])

    def test_structured_or_boolean_array_members_are_rejected(self):
        for value in ['[true]', '[null]', '[{}]', '[[]]']:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                parse_csv_param(value)

    def test_offline_catalog_decodes_json_categories_and_exact_tags(self):
        query = OfflineCatalogQuery(data={'category_ids': '[1,2]', 'tags_filter': '["Mood, anxiety"]'})
        self.assertTrue(query.is_valid(), query.errors)
        self.assertEqual(query.validated_data['category_ids'], [1, 2])
        self.assertEqual(query.validated_data['tags_filter'], ['Mood, anxiety'])

    def test_omitted_offline_filters_mean_no_selection(self):
        query = OfflineCatalogQuery(data={'after': '0'})
        self.assertTrue(query.is_valid(), query.errors)
        self.assertEqual(query.validated_data['category_ids'], [])
        self.assertEqual(query.validated_data['tags_filter'], [])

    def test_duplicate_or_out_of_range_offline_categories_are_rejected(self):
        for categories in ('[1,1]', '[0]', '[-1]', '[9223372036854775808]'):
            with self.subTest(categories=categories):
                query = OfflineCatalogQuery(data={'category_ids': categories, 'tags_filter': '[]'})
                self.assertFalse(query.is_valid())
                self.assertIn('category_ids', query.errors)

    def test_export_arrays_round_trip_exact_tag_identity(self):
        serializer = QuestionExportRequestSerializer(data={'filters': {
            'category_ids': [1, 2], 'tags_filter': ['Mood, anxiety', 'وسم']}})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        filters = serializer.validated_data['filters']
        self.assertEqual(parse_csv_param(filters['category_ids'], coerce=int), [1, 2])
        self.assertEqual(parse_csv_param(filters['tags_filter']), ['Mood, anxiety', 'وسم'])

    def test_empty_export_arrays_remain_empty(self):
        serializer = QuestionExportRequestSerializer(data={'filters': {'tags_filter': [], 'category_ids': []}})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        for value in serializer.validated_data['filters'].values():
            self.assertEqual(parse_csv_param(value), [])

    def test_export_rejects_overlong_arrays_instead_of_truncating_selection(self):
        serializer = QuestionExportRequestSerializer(data={'filters': {'tags_filter': ['x' * 501]}})
        self.assertFalse(serializer.is_valid())
        self.assertIn('filters', serializer.errors)


class DeleteTransportContractTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = actor()

    def authenticated(self, request, user=None):
        force_authenticate(request, user=user or self.user)
        return request

    def test_bodyless_discard_filters_by_caller_and_session(self):
        request = self.authenticated(self.factory.delete('/api/v1/study/discard/?session_id=owned-session'))
        with patch('apps.exams.views.session_views.ExamSession.objects.filter') as select, \
                patch('apps.exams.views.session_views.ExamService.discard_sessions', return_value=1) as discard:
            response = DiscardProgressView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        select.assert_called_once_with(session_id='owned-session', user=self.user)
        discard.assert_called_once_with(select.return_value)

    def test_current_vue_discard_body_still_scopes_owner(self):
        request = self.authenticated(self.factory.delete('/api/v1/study/discard/',
            {'session_id': 'owned-session'}, format='json'))
        with patch('apps.exams.views.session_views.ExamSession.objects.filter') as select, \
                patch('apps.exams.views.session_views.ExamService.discard_sessions', return_value=0):
            response = DiscardProgressView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        select.assert_called_once_with(session_id='owned-session', user=self.user)

    def test_missing_discard_identity_never_calls_service(self):
        request = self.authenticated(self.factory.delete('/api/v1/study/discard/'))
        with patch('apps.exams.views.session_views.ExamService.discard_sessions') as discard:
            response = DiscardProgressView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        discard.assert_not_called()

    def test_master_delete_reads_query_mode_and_checks_management(self):
        request = self.authenticated(self.factory.delete('/api/v1/exam/master/2/?delete_mode=keep_drafts'))
        exam = Mock()
        with patch('apps.master_exams.views.crud_views.get_object_or_404', return_value=exam), \
                patch('apps.master_exams.views.crud_views._can_manage_exam', return_value=True), \
                patch('apps.master_exams.views.crud_views.MasterExamService.delete') as delete:
            response = MasterExamDetailView.as_view()(request, pk=2)
        self.assertEqual(response.status_code, 200)
        delete.assert_called_once_with(exam, 'keep_drafts', request=ANY)

    def test_master_delete_permission_failure_never_calls_service(self):
        request = self.authenticated(self.factory.delete('/api/v1/exam/master/2/?delete_mode=keep_drafts'))
        with patch('apps.master_exams.views.crud_views.get_object_or_404'), \
                patch('apps.master_exams.views.crud_views._can_manage_exam', return_value=False), \
                patch('apps.master_exams.views.crud_views.MasterExamService.delete') as delete:
            response = MasterExamDetailView.as_view()(request, pk=2)
        self.assertEqual(response.status_code, 403)
        delete.assert_not_called()

    def test_admin_post_delete_retains_password_attempt_throttle(self):
        view = AdminUserDeleteView()
        view.request = SimpleNamespace(method='POST')
        self.assertTrue(any(isinstance(throttle, AdminPasswordRateThrottle) for throttle in view.get_throttles()))

    def test_admin_post_delete_requires_capability(self):
        request = self.authenticated(self.factory.post('/api/v1/auth/admin/users/2/delete/',
            {'admin_password': 'secret'}, format='json'), user=actor(permitted=False))
        with patch('apps.users.views.admin_user_views._acquire_admin_lock_set') as lock:
            response = AdminUserDeleteView.as_view()(request, user_id=2)
        self.assertEqual(response.status_code, 403)
        lock.assert_not_called()

    def test_admin_post_delete_rejects_bad_password_before_locks(self):
        request = self.authenticated(self.factory.post('/api/v1/auth/admin/users/2/delete/',
            {'admin_password': 'wrong'}, format='json'))
        with patch('apps.users.views.admin_user_views.admin_password_matches', return_value=False) as verify, \
                patch('apps.users.views.admin_user_views._acquire_admin_lock_set') as lock:
            response = AdminUserDeleteView.as_view()(request, user_id=2)
        self.assertEqual(response.status_code, 403)
        verify.assert_called_once_with(self.user, 'wrong')
        lock.assert_not_called()

    def test_admin_post_delete_rejects_self_before_password_or_locks(self):
        request = self.authenticated(self.factory.post('/api/v1/auth/admin/users/1/delete/', {}, format='json'))
        with patch('apps.users.views.admin_user_views.admin_password_matches') as verify:
            response = AdminUserDeleteView.as_view()(request, user_id=1)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['details']['reason'], 'SELF_DELETE_FORBIDDEN')
        verify.assert_not_called()

    def test_admin_post_delete_protects_last_admin_under_lock(self):
        request = self.authenticated(self.factory.post('/api/v1/auth/admin/users/2/delete/',
            {'admin_password': 'correct'}, format='json'))
        target = SimpleNamespace(is_admin=True, is_active=True, delete=Mock())
        with patch('apps.users.views.admin_user_views.admin_password_matches', return_value=True), \
                patch('apps.users.views.admin_user_views.transaction.atomic', return_value=nullcontext()), \
                patch('apps.users.views.admin_user_views._acquire_admin_lock_set', return_value=(target, [])):
            response = AdminUserDeleteView.as_view()(request, user_id=2)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['details']['reason'], 'LAST_ADMIN_DELETE_FORBIDDEN')
        target.delete.assert_not_called()
