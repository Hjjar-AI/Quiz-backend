from unittest.mock import patch

from rest_framework.test import APIClient
from tests.base import CacheClearingTestCase
from tests.factories import make_admin, make_user


class ImportUnlockTests(CacheClearingTestCase):
    path = '/api/v1/database/import/unlock/'

    def setUp(self):
        super().setUp()
        self.admin = make_admin('import_admin', 'admin-pw-1234')
        self.client = APIClient()
        self.client.force_login(self.admin)

    def unlock(self, password='admin-pw-1234'):
        return self.client.post(self.path, {'admin_password': password}, format='json')

    def exhaust(self):
        for _ in range(10):
            self.assertEqual(self.client.post('/api/v1/database/import/').status_code, 400)
        self.assertEqual(self.client.post('/api/v1/database/import/').status_code, 429)

    def test_password_unlocks_all_import_kinds_after_limit_and_expires_at_ten_minutes(self):
        self.exhaust()
        with patch('apps.core.import_limits.time', return_value=1000):
            response = self.unlock()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['data'], {'active': True, 'expires_at': 1600, 'expires_in': 600})
            for path in ['/api/v1/database/import/', '/api/v1/database/import/telegram/', '/api/v1/database/import/state/']:
                for _ in range(12):
                    self.assertEqual(self.client.post(path).status_code, 400)
        with patch('apps.core.import_limits.time', return_value=1599):
            self.assertEqual(self.client.post('/api/v1/database/import/').status_code, 400)
        with patch('apps.core.import_limits.time', return_value=1600):
            self.assertEqual(self.client.get(self.path).data['data']['active'], False)
            self.assertEqual(self.client.post('/api/v1/database/import/').status_code, 429)

    def test_wrong_or_missing_password_does_not_unlock(self):
        self.exhaust()
        self.assertEqual(self.unlock('incorrect').status_code, 403)
        self.assertEqual(self.client.post(self.path, {}, format='json').status_code, 400)
        self.assertFalse(self.client.get(self.path).data['data']['active'])
        self.assertEqual(self.client.post('/api/v1/database/import/').status_code, 429)

    def test_other_session_and_other_account_at_same_ip_remain_limited(self):
        self.exhaust()
        self.assertEqual(self.unlock().status_code, 200)
        for user in [self.admin, make_admin('other_import_admin', 'another-pw')]:
            client = APIClient()
            client.force_login(user)
            self.assertFalse(client.get(self.path).data['data']['active'])
            self.assertEqual(client.post('/api/v1/database/import/').status_code, 429)

    def test_logout_and_new_login_revoke_unlock(self):
        self.assertEqual(self.unlock().status_code, 200)
        self.client.logout()
        self.client.force_login(self.admin)
        self.assertFalse(self.client.get(self.path).data['data']['active'])

    def test_non_admin_and_anonymous_cannot_unlock_or_read_status(self):
        self.client.force_login(make_user('ordinary_import_user'))
        self.assertEqual(self.unlock().status_code, 403)
        self.assertEqual(self.client.get(self.path).status_code, 403)
        self.client.logout()
        self.assertIn(self.unlock().status_code, (401, 403))

    def test_password_attempts_stay_throttled(self):
        for _ in range(50):
            self.assertEqual(self.unlock('wrong').status_code, 403)
        self.assertEqual(self.unlock().status_code, 429)
        self.assertFalse(self.client.get(self.path).data['data']['active'])

    def test_unlock_requests_refresh_window_only_after_correct_password(self):
        with patch('apps.core.import_limits.time', return_value=1000):
            self.assertEqual(self.unlock().data['data']['expires_at'], 1600)
        with patch('apps.core.import_limits.time', return_value=1300):
            self.assertEqual(self.unlock('wrong').status_code, 403)
            self.assertEqual(self.client.get(self.path).data['data']['expires_at'], 1600)
            self.assertEqual(self.unlock().data['data']['expires_at'], 1900)

    def test_bypassed_requests_do_not_consume_normal_quota(self):
        with patch('apps.core.import_limits.time', return_value=1000):
            self.assertEqual(self.unlock().status_code, 200)
            for _ in range(12):
                self.assertEqual(self.client.post('/api/v1/database/import/').status_code, 400)
        with patch('apps.core.import_limits.time', return_value=1600):
            self.exhaust()
