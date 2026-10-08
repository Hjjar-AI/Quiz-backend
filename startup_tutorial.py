#!/usr/bin/env python3
"""Read-only Tkinter startup tutorial. All commands/results are examples.

Run: python startup_tutorial.py
No app imports, file access, configuration changes, process launches, database
connections or network requests. Learning progress exists only in this window.
"""

from dataclasses import dataclass
import ipaddress
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

STEPS = ('1. Understand', '2. Prepare', '3. Match settings',
         '4. Inspect commands', '5. Troubleshoot', '6. Check understanding')

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


def command_text(arguments):
    """Format an example; never execute it."""
    if sys.platform == 'win32':
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


class Tutorial:
    def __init__(self, tk, ttk, root):
        self.tk, self.root = tk, root
        root.title('Quiz startup tutorial — simulation only')
        root.geometry('1080x780')
        root.minsize(780, 580)
        self.keys = list(SCENARIOS)
        self.step = 0
        self.selected = tk.StringVar(value=SCENARIOS['sqlite'].title)
        self.backend_port = tk.StringVar()
        self.frontend_port = tk.StringVar(value='5173')
        self.browser_host = tk.StringVar(value='192.168.1.10')
        self.data_root = tk.StringVar()
        self.venv = tk.StringVar()
        self.problem = tk.StringVar(value=next(iter(PROBLEMS)))
        self.quiz_answer = tk.StringVar()

        shell = ttk.Frame(root, padding=18)
        shell.pack(fill='both', expand=True)
        ttk.Label(shell, text='Learn to start Quiz', font=('TkDefaultFont', 20, 'bold')).pack(anchor='w')
        ttk.Label(shell, text='SIMULATION ONLY · No commands run · No app files/data/configuration touched',
                  wraplength=950).pack(anchor='w', pady=(4, 14))
        selector = ttk.Combobox(shell, textvariable=self.selected, state='readonly',
                                values=[s.title for s in SCENARIOS.values()])
        selector.pack(fill='x')
        selector.bind('<<ComboboxSelected>>', self.reset)

        settings = ttk.LabelFrame(shell, text='Experiment with example settings', padding=10)
        settings.pack(fill='x', pady=10)
        self.entries = {}
        fields = [('Backend HTTP port', self.backend_port), ('Frontend port', self.frontend_port),
                  ('LAN browser IP/host', self.browser_host), ('SQLite data directory', self.data_root),
                  ('Python venv (optional)', self.venv)]
        for index, (label, variable) in enumerate(fields):
            row, column = divmod(index, 2)
            ttk.Label(settings, text=label).grid(row=row, column=column * 2, sticky='w', padx=6, pady=4)
            entry = ttk.Entry(settings, textvariable=variable)
            entry.grid(row=row, column=column * 2 + 1, sticky='ew', padx=6, pady=4)
            self.entries[label] = entry
        settings.columnconfigure(1, weight=1)
        settings.columnconfigure(3, weight=1)
        ttk.Button(settings, text='Update examples', command=self.render).grid(row=2, column=2, columnspan=2)

        body = ttk.Frame(shell)
        body.pack(fill='both', expand=True)
        self.steps = tk.Listbox(body, height=6, exportselection=False, width=25)
        self.steps.pack(side='left', fill='y', padx=(0, 12))
        for step in STEPS:
            self.steps.insert('end', step)
        self.steps.bind('<<ListboxSelect>>', self.select_step)
        text_frame = ttk.Frame(body)
        text_frame.pack(side='left', fill='both', expand=True)
        self.text = tk.Text(text_frame, wrap='word', padx=14, pady=12, state='disabled')
        scrollbar = ttk.Scrollbar(text_frame, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.text.pack(fill='both', expand=True)
        self.text.tag_configure('title', font=('TkDefaultFont', 15, 'bold'))
        self.text.tag_configure('commands', font='TkFixedFont')

        exercises = ttk.Frame(shell)
        exercises.pack(fill='x', pady=10)
        ttk.Label(exercises, text='Troubleshooting:').pack(side='left')
        issue = ttk.Combobox(exercises, textvariable=self.problem, state='readonly', values=list(PROBLEMS))
        issue.pack(side='left', fill='x', expand=True, padx=8)
        ttk.Button(exercises, text='Explain example', command=lambda: self.go(4)).pack(side='left')
        issue.bind('<<ComboboxSelected>>', lambda event: self.go(4))
        self.quiz = ttk.Frame(shell)
        ttk.Label(self.quiz, text='Which URL opens the development UI?').pack(anchor='w')
        for answer in ('Frontend URL', 'Backend root URL', 'Database host:port'):
            ttk.Radiobutton(self.quiz, text=answer, variable=self.quiz_answer,
                            value=answer, command=self.check_answer).pack(side='left', padx=(0, 15))
        self.feedback = tk.StringVar()
        self.feedback_label = ttk.Label(shell, textvariable=self.feedback, wraplength=950)
        self.feedback_label.pack(anchor='w')
        navigation = ttk.Frame(shell)
        navigation.pack(fill='x', pady=(10, 0))
        self.previous = ttk.Button(navigation, text='← Previous', command=lambda: self.go(self.step - 1))
        self.previous.pack(side='left')
        self.progress = ttk.Label(navigation)
        self.progress.pack(side='left', padx=15)
        self.next = ttk.Button(navigation, text='Next →', command=lambda: self.go(self.step + 1))
        self.next.pack(side='right')
        ttk.Button(navigation, text='Reset lesson', command=self.reset).pack(side='right', padx=10)
        self.reset()

    def key(self):
        return next(key for key in self.keys if SCENARIOS[key].title == self.selected.get())

    def reset(self, event=None):
        scenario = SCENARIOS[self.key()]
        self.backend_port.set(str(scenario.port))
        self.frontend_port.set('5173')
        self.data_root.set(scenario.root)
        self.browser_host.set('192.168.1.10')
        self.venv.set('')
        self.quiz_answer.set('')
        self.entries['LAN browser IP/host'].configure(state='normal' if scenario.lan else 'disabled')
        self.entries['SQLite data directory'].configure(state='normal' if scenario.mode == 'sqlite' else 'disabled')
        self.go(0)

    def select_step(self, event):
        selection = self.steps.curselection()
        if selection and selection[0] != self.step:
            self.go(selection[0])

    def go(self, step):
        self.step = max(0, min(len(STEPS) - 1, step))
        self.render()

    def render(self):
        scenario = SCENARIOS[self.key()]
        self.feedback.set('')
        try:
            commands = examples(self.key(), self.backend_port.get(), self.frontend_port.get(),
                                self.browser_host.get(), self.data_root.get(), self.venv.get())
        except ValueError as exc:
            self.feedback.set(str(exc))
            return
        symptom, explanation = PROBLEMS[self.problem.get()]
        lessons = [
            f'{scenario.summary}\n\n{scenario.expected}\n\n'
            'This tutorial uses fictional examples and values you type. It never '
            'reads your environment, credentials, files or database.',
            f'{scenario.preparation}\n\nThe frontend needs Node, pnpm and installed '
            'dependencies. Tkinter is sufficient for this tutorial; Django and '
            'the app dependencies are not imported. Nothing is installed here.',
            'Backend HTTP port: where the API listens.\nFrontend port: where '
            'the browser UI runs.\nDatabase port: a separate server setting in .env.\n\n'
            'The frontend proxy target must match the backend HTTP port. The '
            'backend browser origin must match the frontend URL exactly. Change '
            'the example fields and select Update examples to explore.\n\n'
            'With two instances, the second pair of ports is the first pair +1. '
            'Each instance also needs a distinct data directory.',
            'Examples only — these are never executed. Environment values below '
            'describe process settings; this tutorial does not set them or edit .env. '
            'Commands are shown for terminals in the indicated folders '
            '(PowerShell on Windows, POSIX shell elsewhere).\n\n' + commands +
            '\n\nThe examples skip SQLite setup/seeding and backend autoreload. '
            'Fresh database initialization is a separate intentional task.',
            f'SIMULATED SYMPTOM — not a result from your computer\n\n{symptom}\n\n'
            f'{explanation}\n\nUse the troubleshooting selector to explore another failure. '
            'The real --diagnose command checks dependencies/configuration, '
            'not database/cache connectivity.',
            f'Expected behavior for this scenario:\n\n{scenario.expected}\n\n'
            'Select an answer below. No app is launched, even after a correct answer. '
            'Your lesson progress disappears when you close this window.',
        ]
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        self.text.insert('end', STEPS[self.step] + '\n\n', 'title')
        self.text.insert('end', lessons[self.step], 'commands' if self.step == 3 else '')
        self.text.configure(state='disabled')
        self.steps.selection_clear(0, 'end')
        self.steps.selection_set(self.step)
        self.progress.configure(text=f'Step {self.step + 1} of {len(STEPS)}')
        self.previous.configure(state='disabled' if self.step == 0 else 'normal')
        self.next.configure(state='disabled' if self.step == len(STEPS) - 1 else 'normal')
        self.quiz.pack_forget()
        if self.step == 5:
            self.quiz.pack(fill='x', before=self.feedback_label, pady=6)
            if self.quiz_answer.get():
                self.check_answer()

    def check_answer(self):
        self.feedback.set('Correct: the frontend serves the development UI; its proxy forwards API/media.'
                          if self.quiz_answer.get() == 'Frontend URL' else
                          'Try again: the API server and database are separate from the browser UI.')


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
