# Django remaining work

Updated 2026-10-10. [Current source status](workDone.md) · [Project map](../../Android/docs/README.md).

The seven rescan and eight deeper-review findings are source-complete. Do not reopen historical unchecked items without tracing current production source. Add new defects with reproduction, affected clients/contracts and priority.

## Pending verification

- Complete PostgreSQL bootstrap and verify schema/cache/workflows against `mpsql` / lowercase `quiz`. The user's `/home/mhmmd/Envs/quiz` server reached HTTP on 5005 with 39 unapplied migrations; no bootstrap completion has been reported. Follow the [PostgreSQL guide](guides/POSTGRESQL_SETUP.md).

- Prepare/verify matching [schema and coordinated clients](contracts/schemaReadiness.md); no readiness is inferred from source or database deletion.
- Execute the [shared functional matrix](../../Android/docs/verification/manualVerification.md), especially lost responses, account/attempt switches, receipts, permissions, revisions, imports/parent locking and planner late/midnight evidence.
- Check selected database row locking/rollback, startup/driver/session/cache integration, exports/PDFs and deliberately isolated backup/restore/clear. PostgreSQL administration remains unsupported.

Builds, suites, migrations/setup, destructive operator actions and versions follow [explicit-request policies](../Agents.md). Current source checks do not establish compilation, HTTP, schema or runtime concurrency.

## 2026-10-10 parity-review follow-up

All seven native gaps, smaller workflow differences and shared web defects from the [latest parity review](../../Android/docs/archive/reviews/2026-10-10-androidParityReview.md) are source-complete. Verify the dedicated account set-state route, partial/unknown batch outcomes, clock-read ownership and the shared manual matrix after matching rollout. Old servers reject the new route without changing account state. Earlier completed fixes remain complete.
