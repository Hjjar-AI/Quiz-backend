# Learning and planner contracts

Current source policy 2026-10-10. [Write/recovery contracts](writeRecovery.md) · [Schema readiness](schemaReadiness.md) · [Verification](../../../Android/docs/verification/manualVerification.md).

## Durable evidence

- `LearningEvent` retains original question ID, assessed fingerprint, source, occurrence/receipt times, classification/concept snapshots, correctness/confidence/error and derived credit. `(user, source_key, original_question_id)` prevents duplicate learning independently of deletable History. Question deletion uses SET_NULL; user deletion clears private evidence.
- `LearningDay` drives streaks. `QuestionExposure` distinguishes allocation/presentation/answer by user/question/fingerprint; `QuestionPresentation` deduplicates responses per source. Presentation means a server response, not proof of screen visibility. Unsynchronized offline study is unknown to the server.
- Assessment fingerprints include base content, assessed translations, concept/case content; explanations are excluded. Translated options must be nonblank, match base counts and preserve indexes. Structural validation cannot prove translation quality. Content changes invalidate current statistics/SRS while retaining frozen historical grading/events; live counters require matching `stats_fingerprint`.

## Chronology and SRS

Closed-book policy also omits withheld concepts from the knowledge map, redacts their nested question titles/objectives (including siblings), and excludes hidden explanations from ordinary search matching/counts. It cannot recall material previously delivered to a client.

Ordinary/master answer timestamps feed learning. New offline packs sign `issued_at`; Android retains a server clock offset and freezes answer/completion times plus UUID/body before upload. Occurrence/answer times must fit issue-to-receipt bounds, with five-minute future tolerance/clamping, and answers precede completion. These are bounded declarations, not proof of human timing. Invalid clocks retain pending material. Legacy undated bodies preserve their identity and use receipt chronology; obsolete material may require new downloads for a first commit, while identical committed receipts remain recoverable.

Delayed evidence replays matching-content events for that question in occurrence/receipt/ID order. First exposure is not a completed due review; early correct answers cannot advance the schedule or bypass relearning. Wrong answers reset the chain; due success exits relearning. Replay recomputes derived due-review/mastery credit.

## Selection, activity and concepts

`coverage` prefers unseen, then lower/older exposures with concept diversity; `balanced` prioritizes unseen/due; `review` prioritizes due/weak. Blueprint category quotas and clinical-case groups remain authoritative. Manual IDs, SRS ordering and fixed master sets retain their contracts. Selection/allocation share the learner transaction; exhausted filters cannot guarantee disjoint exams. Indexed exposure avoids history-JSON scans, but candidate pools are materialized; measure large-bank behavior. See [selection details](questionSelection.md).

Answered learning, including paused/discarded work and late offline uploads, drives activity/leaderboards/planner/streaks by occurrence day. Unanswered Finish adds no answered activity. Completed-session analytics retain their separate meaning. Reports distinguish answer volume, distinct questions/concepts, completed due reviews and net mastery points. Concept mastery needs at least three variants (or all for smaller concepts) and half the available variants; otherwise score remains below mastered.

## Planner scope history

Admin saves capture the previous scope before scalar changes, advance revision and record the final combined scalar/M2M scope. Derived daily ledgers are read-only; learning evidence/scope projection is authoritative.

Planner update/delete requires retained `expected_id` and `expected_version`; accepted updates return authoritative configuration/revision. Id protects against delete/recreate collisions. Both clients explicitly compare latest values and Keep draft/Use server after conflict.

`StudyPlannerScope` records target categories/tag names/date window and effective/ended timestamps; `StudyPlannerScopeDay` stores credit under its original scope. Late events select their historical scope by occurrence time and frozen category/tag snapshots. Explicit filter/date changes reset today's displayed progress; taxonomy rename/merge continues it without copying counts. Today sums scopes since the latest reset; historical days sum all original scope counts, including pre-reset activity after midnight. Global learning evidence remains independent. Explicit planner deletion cascades its planner history, not global learning events.

## Ordinary session display labels and recall controls

Closed-book policy also applies to overlapping ordinary study/recall sessions: start/read/prefetch/answer reject with 409 `details.code=ANSWERS_WITHHELD` while an ordinary exam (paused included) or unfinished master attempt withholds a selected question. Question duplication also checks its source before creating a new ID. Knowledge list/search omits linked answer material; detail/update reads reject. Both frozen and current concept links are protected. Overlapping full-history and offline receipt-result reads wait for exam completion; committed receipts remain durable. This cannot recall material already delivered to a client.

Ordinary finish always persists grading, learning/history and session deletion atomically. Successful finish and owned exact-result GET return the existing authoritative score/count/time summary, `source_session_id`, `history_id`, `mode`, `completion_recorded=true` and `review_withheld`. When another unfinished exam overlaps, `results=[]` with `review_withheld=true`; the complete question review remains stored. Repeating the owned GET after the overlap ends returns that frozen review without grading or learning writes. Score summaries remain available as in existing completed-session reports; withholding is for question answer material, not a promise that aggregate scores reveal no information. Matching Vue/Android show a saved-completion notice and explicit read-only review refresh; read failure retains confirmed completion. Older clients can still decode the score summary but do not explain the empty review.

Shared-case resolution uses the same actor visibility as case reads. A question/draft write can initialize a new case, reuse an existing visible case unchanged, or explicitly detach. It cannot fill or change an existing shared stem, including a blank one; differing supplied text returns validation guidance to the existing authorized revisioned case editor. Case authorship attribution and acting-user authorization are separate inputs. Question edits stabilize old assessed content with their question lock, avoiding an old-parent lock before a newly selected parent. API/admin/link/import writers coordinate through the existing structural gate; this source policy does not verify arbitrary direct ORM writers or runtime locking/performance.

Ordinary answer/navigation writes reject paused state independently of optional expected-index/slot fields. Actions are `same`, `next`, `previous`, `goto`; only goto accepts a required valid target index. A terminal index at the question count cannot acquire answers or advance farther; answer-free previous/goto can recover terminal/legacy invalid positions. 409 reasons distinguish `TIME_EXPIRED`, `SESSION_PAUSED`, `SESSION_PROGRESS_CHANGED` and `SESSION_POSITION_INVALID`. Successful writes include an additive normalized `saved_slot` acknowledgement. Matching Vue sends retained index/slot baselines and requires explicit read/review after uncertain writes; no automatic mutation replay.

`session_label` is descriptive; `tags_filter` and other selection inputs retain their full values. The service bounds session/history display labels to their shared model limit (currently 100 characters), using a trailing ellipsis for longer labels. Labels within the limit remain unchanged; nontext API labels return 400 before replacing a session. This requires no schema change.

Android/Vue recall first save the typed pre-answer with `action=same`, then fetch choices for the same question. Question navigation/ordinary Finish wait for revealed choices and a selected answer. Keyboard choice selection after reveal and pause remain available; this client policy does not add a backend restriction to API navigation.


### Ordinary practice by source book

`GET /questions/source-books/` requires authentication and returns `{items: [{name, count}]}` for nonempty exact `Question.source_document` titles in the public practice bank (private drafts excluded). Exam/study/recall start bodies and `GET /questions/available-count/` accept optional `source_document` (nonblank string, at most 500 characters). Match the complete title exactly; commas and punctuation are literal, not tag separators. Book and other filters intersect; tag alternatives retain their existing OR semantics within the book. An explicit question-ID start with a book title rejects IDs outside that book. Existing start capability and session ownership gates are unchanged. New clients require this backend contract before rollout. Empty source metadata does not appear as a book; no schema change or automatic import is needed.
