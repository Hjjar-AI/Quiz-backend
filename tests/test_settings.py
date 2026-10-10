# tests/test_settings.py
"""
Test-only settings overlay.

Imported by tests/runtests.py when no --settings is given on the
command line. Everything inherits from config.settings; only the
database, cache, hashing and file storage differ.

WHY SQLITE FOR TESTS
--------------------
SQLite provides a self-contained baseline for services, serializers
and HTTP clients. It does not validate PostgreSQL/MariaDB row locking
or all SQL differences; use tests.postgresql_settings for a separate
PostgreSQL run. Relevant backend differences include:

  • QuestionFlag.unique_open_flag_per_user_question is a partial
    unique index. MariaDB silently drops it (SILENCED_SYSTEM_CHECKS
    includes 'models.W036' in config.settings.py); SQLite enforces
    it. The FeedbackService.flag_question pre-check runs on both
    backends, and the test that matters
    (test_second_open_flag_is_refused) exercises that pre-check,
    not the raw constraint.

  • CheckConstraints on Question, UserQuestionAttempt,
    BlueprintWeight, QuestionRating — all supported by modern
    SQLite (3.26+) and enforced identically.

Running against SQLite keeps the suite self-contained: a
contributor can clone the repo and run the tests without ever
touching MySQL.

USAGE
-----
    python tests/runtests.py                          # uses this file
    QUIZ_TEST_POSTGRES_DB=test_quiz_backend python manage.py test tests \
        --settings=tests.postgresql_settings --keepdb --noinput
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory


# Production settings validate these values while they are imported,
# before this test overlay can override Django settings directly.
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-settings-secret-key')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')

from config.settings import *  # noqa: F401,F403


# ── Database: in-memory SQLite ────────────────────────────────────────
#
# NAME=':memory:' creates a private RAM database per connection.
# Django's TestCase opens a single connection for the duration of
# each test class's setup/teardown cycle, so this behaves exactly
# like a fresh, empty database per test class.
#
# No TEST['NAME'] override is needed — the default test database
# name would be derived from NAME and would fail because ':memory:'
# has no filename. Django detects ':memory:' specially and skips
# the CREATE DATABASE step entirely.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


# ── Cache: pin locmem ─────────────────────────────────────────────────
#
# The production cache is selected at import time from CACHE_TYPE in
# the environment. Pinning locmem here means a developer who happens
# to have CACHE_TYPE=RedisCache exported in their shell cannot
# accidentally route a test's cache writes to a shared Redis. Tests
# also call cache.clear() in setUp/tearDown (see tests/base.py), and
# doing that against a shared Redis would wipe production keys.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


# ── Password hashers ──────────────────────────────────────────────────
#
# Django's default PBKDF2 hasher is deliberately slow — that is the
# point in production and the last thing you want across hundreds of
# create_user() calls in a test suite. MD5 is not used anywhere else
# and is selected ONLY for tests; no real credential is ever hashed
# with it.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]


# ── DEBUG ─────────────────────────────────────────────────────────────
#
# Set explicitly so the value does not depend on what happens to be
# in the environment. DEBUG=False here means:
#   • ALLOWED_HOSTS is not required to contain '*' (test client uses
#     'testserver', which Django allow-lists automatically).
#   • The test client surfaces exceptions instead of swallowing them
#     into 500 responses.
#   • The DJANGO_SECRET_KEY placeholder check in config.settings
#     still fires if the env carries an insecure key — which is the
#     correct behavior even under test.
DEBUG = False

# Test uploads/exports/cleanup must never use application-owned directories.
# Keep the owner alive for the process lifetime; TemporaryDirectory cleans up
# at interpreter shutdown, including when the suite reports failures.
_test_storage = TemporaryDirectory(prefix='quiz-python-tests-')
_test_root = Path(_test_storage.name)
MEDIA_ROOT = _test_root / 'media'
UPLOAD_FOLDER = _test_root / 'uploads'
EXPORT_FOLDER = _test_root / 'exports'
BACKUP_FOLDER = _test_root / 'backups'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
for _directory in (MEDIA_ROOT, UPLOAD_FOLDER, EXPORT_FOLDER, BACKUP_FOLDER):
    _directory.mkdir()
