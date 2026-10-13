# Complete backend suite and coverage report

2026-10-10 · current source revision `0540f8f` · Python 3.14.4 / Django 6.1.2 / coverage.py 7.16.2.

Ran every test discovered under `tests` against current backend source on both database configurations. The final PostgreSQL run includes all 35 newer concurrency scenarios plus the original two-thread finish case, with no skips. This is complete existing-suite execution with measured coverage, not 100% behavioral coverage.

| Database | Tests | Passed | Failures/errors | Skipped | Duration | Line coverage | Branch coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PostgreSQL | 982 | 982 | 0/0 | 0 | 97.050s | 9,916/13,820 (71.75%) | 2,377/4,180 (56.87%) |
| In-memory SQLite | 982 | 946 | 0/0 | 36 | 40.762s | 9,742/13,820 (70.49%) | 2,297/4,180 (54.95%) |

The SQLite skips intentionally exclude PostgreSQL row-locking/concurrency semantics. Coverage's combined statement/branch percentage is 68.29% for PostgreSQL and 66.88% for SQLite; the separate percentages above are clearer. The machine-readable [coverage details](backendCoverage.json) contain both runs, module totals, every measured file's missing lines/branches and skipped test names. Counts include `apps`, `config`, `scripts` and the executed `manage.py`; tests, migration files and third-party code are excluded. `start.py` was not imported by the suite and is unmeasured. Coverage started before Django initialization and traced test threads.

## PostgreSQL test schema repair

The first PostgreSQL run had 4 failures and 175 errors because the retained `test_quiz_codex_20261010` schema lacked the current `ClinicalCase.translations` field; dependent import assertions also failed. Read-only comparison of current model fields with test-table columns found that one missing column. Added it using Django's schema editor with explicit configured/current-database guards, then reran the entire suite successfully. This initialized only the isolated test schema. No migration files were inspected, created or changed; application schema/data were not modified. This does not prove the running application's schema is current.

## Coverage by area (PostgreSQL)

| Area | Lines | Branches |
| --- | ---: | ---: |
| apps/analytics | 318/351 (90.60%) | 48/66 (72.73%) |
| apps/core | 1,051/1,617 (65.00%) | 236/390 (60.51%) |
| apps/database | 298/564 (52.84%) | 58/144 (40.28%) |
| apps/exams | 966/1,306 (73.97%) | 220/404 (54.46%) |
| apps/feedback | 198/241 (82.16%) | 21/32 (65.62%) |
| apps/groups | 286/300 (95.33%) | 45/52 (86.54%) |
| apps/learning | 549/599 (91.65%) | 97/124 (78.23%) |
| apps/master_exams | 1,579/1,897 (83.24%) | 307/500 (61.40%) |
| apps/planning | 328/352 (93.18%) | 47/64 (73.44%) |
| apps/questions | 3,387/4,512 (75.07%) | 1,110/1,794 (61.87%) |
| apps/users | 834/980 (85.10%) | 172/256 (67.19%) |
| config | 113/254 (44.49%) | 15/86 (17.44%) |
| manage.py | 9/11 (81.82%) | 1/2 (50.00%) |
| scripts | 0/836 (0.00%) | 0/266 (0.00%) |

## Largest uncovered application files

These are opportunities for future tests, not established production defects. Full missing-line/branch details are in the JSON and temporary HTML reports.

| File | Uncovered statements |
| --- | ---: |
| `apps/core/management/commands/bootstrap.py` | 284 |
| `apps/core/management/commands/doctor.py` | 189 |
| `apps/exams/views/session_views.py` | 133 |
| `apps/questions/services/importing/state_import/validation.py` | 127 |
| `apps/database/services/backup_service.py` | 105 |
| `apps/database/services/_sqlite_reference.py` | 102 |
| `apps/questions/services/importing/flat_import.py` | 97 |
| `apps/questions/views/question_views.py` | 87 |
| `apps/questions/services/importing/state_import/apply.py` | 82 |
| `apps/questions/services/exporting/pdf_export.py` | 75 |

## Isolation and limits

PostgreSQL uses the existing application connection configuration with `DB_ENGINE=postgres`, but the database is explicitly replaced with `test_quiz_codex_20261010`. Both overlays isolate cache and media/upload/export/backup files, and use fast test-only password hashing. No tests were sent to the running HTTP server on `0.0.0.0:5005`, and the application database was not deleted, flushed or changed. Cache/process/HTTP integration, launcher/bootstrap, real operator backup/restore, real PDF rendering, browser/Android behavior and functions/branches not exercised by this suite remain unverified. Do not infer production capacity or migration readiness from the passing suite.

Coverage tooling was installed into `/tmp/quiz-coverage-tools`; project dependency pins and the virtualenv were unchanged. HTML reports are temporary at `/tmp/quiz-backend-coverage/postgresql-html/index.html` and `/tmp/quiz-backend-coverage/sqlite-html/index.html`. Raw test logs can contain generated test credentials and remain temporary, outside repository documentation.

## Reproduce

From `backend/`, use the Quiz Python environment and a current, isolated test schema. The existing PostgreSQL overlay rejects an application database name; `--keepdb` retains the test schema and does not correct missing model columns by itself. These commands reproduce the final suite and coverage setup without changing project dependencies:

```bash
python -m pip install --target /tmp/quiz-coverage-tools coverage==7.16.2
mkdir -p /tmp/quiz-backend-coverage
DB_ENGINE=postgres QUIZ_TEST_POSTGRES_DB=test_quiz_codex_20261010 \
PYTHONPATH=/tmp/quiz-coverage-tools COVERAGE_FILE=/tmp/quiz-backend-coverage/postgresql.coverage \
python -m coverage run --rcfile=tests/coverage.ini manage.py test tests \
  --settings=tests.postgresql_settings --keepdb --noinput
PYTHONPATH=/tmp/quiz-coverage-tools COVERAGE_FILE=/tmp/quiz-backend-coverage/sqlite.coverage \
python -m coverage run --rcfile=tests/coverage.ini manage.py test tests \
  --settings=tests.test_settings --noinput
PYTHONPATH=/tmp/quiz-coverage-tools COVERAGE_FILE=/tmp/quiz-backend-coverage/postgresql.coverage \
python -m coverage report --rcfile=tests/coverage.ini
PYTHONPATH=/tmp/quiz-coverage-tools COVERAGE_FILE=/tmp/quiz-backend-coverage/postgresql.coverage \
python -m coverage html --rcfile=tests/coverage.ini -d /tmp/quiz-backend-coverage/postgresql-html
```
