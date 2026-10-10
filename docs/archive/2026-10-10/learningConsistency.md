> Historical snapshot before the 2026-10-10 documentation reorganization. Current status: [documentation index](../../README.md). Do not use unchecked items here as the current queue.

# Learning consistency implementation — 2026-10-09

Implements the seven findings and learning/recovery improvements in [the review](../reviews/2026-10-09-backendLearningReview.md). Source completion is separate from schema preparation, compilation and live verification.

## Durable evidence and assessed versions

`LearningEvent` retains the original question ID, assessed fingerprint, source identity, occurrence/receipt times, classification/concept snapshots, correctness/confidence/error and derived review/mastery credit. User deletion clears private evidence; question deletion retains historical events through SET_NULL. `(user, source_key, original_question_id)` prevents duplicate side effects independently of deletable history. Ordinary first-attempt markers and offline receipts remain additional protections.

`LearningDay` provides a compact daily answered ledger for streak calculations. `QuestionExposure` stores allocations, first presentations and answers separately for each user/question/fingerprint; `QuestionPresentation` makes repeated question reads idempotent within a source. Presentations mean server-generated question responses, not proof of screen visibility. Session/history deletion does not remove this evidence. Unsynchronized offline study remains unknown to the server.

Question/concept assessed translations now participate in fingerprints. Question explanations and translated explanations do not. Translated option lists must be nonblank, have the base option count and preserve option indexes; semantic translation quality cannot be proven by structural validation. Base content, translated assessment, concept and case invalidation reset current question statistics and SRS state. Historical grading/events remain. Live counters update only from matching assessed content, using `Question.stats_fingerprint`.

## Chronology and scheduling

Ordinary answer slots record first/final server answer times; master answer times feed grading/learning instead of being discarded. New offline packs include a signed `issued_at` anchor. Android saves a download-time clock offset and freezes answer/completion timestamps in encrypted material. No upload retry regenerates those timestamps or the completion identity/body.

Offline occurrence must be between signed issue time and server receipt time, allowing five minutes of future clock tolerance before clamping. Answer times must fall within the same bounds and precede completion. These are bounded client declarations, not cryptographic proof of when a human answered. Invalid clocks fail without changing local pending results. Legacy materials omit new fields and retain the original receipt-body identity; accepted undated uploads use receipt time. Packs created before the assessed-fingerprint change may fail first-commit content validation and require new downloads; local material is retained, and an existing identical completion receipt remains recoverable.

Normally SRS advances from the latest state. A delayed event replays only that question's matching-content events in occurrence/receipt/ID order and recomputes derived due-review/mastery credits, so older evidence cannot become the latest state ahead of newer practice. First exposure is not counted as a completed due review. Early correct practice records confidence/correctness but cannot advance a schedule, including during relearning. Wrong answers reset the chain and enter relearning; a due successful review exits it.

## Activity, coverage and selection

Planner credits use individual occurrence days and preserve plan date/target checks. Streaks derive from learning days, including late gap-filling uploads; expired current streaks render as zero. Activity charts/leaderboards use learning events, so paused/discarded study is visible and finishing an unanswered session adds no answered-learning activity. Completed-session analytics still describe completed assessments where that is the existing contract.

Reports add period-wide distinct questions/concepts, completed due reviews and net mastery change (summed question score points). They retain answer-volume counts and leaderboard ranking. Concept mastery requires mastered evidence from at least three variants (or all variants for smaller concepts) and at least half the available variants; otherwise its score is capped below the mastered threshold.

Both clients offer `selection_strategy`: `coverage` (default), `balanced` and `review`. Coverage prefers never-presented/answered content, then lower allocations/exposure and older timestamps; concept diversity resolves otherwise comparable choices. Balanced prioritizes unseen or due items; review prioritizes due and weak items. Blueprint category quotas remain authoritative, share concept diversity across buckets, and keep selected clinical-case siblings together. Explicit IDs, SRS order and curated master compositions remain unchanged. Ordinary automatic selection and allocation recording occur under the same learner transaction. This prevents concurrent start selection from ignoring the preceding committed allocation, but cannot guarantee disjoint sets when filters/quotas exhaust alternatives.

Selection uses indexed exposure records instead of scanning history JSON. Eligible question pools are still materialized; large-bank performance and server-database locking require runtime measurement.

## Permissions, retention and write recovery

Without `tests.download_full_bank`, every successful selected-pack request shares a server-enforced lifetime budget of 200 distinct question IDs (`OFFLINE_SELECTED_QUESTION_LIMIT` setting override). Re-downloading previously granted IDs is allowed. All pack requests record grants, including privileged downloads; revocation blocks new IDs beyond the budget. The bulk flag cannot bypass the budget. Capability holders retain full-bank access; small banks fitting the selected budget can still be downloaded through allowed selections. Existing local packs are retained and completion synchronization keeps its independent `tests.start` contract.

Deleting a master exam copies completed attempts into caller-owned History before the FK cascade, retaining frozen results, exam identity/name, weighted score, forced finish and original dates. It does not replay learning credit. Deletion locks learners before the exam/attempts to avoid FK-lock inversion with finish; a changed participant set returns 409 before writes. Both clients display archived weighted scores. Explicit history deletion remains possible, while the independent learning ledger survives.

Bookmark GET/PUT reads/sets explicit state; legacy POST toggle remains for older clients. Native detail/bookmark removal and Vue use explicit set operations. An uncertain detail/list update retains its intended state so explicit Retry cannot reverse a previous successful change.

Question create/duplicate accepts optional `operation_id`. `QuestionWriteReceipt` atomically binds caller/UUID/body digest/result; repeated identical requests return the existing visible result and altered bodies reject. Read-only reconciliation uses `GET questions/?operation_id=...` and `GET questions/<source>/duplicate/?operation_id=...`, with current capabilities and caller/visibility checks. New clients retain unknown identities, read receipts and expose explicitly initiated retries of the same identity/body. No automatic create replay occurs. Android new-question identity uses existing encrypted draft recovery; detail duplication and Vue pending writes remain memory-scoped, so those identities do not survive process/page destruction. That durability extension is separate from safe in-session recovery.

Question and knowledge edits require `expected_version` even on partial updates; group metadata adds a version and requires it at the API. Stale edits return 409. Native knowledge/group editors send their retained baseline versions, and existing Vue question/group stores supply versions. Current locks/ownership checks and draft preservation remain. Other taxonomy/case operations retain their existing policies.

## Schema and verification

New tables: `LearningEvent`, `LearningDay`, `QuestionExposure`, `QuestionPresentation`, `OfflineQuestionGrant`, `QuestionWriteReceipt`. New fields: question stats fingerprint, SRS relearning flag, group version and archived-master History metadata. The database clear operation includes these records and resets retained users' streaks. No clear/setup/seed/migration/database action was executed by the agent.

The user plans a fresh database. Follow [startup guidance](../../guides/START_HERE.md): normal SQLite startup generates initial migrations only for model apps whose migration folders are absent. Deleting the database while keeping old migrations does not generate the new schema. `runserver` and interactive startup do not prepare schema. Existing data was not backfilled; this implementation targets the authorized fresh-schema workflow. Reload matching backend and rebuild matching Android only after schema preparation.

Source checks: Python production AST, JavaScript/extracted Vue scripts, locale JSON, Android XML/resource references/placeholder agreement, Kotlin delimiters and diff whitespace. These do not establish Django imports, SQL/transactions, HTTP, Kotlin/Vue compilation, device/browser accessibility or runtime correctness. No builds, suites or migration work were run.

Pending runtime scenarios: concurrent starts; edit/translation/case change during finish; wrong→immediate correct→due correct; delayed offline before/after newer online practice; midnight/gap-filled streaks; altered/identical upload retries; paused/discarded activity; budget bypass attempts and revocation; master deletion/history access; missing/lost create receipts and explicit retries; revision races, private visibility and account/server isolation.

## 2026-10-09 taxonomy/case/settings revisions and content receipts

Added Category.version and ClinicalCase.version (default 1; content-field saves increment), mandatory expected_version on their update/delete/stem APIs, a shared tag forest revision returned by tree reads, and a runtime settings revision returned by GET/POST. Revision comparisons occur within write transactions after the relevant locks; tag create/rename/reparent/delete invalidates the forest revision. Category/case DELETE passes its revision as a query parameter. Case title/stem validation and authorization complete before one atomic write; linked questions are locked before the case in the HTTP mutation paths.

New ContentWriteReceipt has a caller-scoped unique operation UUID, action, canonical request SHA-256 and nullable target ID. Category/knowledge create optionally accepts operation_id; identical successful retries return the original target, changed bodies/actions conflict, deleted results return 404. Receipt creation and target creation share one transaction; the unique receipt row serializes identities without a broad User lock. GET /api/v1/recovery/operations/<uuid>/ returns the caller's action/target metadata; ordinary target reads independently enforce capability/visibility. Own unresolved report state is readable from the question flag endpoint.

Category/Case fields and ContentWriteReceipt require matching fresh schema and clients; no schema setup/migrations/database action was performed. Normal fresh SQLite startup with old app migration folders removed can generate initial schema; deleting only the database while old migration files remain is insufficient. Source checks do not establish live database locking, deadlock behavior across all ORM writers, HTTP or client/device correctness.

## Rescan follow-up DELETE/receipt contracts

Question DELETE and knowledge-object DELETE require query expected_version, validated as an integer >=1 and compared under transactional row locks. Question services also recheck current owned_by/override after locking; visibility is re-evaluated with a locking read. Native/Vue question confirmation captures the displayed revision, and native knowledge deletion retains its editor baseline. Generic content receipt GET adds target_exists for the caller's stored category/knowledge operation, preserving action/target_id. Missing/deleted committed targets do not recreate under the same operation identity; native acknowledgement retires that identity without clearing the user's draft. No new schema fields, schema setup or runtime concurrency verification in this follow-up.

## 2026-10-10 eight deeper findings fixed in source

All eight bounded findings are addressed in production source; the original review remains historical evidence.

- Assessed parent saves lock linked questions before parent rows; knowledge/question/tag writers and state imports coordinate their dependency locks. Existing imported questions and knowledge objects advance the locked local revision instead of adopting the source revision. Imports deliberately take broad user/question locks; large-import contention still needs measurement.
- Master start locks fresh access relations, rechecks new-start/preview access, resumes either active normal or makeup attempts before new-start classification, and finishes expired attempts without granting extra time. Existing owned work is retained.
- Master answers require session_id and the full expected_slot (including null), compared under lock. Identical saved intent is idempotent; conflicting saved intent returns ATTEMPT_PROGRESS_CHANGED. Navigation requires session_id and expected_current_question_id; current-question reads do not persist fallback navigation. Expiry finish failures propagate.
- Web/native master recovery retains uncertain drafts, reads authoritative full answer slots, and requires explicit comparison/rebase/discard before another conflicting write. Web polling has disposal/cancellation generations and exam/session/store/progress ownership guards; route changes cannot adopt an old attempt response.
- Planner update/delete requires expected_id and expected_version; successful updates return accepted configuration/revision. Both clients retain editor baselines and provide explicit conflict resolution. StudyPlannerScope/ScopeDay preserve timestamp-based historical filter attribution: explicit filter/date changes reset today's displayed progress, taxonomy rename/merge continues it, and historical days include all their original scope activity after midnight without double counting. Global learning events remain intact.

Verification is production AST, JavaScript/extracted Vue script syntax, locale JSON, native lexical/XML/resource/placeholder and whitespace checking only. No builds, compilation, automated suites, migration inspection/work, setup/seeding, database writes, deployment or versions. Matching backend/web/native rollout and matching planner schema are required. Actual HTTP, database interleavings, browser/device recovery and accessibility remain release checks.

### Planner schema and rollout

StudyPlanner.version, StudyPlannerScope and StudyPlannerScopeDay require matching schema. For the approved fresh SQLite workflow, normal `python start.py sqlite` with old app migration folders removed generates initial schema from current models. Deleting only the database while old migration files remain does not generate later model changes. `manage.py runserver` and `python start.py -i` skip schema setup. No setup or migration actions were performed here; schema readiness remains unverified.

Master answer/navigation and planner preconditions are mandatory: deploy matching clients together. A legacy native answer draft without the new baseline/session must be explicitly reviewed and rebased. Imported source revisions are not local concurrency tokens. Scope histories attribute delayed evidence by occurrence time, using frozen category/tag snapshots; they do not reinterpret earlier activity under today's filters.
