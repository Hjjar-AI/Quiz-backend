#!/usr/bin/env python3
"""Read-only Tkinter startup tutorial. All commands/results are examples.

Run from backend/: python scripts/startup_tutorial.py
No app imports, file access, configuration changes, process launches, database
connections or network requests. Copy buttons write only to your clipboard.
Learning progress exists only in this window; Alt+Left / Alt+Right change steps.
"""

from dataclasses import dataclass
import ipaddress
import ntpath
import os
import posixpath
import re
import shlex
import sys


@dataclass(frozen=True)
class Scenario:
    title: str
    mode: str
    port: int
    summary: str
    preparation: str
    expected: str
    root: str = ''
    lan: bool = False
    dual: bool = False


SCENARIOS = {
    'sqlite': Scenario(
        'SQLite on this computer', 'sqlite', 5004,
        'Use a local SQLite database with isolated media, cache and cookies.',
        'An existing SQLite database/schema and the Python packages from '
        'requirements-sqlite.txt are needed. The example skips setup/seeding. '
        'A new empty directory is a new instance, not a copy of your current data.',
        'The backend reports the selected SQLite path. Open the frontend URL, '
        'not the backend root, to use the development UI.'),
    'env': Scenario(
        'Use the database selected in .env', 'env', 5005,
        'DB_ENGINE in backend/.env chooses the database; process environment '
        'overrides .env. Missing DB_ENGINE defaults to MariaDB.',
        'The chosen database/schema, Python driver and configured cache service '
        'must already exist. SQLite uses DB_NAME; server databases use their '
        'DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT. No credentials are read here.',
        'The actual launcher resolves the engine. This tutorial deliberately '
        'does not inspect your .env, so its examples cannot confirm your settings.'),
    'postgres': Scenario(
        'Existing PostgreSQL', 'postgres', 5005,
        'Select PostgreSQL for one run; database credentials stay in .env.',
        'PostgreSQL needs an existing database/user/schema and a compatible '
        'psycopg or psycopg2 driver. DB_PORT normally uses 5432; remove a stale '
        'MariaDB port when switching. Configure the cache separately.',
        'Configuration support exists; live PostgreSQL workflows remain pending '
        'verification. Native PostgreSQL backup/restore/provisioning is not supported.'),
    'mariadb': Scenario(
        'Existing MariaDB / MySQL', 'mariadb', 5005,
        'Use an existing server database while keeping credentials in .env.',
        'MariaDB/MySQL needs its service, database/user/schema, MySQLdb driver '
        'and configured cache. Database port 3306 differs from the HTTP app port '
        '5005. The development launcher does not provision the database.',
        'The backend uses existing server data. The browser talks to the '
        'frontend; the frontend proxy forwards API and media requests.'),
    'lan': Scenario(
        'Phone or browser on a trusted LAN', 'sqlite', 5004,
        'Bind development servers to all interfaces and use the computer\'s '
        'actual LAN address in the browser origin.',
        'Use the computer\'s LAN IP/hostname, not the phone\'s address. '
        '0.0.0.0 means listen on all interfaces; it is not a browser destination. '
        'The proxy still reaches the backend locally on 127.0.0.1.',
        'On the phone, open the LAN frontend URL. The backend must trust that '
        'exact scheme/host/port for CSRF. Keep these development servers on a trusted LAN.',
        lan=True),
    'dual': Scenario(
        'Two separate SQLite instances', 'sqlite', 5004,
        'Use separate data directories, backend ports and frontend ports for '
        'two independent instances.',
        'Each directory must already contain its own initialized database. '
        'Different ports alone do not isolate cookies or data. Distinct SQLite '
        'databases get distinct cookies; each frontend needs its own proxy target.',
        'Instance A and B have separate browser URLs and data. An empty second '
        'database does not mean the first instance lost data.',
        root='SQLite/instance-a', dual=True),
    'termux': Scenario(
        'Termux or portable SQLite data', 'sqlite', 5004,
        'Keep runtime data in private storage when source code is on shared storage.',
        'Use a compatible Python environment and existing initialized SQLite data. '
        'The displayed ~ path is illustrative and expands on the machine running '
        'the real launcher. This desktop tutorial needs Tk/display support; '
        'plain Termux can use the terminal launcher instead.',
        'The launcher should report the intended private data directory. '
        'Do not copy or overwrite an active database; stop the real instance '
        'before moving its complete data/media directory.',
        root='~/.local/share/quiz'),
}

START_METHODS = ('Guided launcher (recommended)', 'Separate terminals (advanced)')
SHELLS = ('POSIX shell / Linux / macOS / Termux', 'Windows PowerShell')

PROBLEMS = {
    'Missing Python packages': (
        'Example: "rest_framework, dotenv missing".',
        'Use the matching requirements in the intended Python environment. '
        'Then run dependency diagnostics with that venv. Diagnostics do not '
        'establish database/cache connectivity.'),
    'Frontend cannot reach API': (
        'Example: the UI loads, but API requests fail.',
        'Match VITE_BACKEND_PROXY_TARGET to the backend HTTP port and restart '
        'Vite. Keep VITE_API_BASE_URL=/api/v1 so requests use the proxy. '
        'The proxy target is reached from the frontend server, not the phone.'),
    'Port already occupied': (
        'Example: "Port 5173 is already in use".',
        'Choose another frontend port and update the backend frontend-origin '
        'to match. A backend port change also requires a matching proxy target.'),
    'Login or CSRF failure': (
        'Example: a CSRF rejection after changing host or port.',
        'Use the exact browser scheme/host/port as frontend-origin. Use the '
        'development launchers for HTTP cookie settings. Existing client/backend '
        'login CSRF implementations must be compatible.'),
    'Different or empty SQLite data': (
        'Example: the app shows a different question bank.',
        'Compare the real launcher\'s printed database path/data root with the '
        'intended instance. A different directory selects different data. '
        'This tutorial does not inspect or initialize either database.'),
    'Database or cache unavailable': (
        'Example: backend dependencies pass, but startup cannot connect.',
        'Check the chosen engine, database port, credentials and running '
        'database/cache services on the real machine. A dependency-only '
        'diagnostic cannot prove these services are reachable.'),
}


def command_text(arguments, shell=None):
    """Format an example; never execute it."""
    if shell == 'powershell' or (shell is None and sys.platform == 'win32'):
        # PowerShell single quotes preserve literal paths, including apostrophes.
        return ' '.join(value if re.fullmatch(r'[A-Za-z0-9_./:=+-]+', value)
                        else "'" + value.replace("'", "''") + "'" for value in arguments)
    return shlex.join(arguments)


def examples(key, backend_port, frontend_port, browser_host, root, venv):
    scenario = SCENARIOS[key]
    ports = []
    for raw in (backend_port, frontend_port):
        if not str(raw).isascii() or not str(raw).isdecimal() or not 1 <= int(raw) <= 65535:
            raise ValueError('Use whole-number ports from 1 to 65535.')
        ports.append(int(raw))
    backend_port, frontend_port = ports
    if backend_port == frontend_port:
        raise ValueError('Frontend and backend ports must differ.')
    host = browser_host.strip() if scenario.lan else 'localhost'
    if scenario.lan:
        try:
            valid = not ipaddress.ip_address(host).is_unspecified and ':' not in host
        except ValueError:
            valid = bool(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?', host))
        if not valid:
            raise ValueError('Use a LAN IPv4 address or hostname, without scheme or port.')
    bind = '0.0.0.0' if scenario.lan else 'localhost'
    if scenario.dual and (max(ports) == 65535 or len(set(ports + [p + 1 for p in ports])) != 4):
        raise ValueError('Two instances need four distinct valid ports (each second port is +1).')
    if scenario.dual and posixpath.normpath(root.strip().replace('\\', '/')) == 'SQLite/instance-b':
        raise ValueError('Instance A needs a directory different from SQLite/instance-b.')

    blocks = []
    for index in range(2 if scenario.dual else 1):
        bp, fp = backend_port + index, frontend_port + index
        data_root = 'SQLite/instance-b' if index else root.strip()
        origin = f'http://{host}:{fp}'
        args = ['python', 'start.py', scenario.mode, f'{bind}:{bp}', '--frontend-origin', origin]
        if data_root and scenario.mode == 'sqlite':
            args.extend(['--data-root', data_root])
        if venv.strip():
            args.extend(['--venv', venv.strip()])
        diagnostic = command_text([*args, '--diagnose'])
        if scenario.mode == 'sqlite':
            args.append('--no-setup')
        args.append('--noreload')
        blocks.append(
            f'INSTANCE {"AB"[index]} — EXAMPLES ONLY\n'
            f'Backend terminal: backend/\n'
            f'Backend process environment: SQLITE_AUTO_SETUP=0\n'
            f'Dependency diagnosis: {diagnostic}\n'
            f'Backend example: {command_text(args)}\n\n'
            f'Frontend terminal: frontend/\n'
            f'Frontend process environment:\n'
            f'  VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:{bp}\n'
            f'  VITE_API_BASE_URL=/api/v1\n'
            f'Frontend example: pnpm dev --host {bind} --port {fp} --strictPort\n'
            f'Browser URL: {origin}')
    return '\n\n'.join(blocks)


@dataclass(frozen=True)
class Lesson:
    title: str
    action: str
    where: str
    command: str
    expected: str
    hint: str = ''
    details: str = ''


def shell_environment(values, command, shell):
    """Generate pasteable process settings without changing the environment."""
    if shell == 'powershell':
        return '\n'.join(f"$env:{key} = '{value.replace(chr(39), chr(39) * 2)}'"
                         for key, value in values.items()) + '\n' + command
    return ' '.join(f'{key}={shlex.quote(value)}' for key, value in values.items()) + ' ' + command


def lesson_plan(key, method, backend_port, frontend_port, browser_host, data_root,
                venv, project_dir, shell):
    """Build ordered lessons. No application imports, probes or execution."""
    if method not in ('guided', 'manual') or shell not in ('posix', 'powershell'):
        raise ValueError('Choose a supported startup method and terminal shell.')
    project_dir = project_dir.strip()
    if not project_dir:
        raise ValueError('Enter the backend folder in Advanced options.')
    for value in (project_dir, data_root, venv, browser_host):
        if any(ord(character) < 32 for character in value):
            raise ValueError('Paths and host names must be single-line values.')
    # Preserve the existing scenario/port/path validation contract.
    examples(key, backend_port, frontend_port, browser_host, data_root, venv)
    scenario = SCENARIOS[key]
    bp, fp = int(backend_port), int(frontend_port)
    host = browser_host.strip() if scenario.lan else 'localhost'
    bind = '0.0.0.0' if scenario.lan else 'localhost'
    path_module = ntpath if shell == 'powershell' else posixpath
    frontend_dir = path_module.join(path_module.dirname(project_dir.rstrip('/\\')), 'frontend')
    cd_backend = command_text(['cd', project_dir], shell)
    cd_frontend = command_text(['cd', frontend_dir], shell)
    origin = f'http://{host}:{fp}'
    backend_args = ['python', 'start.py', scenario.mode, f'{bind}:{bp}', '--frontend-origin', origin]
    if data_root.strip() and scenario.mode == 'sqlite':
        backend_args += ['--data-root', data_root.strip()]
    if venv.strip():
        backend_args += ['--venv', venv.strip()]
    diagnostic = cd_backend + '\n' + command_text([*backend_args, '--diagnose'], shell)
    requirements = 'requirements-sqlite.txt' if scenario.mode == 'sqlite' else 'requirements.txt'
    activate = ('. .venv/bin/activate' if shell == 'posix'
                else '& .\\.venv\\Scripts\\Activate.ps1')
    install_help = (f'Only if your Python environment is missing:\n{cd_backend}\n'
                    f'python -m venv .venv\n{activate}\n'
                    f'python -m pip install -r {requirements}\n\n'
                    f'Only if frontend packages are missing:\n{cd_frontend}\npnpm install\n\n'
                    'Install Python, Node and pnpm using the instructions for your OS. '
                    'If .env mode selects SQLite, use requirements-sqlite.txt instead. '
                    'These optional commands create/install local dependencies when YOU run them. '
                    'They do not initialize a database. For a new database, use docs/START_HERE.md '
                    'and the existing setup/deployment workflow before continuing.')
    lessons = [
        Lesson('Choose your setup',
               'Open Advanced options and enter this computer’s actual LAN IP/hostname.'
               if scenario.lan else 'Keep Guided launcher unless you need separate terminals.',
               'This tutorial window', '',
               f'Your selected setup is: {scenario.title}.',
               'The setup dropdown changes the lesson examples only. '
               'The step list jumps between pages; it never starts a server.',
               scenario.summary + '\n\n' + scenario.preparation),
        Lesson('Open the backend folder', 'Open a terminal and copy this FIRST command.',
               'Your computer: a terminal / PowerShell window', cd_backend,
               'Your terminal is in backend/, the folder containing start.py and manage.py.',
               'Use this folder for Python startup commands. This tutorial does not check files.',
               install_help),
        Lesson('Check prerequisites', 'Run the dependency check before starting servers.',
               'The same backend terminal', diagnostic,
               'The launcher reports dependency readiness. Resolve missing packages before Next.',
               'You need an existing initialized database and installed frontend dependencies. '
               'This check does not prove database/cache connectivity.',
               scenario.preparation),
    ]
    for index in range(2 if scenario.dual else 1):
        ibp, ifp = bp + index, fp + index
        instance_root = 'SQLite/instance-b' if index else data_root.strip()
        url = f'http://{host}:{ifp}'
        label = f' {"AB"[index]}' if scenario.dual else ''
        if method == 'guided':
            database_choice = {'env': '1', 'sqlite': '2', 'postgres': '3', 'mariadb': '4'}[scenario.mode]
            database_label = {'env': 'Use DB_ENGINE from .env', 'sqlite': 'Separate local SQLite',
                              'postgres': 'PostgreSQL from .env', 'mariadb': 'MariaDB/MySQL from .env'}[scenario.mode]
            customize = (scenario.lan or scenario.dual or bool(instance_root or venv.strip())
                         or ibp != scenario.port or ifp != 5173)
            answers = [f'Database: enter {database_choice} ({database_label})',
                       'Action: enter 1 (Start backend + frontend)',
                       'Customize: enter y' if customize else 'Customize: press Enter (keep defaults)']
            if customize:
                answers += [f'Backend port: {ibp}', f'Frontend port: {ifp}',
                            'Network: enter 2 (trusted LAN)' if scenario.lan else 'Network: enter 1 (this computer)']
                if scenario.lan:
                    answers += [f'LAN IP/hostname: {host} (replace the example with your computer address)']
                answers += [f'Python venv: {venv.strip() or "press Enter (auto-detect)"}']
                if scenario.mode == 'sqlite':
                    answers += [f'SQLite directory: {instance_root or "press Enter (backend/SQLite)"}']
            lessons.append(Lesson(
                f'Start Quiz{label}', 'Run this command, then answer the terminal menu as shown below.',
                f'Backend terminal{label}' + (' (open another terminal for B)' if index else ''),
                cd_backend + '\npython start.py -i',
                f'Backend uses port {ibp}; Vite reports {url}. Keep this terminal open.',
                'The real launcher starts both servers and matches their proxy/origin settings. '
                'Do not also run the separate-terminal commands.', '\n'.join(answers)))
        else:
            args = ['python', 'start.py', scenario.mode, f'{bind}:{ibp}', '--frontend-origin', url]
            if instance_root and scenario.mode == 'sqlite':
                args += ['--data-root', instance_root]
            if venv.strip():
                args += ['--venv', venv.strip()]
            if scenario.mode == 'sqlite':
                args += ['--no-setup']
            args += ['--noreload']
            backend = shell_environment({'SQLITE_AUTO_SETUP': '0'}, command_text(args, shell), shell)
            frontend = shell_environment(
                {'VITE_BACKEND_PROXY_TARGET': f'http://127.0.0.1:{ibp}', 'VITE_API_BASE_URL': '/api/v1'},
                command_text(['pnpm', 'dev', '--host', bind, '--port', str(ifp), '--strictPort'], shell), shell)
            lessons += [
                Lesson(f'Start backend{label}', 'Copy this block into the backend terminal.',
                       f'Backend terminal{label}', cd_backend + '\n' + backend,
                       f'The API server stays running on port {ibp}.',
                       'Keep this terminal open. The frontend starts in a DIFFERENT terminal next.'),
                Lesson(f'Start frontend{label}', 'Open a NEW terminal and copy this entire block.',
                       f'Frontend terminal{label}', cd_frontend + '\n' + frontend,
                       f'Vite reports {url}. Both backend and frontend terminals stay open.',
                       'The environment assignments are part of the command; copy the whole block.'),
            ]
        lessons.append(Lesson(f'Open the browser{label}', 'Copy this URL into your browser address bar.',
                              'A browser, not a terminal', url,
                              'The Quiz sign-in page opens. Sign in with your existing account.',
                              'Use the frontend URL, not the API port or database port. '
                              'Wait for Vite to report ready before opening it.', scenario.expected))
    lessons.append(Lesson('Finish and stop', 'Keep the servers open while using Quiz.',
                          'The terminal window(s) running the servers', '',
                          'You can explain which terminal, command and browser URL to use.',
                          'To stop: press Ctrl+C in each launcher terminal. Guided mode stops both '
                          'servers together; manual mode needs Ctrl+C in both server terminals.',
                          'If something fails, use Need help below. Help never changes your step or starts anything. '
                          'Next/Back and the step list only navigate this lesson.'))
    return tuple(lessons)


class Tutorial:
    def __init__(self, tk, ttk, root):
        self.tk, self.ttk, self.root = tk, ttk, root
        ttk.Style(root).configure('Guide.TButton', font=('TkDefaultFont', 11, 'bold'), padding=(12, 7))
        root.title('Quiz startup guide — step by step')
        root.geometry('1120x820')
        root.minsize(860, 640)
        self.keys = list(SCENARIOS)
        self.step, self.visited = 0, set()
        self.lessons = ()
        self.selected = tk.StringVar(value=SCENARIOS['sqlite'].title)
        self.method = tk.StringVar(value=START_METHODS[0])
        self.shell_choice = tk.StringVar(value=SHELLS[1 if sys.platform == 'win32' else 0])
        self.backend_port = tk.StringVar()
        self.frontend_port = tk.StringVar(value='5173')
        self.browser_host = tk.StringVar(value='192.168.1.10')
        self.data_root, self.venv = tk.StringVar(), tk.StringVar()
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_dir = tk.StringVar(value=backend_dir)
        self.problem = tk.StringVar(value=next(iter(PROBLEMS)))
        self.feedback = tk.StringVar()
        self.advanced_open = False
        self.current_command = ''

        shell = ttk.Frame(root, padding=16)
        shell.pack(fill='both', expand=True)
        ttk.Label(shell, text='Start Quiz, one step at a time',
                  font=('TkDefaultFont', 20, 'bold')).pack(anchor='w')
        ttk.Label(shell, text='Follow Next →. Copy commands into your own terminal. '
                  'This guide never runs them.', wraplength=1000).pack(anchor='w', pady=(4, 10))
        selector_row = ttk.Frame(shell)
        selector_row.pack(fill='x')
        ttk.Label(selector_row, text='Your startup setup:').pack(side='left', padx=(0, 8))
        selector = ttk.Combobox(selector_row, textvariable=self.selected, state='readonly',
                                values=[s.title for s in SCENARIOS.values()], width=40)
        selector.pack(side='left', fill='x', expand=True)
        selector.bind('<<ComboboxSelected>>', self.reset)
        self.advanced_button = ttk.Button(selector_row, text='Advanced options ▾', command=self.toggle_advanced)
        self.advanced_button.pack(side='right', padx=(10, 0))
        ttk.Label(shell, text='Dropdown = choose the lesson scenario. Changing it resets the steps; '
                  'it does not change your app or database.', wraplength=1000).pack(anchor='w', pady=(4, 8))

        self.settings = ttk.LabelFrame(shell, text='Optional settings — change examples only', padding=8)
        self.entries = {}
        fields = [('Backend folder', self.project_dir), ('Backend HTTP port', self.backend_port),
                  ('Frontend port', self.frontend_port), ('LAN browser IP/host', self.browser_host),
                  ('SQLite data directory', self.data_root), ('Python venv (optional)', self.venv)]
        for index, (label, variable) in enumerate(fields):
            row, column = divmod(index, 2)
            ttk.Label(self.settings, text=label).grid(row=row, column=column * 2, sticky='w', padx=4, pady=3)
            entry = ttk.Entry(self.settings, textvariable=variable)
            entry.grid(row=row, column=column * 2 + 1, sticky='ew', padx=4, pady=3)
            self.entries[label] = entry
        ttk.Label(self.settings, text='Command format:').grid(row=3, column=0, sticky='w', padx=4)
        ttk.Combobox(self.settings, textvariable=self.shell_choice, values=SHELLS,
                     state='readonly').grid(row=3, column=1, sticky='ew', padx=4)
        ttk.Button(self.settings, text='Apply settings', command=self.rebuild).grid(row=3, column=3, sticky='e')
        self.settings.columnconfigure(1, weight=1)
        self.settings.columnconfigure(3, weight=1)

        self.body = ttk.Frame(shell)
        self.body.pack(fill='both', expand=True, pady=(4, 0))
        sidebar = ttk.Frame(self.body, width=205)
        sidebar.pack(side='left', fill='y', padx=(0, 14))
        ttk.Label(sidebar, text='Step navigator', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        ttk.Label(sidebar, text='Click to revisit a page.\nThis list does not run commands.\n✓ means viewed, not verified.',
                  wraplength=200).pack(anchor='w', pady=(4, 8))
        self.steps = tk.Listbox(sidebar, exportselection=False, width=26, height=10,
                                activestyle='none', font=('TkDefaultFont', 10))
        self.steps.pack(fill='both', expand=True)
        self.steps.bind('<<ListboxSelect>>', self.select_step)
        ttk.Button(sidebar, text='Copy full launch plan', command=self.copy_plan).pack(fill='x', pady=(10, 0))
        ttk.Button(sidebar, text='Start lesson again', command=self.reset).pack(fill='x', pady=6)

        content = ttk.Frame(self.body)
        content.pack(side='left', fill='both', expand=True)
        self.step_title = ttk.Label(content, font=('TkDefaultFont', 17, 'bold'), wraplength=760)
        self.step_title.pack(anchor='w', pady=(0, 10))
        self.mode_frame = ttk.LabelFrame(content, text='How do you want to start?', padding=8)
        for method in START_METHODS:
            ttk.Radiobutton(self.mode_frame, text=method, variable=self.method,
                            value=method, command=self.rebuild).pack(anchor='w', pady=2)
        self.action = ttk.Label(content, font=('TkDefaultFont', 12, 'bold'), wraplength=740)
        self.action.pack(anchor='w', pady=(0, 6))
        self.where = ttk.Label(content, wraplength=740)
        self.where.pack(anchor='w', pady=(0, 8))
        self.command_card = ttk.LabelFrame(content, text='Your command / URL — copy only this block', padding=8)
        self.command_card.pack(fill='x', pady=(0, 8))
        self.command = tk.Text(self.command_card, height=5, wrap='none', font='TkFixedFont',
                               padx=8, pady=8, state='disabled')
        command_scroll = ttk.Scrollbar(self.command_card, orient='horizontal', command=self.command.xview)
        self.command.configure(xscrollcommand=command_scroll.set)
        self.command.pack(fill='x')
        command_scroll.pack(fill='x')
        self.copy_button = ttk.Button(self.command_card, text='Copy command', command=self.copy_command,
                                      style='Guide.TButton')
        self.copy_button.pack(anchor='e', pady=(6, 0))
        self.expected = ttk.Label(content, wraplength=740)
        self.expected.pack(anchor='w', pady=(0, 6))
        self.hint = ttk.Label(content, wraplength=740)
        self.hint.pack(anchor='w', pady=(0, 8))
        self.details_frame = ttk.LabelFrame(content, text='Terminal answers / optional explanation', padding=6)
        self.details_frame.pack(fill='both', expand=True)
        self.details = tk.Text(self.details_frame, height=5, wrap='word', padx=8, pady=6, state='disabled')
        detail_scroll = ttk.Scrollbar(self.details_frame, command=self.details.yview)
        self.details.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.pack(side='right', fill='y')
        self.details.pack(fill='both', expand=True)
        self.feedback_label = ttk.Label(shell, textvariable=self.feedback, wraplength=1000)
        self.feedback_label.pack(anchor='w', pady=(8, 0))
        navigation = ttk.Frame(shell)
        navigation.pack(fill='x', pady=(8, 0))
        self.previous = ttk.Button(navigation, text='← Back', command=lambda: self.go(self.step - 1),
                                   style='Guide.TButton')
        self.previous.pack(side='left')
        self.progress = ttk.Label(navigation)
        self.progress.pack(side='left', padx=14)
        ttk.Button(navigation, text='Need help?', command=self.show_help).pack(side='right', padx=(10, 0))
        self.next = ttk.Button(navigation, text='Next →', command=lambda: self.go(self.step + 1),
                               style='Guide.TButton')
        self.next.pack(side='right')
        root.bind('<Alt-Left>', lambda event: self.go(self.step - 1))
        root.bind('<Alt-Right>', lambda event: self.go(self.step + 1))
        content.bind('<Configure>', lambda event: self.resize_content(event.width))
        self.reset()

    def key(self):
        return next(key for key in self.keys if SCENARIOS[key].title == self.selected.get())

    def toggle_advanced(self):
        self.advanced_open = not self.advanced_open
        if self.advanced_open:
            self.settings.pack(fill='x', before=self.body, pady=(0, 8))
        else:
            self.settings.pack_forget()
        self.advanced_button.configure(text='Hide advanced options ▴' if self.advanced_open else 'Advanced options ▾')

    def resize_content(self, width):
        for label in (self.step_title, self.action, self.where, self.expected, self.hint):
            label.configure(wraplength=max(280, width - 12))

    def reset(self, event=None):
        scenario = SCENARIOS[self.key()]
        self.backend_port.set(str(scenario.port))
        self.frontend_port.set('5173')
        self.data_root.set(scenario.root)
        self.browser_host.set('192.168.1.10')
        self.venv.set('')
        self.entries['LAN browser IP/host'].configure(state='normal' if scenario.lan else 'disabled')
        self.entries['SQLite data directory'].configure(state='normal' if scenario.mode == 'sqlite' else 'disabled')
        self.rebuild()
        if scenario.lan and not self.advanced_open:
            self.toggle_advanced()

    def rebuild(self):
        self.feedback.set('')
        self.step, self.visited = 0, set()
        try:
            self.lessons = lesson_plan(self.key(), 'guided' if self.method.get() == START_METHODS[0] else 'manual',
                                       self.backend_port.get(), self.frontend_port.get(), self.browser_host.get(),
                                       self.data_root.get(), self.venv.get(), self.project_dir.get(),
                                       'powershell' if self.shell_choice.get() == SHELLS[1] else 'posix')
        except ValueError as exc:
            self.lessons = ()
            self.feedback.set(f'Fix Advanced options: {exc}')
        if self.lessons and self.advanced_open:
            self.toggle_advanced()
        self.render()

    def select_step(self, event=None):
        selection = self.steps.curselection()
        if selection and selection[0] != self.step:
            self.go(selection[0])

    def go(self, step):
        if self.lessons:
            self.step = max(0, min(len(self.lessons) - 1, step))
            self.feedback.set('')
            self.render()

    def set_text(self, widget, value):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('end', value)
        widget.configure(state='disabled')
        widget.yview_moveto(0)
        widget.xview_moveto(0)

    def render(self):
        self.steps.delete(0, 'end')
        self.mode_frame.pack_forget()
        self.command_card.pack_forget()
        if not self.lessons:
            self.current_command = ''
            self.step_title.configure(text='Check your example settings')
            self.action.configure(text='Open Advanced options, fix the highlighted message, then Apply settings.')
            self.where.configure(text='')
            self.expected.configure(text='')
            self.hint.configure(text='No old commands are available while settings are invalid.')
            self.set_text(self.command, 'No command available.')
            self.set_text(self.details, '')
            self.copy_button.configure(state='disabled')
            self.previous.configure(state='disabled')
            self.next.configure(state='disabled')
            self.progress.configure(text='Fix settings to continue')
            return
        lesson = self.lessons[self.step]
        self.visited.add(self.step)
        for index, item in enumerate(self.lessons):
            mark = '✓ ' if index in self.visited else '  '
            self.steps.insert('end', f'{mark}{index + 1}. {item.title}')
        self.steps.selection_set(self.step)
        self.steps.see(self.step)
        self.step_title.configure(text=f'Step {self.step + 1}: {lesson.title}')
        if self.step == 0:
            self.mode_frame.pack(fill='x', before=self.action, pady=(0, 10))
        self.action.configure(text=lesson.action)
        self.where.configure(text='Where: ' + lesson.where)
        self.current_command = lesson.command
        if lesson.command:
            self.command_card.pack(fill='x', before=self.expected, pady=(0, 8))
        self.set_text(self.command, lesson.command or 'No terminal command on this page. Use Next / Back.')
        self.command.configure(height=min(7, max(2, lesson.command.count('\n') + 1)))
        self.copy_button.configure(state='normal' if lesson.command else 'disabled',
                                   text='Copy URL' if lesson.command.startswith('http') else 'Copy command')
        self.expected.configure(text='You should see: ' + lesson.expected)
        self.hint.configure(text=lesson.hint)
        self.details_frame.configure(text='Answer these prompts in your terminal'
                                     if 'python start.py -i' in lesson.command else 'Optional help / explanation')
        self.set_text(self.details, lesson.details or 'No extra instructions. Follow the action above.')
        self.progress.configure(text=f'{self.step + 1} / {len(self.lessons)} · {len(self.visited)} pages viewed')
        self.previous.configure(state='disabled' if self.step == 0 else 'normal')
        self.next.configure(state='disabled' if self.step == len(self.lessons) - 1 else 'normal',
                            text=f'Next: {self.lessons[self.step + 1].title} →' if self.step + 1 < len(self.lessons) else 'Lesson complete')

    def copy(self, value):
        if not value:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.feedback.set('Copied. Paste into the indicated terminal or browser. Nothing was run here.')

    def copy_command(self):
        self.copy(self.current_command)

    def copy_plan(self):
        if self.lessons:
            self.copy('\n\n'.join(f'{i + 1}. {lesson.title}\nWhere: {lesson.where}\n'
                                    f'{lesson.command}\n{lesson.details}\nExpected: {lesson.expected}'
                                    for i, lesson in enumerate(self.lessons)))
            self.feedback.set('Copied lesson notes. Use each page’s Copy command button for terminal commands.')

    def show_help(self):
        window = self.tk.Toplevel(self.root)
        window.title('Startup help — your current step stays open')
        window.geometry('650x400')
        frame = self.ttk.Frame(window, padding=16)
        frame.pack(fill='both', expand=True)
        self.ttk.Label(frame, text='What went wrong?', font=('TkDefaultFont', 14, 'bold')).pack(anchor='w')
        issue = self.ttk.Combobox(frame, textvariable=self.problem, state='readonly', values=list(PROBLEMS))
        issue.pack(fill='x', pady=10)
        explanation = self.tk.Text(frame, wrap='word', padx=8, pady=8, state='disabled')
        explanation.pack(fill='both', expand=True)
        def update(event=None):
            symptom, answer = PROBLEMS[self.problem.get()]
            self.set_text(explanation, f'Example symptom\n{symptom}\n\nWhat to check\n{answer}\n\n'
                          'Return to your current step after resolving this in your real terminal. '
                          'The tutorial does not diagnose your machine.')
        issue.bind('<<ComboboxSelected>>', update)
        update()
        self.ttk.Button(frame, text='Return to my step', command=window.destroy).pack(anchor='e', pady=(8, 0))


def main():
    if sys.argv[1:]:
        print(__doc__)
        return 0 if sys.argv[1:] in (['--help'], ['-h']) else 2
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        print('This tutorial needs Python Tkinter and a desktop display. '
              'Use a Python installation with Tk support. No app files were changed.')
        return 1
    try:
        root = tk.Tk()
    except tk.TclError:
        print('A desktop display is required for the tutorial. No app files were changed.')
        return 1
    Tutorial(tk, ttk, root)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
