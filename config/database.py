"""Database configuration shared by settings and the development launcher."""

from pathlib import Path


def database_engine(environ):
    value = environ.get('DB_ENGINE', 'mariadb').strip()
    aliases = {
        'mariadb': 'django.db.backends.mysql',
        'mysql': 'django.db.backends.mysql',
        'postgres': 'django.db.backends.postgresql',
        'postgresql': 'django.db.backends.postgresql',
        'sqlite': 'django.db.backends.sqlite3',
        'sqlite3': 'django.db.backends.sqlite3',
    }
    if value.lower() in aliases:
        return aliases[value.lower()]
    if value and '.' in value:
        return value  # Allow installed third-party Django database backends.
    raise ValueError('DB_ENGINE must be mariadb, postgresql, sqlite, or a Django backend module.')


def database_config(environ, base_dir):
    engine = database_engine(environ)
    if engine == 'django.db.backends.sqlite3':
        name = environ.get('SQLITE_DB_PATH') or environ.get('DB_NAME')
        if not name:
            root = Path(environ.get('SQLITE_ROOT', 'SQLite')).expanduser()
            name = str(root / 'db.sqlite3')
        if name != ':memory:':
            path = Path(name).expanduser()
            name = str(path if path.is_absolute() else Path(base_dir) / path)
        return {'ENGINE': engine, 'NAME': name, 'OPTIONS': {
            'timeout': 20, 'transaction_mode': 'IMMEDIATE',
        }}

    config = {
        'ENGINE': engine,
        'NAME': environ.get('DB_NAME', 'quiz'),
        'USER': environ.get('DB_USER', 'quiz'),
        'PASSWORD': environ.get('DB_PASSWORD', ''),
        'HOST': environ.get('DB_HOST', 'localhost'),
        'PORT': environ.get('DB_PORT', {
            'django.db.backends.mysql': '3306',
            'django.db.backends.postgresql': '5432',
        }.get(engine, '')),
        'OPTIONS': {},
    }
    if engine == 'django.db.backends.mysql':
        config['OPTIONS'] = {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    elif engine == 'django.db.backends.postgresql' and environ.get('DB_SSLMODE'):
        config['OPTIONS']['sslmode'] = environ['DB_SSLMODE']
    return config
