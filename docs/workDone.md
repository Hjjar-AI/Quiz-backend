# Work Done

## 2026-10-06

- Partial/deferred-save invariants validate actual persisted field combinations under transaction/row lock.
- Serialize learner reviews with locked read/apply/save, replacing stale bulk overwrite; streaks reread persisted learner. Early correct practice never raises ease/spaced repetitions or defers due date; fragile stays below mastery.
- Separated knowledge-object mastery evidence from question-variant coverage.
- Schema/version-neutral grading snapshot/result fingerprints; question/knowledge/case edits invalidate derived learning. Frozen answers still grade; stale/unidentifiable legacy evidence cannot establish current mastery.
- Added knowledge-object model/translation validation, positive source pages, and transactional API content/tag writes. Added flag resolution/attempt ownership/question membership guards and blocked edits to completed exams.
- Committed learning credits planner, including unfinished/discarded study. Scope/window changes reset today's ledger; target-only changes preserve credit; earlier days stay historical.
- Verified Django model checks, syntax, whitespace, and isolated SQLite scenarios covering partial/deferred saves, due/early reviews, fingerprints, content invalidation, concept coverage, planner ledgers/scope changes, stale streak objects, knowledge validation, and flag relationships. Used only an in-memory database. Full API/CAS integration and MariaDB concurrency checks were unavailable because system Python lacks pandas/DRF and no isolated MariaDB verification instance was used. No project database, migrations, test-suite files, builds, compilation tasks, or versions were changed.
- Runtime guards on Question/TestHistory/MasterExamAttempt/User/UserQuestionAttempt/StudyPlanner: ordinary saves plus field-scoped model clean() errors.
- Guard choices/answers, result counts/percentages, completion/deadlines, counters/streaks, learning and planner dates/targets. Superuser creation rejects contradictory flags/roles; question import duplicate-moderation remains.
- Added explicit validation before the learning service's bulk writes.
- Verified Python syntax, Django model checks, valid instances of all six models, 20 invalid cases through validation and save guards, superuser rejection, and SRS transitions using isolated in-memory settings without database writes. No migration files, test-suite files, builds, compilation tasks, or versions were changed.
- These are runtime guards; raw SQL and other bulk/queryset writes are not covered by them. Existing database schema and constraints are unchanged.
- Normalize Excel/CSV heading whitespace/BOM/case so choice columns through `choice_8` are recognized.
- Reject normalized heading collisions; flat-file validation includes source row. Correct answer must reference filled choice; reported limit uses actual row choice count.
- Verified import changes with Python syntax parsing and diff whitespace checks; no builds, compilation tasks, test suites, or migration work were performed.
- The reported spreadsheet failure still needs confirmation using the original file; heading differences are a possible cause, not a confirmed diagnosis.
- Reviewed the application data model and PDF export pipeline.
- Added safeguards against cyclic tag hierarchies in model writes, serializers, imports, and tag merges.
- Added question lifecycle, verification, counter, and version constraints.
- Added master-exam timing, weight, version, and unique question-order constraints.
- Made master-exam reordering safe while unique order constraints are active.
- Corrected the bundled Arabic font filename used by PDF export.
- Added graceful handling for unavailable WeasyPrint native dependencies.
- Added configurable PDF question/image limits and a PDF-specific rate limit.
- Updated PDF deployment documentation.
- Verified Python compilation, Django model checks, font resolution, and diff whitespace checks.
- Did not create or review migration files.
- Added a comprehensive backend README covering SQLite/MariaDB setup, configuration, API layout, operations, deployment, and troubleshooting.

## Android bulk-tag integration review — 2026-10-07

- BulkTagUpdateView applies `visible_to(request.user)` like bulk verification: inaccessible-only IDs return 400 before service; mixed counts include visible processed rows only.
- Bulk tags lock questions in PK order and include tag creation in transaction. Actual membership changes alone advance revision/timestamp; no-ops preserve revision, enabling normal editor CAS. Processed-count/payload contracts unchanged.
- Reviewed native caller, DTO/payload, capability, tag limits and recovery wiring. Verified production Python AST syntax, source contracts and diff whitespace only. Live MariaDB concurrency, permission and rollback checks remain pending. No test suites, migrations, builds or configured version changes were performed.

## Native exact-name question tags — 2026-10-07

- Question `tags`: legacy CSV or exact-name list; DRF CharField(max_length=50, allow_blank=False) validates/trim/dedups strings while preserving commas. CSV semantics, including empty clear, unchanged.
- Create/locked-CAS update consumes arrays; [] clears, omission preserves. Transactions/permissions/revisions remain. Deploy matching backend with native array-writing editor.
- Reviewed source/AST and native contracts only. DRF is unavailable in this shell; live serializer/database validation remains pending. No migration or test-suite work, builds, configured versions or schema changes were performed.

## Backend logic/model review — 2026-10-08

- Fixed login CSRF enforcement, active-session account expiry, stale password and scheduled-renewal saves, and stale full-row question verification writes.
- Standardized learner user/session locking, ordered author/stat locks, and removed incidental author/owner locks from question editing. Exam edits/starts now check fresh locked lifecycle state; composition caps and inline draft rollback are guarded. Answer deadlines are checked after lock acquisition with durable timeout completion.
- Corrected nullable case stems and case-detail validation, blueprint nonfinite and overflowing weights, audit failure savepoints, knowledge-aware content clearing without implicitly committing sequence-reset DDL, and knowledge tag-merge retention.
- Updated Android login transport to send CSRF and drop the rotated token. Deploy matching client/backend source; old Android login requests will fail CSRF checks.
- Thirteen isolated in-memory SQLite scenarios and AST parsing of 220 production Python files passed. Clear verification substituted backup creation. No project database, migration/test-suite files, builds, compilation, packaging or configured versions changed. DRF/pandas are absent; live HTTP/MariaDB/Android checks remain.
- Findings, scope and verification limits are logged in `backendReview.md`.

## Startup scenarios and configuration — 2026-10-08

- Added `start.py` with SQLite forwarding and an existing-MariaDB HTTP development mode (default ports 5004/5005). MariaDB never runs schema setup or seeding.
- SQLite options: venv/data root/DB/frontend origin and read-only diagnostics. Probe candidates before re-exec; incomplete environments cannot bounce; explicit venv is authoritative.
- Local settings isolate production secure-cookie/cache values, preserve explicit CSRF origins, and distinguish cookies for separate SQLite databases. MariaDB keeps configured credentials/cache while using a separate HTTP settings overlay.
- Frontend proxy target is configurable and forwards media; occupied frontend ports fail explicitly. `START_HERE.md` covers simultaneous databases, custom ports, Termux/private storage, Windows environments, LAN access and diagnosis.
- Launcher help/diagnostics, argument/port guards and temporary copied-settings scenarios passed. No server, migration/setup, database writes, dependency installs, builds or compilation were run. Current shell lacks several Python dependencies and Node; full Django/Vite/Termux/MariaDB startup remains unverified.

## Environment-selected database backend — 2026-10-08

- `.env` DB_ENGINE selects MariaDB/MySQL/PostgreSQL/SQLite or installed Django backend; default MariaDB. Isolated defaults/options; PostgreSQL DB_SSLMODE optional.
- start.py selects .env unless explicit override. Generic local overlay retains old MariaDB import alias; PostgreSQL readiness accepts psycopg/psycopg2 without MySQLdb. Explicit portable SQLite ignores server DB_NAME.
- Missing python-dotenv now fails clearly when a .env exists, avoiding silent use of the wrong database. Updated examples and startup/dependency documentation.
- Inline configuration checks, five temporary copied-settings scenarios, mocked launcher routing, current/candidate driver probes and AST parsing of 227 production Python files passed; whitespace passed. No migration/test-suite files, builds, dependency versions, installs, live servers or project databases were touched.
- PostgreSQL is configuration-ready; live application/locking integration remains unverified. Existing database administration APIs and provisioning do not support it.

## Documentation organization and agent guidance — 2026-10-08

- Kept README/Agents at the project root; moved supporting Markdown into `docs/` and added a documentation index. Preserved work history and pending checks.
- Updated relative links and compacted agent guidance around related-code review, explicit work restrictions, portable configuration and honest verification limits.
- Checked documentation targets, moved content and whitespace; no builds, test-suite or migration work, dependency/version changes or runtime changes were performed.

- Documentation compaction: retained commands, technical literals, dates, headings/links and checklist states; consolidated repeated prose/verification scope. Documentation/whitespace checks only.

## Backend linked-logic follow-up — 2026-10-08

- Serialized bookmark/report writes; retained first-resolution attribution in API/admin, with actual bulk counts and unrelated integrity failures propagated. Master reports use frozen membership.
- Replaced shared permission caching with current DB reads plus request-instance memoization; legacy cleanup follows commit. Malformed role JSON fails closed.
- Replaced nullable joined locks with separate ordered question/case/knowledge locks for editing/SRS. Master finish locks user → exam → attempt and checks time after locking.
- Case resolution protects populated stems from stale callers. Knowledge/group partial edits reread locked state, preserving independent changes and current knowledge revisions. Knowledge/tag counts hide other users' drafts.
- Thirteen new isolated in-memory scenarios and the earlier thirteen passed; AST parsing passed for 226 production Python files and whitespace checks passed. Count queries were source-extracted without DRF; knowledge serializer remains source-reviewed. No live project DB, migration/test-suite, build, installation or version work. PostgreSQL/MariaDB concurrency and full DRF integration remain pending; see `backendReview.md` and `workPlan.md`.

## Interactive development launch — 2026-10-08

- `python start.py -i` / `--interactive`: database selector, combined backend/frontend or backend-only launch, read-only diagnostics and command preview. Optional ports/LAN/venv/SQLite data root. Existing CLI behavior preserved; credentials remain in `.env`.
- Combined mode sets Vite API/media proxy and browser origin per process, checks frontend prerequisites and supervises both processes with Ctrl+C/companion-exit cleanup. No backend autoreloader; frontend hot reload retained. Menu uses existing schemas and disables SQLite setup/seeding.
- Inline menu/routing/validation/cancellation/preview checks and harmless child exit/cleanup passed; AST/whitespace passed. No real app server, database access/setup, builds, dependency installs, migration/test-suite or version work. Full Windows/Termux/runtime/frontend integration remains pending.

## PDF answer sections and paper quiz — 2026-10-08

- POST PDF options: `pdf_mode=study|quiz`, `answer_layout=inline|end|after_25|none`; defaults preserve current themed inline exports and existing GET callers. Validated through API/facade/flat exporter to PDF renderer; filters, limits, locale, images, front matter and attachment behavior retained.
- Separate sections begin on new pages, with global numbering, correct choice/explanation and question ↔ answer anchors. After-25 mode includes the final partial group and starts the next question group on a new page.
- Quiz overrides answer placement to none; compact white/light-grey styling, neutral choices, no explanation/answer links or source/tag hints. Vue controls and Arabic/English copy match the API; other formats remain unchanged.
- Eighty-four isolated HTML/CSS cases passed across two locales, six question counts and seven mode/layout combinations, including anchors, batch order, escaping, theme retention and quiz suppression. WeasyPrint and an unused DRF response import were substituted; no actual PDF or HTTP integration was verified. No app data, migrations/test suites, builds or versions changed.

## Manual PDF question selection — 2026-10-08

- Optional POST `question_ids`: nonempty positive 64-bit IDs, configured PDF limit, deduplication and caller order. Manual selection replaces content filters; filter-based/non-PDF exports retain prior behavior. API/facade/exporter forward the authenticated actor.
- Selected rows are checked against public/owned-draft visibility and verified-only gates. Any unavailable row rejects the whole selection with a generic 404; empty/invalid selection cannot fall back to the entire bank. Recheck after materialization handles intervening deletion. Existing PDF limits/layout/quiz answer suppression remain.
- Six isolated SQLite scenario groups passed for ordering/filter independence, invalid/empty/non-PDF use, limits, missing/private IDs, verified-only and filter-mode regression. PDF renderer/pandas/unused DRF response import substituted; no HTTP/PDF integration, project data, migrations/test suites, builds or versions touched.

## Custom selection for all question exports — 2026-10-08

- Extended ordered POST `question_ids` to Excel/CSV/JSON and verified-only exports, superseding the earlier PDF-only restriction. Shared validation/visibility, deduplication, filter independence and all-or-nothing rejection run before artifact creation. Flat manual selections cap at 10,000 submitted IDs; PDF retains `PDF_EXPORT_MAX_QUESTIONS`. Existing row schemas, formula sanitization and filter GETs retained; portable state packages remain filter-based.
- Disposable in-memory SQLite checks passed across all four formats: ordered/deduplicated rows, malformed/empty/private/missing IDs, no failure artifacts, owner drafts, verified-only gates, filter regressions and independent limits. Actual JSON files checked; pandas CSV/Excel and PDF writers substituted. AST/whitespace checks passed. No project data, migration/test-suite work, builds, installs or versions changed; DRF/real writer/browser integration remains pending.

## Root Python organization — 2026-10-08

- Kept `start.py`/`manage.py` at backend root; moved SQLite launcher, interactive helper and standalone tutorial to the existing `scripts/` package. Updated delegation/imports, backend/frontend/app/data/venv path resolution, current docs/requirements comments and agent guidance. `python start.py sqlite` replaces old root SQLite commands; direct helper: `python scripts/start_sqlite.py`. Tutorial: `python scripts/startup_tutorial.py`. Setup behavior and read-only tutorial contract retained.
- Six Python AST checks, help commands and all four interactive previews passed from backend and `/tmp`; checked root/import/venv paths, interpreter/argument forwarding and server-mode helper/.env routing (loader/dependency probes substituted). Whitespace passed. No actual servers, GUI, project data/settings reads, builds, migration/test-suite work, installs or versions changed. Live app/reloader/Windows/Termux behavior remains pending.
# Backend model relationship review — 2026-10-08

- Reviewed all backend model definitions and related production relationship paths. Recorded four unresolved findings in `backendReview.md` and follow-up work in `workPlan.md`; application code unchanged.
- Disposable in-memory SQLite checks confirmed cross-exam shared-draft deletion, stale learning after case/knowledge deletion, and planner scope broadening after its last target disappears. Tag-cycle concurrency remains a source-derived risk. No project data, migrations/test suites, builds or dependencies were changed.

## Relationship corrections — 2026-10-08

- Preserved master-exam drafts shared with other exams; current-exam-only membership deletion retains other compositions/versions. Added transactional deletion signals to invalidate learning when cases/knowledge objects detach questions.
- Protected planner targets across taxonomy API/admin/queryset deletion; users remove/replace subscriptions before deletion. API returns envelope 409 and admin previews explain protection. Intentional empty targets retain unrestricted behavior; clear ordering removes planners first.
- Serialized tag hierarchy writes with a reserved Setting mutex; used current locked ancestry reads and atomic merges. Preserved merge associations, avoided stale parent writes during renames, and aligned planner API/admin lock ordering with merges. No schema changes.
- Six disposable SQLite scenario groups, isolated Django model checks, production app AST parsing (219 files), and whitespace checks passed. Merge HTTP helpers and clear backup were substituted; source-extracted production leaf functions were exercised. Full DRF/admin integration and live MariaDB/PostgreSQL concurrency remain pending. No project data, migrations/test suites, builds, installs or versions changed.
