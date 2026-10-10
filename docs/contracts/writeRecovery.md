# Writes, recovery and concurrency

Current source contracts 2026-10-10. [Learning](learningConsistency.md) · [Schema/rollout](schemaReadiness.md) · [Pending scenarios](../../../Android/docs/verification/manualVerification.md).

## Shared rules

Backend capabilities and locked current ownership are authoritative. A visible item is not authorization to mutate it. Preserve drafts/readable data and confirmed success on later read/storage failure. Unknown writes require current-state/receipt reconciliation and explicit decisions; never automatically replay ordinary/admin writes. Account/session generations reject late callbacks; master flows additionally scope responses to exam/session/store/progress ownership.

## Receipts and bookmarks

| Operation | Contract |
| --- | --- |
| Question create/duplicate | Optional `operation_id`; `QuestionWriteReceipt` binds caller/UUID/body digest/result atomically. Identical request returns its existing visible result; changed body conflicts. Read via `GET questions/?operation_id=...` or `GET questions/<source>/duplicate/?operation_id=...`. |
| Category/knowledge create | Optional `operation_id`; `ContentWriteReceipt` binds caller/UUID/action/canonical SHA-256/target. `GET /api/v1/recovery/operations/<uuid>/` returns caller-owned action/target metadata and `target_exists`; target reads enforce independent visibility. |
| Deleted committed target | Do not recreate under its old identity. Native acknowledgement retires UUID but keeps draft; only explicit new Save creates another identity. Missing receipt, denied read and transient failure are distinct. |
| Bookmark | GET/PUT explicit state; legacy POST toggle remains compatible. Explicit state retry cannot reverse committed intent. |
| Offline completion | Caller-bound signed packs, frozen UUID/body and durable receipt prevent repeated grading/learning. Explicit sync/retry only; altered/cross-user bodies reject. |

Android uses profile/account-bound encrypted recovery for applicable editor and pending-write state, including detail copies/bookmarks and standalone editors. Restore/discard is explicit; required failed checkpoints block dispatch. Web persists operation identities only, scoped to account UUID/API origin, with text/images memory-only. An orphan/restored create is check/open-only and cannot attach a new form/image; missing-receipt acknowledgement permits new creation. Late confirmations cannot navigate an unmounted form or consume another form's files.

## Revisions and locks

Question/knowledge updates and DELETE require `expected_version` (DELETE query). Question mutations recheck current `owned_by`/override under lock. Category/case update/delete/stem require versions; group metadata requires version. Tag-tree and runtime-settings reads return shared revisions required for writes. Compare after locks; stale writes return 409. Clients keep the baseline shown with the draft; a fresh read alone does not authorize silently replacing it.

Assessed parent saves lock linked questions before their case/knowledge row; API/model/import/learning writers coordinate dependencies. Existing state-import questions/knowledge advance the locked local revision, never adopt a lower/equal exported token. Imports take broad user/question locks; runtime deadlock/rollback/performance checks remain pending, including ORM paths bypassing save hooks.

## Master attempts

- Start locks fresh learner/exam/access relations and rechecks new-start/preview policy. Resolve existing attempts first: resume active normal/makeup without extending time; force-finish expired work. Completed attempts do not receive another attempt through makeup classification. Existing owned work remains accessible under its participation policy.
- Answers require `session_id` and full `expected_slot`, including explicit null for no saved slot. Compare under attempt lock. Already-saved identical answer/confidence/error intent is idempotent; different baseline returns `ATTEMPT_PROGRESS_CHANGED` (409), preserving timestamp/state.
- Goto requires `session_id` and nullable `expected_current_question_id`; fresh locked membership/completion/deadline checks and position comparison serialize navigation. Current-question GET does not persist fallback position. Expiry finish failures propagate rather than claiming completion.
- Web/native retain uncertain answer intent, reconcile full saved slots and require explicit rebase/retry/discard. Legacy native drafts without a session/baseline require review. Polling cancellation/disposal generations and route/attempt ownership prevent stale responses or orphan timers; controls guard simultaneous writes.
- Master deletion archives completed weighted/frozen results in caller-owned History before cascade without replaying learning. Learner-first locks protect finish ordering; participant-set changes reject with 409. Independent learning survives explicit History deletion.
