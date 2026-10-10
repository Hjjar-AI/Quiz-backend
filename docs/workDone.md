# Backend completed source work

Updated 2026-10-09. Full dated history, earlier schema-related records and exact verification limits: [archive](archive/2026-10-09-workDone.md). This review did not inspect migration files.

- Hardened learning/grading snapshots, persisted-state validation, knowledge mastery/coverage, planner credits/streaks, ownership/report/session/master lifecycle and relationship transactions.
- Corrected exact-name and bulk-tag validation/visibility/revisions, taxonomy/knowledge/planner associations, shared-draft/content deletion and finite blueprint weights.
- Implemented coordinated PDF themes (including Ruby), answer layouts/quiz/front matter, custom ordered exports and forward-link wrapper correction; isolated export evidence does not verify current phone deployment.
- Prepared exact ordinary source-session result lookup, offline signed packs/durable completion receipts and own-session inventory/revocation. Actual deployed schema/session engine remain prerequisites.
- Added schema-free narrow `admin.permissions` user lookup and caller-scoped paginated knowledge linked questions for Android.
- Updated portable startup/helpers/interactive launch/tutorial, environment-selected database configuration and isolated SQLite settings. PostgreSQL administration remains outside implemented operator support.

Earlier AST/source/isolated SQLite checks are preserved in the archive and do not establish full HTTP or MariaDB/PostgreSQL concurrency. Recorded local SQLite structural inspection applies only to that file; no migration action occurred in the current review.

## 2026-10-09 cross-client source comparison

Compared current production routes and analytics/content/result/export contracts with Vue actions and Android services/screens/DTOs. Confirmed backend supports the remaining native analytics gate/period, export order and author-rank payload; recorded UI gaps in [Android review](../../Android/docs/functionalityReview.md). Compacted work records and corrected stale unconditional migration-readiness wording. Documentation only; no production fixes, deployment, database writes, build, suites, migrations or version changes.

## 2026-10-09 agent guidance maintenance

Compacted shared working rules without relaxing explicit build/suite/migration/version restrictions; added source-evidenced cross-client review and bounded-completion guidance. Captured uncertain toggle/create recovery, structured errors and dependent/profile freshness; Android also records compiler-signature/opt-in/cancellation/visibility checks. Frontend AGENTS now links its detailed instructions. Documentation links and whitespace checked; no production or runtime work.

## 2026-10-09 full-bank offline catalogue

Added read-only `GET exam/offline/catalog/` with independent `tests.start` permission and `Question.objects.visible_to(request.user)`, ascending-ID keyset pagination bounded by the initial maximum visible ID. IDs protected by the existing unfinished ordinary/master closed-book policy are excluded per page; existing pack generation remains the independent visibility/protection/readiness authority. Response returns candidate IDs, upper bound, nullable next cursor, current bounded visible count and excluded page count. No user/admin data or model/schema changes. Android uses this route for explicit full-bank download/pause/resume with encrypted per-pack storage; Vue contracts are unchanged.

Three changed production files passed Python AST and whitespace checks; Android DTO/request/UI/storage paths were traced. No live HTTP/database checks, suites, migrations/setup, builds, deployment or versions. Keyset bounding is not an atomic snapshot: edits/deletions/access changes still require pack rechecks. Reload the matching backend for this endpoint; completion synchronization retains its existing deployed-schema requirement. See [native contract](../../Android/docs/offlineQuestionBank.md).

## 2026-10-09 full-bank capability

Registered `tests.download_full_bank` in the canonical capability/group catalogue without member/moderator default grants. Existing admin.permissions role and per-user JSON overrides recognize it, including explicit denial overriding a role grant; admins keep their established all-capabilities policy. OfflineCatalogue requires the new capability and independently checks tests.start. PackRequest accepts optional full_bank (default false), and marked bulk snapshot requests require the new capability as well as their existing tests.start gate. Completion and selected-download gates are unchanged. Capabilities are resolved from the current request user, so revocation applies to subsequent catalogue/bulk requests.

Registry/default/group structure, production Python AST and whitespace checks passed; Android request/permission refresh/handler/button guards and web/native permission-editor lookup paths traced. No schema/model changes, migration inspection/work, seeding/setup, suites/builds, database updates, deployment or versions. Real role/override/revocation HTTP validation remains pending. See [native contract](../../Android/docs/offlineQuestionBank.md).

## 2026-10-09 moderator full-bank default

Updated the moderator seed/fallback role to include `tests.download_full_bank`; members remain off by default and per-user deny overrides still apply. Existing saved role rows are preserved rather than overwritten: older deployments can enable this one capability through Permissions → Roles → Moderator. Production AST/registry/default checks and whitespace passed; no database writes, setup/seeding, migrations, suites, builds or deployment.

## 2026-10-09 per-user automatic question variety

Generic ordinary starts now select the eligible filtered pool using user-unseen first, then lower exposure count and older last exposure, with random ties/presentation. This replaces newest-first slicing that repeatedly returned the same category/tag subset. Blueprint category quotas/fallbacks use the same user evidence without changing weights; count-only callers remain user-free. Explicit IDs/order, scheduled SRS, fixed master exams, visibility/filter contracts and maximum question counts are preserved.

A schema-free helper streams caller-owned TestHistory result IDs and ordinary/master allocation IDs; no other user's history/global counter is consulted. Stored allocations are not exact screen-view tracking; missing/deleted records, unsynchronized offline practice and concurrent starts have the limits documented in [selection policy](questionSelection.md). Current Django/Vue/Android payload/caller paths and Python AST/whitespace checked. No suites, migrations/setup, database writes, deployment, builds or versions; HTTP/performance/concurrency checks remain pending.

## 2026-10-09 backend models and learning review

Reviewed all eleven application model modules/persisted invariant hooks and traced principal content, taxonomy, concept/case, ordinary/master assessment, offline completion, SRS/mastery/queue, planner, activity/analytics, feedback, group and identity/permission flows with relevant Vue/Android callers. Recorded source-confirmed inconsistencies in live content statistics, translated assessment provenance, delayed offline chronology, early relearning credit and incremental-versus-completed activity. Distinguished these from allocation-based novelty limits, intentional mastery/retention policies and the full-bank capability's workflow boundary. Architecture, scenarios, source evidence and proposed sequence: [review](backendLearningReview.md).

Documentation only; findings remain unimplemented. Local documentation targets and patch whitespace checked. No production edits, database queries/writes, migrations, suites, builds, live HTTP, deployment or versions. Import/export/PDF/startup/operator branches were not exhaustively traced; source review does not establish runtime or server-database concurrency correctness.

## 2026-10-09 learning/model review implementation

Implemented the reviewed consistency issues and learning improvements: immutable source-identified events and compact learning days; versioned exposure/presentation evidence; content-aware live statistics and translated assessment validation/provenance; chronological delayed-event replay; early relearning guards; occurrence-day planner/streak/activity and richer progress metrics; coverage-qualified concepts; selectable coverage/balanced/review strategies and case-grouped automatic sets; serialized start selection; cumulative selected-download budgets independent of bulk flags; archived master results; explicit bookmark state and caller-owned question creation/duplication receipts; mandatory question/knowledge/group revisions. Coordinated Android/Vue DTOs, setup, reports, archived weighted scores and explicit uncertain-write recovery. Database clear source includes new evidence/receipts and streak resets; it was not executed. Archive deletion acquires learner locks before exam/attempt locks and rejects a changed participant set before writes.

The user explicitly plans to clear old data; new models target a matching fresh schema, with no backfill or migration action performed. [Implementation contract](learningConsistency.md) records exact policies, schema distinctions, pending runtime scenarios and in-session versus durable recovery limits. Production AST, JS/extracted Vue syntax, JSON, Android XML/resources/Kotlin delimiter and whitespace checks only. No builds, suites, database queries/writes/setup, migrations, deployment or versions; live correctness remains unverified.

## 2026-10-09 taxonomy/case/settings revisions and content receipts

Added Category.version and ClinicalCase.version (default 1; content-field saves increment), mandatory expected_version on their update/delete/stem APIs, a shared tag forest revision returned by tree reads, and a runtime settings revision returned by GET/POST. Revision comparisons occur within write transactions after the relevant locks; tag create/rename/reparent/delete invalidates the forest revision. Category/case DELETE passes its revision as a query parameter. Case title/stem validation and authorization complete before one atomic write; linked questions are locked before the case in the HTTP mutation paths.

New ContentWriteReceipt has a caller-scoped unique operation UUID, action, canonical request SHA-256 and nullable target ID. Category/knowledge create optionally accepts operation_id; identical successful retries return the original target, changed bodies/actions conflict, deleted results return 404. Receipt creation and target creation share one transaction; the unique receipt row serializes identities without a broad User lock. GET /api/v1/recovery/operations/<uuid>/ returns the caller's action/target metadata; ordinary target reads independently enforce capability/visibility. Own unresolved report state is readable from the question flag endpoint.

Category/Case fields and ContentWriteReceipt require matching fresh schema and clients; no schema setup/migrations/database action was performed. Normal fresh SQLite startup with old app migration folders removed can generate initial schema; deleting only the database while old migration files remain is insufficient. Source checks do not establish live database locking, deadlock behavior across all ORM writers, HTTP or client/device correctness.

Production source AST/whitespace checks only; suites/builds/setup/migrations were not run.

## 2026-10-09 full Android content-management pagination

Case and knowledge-object list endpoints now accept page/per_page for complete browsing with stable key/PK and title/PK ordering, existing filters/visibility and shared bounded page sizes. Responses include total/page/per_page/total_pages; knowledge count remains available. Requests without pagination parameters retain the legacy autocomplete contract and limits, keeping current Vue/native pickers compatible.

Android management Next/Previous now fetch server pages and render the returned batch directly. Search starts at page 1; retry retains the requested page and filters while failures preserve the previous readable page, counts, selections and editor drafts. Refresh after deletion retries the last available page when the old page is beyond the new total. Pagination controls and handlers retain recovery/permission/uncertain-write guards. The page count label is bilingual.

Verification: two affected Python production ASTs, native lexical/resource/XML/bilingual-placeholder checks and CRLF-aware whitespace checks passed. No builds/compilation, automated suites, migrations, database/setup/data generation or live HTTP/device checks. This pagination change needs matching backend/native source but introduces no schema changes. Verify datasets beyond 100 cases/500 knowledge objects, searches/filter changes, failed next-page requests/retry, final-page deletion and retained drafts against the running backend.

## 2026-10-09 project rescan

Inventoried production source and traced recovery/pagination/account/CRUD/ownership/conflict paths across Django, Android and Vue. Recorded seven prioritized findings in [project rescan](../../Android/docs/projectRescan.md). Review/documentation only; production unchanged, no builds/suites/migrations/database/runtime work. Existing completed source features remain completed; newly evidenced gaps are in the plan.

## 2026-10-09 seven rescan findings fixed in source

- Web transport uses an independent authenticated-session generation for shared requests, cancellation, success/error handling and delayed expiry redirects. Old account requests are aborted/ignored; CRUD completion guards prevent old callbacks from repopulating reset stores. Login/initial restore can publish only their own matching one-step account transition. CSRF rotation remains separate.
- Web AddView marks an orphan pending create as review-only on route departure/re-entry even when storage was already hydrated. Confirmed late results keep their receipt identity for the new view. Save/image flows also check component lifetime/account generation, so an old response cannot consume a new form's images or navigate an unmounted form. Browser draft text/images remain memory-only.
- Question update/delete services recheck current ownership/override against locked rows. Question and knowledge DELETE now require expected_version in query parameters; native detail confirmation and all reachable Vue question-delete handlers capture the displayed version before confirmation. Knowledge native deletion uses its retained editor baseline. Protected relationships/reputation behavior remain, and stale/rejected deletes retain readable items.
- Caller-scoped content receipts report whether their committed target still exists. Native category/knowledge reconciliation distinguishes deleted targets from absent operations/read failures, offers a terminal acknowledgement, preserves the typed draft and retires the exhausted UUID. Only a subsequent explicit new save creates a new identity.
- Shared bilingual Vue revision-review controls load current data independently and expose Keep draft/Use server choices for categories, tags and Settings. Drafts stay intact during read failures; tag source/target identities rebase by ID only after explicit review. Removed categories can prepare a new creation without discarding draft content. Settings dirty-state baselines adopt the reviewed server values without replacing kept inputs. Permissions/account scope gate reads and resolution; no automatic replay.
- Learner case browsing now uses server page/per_page and the configured page size, with Next/Previous. Applied query/results commit only after successful reads; failed search/page requests retain readable results and retry the requested query/page. Management pagination and bounded autocomplete contracts remain intact.

Validation: production Python AST (242 files), JavaScript/extracted Vue script syntax (299), locale JSON, native lexical delimiters (152 files), bilingual XML/resources/positional placeholders (1,382 strings per locale) and CRLF-aware whitespace checks passed. These are source checks, not compilation/runtime evidence. No builds, suites, migration inspection/work, database/setup/data generation, deployment or version changes. Matching backend/native/web rollout is required for the new DELETE preconditions and receipt status; this follow-up introduces no model/schema changes. Verify delayed responses/account switches, orphan creates, deleted receipts, stale ownership/revisions, read failures and large learner case lists over actual HTTP/device/server-database concurrency.

## 2026-10-09 deeper source review

Traced master/ordinary session transactions and callers, offline completion, learning evidence, import updates, planner configuration and web polling. Recorded eight source-evidenced follow-up areas in [deep review](../../Android/docs/deepTransactionReview.md). Review/documentation only: production unchanged, no builds/suites/migrations/database/runtime actions. Existing learning/offline protections were distinguished from new gaps; concurrency impact remains unexercised.

## 2026-10-10 eight deeper findings fixed in source

All eight bounded findings are addressed in production source; the original review remains historical evidence.

- Assessed parent saves lock linked questions before parent rows; knowledge/question/tag writers and state imports coordinate their dependency locks. Existing imported questions and knowledge objects advance the locked local revision instead of adopting the source revision. Imports deliberately take broad user/question locks; large-import contention still needs measurement.
- Master start locks fresh access relations, rechecks new-start/preview access, resumes either active normal or makeup attempts before new-start classification, and finishes expired attempts without granting extra time. Existing owned work is retained.
- Master answers require session_id and the full expected_slot (including null), compared under lock. Identical saved intent is idempotent; conflicting saved intent returns ATTEMPT_PROGRESS_CHANGED. Navigation requires session_id and expected_current_question_id; current-question reads do not persist fallback navigation. Expiry finish failures propagate.
- Web/native master recovery retains uncertain drafts, reads authoritative full answer slots, and requires explicit comparison/rebase/discard before another conflicting write. Web polling has disposal/cancellation generations and exam/session/store/progress ownership guards; route changes cannot adopt an old attempt response.
- Planner update/delete requires expected_id and expected_version; successful updates return accepted configuration/revision. Both clients retain editor baselines and provide explicit conflict resolution. StudyPlannerScope/ScopeDay preserve timestamp-based historical filter attribution: explicit filter/date changes reset today's displayed progress, taxonomy rename/merge continues it, and historical days include all their original scope activity after midnight without double counting. Global learning events remain intact.

Verification is production AST, JavaScript/extracted Vue script syntax, locale JSON, native lexical/XML/resource/placeholder and whitespace checking only. No builds, compilation, automated suites, migration inspection/work, setup/seeding, database writes, deployment or versions. Matching backend/web/native rollout and matching planner schema are required. Actual HTTP, database interleavings, browser/device recovery and accessibility remain release checks.
