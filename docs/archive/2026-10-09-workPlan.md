# Work Plan

## Current priorities

- Verify a fresh Android-requested PDF after reloading the backend with the 2026-10-09 inline-link wrapper fix. Saved WeasyPrint 70.0 exports omitted all forward annotations; the correction restores both directions in isolated 66.0/70.0 renders. Fixed SQLite specimen: `exports/pdf-link-fixed-weasyprint70.pdf`. Existing PDFs must be regenerated; actual deployment/phone click verification remains pending.

- Verify Ruby PDF exports match the coordinated frontend palette in both locales. AST/source palette matching passed; actual PDF rendering remains pending.

- Desktop-check the guided startup tutorial on Linux/Windows/Tk: resized layout, Advanced options, sidebar/Back/Next, clipboard, menu-answer steps, LAN fields and separate help windows. Pure lesson generation, help/syntax/whitespace and headless widget checks passed; real display and actual app launch remain unverified. The tutorial stays read-only apart from clipboard copies.

- Verify the four relationship fixes in `backendReview.md` against full HTTP/admin integration and isolated MariaDB/PostgreSQL concurrency: shared-draft delete versus composition/start, content deletion versus SRS/linkage, planner subscriptions versus taxonomy delete/merge, and reciprocal tag reparenting. Source corrections and disposable SQLite checks are complete; live row-lock behavior remains unverified.

1. Verify end-to-end Arabic/English PDF on a host with WeasyPrint/native libraries.
2. Check small, image-heavy, filtered, verified-only, and front-matter PDF cases.
   - Verify `pdf_mode`/`answer_layout` with DRF and real WeasyPrint: end/after-25 page breaks, question ↔ answer links in PDF viewers, Arabic shaping, long cases/images and compact quiz printing. HTML/CSS boundary/link checks passed; pagination/PDF annotations remain unverified.
   - Verify manual PDF/Excel/CSV/JSON POST `question_ids` validation, actor scope/order, deleted/private/unverified selection errors and rendering across answer-layout boundaries. Isolated service selection checks passed; full DRF integration remains pending. Verify real CSV/Excel downloads with pandas, unchanged schemas/formula sanitization, and the 10,000-ID flat selection cap.
3. Monitor PDF defaults; adjust env limits to worker capacity:
   - `PDF_EXPORT_MAX_QUESTIONS`
   - `PDF_EXPORT_MAX_TOTAL_IMAGE_BYTES`
4. Confirm fresh-database initialization creates the constraints represented by the current models.
5. Only after explicit migration authorization/data audit: consider DB constraints for guarded result counts/percentages/dates, learning state, user counters and planner bounds.
6. Isolated MariaDB: concurrent learner reviews/content edits; complete dependencies: knowledge/question API writes. SQLite scenarios passed; production locking/full API integration unverified.

## Verification

- Run `manage.py check` when the complete backend dependency set is installed.
- Do not inspect or run test suites unless explicitly requested.
- Do not create migration files unless explicitly requested.

## Bulk-tag Android integration — pending verification

- Verify mixed visible/inaccessible IDs and inaccessible-only selection against the bulk tag endpoint; keep private drafts outside the mutation/count scope.
- Verify transactional rollback includes new tags, memberships and question revisions.
- Exercise concurrent bulk tagging and ordinary editor saves on MariaDB: actual tag changes should trigger stale-editor conflicts, while no-op changes retain revision.
- Deploy the matching backend source before validating Android bulk tag recovery. Source/AST checks do not replace live API/database verification; test-suite and migration work still requires explicit authorization.

## Exact-name question tag writes — pending verification

- Deployed exact-list/legacy-CSV `tags`: commas, blank/nonstrings, 50/51 Unicode points, dedup, empty clear/omitted preservation; invalid arrays roll back and stale versions retain 409. Deploy matching Android/backend.
- These are live verification gates; the source implementation is in `workDone.md`.

## Backend review — pending integration verification (2026-10-08)

- Follow-up: PostgreSQL/MariaDB concurrent bookmark/report writes, API/admin repeat resolution, case/knowledge edits versus SRS, cross-case reassignment, and master start/finish/deletion. Verify role revocations/rollback across workers; request-instance permissions intentionally remain memoized until the next request.
- With DRF: concurrent partial knowledge edits/revisions, frozen-attempt reporting, and caller-scoped knowledge/tag counts. Thirteen additional isolated scenarios passed; source-extracted count helpers do not establish HTTP integration.
- Exercise login CSRF, token rotation, account expiry and renewal with Vue and the matching Android transport against actual HTTPS host. Old Android clients omit login CSRF and require the matching update.
- Exercise concurrent learner lifecycle writes, master-exam composition/start/timeout, verification and content edits on isolated MariaDB; SQLite scenarios cannot prove production locking behavior.
- With DRF installed, verify case metadata, finite/normalized blueprint weights, password resets and tag merges preserving knowledge/planner/question associations.
- See `backendReview.md` for implemented corrections and exact verification limits. Test-suite, migration and build restrictions remain in force.

## Startup — pending environment verification (2026-10-08)

- Relocated helpers: live SQLite reloader/venv handoff and Tkinter tutorial on Linux/Windows/Termux; help/path/preview checks passed.
- Interactive `start.py -i`: complete-runtime combined launch, proxy/login/media, occupied ports and Ctrl+C/companion-exit descendant cleanup on Linux/Termux/Windows. Menu/command checks passed; live app integration remains unverified. Uses existing schemas without setup/seeding.
- Complete runtime: simultaneous SQLite/MariaDB with separate Vite ports; verify login/CSRF/media/account isolation.
- Exercise explicit Windows/Termux virtualenvs and Termux-private data directories.
- Verify MariaDB/cache connectivity and Vite config loading; diagnostic checks are deliberately read-only and do not establish service availability.

## Database engine selection — pending integration verification (2026-10-08)

- With a compatible PostgreSQL driver and existing database/user, verify actual connectivity, ORM workflows, concurrency and authentication/cache integration.
- Native PostgreSQL database administration (including backup/restore/provisioning) remains unsupported; implement only as a separately requested scope.
- DB_ENGINE selection, backend-specific options, launcher overrides and isolated SQLite settings have passed source/temporary configuration checks. No live database work, migration/test-suite work or builds were performed.


## Exact ordinary Finish-result recovery — prepared source, migration required (2026-10-08)

- Obtain explicit authorization to create an additive migration for nullable, unique `TestHistory.source_session_id` (36-character session identity). No historical identity backfill: old records remain null. Migration files were not inspected/created/applied; do not deploy the model/service change before the schema is ready.
- After authorized migration/application, verify existing Finish grading/learning effects/history/delete rollback and unique identity on the production database. Compare POST results with GET results for exam/study/recall, including confident/fragile correct answers and frozen case/image/context after content changes/deletion. GET must never grade or mutate.
- Verify `GET /{exam|study|recall}/results/?session_id=...&mode=...`: strict caller ownership even with all-history capability, input length/mode validation, other-user/wrong-mode/unknown/discarded/legacy-null/deleted history all return no accessible result. Keep existing POST behavior and History serializers unchanged.
- Deploy the matching Android GET recovery after backend/schema readiness; older backend 405 or legacy/unknown 404 keeps the personal History fallback. HTTP/runtime/concurrency and authorized test-suite/build checks remain pending.


## Offline synchronization and own-session endpoints — rollout gates, 2026-10-08

- Obtain explicit authorization to create/apply the narrow additive migrations for source-session identity and `OfflineCompletion`; preserve legacy History. Do not deploy pending source against an unmigrated schema. Keep migration/test-suite restrictions in force until separately requested.
- After authorized schema readiness, verify signed pack caller/visibility/closed-book guards, rich snapshots and bounded image/file responses. Exercise tampered/cross-user packs, full answer coverage/ranges/confidence/elapsed limits, active sessions, deleted/changed/inaccessible assessed content and current capabilities.
- Verify production-database concurrent identical/altered/cross-user completion UUID uploads; effects/history/receipt must commit or roll back together, and identical retry after response loss or History deletion must never apply another learning event. Verify normal session identity collisions, upload-day semantics, receipts/History backup/state imports/restore/clear and account deletion. Match the Android immutable body/explicit sync/retained local results.
- Deploy schema-free own-session endpoints with live SessionStore checks: database/cached-db/cache/file engines, current-session missing tracking, auth-hash/expiry/password resets/secret rotation, opaque handles/cross-user/CSRF/password throttles, malformed handle, current/other revocation and in-flight requests. Stateless signed-cookie engines must return unsupported. Presence tracking is not a hardware-device attestation.


## Local learner schema and permission lookup — verification remaining, 2026-10-09

- Read-only inspection confirmed local `SQLite/db.sqlite3` has unique history source-session identity and the offline receipt identity/payload columns. Earlier migration gates still apply to any other database missing these structures; no migration work was performed. Remote deployment and runtime/concurrency remain unverified.
- Reload/deploy the schema-free `GET auth/admin/permissions/users/` lookup with Android: permission-only accounts, non-stub filtering, name/username search, stable bounded pagination, inactive/empty results and denial without admin.permissions. Existing account-management writes still require admin.users.


## Native knowledge linked questions — integration pending, 2026-10-09

- Reload matching source and verify GET knowledge-objects/{pk}/questions/ with Android: existing pagination, draft/retired objects, authorized draft questions versus hidden foreign drafts, closed-book snapshots, deleted object/questions and local last-page clamping. Implementation is schema-free; source AST/whitespace checks do not establish HTTP/runtime behavior.
