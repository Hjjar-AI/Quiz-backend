# Work Done

## 2026-10-06

- Corrected invariant validation for explicit partial and deferred saves using
  the actual persisted field combination inside a transaction/row lock.
- Serialized learner review writes, replaced stale bulk overwrite fallbacks
  with locked read/apply/save operations, and made streak updates reread the
  learner's persisted state. Early correct practice does not increase ease,
  spaced repetitions, or defer the due date. Fragile answers stay below mastery.
- Separated knowledge-object mastery evidence from question-variant coverage.
- Added content fingerprints to grading snapshots/results without schema or
  version changes. Question, knowledge-object, and case-content edits invalidate
  affected derived learning state. Old frozen answers still grade, but stale or
  unidentifiable legacy snapshot evidence does not establish current mastery.
- Added knowledge-object model/translation validation, positive source pages,
  and transactional API content/tag writes. Added flag resolution/attempt
  ownership/question membership guards and blocked edits to completed exams.
- Credited planner progress when learning is committed, retaining unfinished
  and discarded study work. Plan scope/window changes reset today's ledger;
  daily-target-only changes retain credit. Earlier days remain historical.
- Verified Django model checks, syntax, whitespace, and isolated SQLite
  scenarios covering partial/deferred saves, due/early reviews, fingerprints,
  content invalidation, concept coverage, planner ledgers/scope changes, stale
  streak objects, knowledge validation, and flag relationships. Used only an
  in-memory database. Full API/CAS integration and MariaDB concurrency checks
  were unavailable because system Python lacks pandas/DRF and no isolated
  MariaDB verification instance was used. No project database, migrations,
  test-suite files, builds, compilation tasks, or versions were changed.
- Added shared runtime invariant guards to Question, TestHistory,
  MasterExamAttempt, User, UserQuestionAttempt, and StudyPlanner. Guards run on
  ordinary saves and expose field-scoped errors through model clean().
- Strengthened choice list/answer validation, result counters and percentages,
  completion/deadline consistency, user counters/streaks, learning state, and
  planner target/date bounds. Superuser creation rejects contradictory flags
  and roles. Question saves preserve the import duplicate-moderation workflow.
- Added explicit validation before the learning service's bulk writes.
- Verified Python syntax, Django model checks, valid instances of all six
  models, 20 invalid cases through validation and save guards, superuser
  rejection, and SRS transitions using isolated in-memory settings without
  database writes. No migration files, test-suite files, builds, compilation
  tasks, or versions were changed.
- These are runtime guards; raw SQL and other bulk/queryset writes are not
  covered by them. Existing database schema and constraints are unchanged.
- Normalized Excel/CSV import headings for whitespace, BOMs, and capitalization
  so recognized choice columns through `choice_8` are not silently missed.
- Rejected heading normalization collisions and added source row numbers to
  flat-file question validation errors. The correct answer must still refer to
  a filled choice; the reported limit reflects that row's actual choice count.
- Verified import changes with Python syntax parsing and diff whitespace checks;
  no builds, compilation tasks, test suites, or migration work were performed.
- The reported spreadsheet failure still needs confirmation using the original
  file; heading differences are a possible cause, not a confirmed diagnosis.
- Reviewed the application data model and PDF export pipeline.
- Added safeguards against cyclic tag hierarchies in model writes, serializers,
  imports, and tag merges.
- Added question lifecycle, verification, counter, and version constraints.
- Added master-exam timing, weight, version, and unique question-order constraints.
- Made master-exam reordering safe while unique order constraints are active.
- Corrected the bundled Arabic font filename used by PDF export.
- Added graceful handling for unavailable WeasyPrint native dependencies.
- Added configurable PDF question/image limits and a PDF-specific rate limit.
- Updated PDF deployment documentation.
- Verified Python compilation, Django model checks, font resolution, and diff
  whitespace checks.
- Did not create or review migration files.
- Added a comprehensive backend README covering SQLite/MariaDB setup,
  configuration, API layout, operations, deployment, and troubleshooting.


## Android bulk-tag integration review — 2026-10-07

- BulkTagUpdateView now filters selected IDs through `visible_to(request.user)`,
  matching bulk verification. An entirely inaccessible selection returns 400 before
  the service runs; mixed selections report only visible processed rows.
- Bulk tag changes now lock question rows in primary-key order and include tag
  creation within the method transaction. Only actual tag membership changes advance
  the existing question revision/updated timestamp; unchanged rows retain their
  revision. Normal question editor CAS/row locking can therefore detect intervening
  bulk tag changes. Processed-count and payload contracts remain unchanged.
- Reviewed native caller, DTO/payload, capability, tag limits and recovery wiring.
  Verified production Python AST syntax, source contracts and diff whitespace only.
  Live MariaDB concurrency, permission and rollback checks remain pending. No test
  suites, migrations, builds or configured version changes were performed.
