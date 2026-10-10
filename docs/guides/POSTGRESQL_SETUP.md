# PostgreSQL setup for Quiz on Ubuntu

Updated 2026-10-10. This guide starts after PostgreSQL is installed and configures Quiz for local development, the Vue frontend and the Android app. The current installation has PostgreSQL 18.6 on port 5432, user `mpsql` and an existing database named `quiz`. A read-only PostgreSQL catalog query confirmed the lowercase name after the server rejected `Quiz`. Use `quiz` exactly in `DB_NAME` and client commands. Commands use Bash on Ubuntu/Debian and this checkout's paths.

The local ignored `backend/.env` is configured for that database/user. Its existing password was preserved. Read-only connections succeeded to the maintenance database `postgres` and the corrected application database `quiz` as `mpsql`. Launcher dependency diagnostics also reported the user's `/home/mhmmd/Envs/quiz` environment ready. These checks do not verify the application schema or cache service. The earlier cluster-down observation predates the user's startup attempt and these successful reads.

Run commands one at a time. Continue only when the previous command succeeds. Replace example passwords and LAN addresses with your own values. Database initialization writes schema and seed data; the commands below are instructions for you to run, not evidence that setup has already happened.

The project has PostgreSQL settings and a development launcher. Live PostgreSQL integration, concurrency and the application's database administration features remain unverified or unsupported as described in [schema readiness](../contracts/schemaReadiness.md). This guide does not transfer existing SQLite/MariaDB data. It uses ordinary Django initialization rather than the application's MariaDB provisioning workflow.

## 1. Understand the three services

| Service | Default local address | Purpose |
| --- | --- | --- |
| PostgreSQL | `127.0.0.1:5432` | Stores application data; Django connects to it. |
| Django backend | `http://localhost:5005` | API used by Vue and Android. |
| Vue development server | `http://localhost:5173` | Web interface; proxies API/media requests to Django. |

Android connects to Django on port **5005**, not PostgreSQL on port 5432. A physical phone uses the computer's LAN IP. `localhost` on the phone means the phone itself.

## 2. Start PostgreSQL

In any terminal:

```bash
sudo systemctl start postgresql
sudo systemctl status postgresql --no-pager
pg_isready -h 127.0.0.1 -p 5432
```

`pg_isready` should report that the server is accepting connections. This checks server availability, not whether the Quiz user's password works. On Ubuntu, the umbrella service may show `active (exited)` while its database cluster runs normally.

If the server does not respond, inspect the installed clusters:

```bash
pg_lsclusters
```

Use the actual running cluster's port throughout this guide. If there is no cluster, stop here and resolve the PostgreSQL installation before initializing Django.

Optional: start PostgreSQL automatically after reboot:

```bash
sudo systemctl enable postgresql
```

## 3. Verify the existing database user and database

For your existing user `mpsql` and database `quiz`, skip creation and check login over TCP, using the same host/port Django will use:

```bash
psql -h 127.0.0.1 -p 5432 -U mpsql -d quiz -W -c 'SELECT current_database(), current_user;'
```

Enter the PostgreSQL password for `mpsql`. The result should identify database `quiz` and user `mpsql`. Do not use the Linux login password unless you intentionally chose the same value.

If startup reports `database "Quiz" does not exist`, check the exact available names through the maintenance database:

```bash
psql -h 127.0.0.1 -p 5432 -U mpsql -d postgres -W -c 'SELECT datname FROM pg_database ORDER BY datname;'
```

Set `DB_NAME` to the actual name, then restart the backend. Do not create another database to work around a name mismatch. For this installation the verified name is `quiz`, and the local configuration has been corrected.

Only for another fresh installation where these names do not yet exist, create them first:

```bash
sudo -u postgres createuser --login --no-superuser --no-createdb --no-createrole --pwprompt mpsql
sudo -u postgres createdb --owner=mpsql quiz
```

The first command prompts for a new database password; the second creates a database owned by that user. [PostgreSQL createuser](https://www.postgresql.org/docs/current/app-createuser.html) and [createdb](https://www.postgresql.org/docs/current/app-createdb.html) document these options. Django initialization requires permission to create tables in the selected database/schema; successful login alone does not prove those permissions.

If a role/database already exists, do not delete it to make these commands succeed. Select a new name for this fresh instance or establish what the existing one contains first.

## 4. Select the backend Python environment

```bash
cd "/mnt/Common/IT Projects/Quiz/backend"
```

Reuse the environment that already runs Quiz. If its directory is `.venv`:

```bash
source .venv/bin/activate
python --version
python -m pip --version
```

If it is named `venv`, use `source venv/bin/activate` instead. The pip output should identify the selected environment.

If no environment exists, create one with a Python interpreter compatible with the repository's pinned Django and other dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-postgresql.txt
```

`requirements-postgresql.txt` reuses the existing shared core pins and adds Psycopg and the default Memcached client. It does not install MySQL or `django-sslserver`. Preserve the repository's version pins. If pip reports that the pinned Django requires another Python version, select a compatible interpreter rather than changing the project requirements.

For an existing environment that already has the core dependencies, install the PostgreSQL driver and default cache client:

```bash
python -m pip install "psycopg[binary]" pymemcache
```

The project also accepts `psycopg2`; installing both is unnecessary. The binary Psycopg installation packages its client libraries for supported platforms. See [Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html).

For uploads, ensure the system MIME library is installed:

```bash
sudo apt install libmagic1
```

PDF export has additional optional Python/native dependencies. Follow [Deployment: system packages](DEPLOYMENT.md#1-system-packages) when you need PDF output. The minimal installation above does not establish PDF readiness.

## 5. Configure a cache service

Normal PostgreSQL settings require **Memcached or Redis**. PostgreSQL does not replace the cache. If a working cache is already configured, keep it and install its matching Python client in the selected environment.

For a new local setup, the default Memcached path is:

```bash
sudo apt install memcached
sudo systemctl start memcached
python -m pip install pymemcache
```

Use the Memcached entries in the `.env` example below. Keep the cache bound to local interfaces.

If you already use Redis instead, install its Python client:

```bash
python -m pip install django-redis
```

Keep that Redis service running and configure `CACHE_TYPE=RedisCache` with its actual `REDIS_URL`, for example `redis://127.0.0.1:6379/1`. Choose one backend. `CACHE_TYPE=LocMemCache` and `SimpleCache` are not accepted by the normal settings.

## 6. Edit backend/.env

From `backend/`, open the existing configuration:

```bash
nano .env
```

Update the matching database/cache keys rather than adding duplicate entries. Preserve other existing settings:

```dotenv
DB_ENGINE=postgresql
DB_NAME=quiz
DB_USER=mpsql
DB_PASSWORD='REPLACE_WITH_THE_DATABASE_PASSWORD'
DB_HOST=127.0.0.1
DB_PORT=5432
DJANGO_ENABLE_SSLSERVER=False

CACHE_TYPE=MemcachedCache
MEMCACHED_LOCATION=127.0.0.1:11211
```

Replace the password placeholder with the PostgreSQL password for `mpsql` from step 3. The current local configuration preserves the prior password; update it locally if it differs. Use python-dotenv quoting/escaping appropriate to the password; quotes are useful for spaces or `#` characters. Keep credentials out of Git and shared error output.

If you created `.env` from scratch, also set a unique `DJANGO_SECRET_KEY`. Generate its value locally:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Copy the output into `.env` as `DJANGO_SECRET_KEY=...`. Preserve an existing valid secret rather than regenerating it during everyday startup.

Process environment variables override `.env`. If a terminal still exports old database/cache values, correct or unset those overrides before continuing. An old MariaDB `DB_PORT=3306` must not survive the switch to PostgreSQL.

## 7. Check dependencies and Django's connection

With the backend environment active:

```bash
python start.py postgres --venv .venv --diagnose
```

Replace `.venv` with your selected environment path. Diagnostics check interpreter/dependency availability without connecting to PostgreSQL, creating schema or starting the server. They do not comprehensively prove cache/PDF readiness.

Check Django configuration:

```bash
python manage.py check --settings=config.settings_local
```

Confirm Django is actually reaching PostgreSQL without printing credentials:

```bash
python manage.py shell --settings=config.settings_local -c 'from django.db import connection; connection.ensure_connection(); print("Database backend:", connection.vendor)'
```

Expected backend: `postgresql`. The HTTP development settings overlay retains the configured database/cache while applying development cookie/host settings.

## 8. Initialize the fresh database

Run from `backend/`, in the same active Python environment and with the PostgreSQL `.env` selected. This stage creates migration files as needed, applies schema and writes initial application data.

Explicit app labels allow Django to create initial migrations for model apps whose migration packages are absent:

```bash
python manage.py makemigrations core users questions learning feedback exams master_exams groups planning analytics database --settings=config.settings_local
python manage.py migrate --settings=config.settings_local
python manage.py seed_data --settings=config.settings_local
python manage.py seed_capabilities --settings=config.settings_local
```

Stop at any failure and keep the complete error, with secrets removed. Do not delete migration files or switch to a destructive rebuild command as a troubleshooting shortcut. An empty database alone does not establish that existing migration files include all current model changes.

`seed_data` creates the default `admin`, categories and runtime settings. If `ADMIN_PASSWORD` is already configured, that is the initial admin password. Otherwise the command prints a generated password once in the terminal. Keep it privately. First login requires changing it.

`seed_capabilities` initializes role capability records. It is separate from `seed_data` and should be run for this fresh setup.

Optional sample questions and onboarding tips, after the required seed commands succeed:

```bash
python manage.py seed_sample_questions --settings=config.settings_local
python manage.py seed_tips --settings=config.settings_local
```

Check for unapplied migrations:

```bash
python manage.py migrate --check --settings=config.settings_local
```

This checks the available migration graph against database state; it does not prove every feature or PostgreSQL concurrency behavior works. This guide does not use `bootstrap --clean`: application provisioning and backup/restore administration are not currently PostgreSQL workflows.

## 9. Start the backend on this computer

```bash
python start.py postgres --venv .venv
```

The default HTTP address is `http://localhost:5005`. Keep the terminal open; Ctrl+C stops the backend. The API base is `http://localhost:5005/api/v1/`.

`start.py postgres` uses existing schema/data. It does not automatically create the database, run migrations or seed users. Repeat initialization only when deliberately applying source/schema or seed changes, not at every launch.

The backend root URL may not show the Vue interface if no frontend bundle exists. Use the frontend development server below.

### Run PostgreSQL-backed HTTP without django-sslserver

The ordinary HTTP command needs no `sslserver` package, certificate files or `runsslserver`:

```bash
python start.py postgres --venv .venv
```

For a direct Django invocation with the same development overlay:

```bash
python manage.py runserver 127.0.0.1:5005 --settings=config.settings_local
```

`config.settings_local` disables `DJANGO_ENABLE_SSLSERVER` and secure-only cookies for this HTTP development process. The base settings register `sslserver` only when `DJANGO_ENABLE_SSLSERVER=True` is explicitly set. It may remain uninstalled for both the HTTP launcher and nginx/gunicorn HTTPS, where nginx handles TLS.

`django-sslserver` controls an optional Django HTTPS development command. PostgreSQL connection TLS is a separate setting: `DB_SSLMODE` still selects the database driver's SSL mode when configured. Omitting `sslserver` does not disable database TLS, weaken Android HTTPS validation or alter the nginx certificate configuration.

If you intentionally use the optional Django `runsslserver` command, install `django-sslserver` and opt in with `DJANGO_ENABLE_SSLSERVER=True` in the normal settings environment. The HTTP overlay always disables that app. For production HTTPS, follow the existing nginx/gunicorn deployment guide.

## 10. Start the Vue frontend

Open another terminal:

```bash
cd "/mnt/Common/IT Projects/Quiz/frontend"
```

If frontend dependencies have not been installed and pnpm is available:

```bash
pnpm install
```

Create or edit the ignored `frontend/.env.local` file and set:

```dotenv
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:5005
```

Keep `VITE_API_BASE_URL` unset or `/api/v1` so API requests use the proxy. Remove conflicting process environment overrides. Start Vue:

```bash
pnpm dev
```

Open `http://localhost:5173`, log in with `admin` and the seed password, then change the password. Restart Vite after editing its environment configuration.

Alternatively, after setup and dependency installation, run this from `backend/`:

```bash
python start.py -i
```

Choose **3: PostgreSQL from .env**, then **1: Start backend + frontend**. Defaults use backend 5005 and frontend 5173. This menu coordinates the proxy/origin and stops both processes with Ctrl+C; it does not initialize the database or install dependencies.

## 11. Connect the installed Android app over your LAN

Find the computer's LAN address:

```bash
hostname -I
```

Choose the address on the same reachable network as the phone, not a VPN/container address. In this section, `192.168.1.10` is an example to replace.

Stop the localhost backend with Ctrl+C and restart it with a LAN listener:

```bash
cd "/mnt/Common/IT Projects/Quiz/backend"
source .venv/bin/activate
python start.py postgres 0.0.0.0:5005 --venv .venv
```

On Android's server setup screen, enter:

```text
http://192.168.1.10:5005
```

The app adds `/api/v1/` to a bare origin. You may also enter the full URL `http://192.168.1.10:5005/api/v1/`. Use **Change server** if the app already points elsewhere, then sign in to the new database. Changing the runtime server address does not require an Android rebuild.

`0.0.0.0` is the backend bind address, not an address to type into the phone. For an Android emulator on this computer, the host address is normally `http://10.0.2.2:5005` instead.

If an enabled firewall blocks access, allow backend port 5005 only from your actual trusted LAN subnet. For example, for a `192.168.1.0/24` network:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 5005 proto tcp
```

Replace the subnet with yours. PostgreSQL and cache services can remain local to the computer; the phone needs the HTTP backend port. HTTP development launch is for your trusted network. See [Deployment](DEPLOYMENT.md) for production HTTPS and [Android server configuration](../../../Android/docs/contracts/serverConfiguration.md) for client address/TLS behavior.

## 12. Open Vue from a phone browser, if needed

Restart the LAN backend with the exact browser origin allowed:

```bash
python start.py postgres 0.0.0.0:5005 --venv .venv --frontend-origin http://192.168.1.10:5173
```

In the frontend terminal:

```bash
pnpm dev --host 0.0.0.0
```

Open `http://192.168.1.10:5173` on the phone. Vite's proxy target remains `http://127.0.0.1:5005`, because the frontend server and backend run on the same computer. If necessary, allow port 5173 from the same trusted subnet in your firewall.

## 13. Everyday startup and shutdown

After successful initialization, the normal computer-only backend startup is:

```bash
cd "/mnt/Common/IT Projects/Quiz/backend"
source .venv/bin/activate
python start.py postgres --venv .venv
```

Start Vue in a separate terminal with `pnpm dev`, or use the initialized interactive launcher from step 10. Use the LAN backend command from step 11 when connecting Android.

Stop the development servers with Ctrl+C in their terminals. Stopping Django does not delete the database. PostgreSQL/cache services may remain running for the next session.

## 14. Troubleshooting

| Symptom | Next action |
| --- | --- |
| PostgreSQL connection refused | Check `pg_isready`, `pg_lsclusters`, the service and the actual cluster port. |
| Password authentication failed | Repeat the TCP `psql` command from step 3; match user/password/host/port in `.env`. |
| Peer authentication failed | Use `-h 127.0.0.1` for the application-user check. Local socket authentication can differ from TCP. |
| Role or database already exists | Establish which instance it belongs to; use new names for a separate fresh database. |
| `database "Quiz" does not exist` | Query database names through `postgres` as shown in step 3. This installation uses lowercase `DB_NAME=quiz`. |
| Missing `psycopg` or `psycopg2` | Activate the intended venv, install the PostgreSQL driver there and rerun launcher diagnostics. |
| Missing `sslserver` | For HTTP use `start.py postgres` or `--settings=config.settings_local`; keep `DJANGO_ENABLE_SSLSERVER=False`. The package is required only for an intentional opt-in to the optional HTTPS command. |
| Missing `pymemcache` or `django_redis` | Install the client for the configured cache backend in the same venv. |
| Cache connection refused | Start the configured cache service and verify its local address. |
| Unsupported `CACHE_TYPE` | Use exactly `MemcachedCache` or `RedisCache` with the matching service/client. |
| Missing tables or columns | Confirm Django selected PostgreSQL; review initialization command results and current migration/model alignment. Startup does not apply schema. |
| `No changes detected` but a model app has no tables | Review whether initial migrations exist for that app; step 8 supplies explicit app labels. Do not assume `migrate` alone discovers every uninitialized app. |
| Migration fails on PostgreSQL | Stop and capture the failing operation/error. PostgreSQL integration is not established by configuration alone. |
| Admin password is unknown | Check whether `ADMIN_PASSWORD` was configured when seeding. Rerunning `seed_data` does not reset an existing admin. |
| Login requires a password change | Complete the first-login password reset with the newly seeded admin. |
| Vue API requests hit port 5004 | Set `VITE_BACKEND_PROXY_TARGET` to port 5005 and restart Vite; remove conflicting API/proxy overrides. |
| CSRF failure in phone browser | Pass its exact `http://LAN_IP:5173` origin to the backend launcher. |
| Android cannot connect | Check Wi-Fi reachability/client isolation, LAN bind/IP/port and firewall; avoid phone `localhost`. |
| Address already in use | Stop the intended old listener or choose a new backend port; update client/proxy URLs consistently. |
| PDF export fails | Complete the optional Python/native/font dependencies in the deployment guide. |

Share failed commands and error text with passwords, tokens and secret values removed. Do not send the complete `.env` file.

## 15. Record what actually worked

After running the setup, record the source revision/environment and actual results for:

- PostgreSQL TCP login and Django's selected backend.
- Migration and required seed completion.
- Admin login/password change and cache-dependent requests.
- Vue API/media requests through the proxy.
- Android login and ordinary study requests against the LAN backend.

These checks do not replace the [shared manual verification matrix](../../../Android/docs/verification/manualVerification.md), including failure recovery and database concurrency. The guide was checked against production configuration, launcher and seed source; its commands were not executed as part of writing it.

Related project references: [Startup](START_HERE.md), [PostgreSQL dependencies](../../requirements-postgresql.txt), [Deployment](DEPLOYMENT.md), [Schema readiness](../contracts/schemaReadiness.md), [Backend documentation](../README.md).
