# Deployment and optional native dependencies

Updated 2026-10-10. Use [Startup](START_HERE.md) for SQLite/server-database HTTP scenarios and [PostgreSQL setup](POSTGRESQL_SETUP.md) for the current `mpsql` / `quiz_fresh` instance. Run backend commands from `backend/` unless stated otherwise; keep secrets in ignored `.env`.

For worker/database sizing, see the [verified concurrency limits](../verification/concurrencyLimits.md): the current cluster has 100 connection slots with three reserved for superusers; local 16-worker transaction tests do not establish deployed user capacity.

## 1. System packages

Install only the groups your selected features need. Keep Python pins in the repository dependency files; they are not replaced by system packages.

| Feature | Ubuntu/Debian packages | Notes |
| --- | --- | --- |
| MIME-checked uploads | `libmagic1` | Missing library makes upload validation fail closed. |
| MariaDB `mysqlclient` build | `default-libmysqlclient-dev build-essential pkg-config` | PostgreSQL/SQLite do not need this driver. |
| Production reverse proxy/TLS | `nginx openssl curl` | `scripts/quiz_start.sh` uses nginx + gunicorn. |
| PDF export | Packages below | Optional Python `weasyprint` and native stack needed. |
| Default server cache | `memcached` | Python client: `pymemcache`; Redis is an alternative with `django-redis`. |

Example PDF stack for recent Ubuntu/Debian:

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libcairo2 libgdk-pixbuf-2.0-0 libffi8
```

Use package names available for your distro release. `requirements.txt` contains the project's WeasyPrint/gunicorn pins; minimal SQLite/PostgreSQL requirements intentionally omit those optional features. Install the matching pins from that file when needed, with their native dependencies.

Other native package families:

| OS | MariaDB build | PDF/MIME |
| --- | --- | --- |
| Fedora/RHEL | `mariadb-connector-c-devel gcc make pkgconf-pkg-config` | `pango pangoft2 harfbuzz cairo gdk-pixbuf2 libffi file-libs` |
| Alpine | Use distro-appropriate MySQL build headers/tools if needed | `pango pango-dev harfbuzz cairo gdk-pixbuf libffi file` |
| macOS | Homebrew MariaDB headers | `pango cairo libffi file` |

PDF embeds `NotoSansArabicVariable.ttf`, searching `frontend/public/fonts/` then `backend/static/fonts/`. If shipping only frontend build output, preserve that font separately. From the project root:

```bash
mkdir -p backend/static/fonts
cp frontend/public/fonts/NotoSansArabicVariable.ttf backend/static/fonts/
```

Without it, PDF uses a system font fallback; verify Arabic glyphs in actual exported output.

MariaDB date bucketing may require server timezone tables. On a stock Ubuntu/Debian MariaDB installation:

```bash
sudo mysql_tzinfo_to_sql /usr/share/zoneinfo | sudo mysql mysql
```

This is a MariaDB system-database write, not a PostgreSQL/SQLite requirement.

## 2. First-run bootstrap

Activate the correct Python environment and configure `.env` for the selected database/cache. For local HTTP setup of an existing server database:

```bash
python manage.py bootstrap --no-db-setup --settings=config.settings_local
```

| Scenario | Setup path |
| --- | --- |
| Fresh portable SQLite | `python start.py sqlite` performs setup/seeding and starts HTTP. |
| Existing SQLite, launch only | `python start.py sqlite --no-setup` |
| Existing PostgreSQL database/user | Bootstrap above; current application DB is `quiz_fresh`. |
| Existing MariaDB database/user | Bootstrap above. |
| MariaDB database/user need provisioning | Omit `--no-db-setup`; supply `DB_ADMIN_USER` / `DB_ADMIN_PASSWORD` in `.env`. |
| Production server schema/seed | Bootstrap with normal `config.settings` and configured production secrets/cache, instead of the HTTP overlay. |
| Only apply pending migrations | `python manage.py migrate --settings=config.settings_local` for HTTP configuration. |

Bootstrap runs checks, migration package/initial-migration preparation, `migrate`, then `seed_data`, `seed_tips` and `seed_capabilities`. It generates migrations when model apps have no migration files, not for every later model change. When deliberately changing models with existing migration files, generate/review matching changes explicitly before applying them. [Schema readiness](../contracts/schemaReadiness.md).

| Bootstrap flag | Effect |
| --- | --- |
| `--no-db-setup` | Skip MariaDB provisioning; use an existing database/user. |
| `--with-sample-questions` | Include demo questions/cases after default seeders. |
| `--collectstatic` | Collect static files after initialization. |
| `--skip-seed` | Apply schema without default data. |
| `--reset-capabilities` | Replace stored role capabilities with code defaults; discards panel edits. |
| `--clean` | Destructive SQLite/MariaDB table/file/migration reset; unsupported on PostgreSQL. Requires confirmation. |
| `--yes` | Bypass only the destructive clean confirmation; unnecessary for normal setup. |
| `--no-checks` | Bypass checks; keep checks enabled for ordinary setup. |

Avoid putting administrative passwords in CLI arguments; `.env` values take precedence and do not expose passwords through command history/process arguments. A fresh admin uses `ADMIN_PASSWORD` if set, otherwise a one-time password printed to stderr. First login requires changing it. Sample questions are opt-in.

## 3. Optional account and operator commands

Choose the settings for the intended database: `config.settings_local` for server-database HTTP development, `config.settings_sqlite` for portable SQLite, or normal production settings. For a custom SQLite root set `SQLITE_ROOT` consistently before using `manage.py`; do not accidentally administer the default root.

Examples for server-database HTTP development:

```bash
python manage.py seed_pro_users --settings=config.settings_local
python manage.py reset_admin_password --settings=config.settings_local
python manage.py collectstatic --noinput --settings=config.settings_local
python manage.py doctor --settings=config.settings_local
```

`seed_pro_users` creates demo moderator/doctor accounts; passwords come from `SEED_PRO_USER_PASSWORD` or its development fallback `1234test`, and require first-login change. `--reset-passwords` explicitly resets existing demo accounts. `reset_admin_password --qr` optionally displays an ASCII QR credential; keep its terminal output private.

`doctor` reports configuration, database/migration state, cache, PDF/font, directories and frontend bundle availability. It is a diagnostic command, not initialization; cache probes may access the cache. A report does not replace functional/device verification. Missing frontend bundle is expected when using separate Vite development.

## 4. Production HTTPS

The current `scripts/quiz_start.sh` serves nginx HTTPS on **5004**, with gunicorn on a local Unix socket. It does not use `django-sslserver`. Do not run the default SQLite HTTP listener on that same port simultaneously.

Prepare before launch:

- Valid production `.env`: secret key, explicit allowed hosts/origins, secure cookies (`USE_HTTPS=True`), chosen database and shared cache.
- Matching schema and required seed records; complete initialization separately.
- Working nginx and gunicorn in the selected environment.
- Frontend bundle at `frontend/dist/index.html`; building it is a separate action.
- Certificate/key at `backend/cert/quiz/quiz.pem` and `quiz.key`, trusted by intended clients.
- Optional PDF dependencies and font if exporting PDF.

From `backend/`:

```bash
bash scripts/quiz_start.sh
```

The launcher discovers a venv or accepts `QUIZ_VENV`, generates a user-owned nginx configuration/runtime under `$HOME/.config/quiz`, collects missing admin static assets, starts three gunicorn workers and nginx, and stops both on Ctrl+C. It does not bootstrap schema. `QUIZ_NGINX` selects an alternate executable if the system nginx cannot run on the CPU.

Allow only the intended HTTPS listener through your deployment firewall. PostgreSQL/cache can remain local to Django. PostgreSQL `DB_SSLMODE` is independent of browser/Android TLS. Removing `django-sslserver` does not weaken certificate/hostname validation. A Django `runserver` command is for development, not production.

## 5. OS-specific development

### Termux

Use SQLite and private storage for checkout/venv/data; shared Android storage has execution/locking limitations. From the backend checkout after installing its system dependencies:

```bash
pkg install python python-pip build-essential pkg-config libjpeg-turbo libpng zlib freetype harfbuzz cairo pango libffi file tzdata openssl curl
python -m pip install -r requirements-sqlite.txt
python start.py sqlite --data-root "$HOME/.local/share/quiz"
```

On some mirrors `pkgconf` replaces `pkg-config`; `file` supplies libmagic. Use a Python environment compatible with the pinned packages. PDF support on Termux is optional and must be verified separately. Add `0.0.0.0:5004` for trusted LAN access; configure browser origin/proxy as in [Startup](START_HERE.md#phone-lan-and-parallel-instances).

### macOS and Windows

For MariaDB on macOS, `brew install mariadb` and `brew services start mariadb`; select compatible native dependencies from section 1. For Windows use WSL2 with the Ubuntu instructions; native Windows production deployment is not a supported target. Venv activation/interpreter paths differ on native Windows (`.venv\Scripts\python.exe`).

## 6. Troubleshooting and verification

| Problem | Action |
| --- | --- |
| Missing package or wrong interpreter | Select the correct venv/dependency set; run launcher `--diagnose`. |
| App-registry import fails | Current file is `apps/core/management/_app_registry.py`; check checkout completeness rather than moving a historical file. |
| PDF native-library import error | Install the selected OS PDF stack and the matching WeasyPrint pin. |
| Arabic PDF font fallback | Preserve the TTF in one of the configured font directories; inspect a real export. |
| MariaDB invalid date bucketing | Check timezone tables from section 1. |
| Upload MIME failure | Install the system libmagic package. |
| Unstyled production admin | Run `collectstatic` with the intended production settings. |
| PostgreSQL name/login/schema error | Follow [PostgreSQL troubleshooting](POSTGRESQL_SETUP.md#connection-and-name-errors). |
| HTTP cookie/CSRF/proxy issue | Use [Startup recovery](START_HERE.md#diagnose-and-recover). |

The user reported successful PostgreSQL bootstrap on `quiz_fresh`. Isolated [Python suites](../verification/pythonTests.md) pass on SQLite and PostgreSQL, including the PostgreSQL two-thread exam-finish check. Deployed workflows, production cache, PDF rendering and broader concurrency need verification. PostgreSQL provisioning/destructive clean and application-native backup/restore are unsupported. Follow the [shared manual matrix](../../../Android/docs/verification/manualVerification.md).
