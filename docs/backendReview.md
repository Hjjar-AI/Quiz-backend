# Backend logic and model review — 2026-10-08

Reviewed model definitions and principal API/service paths for authentication, permissions, questions/cases/knowledge, ordinary and master exams, learning, planning, feedback, groups, taxonomy, and database operations. Fixes below were traced through their related callers and persistence paths. This is not a claim that every import/export branch or deployment behavior has been exercised. Migration files and test-suite files were excluded from inspection.

## Critical and high-impact fixes

| Finding | Correction and related paths |
| --- | --- |
| Anonymous login bypassed DRF session CSRF enforcement. | Login explicitly calls session authentication's CSRF check. Web already sends a token; Android login now obtains/sends the token and Origin through its standard transport, then drops the token rotated by Django. |
| Existing authenticated sessions could keep using an expired account. | Renewal middleware now signs out expired accounts and returns the standard 401 API envelope, retaining automatic renewal and capability-based expiry exemption. |
| Password and scheduled renewal saves could overwrite unrelated user fields from stale objects. | Self-service password changes lock/reread the account before checking the current hash. Password saves and scheduled renewal write only their intended fields. Admin password resets likewise save only password/forced-change state. |
| A verification toggle could overwrite question content or repeat a stale toggle decision. | Toggle rereads/locks persisted state and saves only verification metadata. Author counters remain in that transaction. |
| Session replacement/resume locked user then session, while answer/finish/pause/cleanup could lock session then user. | Learner writers now consistently acquire users before session/attempt rows. Multi-user cleanup and verification author locks use PK order; question statistics update in question-ID order. Question editing no longer locks joined author/owner rows incidentally. |
| Master-exam mutation and start gates used a stale, pre-lock exam object. | Composition, scalar/audience updates, and starts reread lifecycle/timing under the exam lock. Revision checks also cover no-op additions. Composition enforces the configured question limit, and inline case/draft writes roll back together. Composition audit logging runs after commit. |
| An answer waiting for a row lock could be accepted after its deadline. | Deadline is checked against the locked attempt at acquisition time; forced completion commits outside the rejected answer transaction. Direct service calls also reject nonpositive/boolean answers. |
| Clearing a case stem to null was accepted by the API but rejected by its model. | Model invariants now accept the field's declared null state. Case-detail writes validate title/stem before applying either change. |
| Blueprint weights could contain infinity/NaN; large finite weights could overflow allocation. | API/model guards reject invalid weights, category keys normalize before replacement, bulk writes validate, and selection scales relative weights before arithmetic. |
| A failed best-effort audit insert could poison an enclosing transaction. | Audit inserts have their own savepoint so the documented log-and-continue behavior holds for database errors. |
| Content clearing omitted knowledge objects and ran implicitly committing MariaDB DDL inside its transaction. | Knowledge objects are included. Clearing retains monotonic IDs and executes transactional deletions without sequence-reset DDL. Safety backup remains required. |
| Tag merging discarded knowledge-object memberships and could process a duplicate source twice. | Knowledge associations move to the target before source deletion; each normalized source is consumed once. |

## Verification performed

- AST parsing passed for 220 production Python files, excluding migration/test files.
- Thirteen standalone scenarios passed against a new in-memory SQLite database: stale verification, nullable cases, invalid weights, composition/CAS/caps, stale lifecycle gates, snapshot/start/answer bounds, persisted deadline timeout, password/reset races, account expiry/renewal/exemption, audit savepoints, extreme-weight allocation, incremental learning idempotency, and clear rollback.
- The clear scenario substituted backup creation; no actual backup, project database, restore, or destructive operation was run.
- Optional import/export package facades were bypassed to load actual leaf services without unavailable pandas/DRF. API views/serializers were source-reviewed only.
- Backend and Android diff whitespace checks passed. Existing unrelated edits were preserved. No build, compilation, packaging, migration, test-suite or configured version work was performed.

## Remaining verification

- Full DRF integration: anonymous login CSRF rejection/acceptance, standard error envelopes, case metadata validation, weight validation and normalized category keys, admin password reset, and tag merge relationships/duplicate inputs.
- MariaDB concurrency: simultaneous start/resume/answer/pause/finish/cleanup, verification and content edits; lock ordering was reviewed in source, but SQLite cannot establish production row-lock behavior or absence of all deadlocks.
- Deploy compatible Android source with login CSRF enforcement. Older Android clients explicitly omit the token and will receive 403 until updated. Verify login, token rotation, cookies and expiry against actual HTTPS deployment.
- Existing work-plan PDF/import/export and fresh-database verification gates remain pending. No migration history was audited and no schema update was created.
