# Mukhtabir Backend

Django REST backend for Mukhtabir. It owns authentication, permissions, the
question-bank domain, exam/study workflows, analytics, administration,
imports/exports, and production Vue SPA serving.

## Main capabilities

- Session users, account expiry/renewal, roles, and capability overrides.
- Questions, taxonomy, clinical cases, knowledge objects, translations, images,
  authorship/ownership, moderation, and reputation.
- Exam, study, recall, SRS, confidence, reflection, history, planner, streak, and
  knowledge-map services.
- Scheduled master exams with audiences, ordered composition, drafts, immutable
  attempt snapshots, makeup attempts, lifecycle controls, and result exports.
- Groups, leaderboards, bookmarks, ratings, flags, analytics, and activity reports.
- Excel, CSV, JSON, PDF, and portable state import/export.
- MariaDB production and isolated SQLite development configurations.
- Backups/restores, audit logs, throttling, cleanup, diagnostics, and SPA fallback.

## Technology

Django, Django REST Framework, MariaDB/MySQL, SQLite, Memcached or Redis,
pandas/openpyxl/xlrd, WeasyPrint, Pillow, libmagic, and Gunicorn. Versions are
pinned in `requirements.txt`.

## Prerequisites

- A Python version supported by the pinned Django release
- `venv` and `pip`
- System packages required by the chosen database and export features
- The sibling frontend when Django will serve the compiled SPA

See `DEPLOYMENT.md` for production OS packages and service configuration.

## Quick start: SQLite

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python start_sqlite.py
```

The default address is `localhost:5004`. The launcher isolates its database,
media, uploads, exports, backups, cache, and cookies under the SQLite setup and
performs initial setup for an empty local instance.

Useful forms:

```bash
python start_sqlite.py 5005
python start_sqlite.py 0.0.0.0:8000
python start_sqlite.py --seed-pro-users
python start_sqlite.py --no-setup
```

Read `start_sqlite.py` before enabling threading or binding to an untrusted network.

## MariaDB configuration

Normal `manage.py` uses `config.settings`, which expects MariaDB and shared cache.
A minimal production-shaped `.env` includes:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
ALLOWED_HOSTS=quiz.example.com
CORS_ORIGINS=https://quiz.example.com
USE_HTTPS=True
DB_NAME=quiz
DB_USER=quiz
DB_PASSWORD=replace-me
DB_HOST=127.0.0.1
DB_PORT=3306
CACHE_TYPE=MemcachedCache
MEMCACHED_LOCATION=127.0.0.1:11211
```

Use `python manage.py bootstrap` for the guided bootstrap flow. Read its `--help`
and `DEPLOYMENT.md` before supplying administrative database credentials.

## Configuration

`.env.example` documents the principal settings:

- Core/security: `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `USE_HTTPS`
- Browser origin: `CORS_ORIGINS`
- Database: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- Cache: `CACHE_TYPE`, `MEMCACHED_LOCATION`, `REDIS_URL`
- Upload/state limits: `MAX_UPLOAD_SIZE`, `MAX_STATE_TRANSFER_SIZE`,
  `MAX_STATE_IMPORT_QUESTIONS`
- PDF limits: `PDF_EXPORT_MAX_QUESTIONS`, `PDF_EXPORT_MAX_TOTAL_IMAGE_BYTES`
- Audit retention: `PRIVILEGED_ACTION_RETENTION_DAYS`
- Seed accounts: `SEED_PRO_USER_PASSWORD`

SQLite overrides include `SQLITE_ROOT`, `SQLITE_DB_PATH`,
`SQLITE_SERVER_ADDRESS`, `SQLITE_ALLOWED_HOSTS`, `SQLITE_CORS_ORIGINS`, and
`SQLITE_CSRF_TRUSTED_ORIGINS`.

## API layout

```text
/api/v1/auth/          Authentication, users, roles, and permissions
/api/v1/questions/     Questions, taxonomy, cases, learning, and feedback
/api/v1/exam/          Regular exams and blueprints
/api/v1/study/         Study sessions, groups, streaks, and activity
/api/v1/recall/        Recall sessions
/api/v1/exam/master/   Master exams, attempts, lifecycle, and reports
/api/v1/analytics/     Member and administrative analytics
/api/v1/database/      Import, export, backup, restore, and database operations
/api/v1/history/       Personal history
/api/v1/admin/history/ Administrative history
```

Unknown API paths return an API-shaped 404. Unknown non-API paths fall back to
the compiled SPA when `frontend/dist/` exists. Vue and Android depend on the
standard response envelope, session cookies, and Django CSRF behavior.

## Structure

```text
apps/
├── analytics/       Reporting
├── core/            Utilities, audit, throttles, settings models, commands
├── database/        Backup, restore, database info, imports and exports
├── exams/           Regular sessions and blueprints
├── feedback/        Bookmarks, flags, and ratings
├── groups/          Groups and leaderboards
├── learning/        Attempts, SRS, mastery, and knowledge map
├── master_exams/    Scheduled exams, composition, attempts, and results
├── planning/        Planner and daily progress
├── questions/       Question-bank models, services, serializers, and views
└── users/           Authentication, accounts, capabilities, and sessions
config/              Django settings, routing, WSGI, and ASGI
```

Cross-model or transactional logic belongs in services. Important invariants are
also represented by model constraints.

## Imports, exports, and PDFs

Flat exports are intended for editing/review. Portable state packages preserve
related taxonomy, cases, knowledge objects, identities, and optional images and
are the lossless transfer format.

PDF rendering embeds Noto Sans Arabic and requires WeasyPrint plus the native
Pango/HarfBuzz/Cairo stack. It is synchronous and bounded by question count and
total embedded image bytes; filter large banks into smaller documents.

## Operational commands

Use `python manage.py COMMAND --help` for complete options.

```bash
python manage.py doctor
python manage.py seed
python manage.py seed_capabilities
python manage.py reset_admin_password
python manage.py refresh_author_ranks
python manage.py renew_expired_users
python manage.py sweep_master_exams
python manage.py cleanup_database
python manage.py cleanup_temp_files
python manage.py cleanup_privileged_actions
```

`doctor` checks configuration, database/schema access, cache, PDF dependencies,
font reachability, writable directories, the frontend build, and administrators.

## Production

Build the frontend first if Django will serve it:

```bash
cd ../frontend
pnpm install
pnpm build
cd ../backend
```

Use Gunicorn behind an HTTPS reverse proxy. Configure secure cookies, explicit
hosts/origins, trusted proxy handling, a shared cache, persistent media, backups,
and scheduled cleanup/sweeper commands. Do not use `runserver` or SQLite in
production. See `DEPLOYMENT.md` for the complete guide.

## Troubleshooting

- **Configuration failure:** compare `.env` with `.env.example`.
- **Database failure:** verify MariaDB, credentials, host, and port.
- **Clients share one IP:** configure trusted reverse-proxy handling exactly as documented.
- **PDF 500:** run `python manage.py doctor` and install native PDF libraries.
- **PDF 413:** filter the export or deliberately adjust its safety limits.
- **CSRF/CORS:** align origin, trusted origins, HTTPS, and cookie settings.
- **SQLite/MariaDB cookie conflict:** use `start_sqlite.py` and its isolated overlay.

## Working documents

- `Agents.md` — local contributor constraints
- `workPlan.md` — current planned work
- `workDone.md` — completed work log
- `DEPLOYMENT.md` — detailed deployment guide

