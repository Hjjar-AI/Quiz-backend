# Quiz — Deployment and First-Run Reference

Companion to `requirements.txt` Python pins: native libraries and first run.

## Contents

- [1. System packages](#1-system-packages)
- [2. First-run bootstrap](#2-first-run-bootstrap)
- [3. Troubleshooting](#3-troubleshooting)
- [4. OS-specific notes](#4-os-specific-notes)

---

## 1. System packages

Install host libraries **before** Python environment; none are pip-installable.

### 1.1 Reverse proxy / TLS stack

Only needed for a networked deployment that terminates HTTPS.

```bash
sudo apt install nginx openssl curl
```

- `nginx` — reverse proxy terminating TLS on port 5443.
- `openssl` — generates the self-signed certificate for the 5443 listener.
- `curl` — smoke-tests endpoints during setup and after deploy.

### 1.2 mysqlclient compile-time headers

Required to build `mysqlclient` (pip package from `requirements.txt`).

```bash
# Debian / Ubuntu
sudo apt install default-libmysqlclient-dev build-essential pkg-config

# Fedora / RHEL
sudo dnf install mariadb-connector-c-devel gcc make pkgconf-pkg-config
```

**Compiler-free alternative.** Replace `mysqlclient` in `requirements.txt` with `PyMySQL`, and add to `backend/config/__init__.py`:

```python
import pymysql
pymysql.install_as_MySQLdb()
```

Slower per query; no build toolchain needed.

### 1.3 WeasyPrint runtime libraries

`weasyprint` wheel `dlopen()`s C libraries at import; missing libraries cause `import weasyprint` `OSError` naming `.so` and PDF 500. App still starts; only `fmt=pdf` fails.

```bash
# Debian / Ubuntu (Bookworm and newer)
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 \
                 libharfbuzz0b libcairo2 \
                 libgdk-pixbuf-2.0-0 libffi8

# Fedora / RHEL
sudo dnf install pango pangoft2 harfbuzz cairo gdk-pixbuf2 libffi

# Alpine (slim container images)
apk add pango pango-dev harfbuzz cairo gdk-pixbuf libffi
```

### 1.4 libmagic (required by `python-magic`)

```bash
# Debian / Ubuntu
sudo apt install libmagic1

# Fedora / RHEL
sudo dnf install file-libs

# Alpine
apk add file
```

Missing `libmagic` is a **hard failure** at upload time — the MIME check fails closed rather than accepting unverified files.

### 1.5 Arabic font for PDF export

PDF embeds repository Noto Sans Arabic TTF for self-contained glyphs:

```
frontend/public/fonts/NotoSansArabicVariable.ttf
```

`pdf_export.py` searches (in order):

1. `settings.FRONTEND_DIR / 'public' / 'fonts'`
2. `settings.BASE_DIR / 'static' / 'fonts'`

Development satisfies (1) automatically. A production host that ships only the built `frontend/dist/` tree should copy the TTF during the build:

```bash
mkdir -p backend/static/fonts
cp frontend/public/fonts/NotoSansArabicVariable.ttf \
   backend/static/fonts/
```

Missing font: Pango system fallback still generates PDF; warning names both searched paths.

### 1.6 MariaDB timezone tables

Django's `TruncMonth` / `TruncWeek` / `TruncDate` on a tz-aware `DateTimeField` compile to `CONVERT_TZ(..., 'UTC', <TIME_ZONE>)` on MariaDB. On a stock Debian/Ubuntu install the `mysql.time_zone*` tables are empty, so `CONVERT_TZ` returns `NULL` and Django raises:

```
ValueError: Database returned an invalid datetime value.
Are time zone definitions for your database installed?
```

Load them once per server (idempotent):

```bash
sudo mysql_tzinfo_to_sql /usr/share/zoneinfo | sudo mysql mysql
```

Python bucketing (`apps/analytics/services/admin_advanced.py`) handles empty tables; loading them restores SQL path/helps MariaDB TIMESTAMP arithmetic.

---

## 2. First-run bootstrap

Run from `backend/` with the virtualenv activated and `backend/.env` populated. See `backend/.env.example` for required keys.

### 2.1 Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.2 Schema and seed data

Pick **one** path. Both produce equivalent databases.

#### Path A — incremental (recommended for existing databases)

Runs each seeder individually so a failure is easy to localise.

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data
python manage.py seed_sample_questions
python manage.py seed_capabilities     # ← required; not run by seed_data
python manage.py seed_tips             # ← optional; onboarding tips
```

`seed_data`: `admin`/category taxonomy/default settings; initial password once on **stderr**, `must_change_password=True`. `MustChangePasswordMiddleware` blocks API/`/admin/` except change-password until first-login reset.

`seed_sample_questions`: admin required; run `seed_data` first. Idempotent/safe repeat.

Fresh DB requires `seed_capabilities`: otherwise empty `RoleCapabilities` falls back correctly to `apps/users/capabilities.py` defaults, but panel read-back remains empty until row exists.

#### Path B — clean rebuild (development only; DESTROYS the database)

Drops every table, deletes every migration file under the custom apps, regenerates `0001_initial.py`, migrates, and runs the `seed` orchestrator.

```bash
python manage.py bootstrap --clean --yes --with-sample-questions
```

Equivalent long form, if you prefer explicit flags:

```bash
python manage.py bootstrap \
    --clean \
    --with-sample-questions \
    --reset-capabilities
```

Flags accepted by `bootstrap`:

| Flag | Effect |
|---|---|
| `--clean` | **Destructive.** Drops every table and deletes every migration file for the custom apps. Requires interactive confirmation; use `--yes` to skip in scripts. |
| `--yes`, `-y` | Skip the interactive `--clean` confirmation. |
| `--with-sample-questions` | Also run `seed_sample_questions` after the default seed set. |
| `--reset-capabilities` | Forward `--reset` to `seed_capabilities` — overwrite every `RoleCapabilities` row with code defaults, discarding panel edits. |
| `--no-db-setup` | Skip the MariaDB provisioning step. Use when the database and user already exist, or when running against SQLite. |
| `--db-admin-user` / `--db-admin-password` | Administrative MariaDB credentials. **Lower precedence** than `DB_ADMIN_USER` / `DB_ADMIN_PASSWORD` in `.env`. CLI values are visible in `ps` and shell history. |
| `--collectstatic` | Run `collectstatic` at the end of the pipeline. |
| `--no-checks` | Skip the explicit Django system-check step. Django reserves `--skip-checks` for its own use; this is the equivalent custom flag. |
| `--skip-seed` | Skip the seed wrapper entirely. Useful for CI runs that seed separately. |

### 2.3 Static files

```bash
python manage.py collectstatic --noinput
```

Copies admin CSS/JS from site-packages into `backend/staticfiles/`; absent collection leaves `/admin/` unstyled. Repeat after Django/third-party upgrade.

### 2.4 Firewall and development server

nginx TLS (§ 1.1): **5443**; Django development: **5004**. Independent ports: open 5443 only with nginx in front.

```bash
# Only if nginx is in front:
sudo ufw allow 5443/tcp

# Development server:
python manage.py runserver 0.0.0.0:5004
```

For a self-contained SQLite instance alongside a MariaDB instance, use the SQLite launcher instead:

```bash
pip install -r requirements-sqlite.txt
python scripts/start_sqlite.py                 # interactive address prompt
python scripts/start_sqlite.py 5005            # localhost:5005
python scripts/start_sqlite.py 0.0.0.0:5004    # trusted LAN (DEBUG server)
python scripts/start_sqlite.py --seed-pro-users
python scripts/start_sqlite.py --no-prompt
python scripts/start_sqlite.py --allow-threading  # explicit opt-in; see below
```

`scripts/start_sqlite.py` creates `backend/apps/__init__.py`/custom `migrations/`, runs `makemigrations`/`migrate`, idempotently syncs categories/settings/capabilities each setup. Creates admin only without superuser. `config/settings_sqlite.py` redirects `media/`, `uploads/`, `exports/`, `backups/` and DB into `backend/SQLite/`; separate session/CSRF cookies permit concurrent same-checkout MariaDB.

SQLite defaults: `--nothreading`, `BEGIN IMMEDIATE`, serializing MariaDB-style row-locked read-modify-write. `--allow-threading` only for trusted light single-user development; real concurrency needs MariaDB.

`SQLITE_ROOT=/safe/path` moves the database and all SQLite-owned data folders together. `SQLITE_DB_PATH` still overrides only the database. When binding a concrete LAN address, the launcher adds it to this overlay's `ALLOWED_HOSTS`; a wildcard bind permits Host headers only in this DEBUG-only overlay and prints an exposure warning. Legacy `CORS_ORIGINS=*` values are translated to `CORS_ALLOW_ALL_ORIGINS=True` in this overlay instead of being copied into Django's scheme-required CSRF list. For a separate frontend origin, set `SQLITE_CSRF_TRUSTED_ORIGINS` to explicit URLs such as `http://192.168.1.10:5173`.

### 2.5 Optional — pro / moderator accounts

```bash
python manage.py seed_pro_users
python manage.py seed_pro_users --reset-passwords
```

One moderator/doctor from About; username-idempotent unless `--reset-passwords`. New accounts: `must_change_password=True`, `.env` `SEED_PRO_USER_PASSWORD` or default `1234test`.

### 2.6 Password reset at any time

```bash
python manage.py reset_admin_password
python manage.py reset_admin_password --qr
```

Prints the new password to **stderr**, sets `must_change_password=True`, and (with `--qr`) renders an ASCII QR code for the credential.

### 2.7 Health check

```bash
python manage.py doctor
```

Read-only configuration/DB/cache/PDF/Arabic font/directory/frontend-build report; exit `1` on any failure supports CI/systemd preflight. Check **before** trusting bootstrap: catches missing libraries/fonts before affected feature use.

---

## 3. Troubleshooting

### `ModuleNotFoundError: No module named 'apps.core.management._app_registry'`

`bootstrap.py` (line ~90) and `scripts/start_sqlite.py` (line ~215) both import `apps.core.management._app_registry`, but the file ships at `apps/core/management/commands/_app_registry.py`. Move it up one directory:

```bash
mv backend/apps/core/management/commands/_app_registry.py \
   backend/apps/core/management/_app_registry.py
find backend/apps/core/management -name __pycache__ -type d -exec rm -rf {} +
```

### `import weasyprint` raises `OSError: libpango-1.0.so.0: cannot open shared object file`

System libraries from § 1.3 are missing. The app still runs; only PDF export returns 500.

### `ValueError: Database returned an invalid datetime value`

MariaDB timezone tables are empty. See § 1.6.

### `PermissionDenied` from `python-magic`

`libmagic` is missing. See § 1.4. Uploads will fail closed.

### Empty `/admin/` styles

`collectstatic` was not run. See § 2.3.

---

## 4. OS-specific notes

### Termux (Android)

Termux names differ. SQLite uses dedicated requirements without unused `mysqlclient`/Gunicorn builds. Keep checkout/venv/state in private `$HOME`, not `/sdcard`/`/storage/emulated/0`: shared storage lacks reliable execution/SQLite locking.

```bash
pkg install -y \
    python python-pip \
    build-essential pkg-config \
    libjpeg-turbo libpng zlib freetype harfbuzz cairo pango \
    libffi file tzdata openssl curl

python -m pip install --upgrade pip wheel setuptools
pip install -r backend/requirements-sqlite.txt
```

Notes:

- `pkg-config` exists in Termux; on some mirrors it is `pkgconf`.
- `zlib` is not always pulled transitively by Pillow's build.
- `file` provides `libmagic` for `python-magic`.
- `pkg install python` already bundles pip; `python-pip` is listed defensively for older mirrors.
- `xlrd` still works on Termux; `openpyxl` is pure Python.
- WeasyPrint on Termux is fragile. If `import weasyprint` fails after installing it separately, PDF export is unavailable but every other export format still works. It is deliberately not part of `requirements-sqlite.txt`.

Then:

```bash
SQLITE_ROOT="$HOME/.local/share/quiz" python backend/scripts/start_sqlite.py
```

For access from another device on a trusted Wi-Fi network:

```bash
SQLITE_ROOT="$HOME/.local/share/quiz" \
  python backend/scripts/start_sqlite.py 0.0.0.0:5004
```

### macOS

```bash
brew install mariadb pango cairo libffi
brew services start mariadb
```

`mysqlclient` builds against Homebrew's MariaDB headers out of the box. `libmagic` is provided by `file` (usually already present).

### Windows

Not a supported deployment target. Development is possible under WSL2 with the Debian/Ubuntu instructions above.

---

## 5. Related files

| File | Purpose |
|---|---|
| `requirements.txt` | Python package pins |
| `backend/.env.example` | Environment variable reference |
| `backend/config/settings.py` | Django settings, with inline rationale |
| `backend/apps/core/management/commands/doctor.py` | Health check |
| `backend/apps/core/management/commands/bootstrap.py` | First-run orchestrator |
