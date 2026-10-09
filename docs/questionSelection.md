# Per-user automatic question variety

Implemented in source 2026-10-09; live HTTP/database/performance checks remain pending.

Ordinary automatic exam/study/recall starts now rank the eligible question pool using the current user's existing records. Previously the generic pool took the newest matching rows, so repeating a category/tag with the same requested count frequently produced the same set.

Selection priority is:

1. Questions absent from the user's stored history/session/attempt records.
2. Questions with fewer recorded allocations/completions.
3. Questions whose most recent recorded exposure is older.
4. Random choice for equal priorities, followed by random presentation order.

For example, five-question starts within a twenty-question category prefer questions outside earlier recorded sets while those remain eligible. After the unseen pool is exhausted, less repeated/older questions are preferred instead of failing to supply a session. These are preferences, not a configurable probability percentage or a global popularity score.

## Scope and retained contracts

- `StartSessionView` automatic category, category-list, tag/tag-list, difficulty, verification and bookmark filters still use the existing public question queryset. Requested maximums and no-question errors remain unchanged; filtering happens before ranking.
- Blueprint assembly uses the same user preference inside its existing category quotas and shortage fallback. Weights, eligible counts and presentation shuffle retain their contracts. Count-only callers omit the optional user and do not scan personal history.
- Explicit ordered `question_ids` remain exactly the user's selection. SRS retains its due-date scheduling/order; fixed author-assigned master-exam sets remain unchanged. Social groups do not introduce a new question-pool contract.
- Exposure evidence is strictly scoped to the signed-in user: `TestHistory.results[*].question_id` (legacy `id` accepted), existing ordinary `ExamSession.question_ids`, and `MasterExamAttempt.question_ids`. Each recorded row contributes at most one count per ID; recent completion/start dates distinguish ties. No other user's history or global question counters influence preference.

## Evidence and runtime limits

These stored allocations/snapshots do not prove that an individual screen was viewed. Completed rows with missing/invalid legacy result IDs cannot contribute; deleted history and discarded/replaced sessions lose their evidence. Unsynchronized offline practice is unknown to the server until completion upload creates history. No exposure table, migration or setup is introduced.

Current session allocations help avoid overlap during ordinary sequential use, but selection precedes the existing start transaction. Concurrent starts can still overlap; this is not an atomic no-repeat reservation. Likewise, content/access changes while a request runs retain their existing authorization/session contracts. Blueprint category quotas can require a repeat within one category even if another category has unseen questions.

The helper streams user records and holds ID/count maps, not whole question payloads. Large candidate pools/user histories still need real performance checks. Matching backend reload applies the policy to both web and Android automatically; no client request field or deployment schema change is required.
