"""Local SQLite settings used by :mod:`start_sqlite`.

The regular settings module remains the MariaDB / Memcached (or Redis)
configuration used by the normal launcher. This overlay is
intentionally single-process: SQLite and LocMemCache are convenient
for a self-contained local instance, but neither is intended for a
multi-worker deployment.

RUNNING ALONGSIDE A MARIADB INSTANCE
------------------------------------
Both this configuration and the regular one can run at the same
time, in two terminals, from the same ``backend/`` checkout. The
parts that differ are isolated by this file:

  • The database — SQLite file vs. MariaDB server.

  • The cache — in-process LocMemCache vs. a shared Memcached/Redis.

  • The session and CSRF cookie names. Browsers scope cookies by
    host, NOT by port, so two servers on ``localhost:5004`` and
    ``localhost:5005`` would otherwise overwrite each other's
    ``sessionid`` and log the user out on every tab switch. The
    rename below gives the SQLite instance its own cookies.

  • The four on-disk data folders — media, uploads, exports, and
    backups — AND the SQLite database file itself. Every one of
    them is redirected into ``BASE_DIR/SQLite/`` so nothing the
    SQLite instance writes ever appears in, or overwrites a file
    from, the MariaDB instance running from the same tree. Set
    ``SQLITE_ROOT`` to place that tree somewhere else.

The parts that are NOT isolated and are shared by design:

  • Migration files under ``apps/*/migrations/``. Both instances
    read the same migrations, because both instances run the same
    models. Migrations are source code, not per-database state —
    they describe the schema that the model classes imply, and the
    model classes are identical for both instances.

  • ``.env`` — ``DJANGO_SECRET_KEY``, ``DEBUG``, ``ALLOWED_HOSTS``,
    and the other environment-driven settings.

  • ``frontend/dist/`` — the built SPA.

FOLDER LAYOUT
-------------
::

    backend/
    ├── SQLite/
    │   ├── db.sqlite3    ← the SQLite database itself
    │   ├── media/        ← SQLite instance question images
    │   ├── uploads/      ← SQLite instance import staging
    │   ├── exports/      ← SQLite instance generated exports
    │   └── backups/      ← SQLite instance database backups
    ├── media/            ← MariaDB instance question images
    ├── uploads/
    ├── exports/
    └── backups/

The whole ``backend/SQLite/`` subtree is disposable for the four
folder overrides — delete the folders at any time and they are
recreated on the next launch. The database file is NOT disposable in
that sense: deleting ``SQLite/db.sqlite3`` wipes the SQLite
instance's data, exactly as deleting any database file would. The
launcher recreates it with a fresh schema on the next start, but the
rows are gone.

``SQLITE_DB_PATH`` overrides the default database location. An
absolute path is used as-is; a relative path is resolved against
``BASE_DIR``, not against the current working directory, so the
launcher behaves the same no matter where it is invoked from.

``SQLITE_ROOT`` moves the complete local instance (default database,
media, uploads, exports, and backups). This is useful on Termux, where
the instance should live in Termux-private storage rather than Android
shared storage.
"""

import os
from pathlib import Path


# Local launches must be able to use Django's development server even
# when backend/.env contains production values. Set this before
# importing the base settings because that module validates
# SECRET_KEY and ALLOWED_HOSTS while it is imported.
os.environ['DEBUG'] = 'True'

from .settings import *  # noqa: E402,F401,F403


DEBUG = True

# ``sslserver`` is a MariaDB/deployment convenience and is not used by
# start_sqlite.py (which invokes Django's ordinary runserver). Keeping it
# out of this overlay lets the portable SQLite dependency set remain free
# of an otherwise unused package. The base settings list is copied, so the
# normal manage.py configuration is unchanged.
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'sslserver']


# Add the concrete address selected by start_sqlite.py. A wildcard bind has
# no single request host, so allow any Host header only for this DEBUG-only
# overlay; the launcher prints a warning when it is selected. An explicit
# SQLITE_ALLOWED_HOSTS value takes precedence.
_sqlite_allowed_hosts = os.environ.get('SQLITE_ALLOWED_HOSTS')
if _sqlite_allowed_hosts is not None:
    ALLOWED_HOSTS = [
        host.strip() for host in _sqlite_allowed_hosts.split(',') if host.strip()
    ]
else:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS)
    _bind_host = os.environ.get('SQLITE_BIND_HOST', '').strip().strip('[]')
    if _bind_host in {'0.0.0.0', '::'}:
        if '*' not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append('*')
    elif _bind_host and _bind_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_bind_host)


# django-cors-headers does not accept ``*`` in CORS_ALLOWED_ORIGINS;
# wildcard access is represented by CORS_ALLOW_ALL_ORIGINS instead. The base
# .env used by some local installations predates that distinction and sets
# CORS_ORIGINS=*. Normalise it only in this SQLite overlay. CSRF trusted
# origins are separate and must always include an explicit scheme.
_sqlite_cors_raw = os.environ.get('SQLITE_CORS_ORIGINS')
if _sqlite_cors_raw is None:
    _sqlite_cors_origins = list(CORS_ALLOWED_ORIGINS)
else:
    _sqlite_cors_origins = [
        origin.strip()
        for origin in _sqlite_cors_raw.split(',')
        if origin.strip()
    ]

if '*' in _sqlite_cors_origins:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = [
        origin for origin in _sqlite_cors_origins if origin != '*'
    ]
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = _sqlite_cors_origins

_sqlite_csrf_raw = os.environ.get('SQLITE_CSRF_TRUSTED_ORIGINS')
if _sqlite_csrf_raw is not None:
    CSRF_TRUSTED_ORIGINS = [
        origin.strip()
        for origin in _sqlite_csrf_raw.split(',')
        if origin.strip()
    ]
else:
    # Same-origin requests need no trusted-origin entry. Preserve only
    # valid cross-origin URLs from the CORS configuration.
    CSRF_TRUSTED_ORIGINS = [
        origin
        for origin in CORS_ALLOWED_ORIGINS
        if origin.startswith(('http://', 'https://'))
    ]


# ── Filesystem isolation root ───────────────────────────────────────
#
# Every SQLite-instance path is derived from this one root. This is an
# environment option so Termux can keep state under its private home
# rather than Android shared storage.
_sqlite_root = Path(
    os.environ.get('SQLITE_ROOT', str(BASE_DIR / 'SQLite'))
).expanduser()
if not _sqlite_root.is_absolute():
    _sqlite_root = BASE_DIR / _sqlite_root


# ── Database ────────────────────────────────────────────────────────
#
# The default lives inside ``SQLite/`` rather than at ``BASE_DIR``
# directly, so everything the SQLite instance owns is under one
# directory. ``SQLITE_DB_PATH`` still overrides; a relative value is
# resolved against ``BASE_DIR`` so the launcher's behaviour does not
# depend on the process's current working directory.
_database_path = Path(
    os.environ.get('SQLITE_DB_PATH', str(_sqlite_root / 'db.sqlite3'))
).expanduser()
if not _database_path.is_absolute():
    _database_path = BASE_DIR / _database_path

# The folder is created here rather than in ``start_sqlite.py``
# because ``DATABASES['default']['NAME']`` is read by ``django.setup``
# and by every management command. If the parent folder does not
# exist, SQLite refuses to open the file with "unable to open database
# file". Creating it at settings-import time means ``manage.py``
# invocations — migrate, showmigrations, seed_pro_users — all work
# without going through the launcher first.
_database_path.parent.mkdir(parents=True, exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _database_path,
        'OPTIONS': {
            # Give concurrent requests a short opportunity to finish
            # rather than immediately returning "database is locked".
            'timeout': 20,
            # SQLite ignores SELECT ... FOR UPDATE. BEGIN IMMEDIATE
            # acquires the write reservation at the start of each atomic
            # block, serialising the app's read-modify-write workflows
            # before they read stale state.
            'transaction_mode': 'IMMEDIATE',
        },
    },
}


# ── Cache ───────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'quiz-sqlite-local',
    },
}


# ── Cookie isolation ────────────────────────────────────────────────
#
# Distinct names so the SQLite instance never collides with a MariaDB
# instance running on another port of the same host. Cookie scope is
# host + path only; the port is not part of the scope. Two servers
# on ``localhost`` would otherwise share ``sessionid`` and
# ``csrftoken``, and switching tabs would log the user out of one of
# them on every navigation.
#
# The names differ ONLY on the SQLite side. The MariaDB instance
# keeps Django's defaults (``sessionid`` / ``csrftoken``), so
# existing sessions in a browser continue to work against the
# MariaDB server unchanged.
SESSION_COOKIE_NAME = 'sqlite_sessionid'
CSRF_COOKIE_NAME = 'sqlite_csrftoken'


# ── Filesystem isolation ────────────────────────────────────────────
#
# The base settings module points MEDIA_ROOT, UPLOAD_FOLDER,
# EXPORT_FOLDER, and BACKUP_FOLDER at ``BASE_DIR/...``. Redirecting
# them here means a file written by the SQLite instance never lands
# in the MariaDB instance's tree — question images, import staging
# files, generated Excel/CSV/JSON/PDF exports, and database backups
# all go into ``backend/SQLite/`` instead.
#
# The four variables below are read by:
#
#   • ``apps/core/tasks.py::cleanup_temp_files`` — sweeps UPLOAD,
#     EXPORT, and BACKUP on a schedule.
#   • ``apps/core/management/commands/doctor.py`` — checks that all
#     four are writable and reports failures at startup.
#   • ``apps/database/services/backup_service.py`` — writes and
#     lists backup files.
#   • ``apps/questions/services/exporting/*`` — writes export files.
#   • ``config/settings.py``'s ``MEDIA_URL`` / ``MEDIA_ROOT`` pair —
#     question images are served from MEDIA_ROOT in DEBUG mode.
#
# Nothing reads these paths by a hard-coded literal, so the override
# is complete.
MEDIA_ROOT    = _sqlite_root / 'media'
UPLOAD_FOLDER = _sqlite_root / 'uploads'
EXPORT_FOLDER = _sqlite_root / 'exports'
BACKUP_FOLDER = _sqlite_root / 'backups'

for _folder in (MEDIA_ROOT, UPLOAD_FOLDER, EXPORT_FOLDER, BACKUP_FOLDER):
    _folder.mkdir(parents=True, exist_ok=True)
