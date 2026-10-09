# Backend remaining work

Updated 2026-10-09. Detailed integration scenarios: [archive](archive/2026-10-09-workPlan.md). Current [Android comparison](../../Android/docs/functionalityReview.md) separates missing native controls from existing backend capabilities.

- Verify per-user automatic question variety across repeated category/tag/bookmark/blueprint starts, sparse/legacy history, private visibility, paused/master allocations, quota shortages and large histories. Exact manual IDs, SRS and fixed master sets must retain their contracts; see [selection policy](questionSelection.md).
- Reload matching source and verify Android permission-only user lookup, knowledge linked questions, own-session endpoints, login CSRF/rotation/expiry and exact ordinary result recovery over real HTTP.
- Verify the actual selected database's source-session identity and OfflineCompletion receipt structures. Recorded read-only local SQLite readiness does not verify another deployment. Fresh initialization versus existing migration folders follows [startup guidance](START_HERE.md); setup/migration work requires explicit authorization, rather than an unconditional demand for additive migrations.
- Verify the full-bank offline catalogue over HTTP: independent tests.download_full_bank/tests.start gates and marked pack requests, per-user grants/explicit denial/role inheritance, public/own-draft visibility, closed-book exclusions, bounded keyset traversal and content/permission changes between catalogue and pack reads.
- Verify offline signed packs/snapshots/privacy and durable receipts: identical retry must not duplicate grading/learning; altered/cross-user uploads must reject. Verify history/receipt rollback, imports/backup/restore/clear and deletion integration.
- Verify current PDF links with a freshly generated Android-requested PDF and both locales/layouts/themes. Existing files require regeneration. Check real WeasyPrint pagination/images/limits and manual PDF/Excel/CSV/JSON selection visibility/order/validation.
- Verify [backend review corrections](backendReview.md) over HTTP and isolated MariaDB/PostgreSQL concurrency: relationships, learning/planner state, taxonomy, master composition/start/finish/deletion, permissions and transactional rollback. SQLite checks do not establish production row-lock behavior.
- Verify exact-list/legacy tags, bulk-tag visibility/revisions/rollback, content revision/conflict behavior and account/session lifecycle with both clients.
- Verify real startup/interactive launcher/Tk tutorial, platform virtualenvs/ports/proxy/media/CSRF and simultaneous SQLite/MariaDB isolation; diagnostics remain read-only.
- Verify PostgreSQL connectivity/ORM/session/cache integration with compatible driver and existing database. Native PostgreSQL provisioning/backup/restore administration remains unsupported and requires separate scope.

Run environment/system checks only when authorized and dependencies are available. No migration inspection/work, suites, builds or version changes without explicit request. Keep destructive operator verification deliberate and isolated.
