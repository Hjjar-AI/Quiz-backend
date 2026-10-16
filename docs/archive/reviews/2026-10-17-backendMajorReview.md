# Additional backend major-issue source review

Reviewed 2026-10-17 against current production source, including the uncommitted learning-flow corrections. Relevant Vue form/session/planner callers and Android question/draft/planner DTOs were checked. This review records four additional P1 findings; it does not establish exhaustive backend correctness or deployed behavior.

## B1 — P1: answer withholding can block timed-exam finalization (regression)

`apps/exams/services/exam_service.py:920` calls `require_answers_available` before marking the session inactive, grading, recording learning/history or deleting the live session. Excluding the ordinary session's own identity still leaves every unfinished master attempt in the hidden set (`apps/questions/answer_visibility.py`).

Source-derived reproduction: start an ordinary exam and master attempt sharing public question Q. Finish the ordinary exam, including the web timer-expiry path, before completing the master attempt. The service raises `ANSWERS_WITHHELD` before any completion writes, so the exam remains live and its completion evidence/history is not persisted. Completing the master attempt and retrying can resolve it; this is not a permanently unrecoverable session.

This regression was introduced by the preceding fix batch. Answer disclosure and session completion need separate outcomes: persist completion/learning once, retain its exact recovery identity, and withhold answer-bearing review while the overlapping exam remains unfinished. Coordinate the response and web/native recovery handling so a saved completion is not represented as an uncertain rejected write. Raising the withholding exception inside the completion transaction after grading would roll back the same work and would not fix it. Current source-complete claims for the earlier batch do not close this new finding.

## B2 — P1: case resolution bypasses private-case visibility and shared-stem write permission

`apps/questions/serializers/case_resolver.py:54` looks up an existing clinical case by unrestricted key. It returns that case without checking the visibility rule in `apps/questions/views/case_views.py:30`; lines 64–66 also populate an existing blank shared stem without checking `can_edit_case` or an expected revision.

Reachable paths include public question creation (`QuestionCreateSerializer.create`), editing an owned question (`QuestionService.update_question`), and master draft creation/update. The question form accepts a free-text `case_key` and `case_stem`; native question/draft payloads carry both too. A scoped autocomplete does not constrain submitted keys.

Source-derived reproductions:

- A user who may create a question, or edit an existing own question, submits a known other-author private case key. Resolution attaches it to the caller's question, whose response now contains the private case stem/translations. Creating a public question can make that previously private case readable through normal case visibility. A known key is required; this is an object-authorization bypass, not proof of arbitrary key enumeration.
- A caller lacking shared-case edit permission attaches an owned/new question to an existing blank-stem case and supplies `case_stem`. The resolver writes the shared parent anyway. Its model hook invalidates live learning state for linked questions, so the impact extends beyond the caller's own question.

Enforce visibility before resolving an existing case. Existing-parent stem changes require the actual actor's case authorization and retained revision; initializing a newly created case is a separate operation. Keep omitted versus explicit detach behavior and authorized case reuse. The resolver's user argument also serves authorship attribution in some callers, so verify actor/author identity instead of assuming they are interchangeable.

## B3 — P1: production lock orders contain deadlock cycles

These are source-derived schedules on a database enforcing the requested row locks, such as PostgreSQL; they have not been reproduced live. Transaction rollback protects committed data, but one operation can fail and require recovery.

### Planner update versus category merge

`StudyPlannerService.update_planner` locks the hierarchy mutex, then planner P (`apps/planning/services.py:82–83`), then sets category relations. The pre-add signal locks destination category C (`apps/questions/signals.py:52–60`). `CategoryMergeView` instead locks category rows before affected planners (`apps/questions/views/category_views.py:206,222`), without taking that hierarchy mutex.

Schedule: P currently targets source A. Planner update holds P and plans to add target C. Concurrent merge A into C holds A/C and waits for P; the planner update waits for C. Ordered primary keys within each phase do not fix the opposite ordering across phases. Both clients can update planner targets and invoke category merge; same-request client busy guards cannot serialize two users/devices.

### Blank shared-stem fill versus learning/content writes

`_resolve_case` first locks case C, then calls `case.save` for an existing blank stem. `InvariantValidationMixin`/`RevisionedSaveMixin` call `lock_assessed_dependents`, which locks C's linked questions before saving the parent (`apps/core/model_validation.py`). Learning recording instead locks questions then assessed case/knowledge rows (`apps/learning/events.py:55`, `apps/learning/evidence.py:13`). Dedicated case-edit paths also lock linked questions before the case.

Schedule: learning holds linked question Q and waits for C; the resolver holds C and waits for Q through the save hook. Use different learner/editor actors so the learner lock does not serialize them first. Fixing only the direct case-edit view leaves the shared resolver cycle intact.

Choose one compatible order for the complete participating writer set, re-read relationships after locks and handle changed membership before mutation. Do not add automatic replay of answer/navigation or merge operations as a substitute for ordering.

## B4 — P1: stale auto-renewal can overwrite an administrator's expiry decision

`User.renew_if_eligible` computes a new expiry from the in-memory `expires_at`/`auto_renew_days` (`apps/users/models.py:305–321`). `AutoRenewMiddleware` then saves that expiry separately (`apps/core/middleware.py:164–165`); login repeats the pattern in `apps/users/services/authentication_service.py`. Neither decision is recomputed under the row lock used by administrative account changes.

Source-derived reproduction: an expired account request reads auto-renew=30 days and computes a renewal; before its expiry save, an administrator sets auto-renew=0 and expiry=1 day. The delayed request's partial save then overwrites expiry with roughly 30 days. The save mixin locks and merges current companion fields, but it still writes the stale computed expiry; it does not re-evaluate eligibility against the locked row. The account retains disabled renewal but receives a longer access window than the administrator accepted. The reverse race can reintroduce a finite expiry after an administrator clears expiry.

Compute and persist eligibility/expiry against fresh state within the same learner/account transaction, or use an equivalent conditional write covering all decision inputs. Preserve bypass capability, explicit unlimited expiry, login policy and the canonical admin lock order. Both web and Android rely on this backend policy; no client-side guard can repair the race.

## Limits and remaining work

Review and documentation only; no new production changes during this pass. No automated suites inspected/run, migrations/schema/setup, database access, live HTTP/concurrency reproduction, builds/compilation/packaging, deployment or version changes. Reproduction sequences describe reachable source behavior and interleavings, not observed runtime results. The earlier production edits remain in the working tree; these findings are added to the active plan rather than silently marked complete.

## Source corrections

Implemented at the user's subsequent request to review the flows deeply and fix them:

- **B1:** removed the pre-completion withholding rejection. Finish persists grading/events/planner/history and live-session deletion in its existing learner transaction, then returns `completion_response`. It preserves real score/count/time fields and exact source/history/mode identity; `completion_recorded=true`, `review_withheld=true`, `results=[]` indicates committed completion with temporarily unavailable question review. The owner GET uses the same representation under a learner lock; after overlap ends, it returns the stored full review without any learning replay. Vue and Android show the saved/withheld distinction and an explicit GET refresh with separate busy/error state, retained success and response ownership. Summary reporting remains available, consistent with existing master/history summary behavior; this is not a stronger claim that aggregate scores cannot disclose information. Existing clients retain decodable summary fields.
- **B2:** centralized case visibility in `case_policy.visible_cases`, used by reads and the shared resolver. Existing cases are checked against the actual actor; creating a new case still attributes authorship separately. Equal/omitted stem hints reuse existing content; a differing stem, including filling a blank, returns structured validation directing the user to the existing revisioned case editor. No existing-case save occurs inside resolution. Ordinary and draft updates preserve explicit detach/omission behavior and retain failed drafts through existing client handling. Master draft update now checks current ownership under its question lock within a transaction.
- **B3:** category API writes/merges and planner API/admin writes coordinate on the existing structural gate before taxonomy/planner locks, with the actor/learner acquired first to avoid late audit/FK user inversions. Case/knowledge edits/deletes, question create/update/duplicate, master draft writers, content admin change/delete/bulk-delete and flat/Telegram imports participate before assessed/link writes; existing state imports already take user/gate/question locks. Master draft creation preserves its exam-before-gate lifecycle order. The resolver is link/read-only for existing cases and never takes linked-question save-hook locks after a parent. Question update no longer locks old assessed parents before resolving a new case: its question lock stabilizes old parent content because assessed-parent writers/deleters lock dependents first. The gate freezes app link changes during parent edit locking. Category audits remain transactional and receipts retain their hashes/identity behavior. These changes remove the evidenced cycles; arbitrary direct ORM/management interleavings and total deadlock freedom are not established by source review.
- **B4:** `User.renew_if_eligible` retains its boolean return but now means a persisted renewal. Candidate accounts are re-read under their user row lock, eligibility uses fresh active/stub/expiry/renewal/bypass policy, and the expiry save happens before release. Current fields/memo are refreshed for the caller even when a concurrent change cancels renewal. Middleware, login and the periodic/management-command job no longer follow with a stale expiry save. Login re-reads under the same lock, rejects changed password hashes/disabled/stub accounts, and preserves the authenticated backend and session-lifetime policy. Admin expiry/unlimited/bypass behavior is retained.

The expanded duplicate flow review also evidenced a new-ID answer escape: copying a withheld source could return its correct answer under a different ID. Duplicate now rechecks a fresh visible locked source and shared answer policy before creating anything; learning/history evidence is not replayed.

Updated production Python ASTs, changed JavaScript/extracted Vue-script syntax, bilingual JSON key/placeholder and Android XML/new-resource checks, caller/field/receipt/renewal/lock tracing and whitespace checks passed. No Vue SFC parser is installed; templates and Kotlin were source-reviewed, not compiled. No automated suites inspected/run, migrations/schema/setup/database/HTTP, builds/compilation/packaging, dependency/version changes or deployment. Matching backend-first rollout and manual HTTP/browser/device/concurrency/performance verification remain pending in the active plan. Historical reproduction sequences above are source evidence, not executed runtime results.
