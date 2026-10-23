# Backend Agent Instructions

## Working rules

- Start at [documentation index](docs/README.md). Read applicable instructions and [workPlan](docs/workPlan.md)/[workDone](docs/workDone.md)
  first; inspect current production source and the working tree. Preserve unrelated
  edits and existing authorization; do not commit unless requested.
- Only matching post-fix Android, Vue and backend versions require support, including when revisiting earlier fixes. Do not add or retain old-client/version fallbacks solely for backward compatibility. Check the current Vue callers before changing shared contracts; do not modify frontend application code unless explicitly authorized. Existing stored data, drafts and recovery are separate concerns and must not be discarded under this policy.
- Trace affected contracts and callers before making focused corrections. Do not
  invent endpoints, permissions, idempotency or verification evidence.
- No migration inspection/changes/setup without an explicit request. Supplied logs
  and user-run builds authorize source troubleshooting, not agent-run builds or
  tests. No version changes unless requested. Production study/exam modules are
  application source; exclude suites and migration directories from production searches.
- Internal test-file work and execution follow the milestone approval rules below.
- Lightweight production-source/XML/AST/whitespace checks are allowed. State their
  scope; source completion does not establish compilation, HTTP/device behavior,
  accessibility, deployed schema or database concurrency.
- Reviews must trace reachable controls, DTOs/serializers, gates/ownership, retained
  state and failure/recovery paths across affected clients. Endpoint inventories and
  old Markdown alone are insufficient. Distinguish shared client defects, native
  omissions, backend limits and deployment/runtime gates. Report prioritized findings
  with source evidence; completing a bounded list does not prove full parity.
- Keep remaining work in the plan and completed work/checks/limits in the log.
  Compact stale records with linked archives; keep supporting Markdown in `docs/`
  and root instructions discoverable. Preserve intentional policies when compacting.
- Continue authorized work; ask only for missing decisions. Communicate concise
  findings and limits in English unless requested otherwise. If a visible five-hour
  allowance reaches 20% remaining, finish the current step and stop; never infer usage.
- Keep only `start.py` and Django `manage.py` as root Python entry points; put
  supporting launch/tutorial utilities in `scripts/` and update callers.

## Milestone test approval

- Finish the authorized implementation and lightweight source checks first. At the end of each implementation milestone, propose the smallest useful internal test scope (Android, Python or Vue) and ask for explicit permission to inspect/create/enhance test files and/or run tests, stating the intended coverage and exact run command. Reuse explicit authorization already granted for that milestone and scope; do not treat it as permission for later milestones or broader suites.
- New Android test files are allowed with the same milestone approval as Python/Vue files. A specific user instruction to create or enhance tests authorizes that file work; running them still requires authorization for the proposed command/scope. Continue independent implementation while approval is pending.
- Builds, compilation and packaging require explicit confirmation of their commands/scope, including compilation triggered by a test command. A general implementation request is not confirmation. Migration inspection/changes/setup and version changes still require explicit task authorization.
- Do not start recurring/watch-mode tests, automatic rerun loops, recurring background agent work or other repeated token/resource-intensive checks. Run approved checks once; repeat only after a relevant change, failure or unresolved issue justifies it within the approved scope. Reuse results and keep large output in a local log; report only the result and useful failure context.
- Before an approved build or resource-heavy test run, check active builds/test runners and available memory. Avoid concurrent heavy runs; never stop unrelated processes or clear caches to make room. Check for leftover task-owned runners when finishing; do not leave recurring work running.
- Documentation-only changes need source/link/whitespace checks, not suites. Report source checks, automated tests, compilation and device/browser/live-HTTP verification separately.

## Backend invariants

- Preserve Django service transactions, capability checks, audit logging and the
  API response envelope. Enforce important invariants at service/model boundaries.
- Review lock ordering, fresh state after locks, rollback and concurrent writes when
  relevant; SQLite checks do not establish server-database locking correctness.
- Preserve login/session CSRF, token rotation, account expiry and localized errors.
  Keep Arabic/English consistent and coordinate import/export formats with current clients.
- Verify affected Vue/Android callers directly; document coordinated deployment
  requirements when a contract or authentication change needs matching clients.
- Preserve safe field-validation details and semantic error reasons in the response
  envelope. Distinguish rejected writes from unknown client outcomes; toggle/create
  endpoints are not retry-safe merely because they are transactional. Document actual
  reconciliation/receipt support and its absence without inventing guarantees.
- Keep PDF theme names, palette seeds and aliases aligned with the frontend theme
  registry/bootstrap/locales. Renames must preserve existing export requests;
  honor intentional theme-aware print colors. See the [theme guide](../frontend/docs/guides/theme-guidelines.md).
- Never expose credentials, storage paths or internal exceptions through APIs;
  do not commit secrets or private logs.
- Select the database through `.env`/`DB_ENGINE`; keep driver requirements, ports and
  options specific to the chosen engine. Preserve explicit portable SQLite isolation
  for files/cache/cookies and production versus HTTP development behavior.
- Keep startup portable across virtualenvs, machines and Termux. Diagnostics must
  avoid database writes/setup; do not run setup implicitly during debugging.
- Fresh SQLite setup: normal `python start.py sqlite` generates initial migrations
  only for model apps without migration files, then applies migrations and runs
  setup/seeding. If the database and app migration folders were removed, this creates
  the schema from current models; separate additive migrations are unnecessary for
  that fresh workflow. If migration files remain, deleting the database alone does
  not generate migrations for model changes. `manage.py runserver` and interactive
  `python start.py -i` skip schema setup. Explain these distinctions without running
  setup or migration work unless explicitly requested; never infer verified schema
  readiness from deletion or source checks. See [startup](docs/guides/START_HERE.md).
- PostgreSQL configuration exists; live integration and database administration
  support remain separate pending work. Check [startup](docs/guides/START_HERE.md) and
  [review limits](docs/archive/reviews/2026-10-08-backendReview.md) before claiming backend support.
