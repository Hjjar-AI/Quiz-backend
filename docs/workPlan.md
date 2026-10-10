# Django remaining work

Updated 2026-10-10. [Current source status](workDone.md) · [Project map](../../Android/docs/README.md).

The seven rescan and eight deeper-review findings are source-complete. Do not reopen historical unchecked items without tracing current production source. Add new defects with reproduction, affected clients/contracts and priority.

## Pending verification

- Expand behavioral coverage beyond the passing [982-test suite and coverage report](verification/backendCoverage.md), prioritizing its measured uncovered lines/branches. PostgreSQL line/branch coverage is 71.75%/56.87%; passing suites do not verify every function or deployed behavior. The user's requested complete existing-suite run and coverage report are complete.
- Verify deployed PostgreSQL/cache/workflows against `mpsql` / `quiz_fresh`. The user reported successful bootstrap; the older `quiz` database remains separate recovery work. Follow the [PostgreSQL guide](guides/POSTGRESQL_SETUP.md).

- Prepare/verify matching [schema and coordinated clients](contracts/schemaReadiness.md); no readiness is inferred from source or database deletion.
- Execute the [shared functional matrix](../../Android/docs/verification/manualVerification.md), especially lost responses, account/attempt switches, receipts, permissions, revisions, imports/parent locking and planner late/midnight evidence.
- Extend the passing [35-scenario PostgreSQL concurrency matrix](verification/concurrencyLimits.md) to deployed HTTP/multiple processes/production cache, sustained load and large mixed imports before claiming user capacity. Verify startup/session integration, exports/PDFs and deliberately isolated backup/restore/clear. PostgreSQL administration remains unsupported.

Builds, suites, migrations/setup, destructive operator actions and versions follow [explicit-request policies](../Agents.md). The user's Python-test authorization covered these isolated suites and test database initialization; their results do not establish complete deployed readiness.

## 2026-10-10 parity-review follow-up

All seven native gaps, smaller workflow differences and shared web defects from the [latest parity review](../../Android/docs/archive/reviews/2026-10-10-androidParityReview.md) are source-complete. Verify the dedicated account set-state route, partial/unknown batch outcomes, clock-read ownership and the shared manual matrix after matching rollout. Old servers reject the new route without changing account state. Earlier completed fixes remain complete.

Optional clinical-case translations are source-complete; verify matching `ClinicalCase.translations` schema and Android rollout, snapshots, editor recovery and legacy import/export behavior. See the [contract](contracts/caseTranslations.md). No schema setup has been performed for this extension.
