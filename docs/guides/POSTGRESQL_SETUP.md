# PostgreSQL: setup and common cases

Updated 2026-10-10. Run from `backend/` with `quizon` or your own active venv. This computer uses PostgreSQL 18.6, `127.0.0.1:5432`, user `mpsql` and database **`quiz`**. Read-only login to `quiz` succeeded; the latest user startup reached HTTP 5005 with **39 unapplied migrations**. Schema initialization and functional verification remain pending.

## Existing database: current setup

The ignored `.env` already selects the database below; its password and unrelated settings were preserved. Confirm the password locally if you change accounts. Preserve your valid `DJANGO_SECRET_KEY`.

```dotenv
DB_ENGINE=postgresql
DB_NAME=quiz
DB_USER=mpsql
DB_PASSWORD='YOUR_POSTGRESQL_PASSWORD'
DB_HOST=127.0.0.1
DB_PORT=5432
DJANGO_ENABLE_SSLSERVER=False
CACHE_TYPE=MemcachedCache
MEMCACHED_LOCATION=127.0.0.1:11211
```

Edit existing keys, avoiding duplicate entries. Process environment overrides `.env`. `Quiz` and `quiz` are distinct names when passed to the client; use the actual catalog name. Keep secrets out of Git and shared output.

```bash
# Start installed services if needed (Ubuntu/Debian).
sudo systemctl start postgresql
sudo systemctl start memcached
# Install into the active Quiz environment if dependencies are missing.
python -m pip install -r requirements-postgresql.txt
# Inspect dependencies only: no DB connection/setup.
python start.py postgres --diagnose
```

The PostgreSQL dependency file reuses existing core pins and adds `psycopg[binary]` / `pymemcache`; no MySQL or `sslserver` package is needed. With Redis, install `django-redis`, run Redis and use `CACHE_TYPE=RedisCache` with its actual `REDIS_URL`. Normal server settings accept only Memcached/Redis, not `SimpleCache` or `LocMemCache`.

If Memcached is not installed, use `sudo apt install memcached`; uploads also need `libmagic1`. For a new venv, create/activate it before installing dependencies. [Shared environment/native dependencies](START_HERE.md#python-dependencies). Psycopg's [binary installation](https://www.psycopg.org/psycopg3/docs/basic/install.html) packages its client libraries on supported platforms; the project also accepts `psycopg2`.

## Bootstrap or apply pending migrations

Stop the backend with Ctrl+C. For first setup of the existing database:

```bash
python manage.py bootstrap --no-db-setup --settings=config.settings_local
```

| Case | Command/change |
| --- | --- |
| Include sample questions | Add `--with-sample-questions` to bootstrap |
| Collect static assets too | Add `--collectstatic` |
| Schema only; no seeding | Add `--skip-seed` |
| Only apply existing pending migrations | `python manage.py migrate --settings=config.settings_local` |
| Seed an already initialized schema | `python manage.py seed --settings=config.settings_local` |
| Seed sample content later | Add `--with-sample-questions` to `seed` |

Bootstrap ensures migration packages, generates initial migrations when model apps lack migration files, applies migrations and runs admin/category/settings, tips and capability seeders. It does not automatically generate all later model changes when migration files already exist. Normal bootstrap retains existing data while syncing defaults/adding seed records. PostgreSQL database/user creation is external; `--no-db-setup` explicitly skips MariaDB provisioning. **Do not use `--clean` with PostgreSQL: it is unsupported.**

Save any generated admin password; `ADMIN_PASSWORD`, if configured when creating admin, supplies that initial value. First login requires changing it. Rerunning seeding does not reset an existing admin password.

## Run without django-sslserver

```bash
python start.py postgres
# Or direct HTTP development with the same database/cache overlay:
python manage.py runserver 127.0.0.1:5005 --settings=config.settings_local
```

Open Vue separately or through the [combined menu](START_HERE.md#vue-separate-terminal-or-combined-menu). HTTP launch uses existing schema/data; it never runs bootstrap automatically.

`config.settings_local` disables the optional `sslserver` app and secure-only cookies for HTTP. Base settings register it only with explicit `DJANGO_ENABLE_SSLSERVER=True`. nginx/gunicorn HTTPS also needs no `django-sslserver`; nginx handles TLS. The optional Django HTTPS development command requires installing that package and opting in with normal settings. PostgreSQL driver TLS is independent: `DB_SSLMODE` remains effective when configured.

For Android/LAN, use `python start.py postgres 0.0.0.0:5005` and enter `http://YOUR_PC_LAN_IP:5005` on the phone. Browser/LAN origins, proxy configuration and two-instance examples are in the [startup scenarios](START_HERE.md#phone-lan-and-parallel-instances).

## Fresh installation: database/user do not exist

Only run creation commands when those names are absent; this computer already has them:

```bash
sudo -u postgres createuser --login --no-superuser --no-createdb --no-createrole --pwprompt mpsql
sudo -u postgres createdb --owner=mpsql quiz
```

Use the prompted password in `.env`, then follow bootstrap above. For another instance choose distinct names and update `.env` consistently. Do not delete an existing database to make creation succeed. These options are documented by PostgreSQL [createuser](https://www.postgresql.org/docs/current/app-createuser.html) and [createdb](https://www.postgresql.org/docs/current/app-createdb.html).

## Connection and name errors

```bash
pg_isready -h 127.0.0.1 -p 5432
pg_lsclusters
psql -h 127.0.0.1 -p 5432 -U mpsql -d quiz -W -c 'SELECT current_database(), current_user;'
# To discover the exact database names:
psql -h 127.0.0.1 -p 5432 -U mpsql -d postgres -W -c 'SELECT datname FROM pg_database ORDER BY datname;'
```

| Failure | Check |
| --- | --- |
| Connection refused | Start PostgreSQL; match the running cluster's actual port. The umbrella service can show `active (exited)`. |
| Password authentication failed | Match the role/password in `.env` with the TCP `psql` login above. |
| Peer authentication failed | Use `-h 127.0.0.1` for the TCP application-user check. |
| `database "Quiz" does not exist` | Correct `DB_NAME=quiz`; restart backend. No new database is needed here. |
| Schema permission denied | Database/schema ownership or grants must permit table creation for the application role; login alone does not prove that. |
| Missing tables / unapplied migrations | Complete bootstrap; stop at the first failing operation. |
| Missing `pymemcache` / cache refused | Install the selected client and start/configure its service. |
| Missing `sslserver` | Use the HTTP overlay and keep `DJANGO_ENABLE_SSLSERVER=False`. |

System checks, dependency diagnostics and a successful DB login do not establish schema/cache/concurrency readiness. The application's PostgreSQL provisioning, destructive clean and native backup/restore administration remain unsupported. No data transfer from SQLite/MariaDB is performed by these commands. [Schema/rollout](../contracts/schemaReadiness.md) · [Production/native dependencies](DEPLOYMENT.md) · [Manual verification](../../../Android/docs/verification/manualVerification.md).
