#!/usr/bin/env python3
"""Start a self-contained local Quiz instance with SQLite and LocMemCache.

Usage::

    python scripts/start_sqlite.py
    python scripts/start_sqlite.py 5005
    python scripts/start_sqlite.py localhost:5005
    python scripts/start_sqlite.py 0.0.0.0:8000
    python scripts/start_sqlite.py --seed-pro-users
    python scripts/start_sqlite.py --seed-pro-users --force-pro-users
    python scripts/start_sqlite.py --no-prompt
    python scripts/start_sqlite.py --allow-threading
    SQLITE_DB_PATH=/tmp/quiz.sqlite3 python scripts/start_sqlite.py

ADDRESS PROMPT
--------------
When no address is passed on the command line, the launcher prompts
for one. Three input shapes are accepted:

  • Empty input       → ``localhost:5004`` (or ``SQLITE_SERVER_ADDRESS``
                        if set).
  • A bare port       → ``5005`` becomes ``localhost:5005``.
  • ``host:port``     → used as-is (e.g. ``0.0.0.0:8000``).

The prompt runs ONCE per launch, in the parent process. Django's
development auto-reloader spawns a child process with ``RUN_MAIN=true``
and re-executes this script; the parent rewrites ``sys.argv`` before
spawning so the child reads the already-resolved address as a plain
positional argument and never reaches the prompt a second time.

The prompt is skipped when stdin is not a terminal (CI, pipes,
``< /dev/null``) or when ``--no-prompt`` is passed.

WHAT THIS DOES
--------------
On every launch, in this order:

  1. Re-execs into a virtualenv if Django is not importable from the
     current interpreter.
  2. Asks for a server address when none was given on the command
     line and stdin is interactive.
  3. Creates ``backend/apps/__init__.py`` if missing.
  4. Creates a ``migrations/__init__.py`` inside every custom app
     that does not already have one.
  5. Runs ``makemigrations`` for any model-bearing app whose
     ``migrations/`` directory contains no migration files.
  6. Runs ``migrate`` with ``--fake-initial``.
  7. Synchronises the idempotent base data and capabilities seeders.
     Admin creation is skipped when any superuser already exists, so
     a custom administrator is never replaced by the built-in one.
     The ``tips`` seeder is deliberately omitted.
  8. Optionally runs ``seed_pro_users`` via ``--seed-pro-users``.

Launcher flags (all optional):

  ``--seed-pro-users``     Run ``manage.py seed_pro_users`` during
                           startup. Idempotent — reports ``unchanged``
                           for accounts that already exist.

  ``--force-pro-users``    Also pass ``--reset-passwords`` to
                           ``seed_pro_users``. Implies
                           ``--seed-pro-users``.

  ``--no-setup``           Skip steps 3–7 and go straight to the
                           runserver.

  ``--no-prompt``          Do not prompt for the server address; use
                           the default silently. Implied when stdin
                           is not a terminal.

  ``--allow-threading``    Allow Django's development server to handle
                           concurrent requests. SQLite mode defaults to
                           ``--nothreading`` because several workflows
                           require row-lock semantics SQLite cannot
                           provide. Use this only for trusted, light
                           single-user development.

ENVIRONMENT KNOBS
-----------------
    SQLITE_DB_PATH          Path to the SQLite file.
                            Default: ``backend/SQLite/db.sqlite3``.
    SQLITE_ROOT             Root for the default database, media,
                            uploads, exports, and backups.
                            Default: ``backend/SQLite``.
    SQLITE_SERVER_ADDRESS   Default address when nothing is passed on
                            the command line or at the prompt.
                            Default: ``localhost:5004``.
    SQLITE_ALLOWED_HOSTS    Optional comma-separated host allow-list.
                            The selected bind host is added automatically.
    SQLITE_CORS_ORIGINS     Optional comma-separated browser origins.
                            ``*`` enables CORS allow-all mode.
    SQLITE_CSRF_TRUSTED_ORIGINS
                            Optional explicit origins including schemes,
                            e.g. ``http://192.168.1.10:5173``.
    SQLITE_AUTO_SETUP       Set to ``False``/``0``/``no``/``off`` to
                            behave as if ``--no-setup`` was passed.
    SQLITE_ALLOW_THREADING  Truthy equivalent of ``--allow-threading``.
    QUIZ_VENV               Path to a virtualenv to re-exec into when
                            the current interpreter cannot import
                            Django.

APP REGISTRY
------------
``CUSTOM_APPS``, ``MODEL_APPS``, and ``APP_INIT_CONTENT`` are imported
from ``apps.core.management._app_registry`` so this launcher and
``manage.py bootstrap`` share one source of truth. See that module's
docstring for the full rationale.

The import below runs BEFORE ``django.setup()`` — that is safe because
``_app_registry`` imports nothing from Django. A top-level Django
import there would raise ``AppRegistryNotReady``.
"""

import os
import sys
import json
import subprocess
from importlib.util import find_spec
from pathlib import Path

# Resolve backend paths independently of the current directory. Direct script
# execution puts scripts/ on sys.path; app imports still need backend/.
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from apps.core.management._app_registry import (  # noqa: E402
    APP_INIT_CONTENT,
    CUSTOM_APPS,
    MODEL_APPS,
)


_REQUIRED_MODULES = (
    'django',
    'jazzmin',
    'rest_framework',
    'corsheaders',
    'django_filters',
    # These are imported while Django resolves the URL configuration,
    # before the corresponding endpoints are called.
    'pandas',
    'openpyxl',
    'PIL',
    'dotenv',
)

# Each group requires at least one installed module (e.g. PostgreSQL drivers).
_REQUIRED_MODULE_GROUPS = ()


_LAUNCHER_FLAGS = {
    '--diagnose': 'diagnose',
    '--seed-pro-users': 'seed_pro_users',
    '--force-pro-users': 'force_pro_users',
    '--no-setup': 'no_setup',
    '--no-prompt': 'no_prompt',
    '--allow-threading': 'allow_threading',
}

_VALUE_FLAGS = {
    '--venv': 'QUIZ_VENV',
    '--db-path': 'SQLITE_DB_PATH',
    '--data-root': 'SQLITE_ROOT',
    '--frontend-origin': 'SQLITE_FRONTEND_ORIGINS',
}

_DEFAULT_HOST = 'localhost'
_DEFAULT_PORT = '5004'

# Django's autoreload module sets this environment variable in the
# child process it spawns for the actual worker. We use the same
# convention so our own "is this the reloader child?" check is
# indistinguishable from Django's.
_RELOADER_ENV_VAR = 'RUN_MAIN'


def _split_argv(argv):
    """
    Return (flags, positional_args).

    Every token matching a key in ``_LAUNCHER_FLAGS`` is a boolean
    launcher flag; everything else is collected in order into
    ``positional_args``, which the runserver will interpret as the
    bind address.
    """
    flags = {value: False for value in _LAUNCHER_FLAGS.values()}
    positional = []

    tokens = iter(argv)
    for token in tokens:
        option, separator, inline = token.partition('=')
        if option in _VALUE_FLAGS:
            value = inline if separator else next(tokens, '')
            if not value or value.startswith('--'):
                raise SystemExit(f'{option} requires a value. See --help.')
            os.environ[_VALUE_FLAGS[option]] = value
            continue
        if token in _LAUNCHER_FLAGS:
            flags[_LAUNCHER_FLAGS[token]] = True
        elif token in ('--help', '-h'):
            _print_help()
            raise SystemExit(0)
        else:
            positional.append(token)

    if flags['force_pro_users']:
        flags['seed_pro_users'] = True

    return flags, positional


def _print_help():
    print(__doc__)
    print('Additional startup options:')
    print('  --diagnose                   Report configuration/dependencies only; no setup/server.')
    print('  --venv PATH                  Select a virtualenv or Python executable.')
    print('  --db-path PATH               Select the SQLite database file.')
    print('  --data-root PATH             Isolate database/media/backups under this directory.')
    print('  --frontend-origin URL[,URL]  Trust these browser dev-server origins.')


def _runtime_candidates():
    backend_dir = _BACKEND_DIR
    project_dir = backend_dir.parent
    candidates = []

    def add_venv(venv_path):
        """Add both POSIX and Windows interpreter layouts."""
        root = Path(venv_path).expanduser()
        if root.is_file():
            candidates.append(root)
            return
        candidates.extend([
            root / 'bin' / 'python',
            root / 'bin' / 'python3',
            root / 'Scripts' / 'python.exe',
        ])

    if os.environ.get('QUIZ_VENV'):
        add_venv(os.environ['QUIZ_VENV'])
    # docs/DEPLOYMENT.md creates .venv while the shell is in backend/. Keep
    # repository-root layouts as fallbacks for existing installations.
    add_venv(backend_dir / 'venv')
    add_venv(backend_dir / '.venv')
    add_venv(project_dir / 'venv')
    add_venv(project_dir / '.venv')
    add_venv(Path.home() / 'Environments' / 'quizenv')

    return list(dict.fromkeys(candidates))


def _runtime_missing(interpreter=None):
    if interpreter is None:
        missing = [name for name in _REQUIRED_MODULES if find_spec(name) is None]
        missing.extend(' or '.join(group) for group in _REQUIRED_MODULE_GROUPS
                       if not any(find_spec(name) is not None for name in group))
        return missing
    probe = subprocess.run([
        str(interpreter), '-c',
        'import importlib.util,json; print(json.dumps([n for n in '
        + repr(_REQUIRED_MODULES)
        + ' if importlib.util.find_spec(n) is None] + [" or ".join(g) for g in '
        + repr(_REQUIRED_MODULE_GROUPS)
        + ' if not any(importlib.util.find_spec(n) is not None for n in g)]))',
    ], capture_output=True, text=True, timeout=10)
    if probe.returncode:
        raise ValueError('Interpreter could not check dependencies')
    missing = json.loads(probe.stdout)
    if not isinstance(missing, list):
        raise ValueError('Unexpected dependency check result')
    return missing


def _ensure_runtime(launcher_path=None):
    """Choose a complete environment before re-exec; never bounce between venvs."""
    missing = _runtime_missing()
    if not missing and not os.environ.get('QUIZ_VENV'):
        return
    current = Path(sys.executable).absolute()
    candidates = _runtime_candidates()
    if os.environ.get('QUIZ_VENV'):
        root = Path(os.environ['QUIZ_VENV']).expanduser()
        candidates = [root] if root.is_file() else [
            root / 'bin' / 'python', root / 'bin' / 'python3', root / 'Scripts' / 'python.exe',
        ]
    for candidate in candidates:
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        if candidate.absolute() == current:
            if not missing:
                return
            continue
        try:
            candidate_missing = _runtime_missing(candidate)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            continue
        if candidate_missing:
            continue
        os.execv(
            str(candidate),
            [str(candidate), str(Path(launcher_path or __file__).resolve()), *sys.argv[1:]],
        )

    raise SystemExit(
        'No complete Python environment found'
        + (': missing ' + ', '.join(missing) if missing else ' in the selected QUIZ_VENV')
        + '. Run --diagnose; install the matching requirements in your chosen environment.'
    )


def _diagnose(runserver_args):
    """Read-only checks; deliberately avoid importing Django settings/setup."""
    print(f'Python: {sys.executable}')
    missing = _runtime_missing()
    print('Current Python dependencies: ' + (', '.join(missing) + ' missing' if missing else 'ready'))
    for candidate in _runtime_candidates():
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        try:
            candidate_missing = _runtime_missing(candidate)
            status = ', '.join(candidate_missing) + ' missing' if candidate_missing else 'ready'
        except (OSError, ValueError, subprocess.TimeoutExpired):
            status = 'could not check dependencies'
        print(f'Environment {candidate}: {status}')
    root = Path(os.environ.get('SQLITE_ROOT', str(_BACKEND_DIR / 'SQLite'))).expanduser()
    if not root.is_absolute():
        root = _BACKEND_DIR / root
    database = Path(os.environ.get('SQLITE_DB_PATH', str(root / 'db.sqlite3'))).expanduser()
    if not database.is_absolute():
        database = _BACKEND_DIR / database
    print(f'Database: {database} ({"exists" if database.is_file() else "not created"})')
    print(f'Data directory: {root}')
    print(f'Bind address: {runserver_args[0]}')
    print('Transport: HTTP; inherited production HTTPS cookie flags are ignored.')
    print(f'Frontend origins: {os.environ.get("SQLITE_FRONTEND_ORIGINS", "defaults from SQLite settings")}')
    print('No database setup, seeding, migration work, or server was run.')


def _enabled(name, default=True):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {'0', 'false', 'no', 'off'}


def _normalize_address(raw):
    """
    Turn a user-supplied address into a ``host:port`` string.

    Accepted shapes:

      • ``""``          → caller's default (handled by the caller).
      • ``"5005"``      → ``"localhost:5005"``.
      • ``":5005"``     → ``"localhost:5005"`` (empty host).
      • ``"host:5005"`` → returned unchanged.

    Anything not recognised as a port number when there is no colon is
    returned as-is and left for Django to reject with its own message.
    """
    value = raw.strip()
    if not value:
        return ''

    def checked_port(port):
        number = int(port)
        if not 1 <= number <= 65535:
            raise SystemExit(f'Invalid server port: {port}. Expected 1-65535.')
        return str(number)

    if value.isdigit():
        return f'{_DEFAULT_HOST}:{checked_port(value)}'

    if value.startswith(':'):
        tail = value[1:]
        if tail.isdigit():
            return f'{_DEFAULT_HOST}:{checked_port(tail)}'

    # Validate the port in ordinary host:port and bracketed IPv6 forms.
    if value.startswith('[') and ']:' in value:
        host, port = value.rsplit(':', 1)
        if port.isdigit():
            return f'{host}:{checked_port(port)}'
    elif value.count(':') == 1:
        host, port = value.rsplit(':', 1)
        if host and port.isdigit():
            return f'{host}:{checked_port(port)}'

    return value


def _resolve_server_address(positional_args, flags):
    """
    Return the list of arguments the runserver should receive after
    ``runserver``.

    Order of precedence:

      1. Anything passed on the command line, normalised through
         ``_normalize_address``.
      2. Interactive prompt, when stdin is a terminal and
         ``--no-prompt`` was not given.
      3. ``SQLITE_SERVER_ADDRESS`` environment variable.
      4. ``localhost:5004``.

    Only called from the parent process — see ``main`` for why.
    """
    configured_default = os.environ.get(
        'SQLITE_SERVER_ADDRESS', f'{_DEFAULT_HOST}:{_DEFAULT_PORT}',
    )
    default = _normalize_address(configured_default)
    if not default:
        default = f'{_DEFAULT_HOST}:{_DEFAULT_PORT}'

    if positional_args:
        # An option-only invocation (for example ``--noreload``) still
        # receives our port instead of falling back to Django's :8000.
        if positional_args[0].startswith('-'):
            return [default, *positional_args]
        head = _normalize_address(positional_args[0]) or default
        return [head, *positional_args[1:]]

    if flags['no_prompt'] or not sys.stdin.isatty():
        return [default]

    print('')
    print('Server address')
    print(f'  Enter             → default [{default}]')
    print(f'  A port number     → {_DEFAULT_HOST}:<port>   (e.g. 5005)')
    print('  host:port         → used as-is    (e.g. 0.0.0.0:8000)')
    print('')

    try:
        answer = input('> ').strip()
    except (EOFError, KeyboardInterrupt):
        print('')
        answer = ''

    print('')
    normalized = _normalize_address(answer)
    return [normalized if normalized else default]


def _address_host(address):
    """Extract the host portion of a normalized runserver address."""
    value = str(address).strip()
    if value.startswith('[') and ']:' in value:
        return value[1:value.rfind(']')]
    if ':' in value:
        return value.rsplit(':', 1)[0]
    return value


def _configure_sqlite_network(runserver_args):
    """Pass the selected bind host to the SQLite settings overlay."""
    if not runserver_args:
        return
    host = _address_host(runserver_args[0])
    if host:
        os.environ['SQLITE_BIND_HOST'] = host
    if (
        host in {'0.0.0.0', '::'}
        and os.environ.get('SQLITE_NETWORK_WARNING_SHOWN') != '1'
    ):
        print(
            'WARNING: SQLite development server is listening on all interfaces.\n'
            '         Use it only on a trusted LAN; do not expose it to the internet.'
        )
        os.environ['SQLITE_NETWORK_WARNING_SHOWN'] = '1'


def _configure_threading(runserver_args, flags):
    """Serialize requests unless concurrent SQLite use was explicitly requested."""
    allow_threading = flags['allow_threading'] or _enabled(
        'SQLITE_ALLOW_THREADING', default=False,
    )
    if flags['allow_threading']:
        os.environ['SQLITE_ALLOW_THREADING'] = '1'
    if not allow_threading and '--nothreading' not in runserver_args:
        runserver_args.append('--nothreading')


def _ensure_package_files(backend_dir):
    """
    Create ``apps/__init__.py`` and one ``migrations/__init__.py`` per
    custom app if any of them are missing.

    MUST run before ``django.setup()``.
    """
    apps_dir = backend_dir / 'apps'

    apps_init = apps_dir / '__init__.py'
    if not apps_init.exists():
        apps_init.write_text(APP_INIT_CONTENT, encoding='utf-8')
        print(f'[setup] created {apps_init.relative_to(backend_dir)}')

    for app in CUSTOM_APPS:
        app_dir = apps_dir / app
        if not app_dir.is_dir():
            continue
        mig_dir = app_dir / 'migrations'
        mig_dir.mkdir(exist_ok=True)
        mig_init = mig_dir / '__init__.py'
        if not mig_init.exists():
            mig_init.write_text('', encoding='utf-8')
            print(f'[setup] created {mig_init.relative_to(backend_dir)}')


def _app_needs_makemigrations(backend_dir, app):
    mig_dir = backend_dir / 'apps' / app / 'migrations'
    if not mig_dir.is_dir():
        return True
    for entry in mig_dir.iterdir():
        if entry.is_file() and entry.suffix == '.py' and entry.name != '__init__.py':
            return False
    return True


def main():
    flags, positional = _split_argv(sys.argv[1:])
    if flags['diagnose']:
        flags['no_prompt'] = True
        _diagnose(_resolve_server_address(positional, flags))
        return

    # Persist launcher-only choices through Django's autoreloader, which
    # re-executes this script after the custom flags have been removed from
    # sys.argv. This keeps --no-setup and --allow-threading effective in the
    # worker child without leaking unknown options into ``runserver``.
    if flags['no_setup']:
        os.environ['SQLITE_AUTO_SETUP'] = '0'
    if flags['allow_threading']:
        os.environ['SQLITE_ALLOW_THREADING'] = '1'

    _ensure_runtime()

    if os.environ.get(_RELOADER_ENV_VAR) == 'true':
        # Child process. Do not prompt, do not run setup.
        runserver_args = positional or [
            os.environ.get(
                'SQLITE_SERVER_ADDRESS',
                f'{_DEFAULT_HOST}:{_DEFAULT_PORT}',
            )
        ]
    else:
        # Parent process. Resolve the address once, then rewrite
        # sys.argv so the child inherits it.
        runserver_args = _resolve_server_address(positional, flags)
        _configure_threading(runserver_args, flags)
        _configure_sqlite_network(runserver_args)
        sys.argv = [sys.argv[0], *runserver_args]

    # The reloader child receives the already-resolved arguments. Reapply
    # only environment-derived configuration that is harmless and idempotent.
    if os.environ.get(_RELOADER_ENV_VAR) == 'true':
        _configure_threading(runserver_args, flags)
        _configure_sqlite_network(runserver_args)

    backend_dir = _BACKEND_DIR

    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_sqlite'

    auto_setup = (
        _enabled('SQLITE_AUTO_SETUP')
        and not flags['no_setup']
    )

    if auto_setup:
        _ensure_package_files(backend_dir)

    try:
        import django
        from django.conf import settings
        from django.core.management import call_command, execute_from_command_line
    except ImportError as exc:
        raise SystemExit(
            "Django is unavailable. Activate the Quiz virtual environment "
            "and run this launcher again."
        ) from exc

    django.setup()

    database_path = settings.DATABASES['default']['NAME']
    print(f'Using SQLite database: {database_path}')
    print('Using cache: LocMemCache (single process)')
    if os.environ.get(_RELOADER_ENV_VAR) != 'true':
        print('Frontend: set VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:'
              + runserver_args[0].rsplit(':', 1)[-1])

    # Setup steps run only in the parent. The child re-exec reached
    # this point with RUN_MAIN=true and would otherwise re-run every
    # step on every code save.
    is_parent = os.environ.get(_RELOADER_ENV_VAR) != 'true'

    if is_parent and auto_setup:
        needs = [app for app in MODEL_APPS
                 if _app_needs_makemigrations(backend_dir, app)]
        if needs:
            print(f'[setup] generating initial migrations for: {", ".join(needs)}')
            call_command('makemigrations', *needs)

        print('Applying pending migrations...')
        call_command('migrate', interactive=False, fake_initial=True)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            has_superuser = User.objects.filter(is_superuser=True).exists()
        except Exception as exc:
            print('')
            print('ERROR: could not query the users table.')
            print(f'  {type(exc).__name__}: {exc}')
            print('')
            print('Check that:')
            print('  1. backend/apps/__init__.py exists (empty file).')
            print('  2. Each custom app has a migrations/ directory')
            print('     with an empty __init__.py.')
            print('  3. `manage.py showmigrations users` lists at least')
            print('     the 0001_initial migration.')
            print('')
            print('If a partial database was created by an earlier run,')
            print('delete it and retry:  rm -f backend/SQLite/db.sqlite3')
            raise SystemExit(1)

        if not has_superuser:
            print('No superuser found — creating the default admin...')
            print(f'  (skipping tips; run `manage.py seed --only tips` '
                  f'later if needed)')
            print('(The admin password will be printed to stderr below.)')
        else:
            print('Superuser already present — preserving existing admin accounts.')

        # Both commands are idempotent. Run them on every setup so a
        # partially interrupted first launch repairs missing categories,
        # runtime settings, and capability rows. ``skip_admin`` prevents
        # seed_data from adding its built-in admin when a custom superuser
        # already exists.
        print('[setup] synchronising base data and capabilities...')
        call_command('seed_data', skip_admin=has_superuser)
        call_command('seed_capabilities')

        if not User.objects.filter(is_superuser=True, is_active=True).exists():
            print(
                'WARNING: no active superuser exists. Reactivate an existing '
                'superuser or create one with `manage.py createsuperuser`.'
            )
        print('Seeding complete.')

        if flags['seed_pro_users']:
            kwargs = {}
            if flags['force_pro_users']:
                kwargs['reset_passwords'] = True
                print('[setup] running seed_pro_users --reset-passwords...')
            else:
                print('[setup] running seed_pro_users...')
            call_command('seed_pro_users', **kwargs)

    elif is_parent and flags['seed_pro_users']:
        kwargs = {}
        if flags['force_pro_users']:
            kwargs['reset_passwords'] = True
        print('[setup] running seed_pro_users (setup otherwise skipped)...')
        call_command('seed_pro_users', **kwargs)

    execute_from_command_line([
        sys.argv[0],
        'runserver',
        *runserver_args,
    ])


if __name__ == '__main__':
    main()
