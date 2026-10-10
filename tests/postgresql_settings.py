"""Run suites on an explicitly isolated PostgreSQL database with test cache/files."""

from copy import deepcopy
import os

from django.core.exceptions import ImproperlyConfigured

from tests.test_settings import *  # noqa: F401,F403
from config.settings import DATABASES as _application_databases

_test_name = os.environ.get('QUIZ_TEST_POSTGRES_DB', 'test_quiz_backend')
_database = deepcopy(_application_databases['default'])
if _database['ENGINE'] != 'django.db.backends.postgresql':
    raise ImproperlyConfigured('Select PostgreSQL in .env before using PostgreSQL test settings.')
if not _test_name.startswith('test_') or _test_name == _database['NAME']:
    raise ImproperlyConfigured('QUIZ_TEST_POSTGRES_DB must name a separate database beginning with test_.')
_database['NAME'] = _test_name
_database['TEST'] = {'NAME': _test_name}
DATABASES = {'default': _database}
