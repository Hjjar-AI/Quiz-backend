# Backend Agent Instructions

## Working rules

- Read applicable instructions and [workPlan](docs/workPlan.md)/[workDone](docs/workDone.md)
  first; inspect current production source and the working tree. Preserve unrelated
  edits and existing authorization; do not commit unless requested.
- Trace affected contracts and callers before making focused corrections. Do not
  invent endpoints, permissions, idempotency or verification evidence.
- No migration inspection/changes/setup, automated-suite inspection/work, or
  Gradle/build/compilation/packaging without an explicit request. Supplied logs and
  user-run builds authorize source troubleshooting, not agent-run builds. No version
  changes unless requested. Production study/exam modules are application source;
  exclude actual suites and migration directories from content searches.
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

## Backend invariants

- Preserve Django service transactions, capability checks, audit logging and the
  API response envelope. Enforce important invariants at service/model boundaries.
- Review lock ordering, fresh state after locks, rollback and concurrent writes when
  relevant; SQLite checks do not establish server-database locking correctness.
- Preserve login/session CSRF, token rotation, account expiry and localized errors.
  Keep Arabic/English consistent and import/export formats backward-compatible.
- Verify affected Vue/Android callers directly; document coordinated deployment
  requirements when a contract or authentication change needs matching clients.
- Preserve safe field-validation details and semantic error reasons in the response
  envelope. Distinguish rejected writes from unknown client outcomes; toggle/create
  endpoints are not retry-safe merely because they are transactional. Document actual
  reconciliation/receipt support and its absence without inventing guarantees.
- Keep PDF theme names, palette seeds and aliases aligned with the frontend theme
  registry/bootstrap/locales. Renames must preserve existing export requests;
  honor intentional theme-aware print colors. See the [theme guide](../frontend/docs/theme-guidelines.md).
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
  readiness from deletion or source checks. See [startup](docs/START_HERE.md).
- PostgreSQL configuration exists; live integration and database administration
  support remain separate pending work. Check [startup](docs/START_HERE.md) and
  [review limits](docs/backendReview.md) before claiming backend support.
