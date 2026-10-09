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

Implemented the reviewed consistency issues and learning improvements: immutable source-identified events and compact learning days; versioned exposure/presentation evidence; content-aware live statistics and translated assessment validation/provenance; chronological delayed-event replay; early relearning guards; occurrence-day planner/streak/activity and richer progress metrics; coverage-qualified concepts; selectable coverage/balanced/review strategies and case-grouped automatic sets; serialized start selection; cumulative selected-download budgets independent of bulk flags; archived master results; explicit bookmark state and caller-owned question creation/duplication receipts; mandatory question/knowledge/group revisions. Coordinated Android/Vue DTOs, setup, reports, archived weighted scores and explicit uncertain-write recovery. Database clear source includes new evidence/receipts and streak resets; it was not executed.

The user explicitly plans to clear old data; new models target a matching fresh schema, with no backfill or migration action performed. [Implementation contract](learningConsistency.md) records exact policies, schema distinctions, pending runtime scenarios and in-session versus durable recovery limits. Production AST, JS/extracted Vue syntax, JSON, Android XML/resources/Kotlin delimiter and whitespace checks only. No builds, suites, database queries/writes/setup, migrations, deployment or versions; live correctness remains unverified.
