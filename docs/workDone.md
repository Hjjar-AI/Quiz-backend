# Current Django source status

Updated 2026-10-10. [Remaining gates](workPlan.md) · [Historical evidence](archive/README.md).


- Learning evidence/fingerprints, occurrence chronology/SRS replay, activity/mastery/variety and planner scope history: [learning contracts](contracts/learningConsistency.md).
- Locked ownership, monotonic import revisions, edit/delete preconditions, receipts/bookmarks, master start/resume/access/answer/navigation and archive results: [write contracts](contracts/writeRecovery.md).
- Full-bank capability/catalogue, marked pack gates, cumulative selected-ID budget and durable completion processing: [offline policy](../../Android/docs/contracts/offlineQuestionBank.md).
- Stable complete case/knowledge management and learner case pagination, preserving bounded legacy autocomplete; permission-only user lookup and linked-knowledge question contracts.
- Startup/database selection, ordered exports/PDF links/themes and operator dependencies are represented; actual environment/SQL/PDF checks remain pending.

## Evidence and documentation

On 2026-10-10 the user reported a missing `pymemcache` error followed by a later run passing Django system checks but rejecting database `Quiz`. A read-only PostgreSQL catalog query using the existing credentials confirmed lowercase `quiz` through the maintenance database `postgres`; corrected ignored local `.env`, the example and guides accordingly. A subsequent read-only connection to `quiz` as `mpsql` succeeded, and launcher dependency diagnostics reported `/home/mhmmd/Envs/quiz` ready. Documentation links, 34 Bash block syntax checks and whitespace passed. Existing user/password/settings preserved. No database creation/rename/writes, migration inspection/setup, server launch, package changes, builds or suites. Application schema/cache/HTTP verification remains pending.

On 2026-10-10 configured ignored local `.env` and its example for PostgreSQL user `mpsql`, database `Quiz`, localhost TCP port 5432; retained the existing password and unrelated settings. Made `django-sslserver` explicitly optional through `DJANGO_ENABLE_SSLSERVER`, disabled it in the HTTP overlay and removed the HTTP launcher's package requirement. Added `requirements-postgresql.txt` using existing core pins plus Psycopg/Memcached and updated the PostgreSQL/startup guides for existing-database HTTP launch without that package. No SQLite source changes or existing dependency version changes.

Observed PostgreSQL client 18.6 and cluster `18/main` configured on 5432 but down. System-Python launcher diagnostics reported missing core packages/dotenv; no complete candidate environment was listed. Checked changed Python ASTs, Markdown links, Bash block syntax, redacted local configuration and whitespace. No database connection/writes, migration inspection/setup, package/service changes, builds or suites; password validity, schema, cache and live PostgreSQL behavior remain unverified.

On 2026-10-10 added the [fresh PostgreSQL setup guide](guides/POSTGRESQL_SETUP.md), linked from startup and the documentation index. Covers Ubuntu services, database ownership/login, existing/new venvs, cache/driver dependencies, `.env`, explicit fresh-schema/seed instructions, Vue/Android LAN access and troubleshooting. Checked production configuration/launcher/seed declarations, local links and whitespace. Documentation only; no installation, database connection/setup, migration inspection/execution, builds or suites. Live PostgreSQL integration and administration limits remain unchanged.

Latest shared source checks: 242 Python production ASTs, 299 JavaScript/extracted Vue scripts, 152 Kotlin lexical files, 1,383 bilingual resource entries and whitespace/XML/placeholders. No compilation/runtime/schema guarantee follows. No builds, suites, migration/setup/database/deployment/version actions were run in the latest fix batch. Matching deployment and manual checks remain required.

On 2026-10-10 documentation was grouped by function, active records compacted, historical evidence retained and links checked. Runtime behavior was unchanged; launcher/tutorial/comment references were updated to moved guides.

## 2026-10-10 parity contract fixes

The dedicated admin/users/<id>/active/ route requires boolean is_active and sets desired state under existing reauth/canonical locks/self/stub/last-admin rules and returns id/is_active/changed; the old toggle route stays compatible. Both clients use explicit states and retained partial/unknown outcomes with read/review, never automatic resend. Vue initial master clock correction is account/attempt-scoped with independent status; planner week uses server today. Native workflow closure is [archived evidence](../../Android/docs/archive/reviews/2026-10-10-androidParityReview.md).

Matching backend-first rollout required; this batch adds no schema. Source AST/JS/native lexical/XML/locale/whitespace checks only; builds/suites/migrations/setup/database/runtime/deployment/version work unperformed.
