#!/usr/bin/env python3
"""Start an HTTP development server using backend/.env database settings.

    python start.py
    python start.py --interactive
    python start.py env 5005 --diagnose
    python start.py env --frontend-origin http://localhost:5174
    python start.py sqlite 5004 --data-root /path/to/local-data
    python start.py sqlite --diagnose
    python start.py mariadb
    python start.py postgres

No mode (or 'env') selects DB_ENGINE from .env. Explicit database modes override
DB_ENGINE for this process. SQLite forwards to scripts/start_sqlite.py with its setup
options; server databases use an existing schema without setup or seeding.
Production HTTPS uses scripts/quiz_start.sh and docs/DEPLOYMENT.md instead.
"""

import argparse
import os
import sys
from pathlib import Path

from config.database import database_engine


def main():
    argv = sys.argv[1:]
    if argv in (['--interactive'], ['-i']):
        from scripts.interactive_launch import main as interactive_main
        raise SystemExit(interactive_main())
    if argv and argv[0] in {'--help', '-h'}:
        print(__doc__)
        return
    modes = {'env', 'sqlite', 'sqlite3', 'mysql', 'mariadb', 'postgres', 'postgresql'}
    mode = argv.pop(0) if argv and argv[0] in modes else 'env'
    if mode != 'env':
        os.environ['DB_ENGINE'] = mode
    # Explicit portable SQLite stays independent of server credentials in .env.
    if mode in {'sqlite', 'sqlite3'}:
        _start_sqlite(argv)

    parser = argparse.ArgumentParser(description='Use the database selected by DB_ENGINE in backend/.env.')
    parser.add_argument('address', nargs='?', default=None)
    parser.add_argument('--venv')
    parser.add_argument('--frontend-origin', help='Comma-separated browser origins including http:// or https://')
    parser.add_argument('--diagnose', action='store_true', help='Check dependencies only; no setup or server')
    parser.add_argument('--noreload', action='store_true')
    args, remaining = parser.parse_known_args(argv)
    if args.venv:
        os.environ['QUIZ_VENV'] = args.venv
    if args.frontend_origin:
        origins = [value.strip().rstrip('/') for value in args.frontend_origin.split(',')]
        if any(not value.startswith(('http://', 'https://')) for value in origins):
            parser.error('Frontend origins must include http:// or https://.')
        os.environ['QUIZ_FRONTEND_ORIGINS'] = ','.join(origins)

    from scripts import start_sqlite as runtime
    # Resolve core dependencies first so python-dotenv is available to read the
    # selector. Then check only the selected backend's driver before starting.
    if not args.diagnose:
        runtime._ensure_runtime(launcher_path=__file__)
    try:
        from dotenv import load_dotenv
    except ImportError:
        print('Cannot read backend/.env: python-dotenv is missing; database selection is unverified.')
        if not args.diagnose:
            raise SystemExit(1)
        try:
            engine = database_engine(os.environ) if os.environ.get('DB_ENGINE') else None
        except ValueError as exc:
            parser.error(str(exc))
    else:
        load_dotenv(Path(__file__).resolve().with_name('.env'))
        try:
            engine = database_engine(os.environ)
        except ValueError as exc:
            parser.error(str(exc))

    if engine == 'django.db.backends.sqlite3':
        # Generic mode respects the database filename in .env; explicit sqlite
        # mode above retains its separate portable data-root behavior.
        if os.environ.get('DB_NAME'):
            os.environ.setdefault('SQLITE_DB_PATH', os.environ['DB_NAME'])
        _start_sqlite(argv)
    if remaining:
        parser.error('unrecognized arguments: ' + ' '.join(remaining))
    if engine == 'django.db.backends.mysql':
        runtime._REQUIRED_MODULES += ('MySQLdb',)
    elif engine == 'django.db.backends.postgresql':
        runtime._REQUIRED_MODULE_GROUPS = (('psycopg', 'psycopg2'),)
    runtime._REQUIRED_MODULES += ('sslserver',)

    address = runtime._normalize_address(args.address or 'localhost:5005')
    os.environ['QUIZ_BIND_HOST'] = runtime._address_host(address)
    if args.diagnose:
        print('Database engine: ' + (engine or 'unknown (install python-dotenv)'))
        print(f'Bind address: {address}')
        print('Database/cache credentials: backend/.env (values not displayed)')
        print(f'Python: {sys.executable}')
        missing = runtime._runtime_missing()
        print('Current Python dependencies: ' + (', '.join(missing) + ' missing' if missing else 'ready'))
        for candidate in runtime._runtime_candidates():
            if not candidate.is_file() or not os.access(candidate, os.X_OK):
                continue
            try:
                missing = runtime._runtime_missing(candidate)
                print(f'Environment {candidate}: ' + (', '.join(missing) + ' missing' if missing else 'ready'))
            except (OSError, ValueError, runtime.subprocess.TimeoutExpired):
                print(f'Environment {candidate}: could not check dependencies')
        print('No database connection, setup, seeding, migration work, or server was run.')
        return

    runtime._ensure_runtime(launcher_path=__file__)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_local'
    from django.core.management import execute_from_command_line
    print(f'{engine} HTTP development at {address}; using existing schema/data.')
    print('Frontend: set VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:' + address.rsplit(':', 1)[-1])
    options = ['--noreload'] if args.noreload else []
    execute_from_command_line([sys.argv[0], 'runserver', address, *options])


def _start_sqlite(argv):
    launcher = Path(__file__).resolve().parent / 'scripts' / 'start_sqlite.py'
    os.execv(sys.executable, [sys.executable, str(launcher), *argv])


if __name__ == '__main__':
    main()
