"""HTTP development overlay; keep database/cache credentials from normal settings."""

import os

os.environ['DEBUG'] = 'True'
os.environ['USE_HTTPS'] = 'False'
if os.environ.get('QUIZ_FRONTEND_ORIGINS'):
    os.environ['CORS_ORIGINS'] = os.environ['QUIZ_FRONTEND_ORIGINS']

from .settings import *  # noqa: E402,F401,F403

DEBUG = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]
_bind_host = os.environ.get('QUIZ_BIND_HOST', 'localhost').strip('[]')
if _bind_host in {'0.0.0.0', '::'}:
    ALLOWED_HOSTS.append('*')
elif _bind_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_bind_host)

CORS_ALLOWED_ORIGINS = [origin.strip().rstrip('/') for origin in CORS_ALLOWED_ORIGINS]
CORS_ALLOW_ALL_ORIGINS = '*' in CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [origin for origin in CORS_ALLOWED_ORIGINS if origin != '*']
for _origin in ('http://localhost:5173', 'http://127.0.0.1:5173'):
    if _origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(_origin)
CSRF_TRUSTED_ORIGINS = [
    origin for origin in CORS_ALLOWED_ORIGINS if origin.startswith(('http://', 'https://'))
]
