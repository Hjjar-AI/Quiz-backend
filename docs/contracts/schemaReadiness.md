# Schema and coordinated rollout

Current requirements 2026-10-10. [Startup](../guides/START_HERE.md) · [Deployment](../guides/DEPLOYMENT.md).

## Required matching schema

Recent source requires learning/exposure/presentation/day records, offline grants/completion receipts, question/content write receipts, question statistics fingerprint, SRS relearning, group/category/case revisions, exact source-session and archived-master History fields, and planner version/scope/scope-day history. Operator clear includes these dependent records. Source presence does not establish the schema of a phone-selected or deployed database.

For the user's approved fresh SQLite workflow, normal `python start.py sqlite` with old app migration folders removed generates initial migrations/schema from current models and runs setup/seeding. Deleting only the database while old migration files remain does not generate later model changes. `manage.py runserver` and `python start.py -i` skip schema setup. Existing data needs its deliberate upgrade/backfill policy; the learning changes target fresh setup.

Describing this workflow does not authorize agents to inspect/create/apply migrations or run setup/seeding. Those actions, builds, suites and versions still require explicit request under [agent rules](../../Agents.md).

## Deploy together

Use matching backend, Vue and Android for mandatory revision DELETE/edit payloads, master answer/session/navigation preconditions, planner id/version and returned configuration, receipt status and richer learning metadata. Reloading source alone does not update schema. Retain legacy History/undated offline recovery where supported; old signed material may require a new download for first commit.

Latest source checks covered Python AST, JavaScript/extracted Vue syntax, JSON, Android lexical/XML/resources/placeholders and whitespace. They do not validate Django imports, SQL/deadlocks, HTTP, Kotlin/Vue compilation, browser/device behavior or accessibility. The latest source-fix batch did not run builds, suites, migration work, database/setup/seeding, deployment or version changes.

PostgreSQL read-only login to lowercase `quiz` as `mpsql` succeeded, and the user's development server started on 5005 with 39 unapplied migrations. This does not establish schema readiness, workflows or concurrency. For first setup of that existing database, see [PostgreSQL bootstrap](../guides/POSTGRESQL_SETUP.md#bootstrap-or-apply-pending-migrations). Native provisioning/destructive clean/backup/restore administration remains unsupported. Verify the actual selected database, not a historical local SQLite diagnostic.
