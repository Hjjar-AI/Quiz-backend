# Quiz startup: SQLite, PostgreSQL and MariaDB

Updated 2026-10-10. Run backend commands from `backend/` and frontend commands from `frontend/`. Use your active Python environment; this computer's existing shortcut is `quizon` (`/home/mhmmd/Envs/quiz`). Otherwise activate your own venv. Run commands separately and stop at any failure.

## Choose your scenario

| Scenario | First setup | Everyday backend command | HTTP port |
| --- | --- | --- | --- |
| Portable/local SQLite | Install `requirements-sqlite.txt`; normal launch initializes schema/seed data | `python start.py sqlite --no-setup` | 5004 |
| Separate SQLite instance | Normal launch with `--data-root PATH` | `python start.py sqlite --data-root PATH --no-setup` | 5004 unless changed |
| Existing PostgreSQL database | Install `requirements-postgresql.txt`; configure `.env`; bootstrap below | `python start.py postgres` | 5005 |
| Existing MariaDB/MySQL database | Install `requirements.txt` plus cache client; configure `.env`; bootstrap below | `python start.py mariadb` | 5005 |
| Database selected in `.env` | Complete its corresponding setup | `python start.py` | SQLite 5004; server DB 5005 |
| Initialized backend + Vue together | Both dependency sets and database ready | `python start.py -i` | Backend 5004/5005; Vue 5173 |

Explicit modes override `DB_ENGINE` for that run. Environment variables override `.env`. Missing `DB_ENGINE` retains the legacy MariaDB default. Specify another port after the mode, e.g. `python start.py postgres 5010`.

## Python dependencies

Reuse your working environment. For a new one:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Choose one dependency file:

```bash
# SQLite
python -m pip install -r requirements-sqlite.txt
# PostgreSQL: shared core + Psycopg + Memcached client
python -m pip install -r requirements-postgresql.txt
# MariaDB/production dependency set; includes mysqlclient
python -m pip install -r requirements.txt
```

Server-database modes need a running cache: default Memcached with `pymemcache`, or Redis with `django-redis`. Install the matching client in the selected environment. SQLite uses an isolated in-process cache. Keep repository version pins; select a compatible Python interpreter if pip rejects them. [Native/PDF/OS dependencies](DEPLOYMENT.md#1-system-packages).

## SQLite: first run and isolation

```bash
python start.py sqlite
```

This normally ensures package files, generates initial migrations for model apps without migration files, applies pending migrations and seeds categories/settings/capabilities. It creates the default admin only when no superuser exists; save any printed credential and change it on first login. It starts HTTP on 5004, with an address prompt when appropriate.

| Case | Command/options |
| --- | --- |
| Default root | `python start.py sqlite` → `backend/SQLite/` |
| Existing initialized instance; skip setup | `python start.py sqlite --no-setup` |
| Separate instance and port | `python start.py sqlite 5006 --data-root SQLite/sandbox` |
| Select only the database file | `python start.py sqlite --db-path /path/to/db.sqlite3` |
| Avoid address prompt | Add `--no-prompt`, or supply a port / `host:port` |
| Optional moderator/pro accounts | Add `--seed-pro-users` during normal setup |
| Disable backend autoreload | Add `--noreload` |
| Explicit concurrent development requests | Add `--allow-threading`; only for trusted light use |

`--data-root` moves database/media/uploads/exports/backups together; `--db-path` changes only the database. Roots isolate cache/cookies as well. An empty root is a new instance, not a copy. To relocate existing SQLite data, stop its server and copy the whole root before selecting the copied path. Never overwrite an active instance.

SQLite defaults to `--nothreading` and `BEGIN IMMEDIATE`. If model apps have no migration files, normal setup creates initial migrations from current models. If migration files already exist, deleting the database alone does not generate migrations for later model changes. See [schema readiness](../contracts/schemaReadiness.md).

For Termux/private phone storage:

```bash
python start.py sqlite --data-root "$HOME/.local/share/quiz"
```

## Server databases: configuration and bootstrap

Keep credentials in ignored `backend/.env`. Use the actual database name/port and preserve the existing secret key and unrelated settings.

| Key | Current PostgreSQL | MariaDB example |
| --- | --- | --- |
| `DB_ENGINE` | `postgresql` | `mariadb` |
| `DB_NAME` | `quiz_fresh` (user-bootstrap completed) | Your existing database |
| `DB_USER` | `mpsql` | Your application user |
| `DB_PASSWORD` | That user's database password | That user's database password |
| `DB_HOST` | `127.0.0.1` | `127.0.0.1` |
| `DB_PORT` | `5432` | `3306` |

PostgreSQL database/user must already exist: [PostgreSQL cases](POSTGRESQL_SETUP.md). For an existing PostgreSQL or MariaDB database, stop the server and initialize it:

```bash
python manage.py bootstrap --no-db-setup --settings=config.settings_local
```

Add `--with-sample-questions` for demo questions. Bootstrap applies migrations and runs `seed_data`, `seed_tips` and `seed_capabilities`; it generates initial migrations when model apps lack migration files. It does not generate every later model change automatically. Normal bootstrap preserves existing data; seeders may sync defaults/add records.

For MariaDB database/user provisioning, omit `--no-db-setup` and configure `DB_ADMIN_USER` / `DB_ADMIN_PASSWORD` in `.env`. PostgreSQL provisioning is external. `--clean` destroys data and migration files and supports only SQLite/MariaDB; it is not a PostgreSQL initialization option.

If existing migration files need to represent deliberate model changes, use `makemigrations` explicitly before applying them. If only pending migrations need applying, use:

```bash
python manage.py migrate --settings=config.settings_local
```

`start.py postgres`, `start.py mariadb`, direct `runserver` and the interactive menu do not initialize schema/seed data. The user subsequently completed PostgreSQL bootstrap on `quiz_fresh`; the old `quiz` database remains separate.

HTTP and nginx/gunicorn HTTPS need no `django-sslserver`. `config.settings_local` disables that optional app and uses HTTP-compatible cookies. The optional Django HTTPS command requires installing `django-sslserver` and explicitly setting `DJANGO_ENABLE_SSLSERVER=True` with normal settings. `DB_SSLMODE` controls PostgreSQL connection TLS separately.

## Vue: separate terminal or combined menu

From `frontend/`, install dependencies with `pnpm install` if needed. Set the selected backend in ignored `.env.local`, then restart Vite:

```dotenv
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:5005
```

Use 5004 for default SQLite. Keep `VITE_API_BASE_URL` unset or `/api/v1`, and remove conflicting process overrides.

```bash
pnpm dev
```

Open `http://localhost:5173`. Backend `/` may not display Vue without a frontend bundle. An occupied Vite port is an error; select another explicitly, e.g. `pnpm dev --port 5174`, then trust that origin in the backend.

For a combined initialized launch, run `python start.py -i` from `backend/`. Choose the database, then backend + frontend. Customization offers ports, LAN address, venv and SQLite root. Enter accepts defaults; `0` cancels. The menu configures the proxy/origin, skips schema/seed setup and does not install dependencies. Backend autoreload is disabled; restart after backend edits. Ctrl+C or either process exiting stops both.

## Phone, LAN and parallel instances

Replace `192.168.1.10` with the computer's reachable LAN IP (`hostname -I`). Both devices need network access; allow the chosen HTTP ports through any enabled firewall only from your trusted LAN.

| Client | Backend launch | Client address |
| --- | --- | --- |
| Android + SQLite | `python start.py sqlite 0.0.0.0:5004 --no-setup` | `http://192.168.1.10:5004` |
| Android + PostgreSQL | `python start.py postgres 0.0.0.0:5005` | `http://192.168.1.10:5005` |
| Android + MariaDB | `python start.py mariadb 0.0.0.0:5005` | `http://192.168.1.10:5005` |
| Phone browser + PostgreSQL | Add `--frontend-origin http://192.168.1.10:5173` to the LAN launch | `http://192.168.1.10:5173` |
| Phone browser + SQLite/MariaDB | Same origin option, matching mode/port | `http://192.168.1.10:5173` |
| Android emulator on this PC | Backend accepts host connections | `http://10.0.2.2:5004` or `:5005` |

For phone browsers run Vue with `pnpm dev --host 0.0.0.0`. Its proxy remains `127.0.0.1:BACKEND_PORT` when both servers run on this computer. `0.0.0.0` is a bind address, not a client URL; phone `localhost` means the phone. Android accepts an origin or full `/api/v1/` URL through **Change server**, without rebuilding. [Native address/TLS rules](../../../Android/docs/contracts/serverConfiguration.md).

For two instances, choose distinct backend ports and SQLite roots where relevant. Example backend terminals: SQLite 5004 and PostgreSQL 5005. Choose either proxy target, or use separate Vue terminals:

```bash
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:5004 pnpm dev --port 5173
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:5005 pnpm dev --port 5174
```

Trust each matching browser origin with `--frontend-origin`. Stop development servers with Ctrl+C; their data remains. [Production HTTPS](DEPLOYMENT.md).

## Diagnose and recover

```bash
python start.py sqlite --diagnose
python start.py postgres --venv /home/mhmmd/Envs/quiz --diagnose
```

Use your actual venv path; explicit `--venv` does not silently fall back. Diagnostics check interpreter/dependencies without DB connections, setup or server launch. They do not establish cache, schema or PDF readiness.

| Symptom | Action |
| --- | --- |
| Missing Python package | Install the matching dependency set/client in the selected venv. |
| Missing PostgreSQL `Quiz` | Use the actual catalog name; current initialized DB is `quiz_fresh`. See [name/login checks](POSTGRESQL_SETUP.md#connection-and-name-errors). |
| Unapplied migrations | Stop server and run bootstrap for first setup, or deliberate `migrate` for pending schema updates. |
| Cache connection error | Start the configured Memcached/Redis service; match its client/location. |
| Login lost on HTTP | Use the development overlays/launchers, which disable secure-only cookies. |
| CSRF failure | Pass the exact browser scheme/host/port through `--frontend-origin`. |
| Vue API/media failure | Match proxy target/port, remove conflicting API overrides and restart Vite. |
| Empty/different SQLite content | Check the printed DB path and selected root; a new root is a separate instance. |
| Port occupied | Stop the intended old listener or choose another port and update client/proxy URLs. |

The read-only desktop tutorial is `python scripts/startup_tutorial.py` (Tkinter/display needed); it provides copyable plans without launching/installing/setup. Root Python entry points remain `start.py` and `manage.py`; direct SQLite compatibility entry is `scripts/start_sqlite.py`.

Source-aligned instructions do not prove runtime correctness. Record actual setup/device results; keep [schema/rollout gates](../contracts/schemaReadiness.md) and the [manual matrix](../../../Android/docs/verification/manualVerification.md) separate.
