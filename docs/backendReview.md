# Backend logic and model review — 2026-10-08

## Additional relationship review — findings corrected (2026-10-08)

- High: `master_exam_service/lifecycle.py` deletes all `MasterExamQuestion` memberships for drafts selected by one exam's delete operation, including memberships in other exams. Their composition changes without a version bump, and the shared question disappears. Preserve drafts referenced by another exam and restrict detachment to the exam being deleted.
- High: deleting `ClinicalCase` or `KnowledgeObject` detaches questions through SET_NULL without invalidating `UserQuestionAttempt`. Save hooks cover edits but no deletion hook covers these paths. Existing SRS/mastery evidence survives assessed-content removal. Invalidate affected learning records transactionally across API, admin and queryset deletion paths.
- Medium: removing a planner's last category/tag target through taxonomy deletion leaves empty M2M sets. Progress interprets that as unrestricted scope and credits unrelated answers. Preserve the distinction between an intentionally unrestricted plan and a targeted plan whose targets disappeared.
- Medium, concurrency risk: `Tag.save()` checks ancestry before writing without serializing hierarchy changes. Concurrent A → B and B → A edits can both pass against the old graph and create a cycle; the self-parent constraint does not prevent it. The tree endpoint then has no root for that component. Serialize hierarchy mutations and validate current ancestry within the same transaction, including merge/import/admin paths.

Verification: disposable in-memory SQLite checks confirmed retained learning rows after case and knowledge-object deletion, loss of another exam's shared draft/membership without its version changing, and unrelated planner progress changing from zero to one after target deletion. The exam deletion check executed the actual source-extracted production functions to avoid optional package dependencies. All backend model definitions were read, including empty analytics/database model modules, with related production callers traced. Tag concurrency is a source-derived risk, not a reproduced server-database race. No application code was changed, project data accessed, migration/test-suite files inspected, or builds run.

### Implementation and verification follow-up

- Exam deletion locks candidate drafts, retains those referenced by another exam, and restricts membership deletion to the current exam. Other exams keep their questions and revisions.
- Questions app signals capture affected question IDs under locks, then invalidate learning after SET_NULL deletion inside the collector transaction. Instance/admin/queryset deletion uses the same behavior, with rollback preserving both links and evidence.
- Planner-subscribed tags/categories are protected from deletion until users remove or replace the targets. API returns an envelope 409; admin deletion previews display protected plans. M2M additions share taxonomy locks with deletion guards. Intentional target clearing still allows unrestricted plans. Database clear removes planners before protected taxonomy.
- Tag saves and merges serialize through a reserved Setting row on the selected database. Ancestor reads under the lock use current locking queries. Merges run atomically and preserve planner subscriptions, knowledge/question links and child hierarchy; planner API/admin writes acquire hierarchy before planner locks. Partial tag rename saves preserve parent state. The mutex is hidden from settings administration.
- Six isolated scenario groups passed: case/knowledge instance/queryset deletion, unrelated evidence and rollback; shared versus exclusive draft deletion; protected tag/category deletion and intentional scope clearing; cycle rejection/partial saves; merge associations, duplicate sources and ancestor rejection; content-clear ordering with backup substituted. Lifecycle/merge/clear leaf code was source-extracted to avoid unavailable optional dependencies; DRF validation/response/audit helpers were substituted for merge checks.
- Django model checks (isolated settings with the actual custom user model), AST parsing of 219 production app files, and diff whitespace checks passed. Vue taxonomy stores already preserve local state on envelope failures; Android uses standard API error handling. No payload changes are required.
- No live project database, migrations, test-suite files, builds, dependency installs, or versions were changed. Full HTTP/admin behavior and MariaDB/PostgreSQL concurrency remain verification gates. Direct raw SQL/bulk parent updates must observe the same hierarchy mutex; existing corrupt data was not inspected or repaired.

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
- Follow-up fixes below also require live PostgreSQL/MariaDB and DRF verification.

## Follow-up: concurrency, permissions and linked content — 2026-10-08

| Finding | Correction and related paths |
| --- | --- |
| Concurrent reports could bypass MariaDB's unsupported partial unique index; bookmark toggles could race. | Feedback writes lock the learner before reading/writing feedback rows. Duplicate handling retains its savepoint and propagates unrelated integrity failures. Direct ORM writers still need equivalent serialization on MariaDB. |
| Repeated API/admin resolutions replaced the first moderator's attribution. | Both use conditional unresolved-row updates through one service; bulk administration reports actual changes. |
| Shared permission caching could retain revoked grants or publish rolled-back grants. | Role resolution reads the database and keeps request-instance memoization. Legacy cache cleanup waits for commit; malformed stored role JSON fails closed. This adds a role lookup per resolved user instance. |
| Nullable joined locks fail on PostgreSQL and obscure the related rows being locked. | Question editing and SRS lock questions, then case/knowledge rows separately in ordered queries. Learning fingerprints and invalidation remain protected. Master finishing explicitly locks user → exam → attempt, matching start. |
| A stale case instance could overwrite a populated shared stem. | Every case resolver caller now rereads/locks current state before filling an empty stem; existing populated stems are retained. |
| Partial knowledge/group edits could write unrelated stale fields and lose concurrent changes. | Updates reread locked rows before applying the supplied fields; knowledge revisions advance from current state. |
| Tag/knowledge counts exposed other users' private drafts. | List/detail/update counts use the same visible-question scope as question reads; verified tag counts apply both filters. Response shapes are unchanged. |
| Master reporting used current composition rather than the attempt snapshot; finishing timed the request before waiting for locks. | Reports check frozen question IDs, matching model invariants. Finish classifies timeout and records completion time after acquiring locks. |

- Thirteen additional disposable in-memory SQLite scenarios passed: bookmark state; report dedup/resolution/bulk attribution; rollback/error propagation; stale case stems; permission cache/revocation/rollback; commit-only cleanup; nullable lock-query structure; stale learning evidence; delayed finish; malformed role JSON; stale group edits; knowledge counts; tag counts. Earlier thirteen scenarios also passed again.
- Count checks execute source-extracted production query helpers without DRF. Nullable-lock checks inspect query structure and execute on SQLite; they do not prove PostgreSQL SQL/locking or server-database concurrency. Knowledge serializer changes remain source-reviewed pending DRF.
- AST parsing passed for 226 production Python files, excluding migration/test-suite paths; final diff whitespace checks passed.
- Related feedback, case-resolution, permission, exam, learning, administration and Vue/Android transport callers were traced. No endpoint/request shape changed; clients need no payload changes for this pass.
- No project database, migration/test-suite files, builds, packaging, dependency installation or versions were changed. DRF/pandas remain unavailable; live HTTP and PostgreSQL/MariaDB integration remain pending.
