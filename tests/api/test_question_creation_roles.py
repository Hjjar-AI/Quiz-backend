from rest_framework.test import APIRequestFactory, force_authenticate

from apps.questions.views.question_views import QuestionListView, QuestionDuplicateView
from apps.users.serializers import UserSerializer
from tests.base import CacheClearingTestCase
from tests.factories import make_user


class QuestionCreationRoleTests(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.member = make_user()
        self.factory = APIRequestFactory()

    def test_member_create_is_forbidden_before_validation(self):
        request = self.factory.post('/', {}, format='json')
        force_authenticate(request, user=self.member)
        self.assertEqual(QuestionListView.as_view()(request).status_code, 403)

    def test_member_duplicate_is_forbidden_before_lookup(self):
        request = self.factory.post('/', {}, format='json')
        force_authenticate(request, user=self.member)
        response = QuestionDuplicateView.as_view()(request, question_id=999999)
        self.assertEqual(response.status_code, 403)

    def test_profile_hides_creation_permissions_from_both_clients(self):
        caps = UserSerializer(self.member).data['capabilities']
        self.assertNotIn('questions.create', caps)
        self.assertNotIn('questions.duplicate', caps)

    def test_moderator_reaches_create_validation(self):
        request = self.factory.post('/', {}, format='json')
        force_authenticate(request, user=make_user(role='moderator'))
        self.assertEqual(QuestionListView.as_view()(request).status_code, 400)

    def test_member_with_creation_grant_reaches_validation(self):
        user = make_user(capabilities={'questions.create': True})
        request = self.factory.post('/', {}, format='json')
        force_authenticate(request, user=user)
        self.assertEqual(QuestionListView.as_view()(request).status_code, 400)
        self.assertIn('questions.create', UserSerializer(user).data['capabilities'])

    def test_member_with_duplication_grant_reaches_lookup(self):
        user = make_user(capabilities={'questions.duplicate': True})
        request = self.factory.post('/', {}, format='json')
        force_authenticate(request, user=user)
        response = QuestionDuplicateView.as_view()(request, question_id=999999)
        self.assertEqual(response.status_code, 404)
