# Work Plan

## Current priorities

1. Verify end-to-end Arabic/English PDF on a host with WeasyPrint/native libraries.
2. Check small, image-heavy, filtered, verified-only, and front-matter PDF cases.
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

- Interactive `start.py -i`: complete-runtime combined launch, proxy/login/media, occupied ports and Ctrl+C/companion-exit descendant cleanup on Linux/Termux/Windows. Menu/command checks passed; live app integration remains unverified. Uses existing schemas without setup/seeding.
- Complete runtime: simultaneous SQLite/MariaDB with separate Vite ports; verify login/CSRF/media/account isolation.
- Exercise explicit Windows/Termux virtualenvs and Termux-private data directories.
- Verify MariaDB/cache connectivity and Vite config loading; diagnostic checks are deliberately read-only and do not establish service availability.

## Database engine selection — pending integration verification (2026-10-08)

- With a compatible PostgreSQL driver and existing database/user, verify actual connectivity, ORM workflows, concurrency and authentication/cache integration.
- Native PostgreSQL database administration (including backup/restore/provisioning) remains unsupported; implement only as a separately requested scope.
- DB_ENGINE selection, backend-specific options, launcher overrides and isolated SQLite settings have passed source/temporary configuration checks. No live database work, migration/test-suite work or builds were performed.
