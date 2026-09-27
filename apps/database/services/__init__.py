# backend/apps/database/services/__init__.py
"""
Package surface for the database services.

Split from a single ~600-line module into four sibling modules:

  • backend.py            — backend detection (`_is_sqlite`,
                            `_is_mariadb`) and the two MySQL config
                            helpers (`_mysql_config`,
                            `_write_defaults_file`).
  • backup_service.py     — the `BackupService` class. Every public
                            method (get_info, create_backup,
                            list_backups, restore_backup,
                            clear_database) keeps its original
                            signature and MariaDB branch.
  • _sqlite_reference.py  — SQLite backup/restore implementation,
                            imported lazily only when the configured
                            connection vendor is SQLite.

`BackupService` is re-exported here unchanged, so
`from .services import BackupService` in apps/database/views.py
keeps working without modification.

WHY THE SQLITE CODE IS SEPARATE
-------------------------------
Keeping SQLite's online-backup API and sequence-reset details in a
dedicated module prevents them from complicating the MariaDB subprocess
path. `backup_service.py` performs a small vendor check and imports the
SQLite module lazily; MariaDB behavior and imports remain unchanged.
"""

from .backup_service import BackupService


__all__ = ['BackupService']
