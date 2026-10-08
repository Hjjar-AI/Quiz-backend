# Backend Agent Instructions

## Working rules

- Read applicable parent/local agent instructions, [workPlan](docs/workPlan.md) and
  [workDone](docs/workDone.md); check the working tree and affected folders first.
- Trace related production code and callers before fixing a defect; keep models,
  services, permissions, configuration and client contracts consistent. Prefer
  critical, focused corrections that address the cause and preserve existing behavior.
- Preserve unrelated/current user edits. Do not commit unless requested. Continue
  authorized work without repeated confirmation; ask only for missing decisions.
- Do not inspect, review, edit or create migration files without an explicit migration
  request. Fresh-project/model edits do not authorize migration work.
- Do not inspect, review or run test suites without an explicit test-work request;
  exclude test directories and test-named files from source-content searches.
- Do not run Gradle, builds, compilation or packaging without explicit permission;
  supplied logs or user-run builds are not authorization. Change versions only
  when explicitly requested.
- Simple scripts and source/XML/AST/whitespace checks are allowed. Report their
  actual scope; do not claim builds, runtime/device checks or database concurrency.
- If known five-hour usage reaches 20% remaining, finish the bounded step and stop.
- Keep only `start.py` and Django `manage.py` as root Python entry points; place
  supporting launch/tutorial utilities in `scripts/`, updating paths and callers.
- Keep root README/Agents files discoverable; supporting Markdown belongs in `docs/`.
  Update links when moving docs. Record remaining work in the plan and completed
  portions/limits in the work log; keep implementation separate from verification.
- Communicate concisely in English unless asked otherwise; state changes and limits.

## Backend invariants

- Preserve Django service transactions, capability checks, audit logging and the
  API response envelope. Enforce important invariants at service/model boundaries.
- Review lock ordering, fresh state after locks, rollback and concurrent writes when
  relevant; SQLite checks do not establish server-database locking correctness.
- Preserve login/session CSRF, token rotation, account expiry and localized errors.
  Keep Arabic/English consistent and import/export formats backward-compatible.
- Verify affected Vue/Android callers directly; document coordinated deployment
  requirements when a contract or authentication change needs matching clients.
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
- PostgreSQL configuration exists; live integration and database administration
  support remain separate pending work. Check [startup](docs/START_HERE.md) and
  [review limits](docs/backendReview.md) before claiming backend support.
