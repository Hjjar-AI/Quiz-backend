# Mukhtabir Backend

Django REST backend: authentication/permissions, question bank, exams/study, analytics/admin, import/export and production Vue SPA serving.

## Main capabilities

- Session users, account expiry/renewal, roles, and capability overrides.
- Questions, taxonomy, clinical cases, knowledge objects, translations, images, authorship/ownership, moderation, and reputation.
- Exam, study, recall, SRS, confidence, reflection, history, planner, streak, and knowledge-map services.
- Scheduled master exams with audiences, ordered composition, drafts, immutable attempt snapshots, makeup attempts, lifecycle controls, and result exports.
- Groups, leaderboards, bookmarks, ratings, flags, analytics, and activity reports.
- Excel, CSV, JSON, PDF, and portable state import/export.
- Database selection from .env (MariaDB/MySQL, PostgreSQL or SQLite).
- Backups/restores, audit logs, throttling, cleanup, diagnostics, and SPA fallback.

## Technology

Stack: Django/DRF, MariaDB/MySQL/SQLite, Memcached/Redis, pandas/openpyxl/xlrd, WeasyPrint/Pillow/libmagic/Gunicorn. Pins: `requirements.txt`.

## Prerequisites

- A Python version supported by the pinned Django release
- `venv` and `pip`
- System packages required by the chosen database and export features
- The sibling frontend when Django will serve the compiled SPA

See `docs/DEPLOYMENT.md` for production OS packages and service configuration.

## Quick start: SQLite

Ports, SQLite/MariaDB switching, Termux/Windows and diagnostics: [START_HERE.md](docs/START_HERE.md). Entry points: `python start.py sqlite` or `.env`-selected `python start.py`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-sqlite.txt
cp .env.example .env
python start_sqlite.py
```

Default `localhost:5004`; launcher initializes empty local instances and isolates SQLite database/media/uploads/exports/backups/cache/cookies.

Useful forms:

```bash
python start_sqlite.py 5005
python start_sqlite.py 0.0.0.0:8000
python start_sqlite.py --seed-pro-users
python start_sqlite.py --no-setup
```

Read `start_sqlite.py` before enabling threading or binding to an untrusted network.

## Database configuration

`manage.py` uses `config.settings`: `.env` `DB_ENGINE`/credentials, MariaDB default if omitted; shared cache configured separately. Minimal production-shaped `.env`:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
ALLOWED_HOSTS=quiz.example.com
CORS_ORIGINS=https://quiz.example.com
USE_HTTPS=True
DB_ENGINE=mariadb
DB_NAME=quiz
DB_USER=quiz
DB_PASSWORD=replace-me
DB_HOST=127.0.0.1
DB_PORT=3306
CACHE_TYPE=MemcachedCache
MEMCACHED_LOCATION=127.0.0.1:11211
```

PostgreSQL: `DB_ENGINE=postgresql`, `DB_PORT=5432`, compatible `psycopg`/`psycopg2`, existing database/user, optional `DB_SSLMODE`. MySQL options apply only to MariaDB/MySQL. Installed third-party Django backend module names are accepted; integration needs separate validation.

SQLite: `DB_ENGINE=sqlite`, `DB_NAME=SQLite/db.sqlite3`; relative paths use `backend/`. `python start.py` selects portable overlay; `manage.py` retains independent cache/storage. Explicit `python start.py sqlite` ignores server `DB_NAME` in `.env`.

Database administration (native backup/restore/provisioning) supports MariaDB/MySQL/SQLite only; PostgreSQL configuration adds none. Startup/dependencies: [START_HERE.md](docs/START_HERE.md).

Use `python manage.py bootstrap` for the guided MariaDB bootstrap flow. Read its `--help` and `docs/DEPLOYMENT.md` before supplying administrative database credentials.

## Configuration

`.env.example` documents the principal settings:

- Core/security: `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `USE_HTTPS`
- Browser origin: `CORS_ORIGINS`
- Database: `DB_ENGINE`, `DB_SSLMODE` (PostgreSQL), `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- Cache: `CACHE_TYPE`, `MEMCACHED_LOCATION`, `REDIS_URL`
- Upload/state limits: `MAX_UPLOAD_SIZE`, `MAX_STATE_TRANSFER_SIZE`, `MAX_STATE_IMPORT_QUESTIONS`
- PDF limits: `PDF_EXPORT_MAX_QUESTIONS`, `PDF_EXPORT_MAX_TOTAL_IMAGE_BYTES`
- Audit retention: `PRIVILEGED_ACTION_RETENTION_DAYS`
- Seed accounts: `SEED_PRO_USER_PASSWORD`

SQLite overrides include `SQLITE_ROOT`, `SQLITE_DB_PATH`, `SQLITE_SERVER_ADDRESS`, `SQLITE_ALLOWED_HOSTS`, `SQLITE_CORS_ORIGINS`, and `SQLITE_CSRF_TRUSTED_ORIGINS`.

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

Unknown API paths return API-envelope 404 responses; other paths fall back to compiled SPA if `frontend/dist/` exists. Vue/Android require standard envelope, session cookies and Django CSRF.

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

Cross-model or transactional logic belongs in services. Important invariants are also represented by model constraints.

## Imports, exports, and PDFs

Flat exports: editing/review. Lossless portable state: taxonomy/cases/knowledge/identities and optional images.

Synchronous PDF embeds Noto Sans Arabic; needs WeasyPrint/native Pango/HarfBuzz/Cairo. Question/image-byte caps require splitting large banks.

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

`doctor` checks configuration, database/schema access, cache, PDF dependencies, font reachability, writable directories, the frontend build, and administrators.

## Production

Build the frontend first if Django will serve it:

```bash
cd ../frontend
pnpm install
pnpm build
cd ../backend
```

Production: Gunicorn behind HTTPS proxy; secure cookies, explicit hosts/origins, trusted proxy handling, shared cache, persistent media/backups and scheduled cleanup/sweepers. Never production `runserver`/SQLite. Guide: `docs/DEPLOYMENT.md`.

## Troubleshooting

- **Configuration failure:** compare `.env` with `.env.example`.
- **Database failure:** verify MariaDB, credentials, host, and port.
- **Clients share one IP:** configure trusted reverse-proxy handling exactly as documented.
- **PDF 500:** run `python manage.py doctor` and install native PDF libraries.
- **PDF 413:** filter the export or deliberately adjust its safety limits.
- **CSRF/CORS:** align origin, trusted origins, HTTPS, and cookie settings.
- **SQLite/MariaDB cookie conflict:** use `start_sqlite.py` and its isolated overlay.

## Working documents

See the [documentation index](docs/README.md) for all supporting guides.

- [Agents.md](Agents.md) — local contributor constraints
- [workPlan.md](docs/workPlan.md) — current planned work
- [workDone.md](docs/workDone.md) — completed work log
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — detailed deployment guide
