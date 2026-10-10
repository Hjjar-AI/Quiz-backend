# backend/apps/core/management/commands/seed_pro_users.py
"""
Seed normal member accounts for the credited team and named offline learners.

Usage: manage.py seed_pro_users [--reset-passwords] [--quiet]

Accounts match stable usernames. Every run restores member status and clears
staff/superuser flags; only the five OFFLINE_BANK_USERS receive an explicit
full-bank grant. Other per-user overrides and existing display names/passwords
are preserved. Missing accounts are created with a one-time password from
SEED_PRO_USER_PASSWORD (development fallback: 1234test), requiring a change
on first login. --reset-passwords explicitly replaces existing passwords.
"""

import os
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


User = get_user_model()


# Username → display names. No password column — the seeded password
# is a single value shared across every account and sourced from
# SEED_PRO_USER_PASSWORD at run time.
#
# Usernames are latinised first names. They satisfy the User model's
# USERNAME_REGEX (letters, digits, underscores, 3-50 chars).
#
# Includes the credited team plus the designated offline-bank learners.
PRO_USERS = [
    ('aya_kseibi',        'د. آية كسيبي',              'Dr. Aya Kseibi'),
    ('ayham_shaykha',     'د. أيهم شيخة',              'Dr. Ayham Shaykha'),
    ('ibrahim_tarsha',    'د. إبراهيم طرشه',           'Dr. Ibrahim Tarsha'),
    ('iman_alshayeb',     'د. إيمان الشايب',           'Dr. Iman Al-Shayeb'),
    ('haneen_alaji',      'د. حنين العجي',             'Dr. Haneen Al-Aji'),
    ('shvan_shamsi',      'د. شفان شمسي',              'Dr. Shvan Shamsi'),
    ('zilal_alwaw',       'د. ظلال الواو',             'Dr. Zilal Al-Waw'),
    ('nidal_abdulwahhab', 'د. محمد نضال عبد الوهاب',   'Dr. Muhammad Nidal Abdul-Wahhab'),
    ('nour_alsayed',      'د. محمد نور السيد',         'Dr. Muhammad Nour Al-Sayed'),
    ('nour_dahdouh',      'د. نور دحدوح',              'Dr. Nour Dahdouh'),
    ('hadiyatullah_malas','د. هدية الله ملص',          'Dr. Hadiyatullah Malas'),
]


OFFLINE_BANK_CAPABILITY = 'tests.download_full_bank'
OFFLINE_BANK_USERS = frozenset({
    'aya_kseibi', 'iman_alshayeb', 'nour_dahdouh', 'haneen_alaji', 'zilal_alwaw',
})


# Default one-time password when SEED_PRO_USER_PASSWORD is not set.
# Every account seeded with this value is required to change it on
# first login via `must_change_password=True` below.
_DEFAULT_SEED_PASSWORD = '1234test'


DEFAULTS = {
    'role': 'member',
    'is_active': True,
    'is_staff': False,
    'is_superuser': False,
    'is_stub': False,
    # One-time credential — the middleware gates the session until
    # the password is changed. See the module docstring for why this
    # is True.
    'must_change_password': True,
    'auto_renew_days': 0,
    'expires_at': None,
}


class Command(BaseCommand):
    help = (
        'Seed normal member accounts; grant full offline-bank downloads to '
        'the five designated learners. Idempotent by username.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help=(
                'Reset the password on existing accounts to the seeded '
                'value (from SEED_PRO_USER_PASSWORD, or the built-in '
                'default). Without this flag, an existing account '
                'keeps its password; member status and designated offline '
                'permissions are still enforced.'
            ),
        )
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress the summary line on success (for CI/cron).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset_passwords = options['reset_passwords']
        quiet = options['quiet']

        # Resolve the shared one-time password once. Prefer the .env
        # variable because a default literal in source is visible to
        # anyone with read access to this file.
        seed_password = (
            os.environ.get('SEED_PRO_USER_PASSWORD')
            or _DEFAULT_SEED_PASSWORD
        )

        created = 0
        updated = 0
        unchanged = 0
        credentials = []

        for username, full_name_ar, full_name_en in PRO_USERS:
            user, was_created = User.objects.select_for_update().get_or_create(
                username=username,
                defaults={
                    'full_name': full_name_ar,
                    **DEFAULTS,
                    'capabilities': ({OFFLINE_BANK_CAPABILITY: True}
                                     if username in OFFLINE_BANK_USERS else {}),
                },
            )

            if was_created:
                user.set_password(seed_password)
                # Belt-and-braces: DEFAULTS already sets this, but
                # set it again explicitly so a future change to
                # DEFAULTS cannot silently drop the flag on the
                # create path.
                user.must_change_password = True
                user.save(update_fields=['password', 'must_change_password'])
                created += 1
                credentials.append((username, full_name_en, seed_password))
                continue

            # Existing account: restore member status while retaining unrelated
            # overrides, chosen display names and passwords unless reset.
            dirty_fields = []
            if user.role != DEFAULTS['role']:
                user.role = DEFAULTS['role']
                dirty_fields.append('role')
            for field in ('is_staff', 'is_superuser'):
                if getattr(user, field):
                    setattr(user, field, False)
                    dirty_fields.append(field)
            if username in OFFLINE_BANK_USERS:
                overrides = dict(user.capabilities or {})
                if overrides.get(OFFLINE_BANK_CAPABILITY) is not True:
                    overrides[OFFLINE_BANK_CAPABILITY] = True
                    user.capabilities = overrides
                    dirty_fields.append('capabilities')
            if not user.is_active:
                user.is_active = True
                dirty_fields.append('is_active')
            # Fill the seeded Arabic full name if the current one is empty;
            # otherwise leave the admin's chosen display name alone.
            if not user.full_name:
                user.full_name = full_name_ar
                dirty_fields.append('full_name')

            if reset_passwords:
                user.set_password(seed_password)
                # A reset implies the new credential is also one-time.
                # Set the flag True regardless of its prior state.
                user.must_change_password = True
                dirty_fields.extend(['password', 'must_change_password'])
                credentials.append((username, full_name_en, seed_password))

            if dirty_fields:
                user.save(update_fields=dirty_fields)
                if hasattr(user, '_resolved_caps_cache'):
                    delattr(user, '_resolved_caps_cache')
                updated += 1
            else:
                unchanged += 1

        # The admin asked for hand-out credentials — print them on
        # stderr so they are not interleaved with the command's
        # stdout summary and can be piped separately if desired.
        for username, full_name, password in credentials:
            sys.stderr.write(f'{username:<22} {password:<22}  # {full_name}\n')

        if quiet:
            return

        self.stdout.write(self.style.SUCCESS(
            f'Pro users: {created} created, {updated} updated, '
            f'{unchanged} unchanged.'
        ))
        if credentials:
            self.stdout.write(
                f'Printed {len(credentials)} credential line(s) to stderr. '
                f'Created/reset accounts carry must_change_password=True and will '
                f'be required to change the password on first login.'
            )
        else:
            self.stdout.write(
                'No passwords printed. Pass --reset-passwords to reset '
                'existing accounts.'
            )
