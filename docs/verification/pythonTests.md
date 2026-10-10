# Backend Python verification

2026-10-10 · baseline revision `8274707` plus the test changes below · Python 3.14.4 / Django 6.1.2 / PostgreSQL 18.6.

The last full discovered suite **passed on both databases** after failure triage and repairs, before the later session-label changes below. [Structured results and historical failure/function inventory](pythonTestDetails.json) contain no credentials or raw logs. The earlier 930-test run had 42 failures and 109 errors on each database; those failures are resolved in the final suite.

| Database | Run | Passed | Failures | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| In-memory SQLite | 971 | 935 | 0 | 0 | 36 |
| Isolated PostgreSQL | 971 | 971 | 0 | 0 | 0 |

SQLite took 35.038 seconds; PostgreSQL took 104.435 seconds. The earlier 102-test repair run also passed. Django system checks reported no issues. See the concurrency report for the new matrix and repeat runs; source/document checks are recorded in the work log.

Before expanding the matrix, rechecked the original skipped test separately on 2026-10-10: SQLite skipped it as expected; PostgreSQL ran it and passed in 0.494 seconds. It verifies that two threads finishing the same master attempt record SRS once. The skip remains because SQLite does not implement the row locking this test exercises.

## Later focused session-label regression run

The 20-test `tests.exams.test_exam_service` module passes on isolated PostgreSQL (2.386s) and in-memory SQLite (0.927s), with zero failures/errors/skips. Four added tests cover long Arabic/English labels through start/history in all three modes, unchanged labels at/below the boundary, full multi-tag selection over HTTP, and nontext-label rejection preserving the existing session. Existing recall reveal/answer tests also pass. Application databases remain untouched. The full suite was not rerun after this change; the 971-test table above is historical evidence.

## Later member/offline seeder regression run

After changing `seed_pro_users` to member accounts and adding three missing offline learners, all nine `tests.management.test_seed_pro_users` tests pass on SQLite (0.500s) and isolated PostgreSQL (1.534s), with zero failures/errors/skips. They verify the five per-user full-bank grants, normal member permissions, role/staff flag repair, preserved unrelated overrides/passwords/names, missing-user creation and credential/reset behavior. Application seeding and a full-suite rerun were not performed.

## What was verified and changed

- Added [35 PostgreSQL concurrency scenarios](concurrencyLimits.md), with three passing focused runs plus the full suite: retries, revisions, learning counters, quotas, imports, admin preservation, approximate throttling and timeout rollback/recovery. Tests use up to 16 independent workers. SQLite skips these 35 cases plus the original locking test; maximum deployed user/HTTP capacity remains unmeasured.

- Fixed a backend state-export defect: DRF interpreted `?format=xlsx` as a response-renderer selector and returned 404 before exporting. The export view now handles that parameter as the file format. Vue and Android both use this request shape. Tests verify XLSX success, unsupported-format rejection, member denial and Accept-header validation.
- Added six `seed_pro_users` tests: account creation, repeat/password/name preservation, role repair/reactivation, explicit password reset, quiet credential handout and no repeat credential output. All six pass on both databases.
- Updated the concurrency fixture to assign its student to the exam and provide the current answer/session baseline. The two-thread PostgreSQL exam-finish test passes and records the SRS answer exactly once. SQLite skips this row-locking scenario.
- Test settings now isolate upload/media/export/backup directories in temporary storage, use a process-local cache and test password hashing. PostgreSQL settings require a separate `test_` database name and reject the configured application database name.
- Application databases `quiz_fresh` and the older `quiz` were not migrated, seeded or modified by these runs. The Django runner initialized only the dedicated PostgreSQL test database `test_quiz_codex_20261010`, which remains available for reruns via `--keepdb`.

## Failure repairs

No failures remain in these runs. Tests were repaired against current production source, preserving validation and capability rules:

| Pattern | Repair |
| --- | --- |
| Histories, attempts, verified questions and resolved flags omit invariant fields | Coherent positive fixtures; negative database-constraint tests use bulk writes to exercise the constraint directly. |
| Write calls omit revision, planner ID or master-answer/session baselines | Supply current baselines; added missing/stale planner baseline checks. |
| Activity tests rely on history rows | Commit immutable learning events through the current recording/progress path. |
| Removed bulk-SRS API and older mastery/review expectations | Verify event recording, duplicate-source suppression, early-practice limits, conservative mastery and same-day relearning. |
| Login expected CSRF exemption | Verify rejection without a token and credential validation with a valid token. |
| Imports expected duplicate-choice rejection or preservation after assessed-content changes | Verify marked quality-review imports, reset counters on changed content, preserve omitted counters on unchanged content and advance local revisions. |
| Seeder, batch response, cleanup, deadlines, translation and image stubs use older assumptions | Match 28 categories, `total`, retention based on start time, valid chronological deadlines, matching option counts and storage metadata. |

The six additional regression scenarios cover login with/without CSRF (replacing one old test), missing/stale planner baselines, export permission/Accept behavior and unchanged-content import preservation. Existing tests were renamed where their behavior changed; none was disabled to obtain a passing result.

## Function reachability and limits

The **earlier, pre-repair** SQLite suite used standard-library `sys.setprofile`: **608 of 912 function bodies observed; 304 unobserved** in `apps/`, `config/` and `scripts/`. This historical inventory was not remeasured after the repairs. Profiling began after `django.setup()` and recorded only the main thread. It excludes tests, migrations, generated files and root entry points (`start.py`, `manage.py`); startup hooks therefore appear unobserved. It measures calls, not line/branch coverage or successful assertions.

| Area | Observed / defined |
| --- | ---: |
| analytics | 24 / 25 |
| core | 86 / 126 |
| database | 20 / 44 |
| exams | 35 / 73 |
| feedback | 12 / 20 |
| groups | 23 / 27 |
| learning | 35 / 39 |
| master_exams | 100 / 135 |
| planning | 17 / 26 |
| questions | 189 / 261 |
| users | 67 / 88 |
| config | 0 / 4 |
| scripts | 0 / 44 |

This is not verification of every backend function. MariaDB, production cache/hashing, real backup/restore, full PDF rendering/native dependencies, deployed HTTP/device workflows and concurrent workloads beyond the [bounded PostgreSQL matrix](concurrencyLimits.md) remain unverified. Mocked operator tests do not establish real database administration support. See the [manual matrix](../../../Android/docs/verification/manualVerification.md).

## Reproduce

Run from `backend/` in the Quiz Python environment:

```bash
python manage.py test tests --settings=tests.test_settings --noinput
QUIZ_TEST_POSTGRES_DB=test_quiz_codex_20261010 python manage.py test tests --settings=tests.postgresql_settings --keepdb --noinput
```

The PostgreSQL overlay reads the existing PostgreSQL connection credentials from the application configuration but substitutes the isolated test database. `mpsql` lacks `CREATEDB`; the user already provisioned this database. On another computer, create a dedicated test database once using an administrator, then use its exact name:

```bash
sudo -u postgres createdb --owner=mpsql test_quiz_backend
QUIZ_TEST_POSTGRES_DB=test_quiz_backend python manage.py test tests --settings=tests.postgresql_settings --keepdb --noinput
```

Use a dedicated test database: tests create/flush tables and records there. `--keepdb` retains its schema for the next run. Suite output can include generated test credentials; keep raw output private. Never select an application database as the test database.

For focused reruns replace `tests` with `tests.management.test_seed_pro_users` or `tests.edge_cases.test_concurrency_limits`. The original two-thread case is `tests.edge_cases.test_concurrency`. Fix and rerun affected suites before repeating the full matrix.
