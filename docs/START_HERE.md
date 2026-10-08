# Starting Quiz

Run `python` commands from `backend/`; use `python3` where needed. Absolute script paths work elsewhere; relative data paths use `backend/`.

## Interactive launch

```bash
python start.py -i
```

Choose `.env`, separate SQLite, PostgreSQL or MariaDB, then backend + frontend, backend only, read-only diagnostics or command preview. Enter accepts defaults; `0` cancels menus. Optional customization covers ports, LAN browser address, Python venv and separate SQLite data directories.

The combined launch sets Vite's API/media proxy and backend browser origin for the selected ports, overriding inherited frontend API/proxy settings for that process. No `.env` edits are needed; credentials remain there. Open the printed frontend URL once Vite is ready. Ctrl+C stops both processes; either process exiting stops its companion. Backend auto-reload is disabled in this menu; restart after backend source edits. Frontend hot reload remains enabled.

Requires existing database/schema and installed Python dependencies; combined mode also requires pnpm and installed frontend dependencies. The menu skips SQLite schema setup/seeding and never installs dependencies or provisions databases. Use diagnostics first for startup failures. `.env` mode defaults to port 5005 even when its selected engine is SQLite; separate SQLite defaults to 5004. Existing CLI commands below retain their behavior.

## Choose the database

Set the engine in `backend/.env`, alongside its credentials:

```dotenv
DB_ENGINE=postgresql
DB_NAME=quiz
DB_USER=quiz
DB_PASSWORD=replace-me
DB_HOST=localhost
DB_PORT=5432
```

Run `python start.py`; `.env` engines: `mariadb`/3306, `postgresql`/5432, `sqlite` with `DB_NAME=SQLite/db.sqlite3`. Change/remove `DB_PORT` when switching; explicit port wins. Missing `DB_ENGINE` defaults MariaDB. Environment overrides `.env`; explicit modes override engine for that run.

| Scenario | Backend command | Backend HTTP address |
| --- | --- | --- |
| SQLite on this computer | `python start.py sqlite` | `http://localhost:5004` |
| SQLite on another port | `python start.py sqlite 5006` | `http://localhost:5006` |
| Separate SQLite instance | `python start.py sqlite 5006 --data-root SQLite/sandbox` | `http://localhost:5006` |
| Database selected in `.env` | `python start.py` | `http://localhost:5005` (SQLite: 5004) |
| Existing PostgreSQL | `python start.py postgres` | `http://localhost:5005` |
| Existing MariaDB | `python start.py mariadb` | `http://localhost:5005` |
| Existing MariaDB on another port | `python start.py mariadb 5010` | `http://localhost:5010` |

`start_sqlite.py` remains supported; first-run setup runs unless `--no-setup`. New entry point never deletes/resets data. Server modes run no setup/migrations/seeders; initialize those instances through existing deployment workflow.

All development modes use HTTP cookies despite production `.env` `USE_HTTPS=True`. Server credentials/cache remain configured. SQLite isolates database/files/local cache/cookies; distinct databases get distinct cookies because browsers do not isolate by port.

## Start the frontend against the selected backend

The backend is the API server. The frontend development page is normally at `http://localhost:5173`. Start it separately from `frontend/`:

```bash
pnpm dev
```

The default proxy target is SQLite on port 5004. For MariaDB or any other backend port, put this in the uncommitted `frontend/.env.local`, then restart `pnpm dev`:

```dotenv
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:5005
```

Use selected backend port; keep `VITE_API_BASE_URL` unset or `/api/v1` so requests use proxy. Remove conflicting frontend env values. Proxy forwards `/media` question images.

The frontend now refuses an occupied port instead of changing origin silently. Choose another port explicitly if you need two frontend instances.

## Two databases at the same time

Use two backend terminals:

```bash
python start.py sqlite 5004
python start.py mariadb 5005
```

Point the frontend proxy at whichever instance you want to use, and restart the frontend when changing its env file. To keep both UIs open, use separate frontend processes with distinct ports and proxy targets. For example on Linux/Termux:

```bash
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:5004 pnpm dev --port 5173
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:5005 pnpm dev --port 5174
```

Pass the matching browser origin to each backend if needed:

```bash
python start.py sqlite 5004 --frontend-origin http://localhost:5173
python start.py mariadb 5005 --frontend-origin http://localhost:5174
```

## Termux or a different computer

For a new SQLite environment, install `requirements-sqlite.txt`, which avoids the MariaDB driver, gunicorn and optional PDF dependencies:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-sqlite.txt
python start.py sqlite --venv .venv --diagnose
```

Windows: `.venv\Scripts\python.exe -m pip install -r requirements-sqlite.txt`; `--venv .venv` works on either system. MariaDB needs `requirements.txt` plus configured DB/cache. PostgreSQL: avoid full requirements' optional MySQL build dependency by using `requirements-sqlite.txt` plus compatible `psycopg[binary]`/`psycopg2-binary`, `django-sslserver`, cache client (`pymemcache`/Memcached or `django-redis`/Redis). Versions unchanged. PostgreSQL accepts either driver, never requires MySQLdb. Native Termux dependencies: `DEPLOYMENT.md`.

PostgreSQL database/users must exist beforehand. Native backup/restore and the MariaDB provisioning workflow do not yet support PostgreSQL. These settings and launcher changes remain unverified against a live PostgreSQL server.

On Termux keep runtime data in private storage, even if the source checkout is on shared storage:

```bash
python start.py sqlite --data-root "$HOME/.local/share/quiz"
```

Separate instances need separate roots; empty root creates new data, not a copy. To move SQLite, stop instance, copy complete data directory/media, select copied `--data-root`; never overwrite an active instance.

For a phone/browser on your trusted local network, bind the backend to all interfaces and trust the actual browser origin, replacing the example IP:

```bash
python start.py sqlite 0.0.0.0:5004 --frontend-origin http://192.168.1.10:5173
```

Run the frontend with `pnpm dev --host 0.0.0.0`, keeping its proxy target pointed at the backend address reachable **from the frontend server**, normally `http://127.0.0.1:5004`. Open `http://192.168.1.10:5173` on the phone. `0.0.0.0` is a bind address, not a browser address. These are development servers; production HTTPS still uses `scripts/quiz_start.sh` and `DEPLOYMENT.md`.

## Diagnose before launching

```bash
python start.py sqlite --diagnose
python start.py --diagnose
python start.py postgres --diagnose
python start.py sqlite --venv /path/to/venv --data-root /path/to/data --diagnose
```

Diagnostics list dependencies/interpreter candidates/settings without server, DB connection or setup; connectivity remains unverified. Startup selects only module-complete environments; explicit `--venv` never silently falls back.

| Symptom | Check |
| --- | --- |
| Missing Python packages | Use `--diagnose`, then install the matching requirements into the selected venv. |
| UI opens but API requests fail | Match `VITE_BACKEND_PROXY_TARGET` to the backend port and restart Vite; check any overriding `VITE_API_BASE_URL`. |
| Login does not stay signed in on HTTP | Use these development launchers; they override inherited secure-cookie settings. |
| CSRF rejection | Pass the exact browser scheme/host/port using `--frontend-origin`. |
| MariaDB/cache connection failure | Verify existing `.env` configuration and that the relevant services are running. |
| Backend `/` has no page | Use the Vite frontend URL if no built frontend bundle exists. |
| SQLite shows different/empty data | Check the printed database path and `--data-root`/`--db-path`. |
