#!/usr/bin/env python3
"""Interactive development launch; existing data only, no automatic setup."""

import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import time


BACKEND = Path(__file__).resolve().parent
FRONTEND = BACKEND.parent / 'frontend'


def _choice(title, choices, default):
    print(f'\n{title}')
    for key, label in choices.items():
        print(f'  {key}. {label}')
    while True:
        value = input(f'Choose [{default}]: ').strip() or default
        if value == '0':
            raise KeyboardInterrupt
        if value in choices:
            return value
        print('Enter one of the listed numbers, or 0 to cancel.')


def _port(label, default):
    while True:
        raw = input(f'{label} [{default}]: ').strip() or str(default)
        if raw.isascii() and raw.isdecimal() and 1 <= int(raw) <= 65535:
            return int(raw)
        print('Enter a port from 1 to 65535.')


def _command(argv):
    return subprocess.list2cmdline(argv) if os.name == 'nt' else shlex.join(argv)


def _plan():
    mode_key = _choice('Database (credentials stay in backend/.env)', {
        '1': 'Use DB_ENGINE from .env',
        '2': 'Separate local SQLite',
        '3': 'PostgreSQL from .env',
        '4': 'MariaDB/MySQL from .env',
        '0': 'Cancel',
    }, '1')
    mode = {'1': 'env', '2': 'sqlite', '3': 'postgres', '4': 'mariadb'}[mode_key]
    action = _choice('Action', {
        '1': 'Start backend + frontend',
        '2': 'Start backend only',
        '3': 'Diagnose backend dependencies (read-only)',
        '4': 'Preview backend + frontend commands',
        '0': 'Cancel',
    }, '1')
    backend_port = 5004 if mode == 'sqlite' else 5005
    frontend_port = 5173
    host = 'localhost'
    browser_host = 'localhost'
    venv = data_root = ''
    print(f'\nDefaults: backend {host}:{backend_port}, frontend :{frontend_port}.')
    if input('Customize ports, network or paths? [y/N]: ').strip().lower() in {'y', 'yes'}:
        backend_port = _port('Backend port', backend_port)
        frontend_port = _port('Frontend port', frontend_port)
        while frontend_port == backend_port:
            print('Frontend and backend need different ports.')
            frontend_port = _port('Frontend port', 5173)
        network = _choice('Network access', {
            '1': 'This computer only', '2': 'Trusted local network', '0': 'Cancel',
        }, '1')
        if network == '2':
            host = '0.0.0.0'
            while True:
                browser_host = input('This computer\'s LAN IP or hostname (for the browser): ').strip()
                if (browser_host and browser_host not in {'0.0.0.0', '::'}
                        and all(char.isascii() and (char.isalnum() or char in '.-')
                                for char in browser_host)):
                    break
                print('Enter an IP/hostname, such as 192.168.1.10, without scheme or port.')
        venv = input('Python venv directory/interpreter [auto-detect]: ').strip()
        if mode == 'sqlite':
            data_root = input('SQLite data directory [backend/SQLite]: ').strip()

    origin = f'http://{browser_host}:{frontend_port}'
    backend = [sys.executable, str(BACKEND / 'start.py'), mode,
               f'{host}:{backend_port}', '--frontend-origin', origin]
    if venv:
        backend.extend(['--venv', str(Path(venv).expanduser())])
    if data_root:
        backend.extend(['--data-root', str(Path(data_root).expanduser())])
    backend.append('--diagnose' if action == '3' else '--noreload')
    frontend = ['pnpm', 'dev', '--host', host, '--port', str(frontend_port), '--strictPort']
    env = os.environ.copy()
    env['SQLITE_AUTO_SETUP'] = '0'
    env['VITE_BACKEND_PROXY_TARGET'] = f'http://127.0.0.1:{backend_port}'
    # Use Vite's proxy even if an inherited frontend env selects another API host.
    env['VITE_API_BASE_URL'] = '/api/v1'
    return action, backend, frontend, env, origin


def _stop(process):
    if os.name != 'nt':
        # pnpm/Vite may leave descendants after their wrapper exits.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    elif process.poll() is None:
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)
        except OSError:
            process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != 'nt':
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            try:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               check=False, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
        process.wait(timeout=5)


def _run(backend, frontend, env):
    if frontend:
        pnpm = shutil.which('pnpm')
        if not pnpm or not (FRONTEND / 'node_modules' / 'vite').is_dir():
            print('Frontend needs pnpm and installed dependencies. Choose backend-only or diagnose.')
            return 1
        frontend = [pnpm, *frontend[1:]]
    options = ({'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt'
               else {'start_new_session': True})
    processes = []
    try:
        processes.append(subprocess.Popen(backend, cwd=BACKEND, env=env, **options))
        if frontend:
            processes.append(subprocess.Popen(frontend, cwd=FRONTEND, env=env, **options))
        print('\nCtrl+C stops the launched processes.', flush=True)
        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    return code
            time.sleep(0.2)
    except KeyboardInterrupt:
        return 130
    except OSError as exc:
        print(f'Could not launch: {exc}')
        return 1
    finally:
        for process in reversed(processes):
            _stop(process)


def main():
    try:
        print('Quiz development launcher — existing databases; no setup or seeding.\n0 cancels a menu.')
        action, backend, frontend, env, origin = _plan()
        print(f'\nBackend: {_command(backend)}')
        print('Backend environment: SQLITE_AUTO_SETUP=0')
        if action in {'1', '4'}:
            print(f'Frontend (from {FRONTEND}): {_command(frontend)}')
            print(f'Frontend environment: VITE_BACKEND_PROXY_TARGET={env["VITE_BACKEND_PROXY_TARGET"]}; '
                  'VITE_API_BASE_URL=/api/v1')
            print(f'Open {origin} once Vite reports ready.')
        if action == '4':
            return 0
        sys.stdout.flush()
        if action == '3':
            return subprocess.call(backend, cwd=BACKEND, env=env)
        return _run(backend, frontend if action == '1' else None, env)
    except (EOFError, KeyboardInterrupt):
        print('\nLaunch cancelled.')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
