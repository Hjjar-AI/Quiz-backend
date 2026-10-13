# backend/apps/database/services/_sqlite_reference.py
"""
SQLite implementation behind ``BackupService``.

The filename is retained to avoid unnecessary module churn, but this is
now live code: ``backup_service.py`` imports these functions lazily when
the configured connection vendor is SQLite. MariaDB never imports this
module and retains its existing implementation.
"""

import logging
import os
import sqlite3
import threading
from contextlib import closing
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connections
from apps.core.artifacts import reserve_artifact_path


logger = logging.getLogger(__name__)


# Serialise database-file backup and restore operations inside this process.
# The SQLite launcher also defaults runserver to one request thread, but this
# lock protects direct management-command or explicitly threaded callers.
_SQLITE_OPERATION_LOCK = threading.RLock()


def _sqlite_db_path():
    return Path(settings.DATABASES['default']['NAME'])


def _sqlite_timeout():
    return float(settings.DATABASES['default'].get('OPTIONS', {}).get('timeout', 20))


def _backup_database(source_path, target_path):
    """Use SQLite's online backup API and always close both handles."""
    with closing(sqlite3.connect(str(source_path), timeout=_sqlite_timeout())) as src:
        with closing(sqlite3.connect(str(target_path), timeout=_sqlite_timeout())) as dst:
            with dst:
                src.backup(dst)


def get_info():
    """SQLite port of BackupService.get_info()."""
    db_path = _sqlite_db_path()
    if not db_path.is_file():
        return {'error': 'قاعدة البيانات غير موجودة', 'code': 404}

    size = os.path.getsize(db_path)
    modified = datetime.fromtimestamp(
        os.path.getmtime(db_path)
    ).strftime('%Y-%m-%d %H:%M:%S')

    from apps.questions.models import Question, Category
    from apps.users.models import User
    from apps.exams.models import TestHistory

    return {
        'file_path': os.path.abspath(db_path),
        'file_size': f'{size / 1024:.2f} KB',
        'file_modified': modified,
        'database_type': 'SQLite',
        'total_questions':  Question.objects.count(),
        'verified_count':   Question.objects.filter(verified=True).count(),
        'total_users':      User.objects.count(),
        'total_categories': Category.objects.count(),
        'total_sessions':   TestHistory.objects.count(),
    }


def create_backup(safety=False):
    """SQLite port of BackupService.create_backup()."""
    db_path = _sqlite_db_path()
    if not db_path.is_file():
        return {'error': 'قاعدة البيانات غير موجودة', 'code': 404}

    backup_dir = Path(settings.BACKUP_FOLDER)
    prefix = 'pre_restore' if safety else 'questions_backup'
    backup_path = None

    with _SQLITE_OPERATION_LOCK:
        try:
            backup_path = reserve_artifact_path(backup_dir, prefix, '.db')
            _backup_database(db_path, backup_path)
            logger.info('Backup created: %s', backup_path)
        except (OSError, sqlite3.Error) as exc:
            logger.exception('Failed to create backup: %s', exc)
            if backup_path is not None:
                backup_path.unlink(missing_ok=True)
            return {'error': 'فشل إنشاء النسخة الاحتياطية', 'code': 500}

    return {'message': 'تم إنشاء نسخة احتياطية', 'path': str(backup_path)}


def list_backups():
    """
    SQLite port of BackupService.list_backups().

    The only difference from the MariaDB implementation is the glob
    pattern: `*.db` instead of `*.sql`.
    """
    backup_dir = Path(settings.BACKUP_FOLDER)
    if not backup_dir.exists():
        return {'items': [], 'total': 0}

    backups = []
    for f in backup_dir.glob('*.db'):
        size = f.stat().st_size
        modified = datetime.fromtimestamp(f.stat().st_mtime)
        backups.append({
            'name':     f.name,
            'size':     f'{size / 1024:.2f} KB',
            'modified': modified.strftime('%Y-%m-%d %H:%M:%S'),
        })
    backups.sort(key=lambda x: x['modified'], reverse=True)
    return {'items': backups, 'total': len(backups)}


def restore_backup(backup_name):
    """SQLite port of BackupService.restore_backup()."""
    backup_dir = Path(settings.BACKUP_FOLDER)
    target_path = (backup_dir / backup_name).resolve()

    # Path traversal guard — must stay in sync with the MariaDB
    # branch in backup_service.py.
    try:
        target_path.relative_to(backup_dir.resolve())
    except ValueError:
        return {'error': 'مسار ملف غير مسموح به', 'code': 400}

    if not target_path.is_file() or target_path.suffix.lower() != '.db':
        return {'error': 'الملف غير موجود', 'code': 404}

    db_path = _sqlite_db_path()
    if target_path == db_path.resolve():
        return {'error': 'لا يمكن استعادة قاعدة البيانات من نفسها', 'code': 400}

    with _SQLITE_OPERATION_LOCK:
        # Integrity-check the candidate before touching the live database.
        try:
            with closing(sqlite3.connect(
                str(target_path), timeout=_sqlite_timeout(),
            )) as candidate:
                result = candidate.execute('PRAGMA integrity_check').fetchone()
            if not result or result[0] != 'ok':
                return {'error': 'النسخة الاحتياطية تالفة', 'code': 400}
        except sqlite3.Error as exc:
            logger.exception('Integrity check failed: %s', exc)
            return {'error': 'النسخة الاحتياطية تالفة', 'code': 400}

        # A failed safety snapshot aborts the restore.
        safety = create_backup(safety=True)
        if 'error' in safety:
            logger.error('Aborting SQLite restore: safety backup failed')
            return {'error': 'فشل إنشاء نسخة الأمان قبل الاستعادة', 'code': 500}

        connections.close_all()
        try:
            _backup_database(target_path, db_path)
        except (OSError, sqlite3.Error) as exc:
            logger.exception('Failed to restore backup: %s', exc)
            return {'error': 'فشل استعادة النسخة الاحتياطية', 'code': 500}
        finally:
            connections.close_all()

    return {'message': 'تم استعادة قاعدة البيانات بنجاح'}


def reset_autoincrement(cursor, model_names):
    """
    SQLite-specific AUTO_INCREMENT reset, called after the shared
    model-deletion loop in `clear_database`.

    SQLite stores sequence state in the `sqlite_sequence` table;
    deleting a row does not remove its sequence entry. The MariaDB
    branch uses ALTER TABLE ... AUTO_INCREMENT = 1 instead.

    `cursor`       — an open Django DB cursor.
    `model_names`  — iterable of 'app.Model' strings already deleted.

    Django cursors use ``%s`` placeholders on every backend, including
    SQLite; the backend translates them for sqlite3.
    """
    from django.apps import apps
    cursor.execute(
        "SELECT 1 FROM sqlite_master "
        "WHERE type = 'table' AND name = 'sqlite_sequence'"
    )
    if cursor.fetchone() is None:
        return

    for model_name in model_names:
        model = apps.get_model(model_name)
        table_name = model._meta.db_table
        cursor.execute(
            "DELETE FROM sqlite_sequence WHERE name = %s",
            [table_name],
        )
