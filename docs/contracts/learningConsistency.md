# Learning and planner contracts

Current source policy 2026-10-10. [Write/recovery contracts](writeRecovery.md) · [Schema readiness](schemaReadiness.md) · [Verification](../../../Android/docs/verification/manualVerification.md).

## Durable evidence

- `LearningEvent` retains original question ID, assessed fingerprint, source, occurrence/receipt times, classification/concept snapshots, correctness/confidence/error and derived credit. `(user, source_key, original_question_id)` prevents duplicate learning independently of deletable History. Question deletion uses SET_NULL; user deletion clears private evidence.
- `LearningDay` drives streaks. `QuestionExposure` distinguishes allocation/presentation/answer by user/question/fingerprint; `QuestionPresentation` deduplicates responses per source. Presentation means a server response, not proof of screen visibility. Unsynchronized offline study is unknown to the server.
- Assessment fingerprints include base content, assessed translations, concept/case content; explanations are excluded. Translated options must be nonblank, match base counts and preserve indexes. Structural validation cannot prove translation quality. Content changes invalidate current statistics/SRS while retaining frozen historical grading/events; live counters require matching `stats_fingerprint`.

## Chronology and SRS

Ordinary/master answer timestamps feed learning. New offline packs sign `issued_at`; Android retains a server clock offset and freezes answer/completion times plus UUID/body before upload. Occurrence/answer times must fit issue-to-receipt bounds, with five-minute future tolerance/clamping, and answers precede completion. These are bounded declarations, not proof of human timing. Invalid clocks retain pending material. Legacy undated bodies preserve their identity and use receipt chronology; obsolete material may require new downloads for a first commit, while identical committed receipts remain recoverable.

Delayed evidence replays matching-content events for that question in occurrence/receipt/ID order. First exposure is not a completed due review; early correct answers cannot advance the schedule or bypass relearning. Wrong answers reset the chain; due success exits relearning. Replay recomputes derived due-review/mastery credit.

## Selection, activity and concepts

`coverage` prefers unseen, then lower/older exposures with concept diversity; `balanced` prioritizes unseen/due; `review` prioritizes due/weak. Blueprint category quotas and clinical-case groups remain authoritative. Manual IDs, SRS ordering and fixed master sets retain their contracts. Selection/allocation share the learner transaction; exhausted filters cannot guarantee disjoint exams. Indexed exposure avoids history-JSON scans, but candidate pools are materialized; measure large-bank behavior. See [selection details](questionSelection.md).

Answered learning, including paused/discarded work and late offline uploads, drives activity/leaderboards/planner/streaks by occurrence day. Unanswered Finish adds no answered activity. Completed-session analytics retain their separate meaning. Reports distinguish answer volume, distinct questions/concepts, completed due reviews and net mastery points. Concept mastery needs at least three variants (or all for smaller concepts) and half the available variants; otherwise score remains below mastered.

## Planner scope history

Planner update/delete requires retained `expected_id` and `expected_version`; accepted updates return authoritative configuration/revision. Id protects against delete/recreate collisions. Both clients explicitly compare latest values and Keep draft/Use server after conflict.

`StudyPlannerScope` records target categories/tag names/date window and effective/ended timestamps; `StudyPlannerScopeDay` stores credit under its original scope. Late events select their historical scope by occurrence time and frozen category/tag snapshots. Explicit filter/date changes reset today's displayed progress; taxonomy rename/merge continues it without copying counts. Today sums scopes since the latest reset; historical days sum all original scope counts, including pre-reset activity after midnight. Global learning evidence remains independent. Explicit planner deletion cascades its planner history, not global learning events.
