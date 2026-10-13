> Historical snapshot before the 2026-10-10 documentation reorganization. Current status: [documentation index](../../README.md). Do not use unchecked items here as the current queue.

# Backend remaining work

Updated 2026-10-09. Detailed integration scenarios: [archive](../2026-10-09-workPlan.md). Current [Android comparison](../../../../Android/docs/reference/functionalityReview.md) separates missing native controls from existing backend capabilities.

- [Learning/model review findings](../reviews/2026-10-09-backendLearningReview.md) are implemented in source; see [contracts and fresh-schema requirements](../../contracts/learningConsistency.md). Verify event ordering/replay, content/translation statistics, relearning, occurrence-day activity, concept diversity/coverage, selected-download budgets, archived master results, write receipts and mandatory revisions over live HTTP/server-database concurrency. No database/setup/migration action has been run; deleting a DB alone with old migration files present is insufficient.
- Verify per-user automatic question variety across repeated category/tag/bookmark/blueprint starts, sparse/legacy history, private visibility, paused/master allocations, quota shortages and large histories. Exact manual IDs, SRS and fixed master sets must retain their contracts; see [selection policy](../../contracts/questionSelection.md).
- Reload matching source and verify Android permission-only user lookup, knowledge linked questions, own-session endpoints, login CSRF/rotation/expiry and exact ordinary result recovery over real HTTP.
- Verify the actual selected database's source-session identity and OfflineCompletion receipt structures. Recorded read-only local SQLite readiness does not verify another deployment. Fresh initialization versus existing migration folders follows [startup guidance](../../guides/START_HERE.md); setup/migration work requires explicit authorization, rather than an unconditional demand for additive migrations.
- Verify the full-bank offline catalogue over HTTP: independent tests.download_full_bank/tests.start gates and marked pack requests, per-user grants/explicit denial/role inheritance, public/own-draft visibility, closed-book exclusions, bounded keyset traversal and content/permission changes between catalogue and pack reads.
- Verify offline signed packs/snapshots/privacy and durable receipts: identical retry must not duplicate grading/learning; altered/cross-user uploads must reject. Verify history/receipt rollback, imports/backup/restore/clear and deletion integration.
- Verify current PDF links with a freshly generated Android-requested PDF and both locales/layouts/themes. Existing files require regeneration. Check real WeasyPrint pagination/images/limits and manual PDF/Excel/CSV/JSON selection visibility/order/validation.
- Verify [backend review corrections](../reviews/2026-10-08-backendReview.md) over HTTP and isolated MariaDB/PostgreSQL concurrency: relationships, learning/planner state, taxonomy, master composition/start/finish/deletion, permissions and transactional rollback. SQLite checks do not establish production row-lock behavior.
- Verify exact-list/legacy tags, bulk-tag visibility/revisions/rollback, content revision/conflict behavior and account/session lifecycle with both clients.
- Verify real startup/interactive launcher/Tk tutorial, platform virtualenvs/ports/proxy/media/CSRF and simultaneous SQLite/MariaDB isolation; diagnostics remain read-only.
- Verify PostgreSQL connectivity/ORM/session/cache integration with compatible driver and existing database. Native PostgreSQL provisioning/backup/restore administration remains unsupported and requires separate scope.

Run environment/system checks only when authorized and dependencies are available. No migration inspection/work, suites, builds or version changes without explicit request. Keep destructive operator verification deliberate and isolated.

Verify the new category/case/tag/settings revision contracts and category/knowledge creation receipts with matching clients, fresh schema and real lost-response/concurrent HTTP writes; see [contract log](../../contracts/learningConsistency.md). Source implementation is complete; runtime/schema verification is pending.

Full Android case/knowledge management pagination is implemented in source. Verify large result sets, page failures/retry, searches and deleted final pages with matching backend/app; see the latest [work log](../../workDone.md).

## 2026-10-09 project rescan follow-up

The [new source review](../../../../Android/docs/archive/reviews/2026-10-09-projectRescan.md) identifies seven additional bounded gaps: web account-generation guards; orphan pending-create/form association; transactional question ownership checks; knowledge-delete revisions; terminal/deleted receipt recovery; web conflict resolution; learner case pagination/read retention. All seven are now addressed in source; remaining checks are runtime release gates.

The seven rescan findings are source-complete. Validate coordinated DELETE/receipt contracts, account-switch cancellation, conflict review, orphan-save recovery and learner paging; see the latest [work log](../../workDone.md).

## 2026-10-09 deeper transaction/lifecycle findings

The [deeper source review](../../../../Android/docs/archive/reviews/2026-10-09-deepTransactionReview.md) records eight new follow-up areas: knowledge/learning lock order, import revision reuse, master attempt resume/makeup and fresh access gates, master answer/navigation concurrency and web uncertainty handling, polling disposal/attempt scope, and planner revision/scope epochs. All eight findings are now source-complete; verify coordinated contracts, fresh planner schema and live interleavings. See the latest work log.
