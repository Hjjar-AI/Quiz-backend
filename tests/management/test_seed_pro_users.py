from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.core.management.commands.seed_pro_users import PRO_USERS, OFFLINE_BANK_USERS, OFFLINE_BANK_CAPABILITY
from tests.base import CacheClearingTestCase


class SeedProUsersTests(CacheClearingTestCase):
    def seed(self, *args, password='temporary-pro-credential'):
        out, err = StringIO(), StringIO()
        with patch.dict('os.environ', {'SEED_PRO_USER_PASSWORD': password}), patch('sys.stderr', err):
            call_command('seed_pro_users', *args, stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    def test_creates_all_members_with_one_time_password(self):
        self.seed()
        users = get_user_model().objects.filter(username__in=[row[0] for row in PRO_USERS])
        self.assertEqual(users.count(), len(PRO_USERS))
        for user in users:
            self.assertEqual(user.role, 'member')
            self.assertTrue(user.is_active)
            self.assertTrue(user.must_change_password)
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)
            self.assertTrue(user.check_password('temporary-pro-credential'))

    def test_repeat_preserves_changed_password_and_display_name(self):
        self.seed()
        user = get_user_model().objects.get(username=PRO_USERS[0][0])
        user.set_password('chosen-by-account-holder')
        user.must_change_password = False
        user.full_name = 'Custom display name'
        user.save()
        self.seed(password='different-seed-credential')
        user.refresh_from_db()
        self.assertTrue(user.check_password('chosen-by-account-holder'))
        self.assertFalse(user.must_change_password)
        self.assertEqual(user.full_name, 'Custom display name')
        self.assertEqual(get_user_model().objects.count(), len(PRO_USERS))

    def test_repeat_repairs_role_and_reactivates_account(self):
        self.seed()
        user = get_user_model().objects.get(username=PRO_USERS[0][0])
        user.role = 'moderator'
        user.is_staff = True
        user.is_superuser = True
        user.is_active = False
        user.full_name = ''
        user.save()
        self.seed()
        user.refresh_from_db()
        self.assertEqual(user.role, 'member')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.full_name, PRO_USERS[0][1])

    def test_explicit_reset_requires_first_login_password_change(self):
        self.seed()
        self.seed('--reset-passwords', password='new-one-time-credential')
        for user in get_user_model().objects.all():
            self.assertTrue(user.check_password('new-one-time-credential'))
            self.assertTrue(user.must_change_password)

    def test_quiet_still_prints_new_handout_credentials_to_stderr(self):
        out, err = self.seed('--quiet')
        self.assertEqual(out, '')
        self.assertEqual(len(err.strip().splitlines()), len(PRO_USERS))
        self.assertIn(PRO_USERS[0][0], err)

    def test_repeat_without_reset_prints_no_credentials(self):
        self.seed()
        out, err = self.seed()
        self.assertEqual(err, '')
        self.assertIn('No passwords printed', out)

    def test_only_designated_members_receive_full_bank_download_permission(self):
        self.seed()
        self.assertEqual(len(OFFLINE_BANK_USERS), 5)
        for username, _, _ in PRO_USERS:
            user = get_user_model().objects.get(username=username)
            self.assertEqual(
                user.has_capability(OFFLINE_BANK_CAPABILITY),
                username in OFFLINE_BANK_USERS,
            )
            self.assertTrue(user.has_capability('tests.start'))
            self.assertFalse(user.has_capability('questions.edit_any'))
            self.assertFalse(user.has_capability('questions.verify'))

    def test_repeat_grants_designated_download_and_preserves_other_overrides(self):
        self.seed()
        user = get_user_model().objects.get(username='aya_kseibi')
        user.capabilities = {
            OFFLINE_BANK_CAPABILITY: False,
            'questions.create': False,
            'tests.use_blueprint': True,
        }
        user.save(update_fields=['capabilities'])
        self.seed()
        user.refresh_from_db()
        self.assertEqual(user.capabilities, {
            OFFLINE_BANK_CAPABILITY: True,
            'questions.create': False,
            'tests.use_blueprint': True,
        })

    def test_creates_missing_designated_learners_on_repeat(self):
        self.seed()
        get_user_model().objects.filter(username__in=[
            'iman_alshayeb', 'nour_dahdouh', 'haneen_alaji',
        ]).delete()
        self.seed()
        self.assertEqual(get_user_model().objects.count(), len(PRO_USERS))
        for username in OFFLINE_BANK_USERS:
            user = get_user_model().objects.get(username=username)
            self.assertEqual(user.role, 'member')
            self.assertTrue(user.has_capability(OFFLINE_BANK_CAPABILITY))
