# Schema and coordinated rollout

Current requirements 2026-10-10. [Startup](../guides/START_HERE.md) · [Deployment](../guides/DEPLOYMENT.md).

## Required matching schema

Recent source requires learning/exposure/presentation/day records, offline grants/completion receipts, question/content write receipts, optional clinical-case translations, question statistics fingerprint, SRS relearning, group/category/case revisions, exact source-session and archived-master History fields, and planner version/scope/scope-day history. Operator clear includes these dependent records. Source presence does not establish the schema of a phone-selected or deployed database.

For the user's approved fresh SQLite workflow, normal `python start.py sqlite` with old app migration folders removed generates initial migrations/schema from current models and runs setup/seeding. Deleting only the database while old migration files remain does not generate later model changes. `manage.py runserver` and `python start.py -i` skip schema setup. Existing data needs its deliberate upgrade/backfill policy; the learning changes target fresh setup.

Describing this workflow does not authorize agents to inspect/create/apply migrations or run setup/seeding. Those actions, builds, suites and versions still require explicit request under [agent rules](../../Agents.md).

## Deploy together

Use matching backend, Vue and Android for mandatory revision DELETE/edit payloads, master answer/session/navigation preconditions, planner id/version and returned configuration, receipt status and richer learning metadata. Reloading source alone does not update schema. Retain legacy History/undated offline recovery where supported; old signed material may require a new download for first commit.

Earlier parity source checks covered Python AST, JavaScript/extracted Vue syntax, JSON, Android lexical/XML/resources/placeholders and whitespace. Those checks did not validate runtime behavior. Subsequent isolated SQLite/PostgreSQL suites pass as recorded in [Python verification](../verification/pythonTests.md); they do not establish complete SQL/deadlock, deployed HTTP, Kotlin/Vue compilation, browser/device or accessibility readiness. No application migration/setup, deployment or version changes were performed in the test-repair batch.

The user reported successful PostgreSQL bootstrap on `quiz_fresh` as `mpsql`, including default seed data and 16 sample questions. The older `quiz` database retains its inconsistent regenerated-migration/schema history; recreating files did not repair its tables. Automated checks use a separate PostgreSQL database: [Python results](../verification/pythonTests.md). Bootstrap completion does not establish all workflows, concurrency or deployed-client parity. Native provisioning/destructive clean/backup/restore administration remains unsupported. Verify the actual selected database, not a historical local SQLite diagnostic.

The optional case-translation extension requires the `ClinicalCase.translations` JSON column. [Contract and coordinated Android behavior](caseTranslations.md); source changes do not establish deployed schema readiness.
