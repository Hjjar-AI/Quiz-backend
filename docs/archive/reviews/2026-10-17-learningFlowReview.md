# Backend learning-flow source review

Reviewed 2026-10-17. Scope: ordinary start/read/prefetch/answer/pause/discard/finish; master start/answer/navigation/finish; signed offline packs/completion receipts; durable events, replay, exposure, SRS, mastery, activity/streaks and planner scope attribution. Checked relevant Vue controllers and Android ordinary/offline DTOs and synchronization callers. This is a bounded source review, not an exhaustive correctness or runtime claim.

## Findings

### L1 — P1: study/recall bypass closed-book answer withholding

`apps/exams/services/exam_service.py:199` replaces only the same mode, so study and exam sessions coexist. Explicit-ID starts check question visibility, not `closed_book_question_ids` (`apps/exams/views/session_views.py:175`). `GetSessionQuestionsView` passes `include_study_feedback=True` for every page (`:280`); `ExamService.get_question` exposes study keys and explanations solely on mode (`exam_service.py:305`). Study/recall answer responses also expose correctness/explanations without the shared restriction (`session_views.py:368`).

Reproduction: start an ordinary exam or unfinished master attempt containing public Q; start study with explicit ID Q; fetch the owned study question bundle. It returns Q's answer before the exam is finished. A pre-existing overlapping study session works too; merely filtering new starts would leave that path open. Vue supports explicit-ID study starts; Android downloads owned study bundles. This is a backend authorization/policy gap, independent of client UI guards.

Apply shared closed-book policy at every feedback delivery boundary, including prefetch and completed study result delivery while another exam remains open. Coordinate a clear rejected/withheld contract with clients that currently expect downloaded study keys. Previously downloaded keys cannot be recalled; prevention cannot promise secrecy for material already supplied.

### L2 — P1: knowledge-object reads disclose answer material during closed-book work

`apps/questions/views/knowledge_object_views.py:15` annotates visible question counts but does not filter knowledge objects or apply answer withholding. Authenticated list/detail reads serialize `canonical_answer`, `key_facts`, `misconceptions` and all translations (`apps/questions/serializers/knowledge_object.py:33`). The list also permits searching canonical answers (`knowledge_object_views.py:48`). Unlike linked-question serialization, none of these reads uses the shared closed-book policy.

Reproduction: link a question to a knowledge object whose canonical answer identifies its correct choice; start an unfinished exam containing it; read the knowledge object by ID or list/search. The assessed answer remains available even though the question serializer withholds the key. Android has reachable knowledge-detail navigation; frontend question authoring also fetches knowledge objects. Missing UI links do not protect the API.

Define a learner-safe representation for objects linked to withheld questions, preserve authorized management separately, and account for list/search and translated material as well as detail reads. The queryset also returns objects linked only to others' private drafts; whether knowledge objects are intentionally globally readable needs an explicit content-visibility policy before classifying that broader behavior as a separate defect.

### L3 — P1: paused ordinary sessions still accept answers and navigation

`apps/exams/services/exam_service.py:419` checks `is_active` only inside `expected_index is not None`. That field is optional in `SubmitAnswerSerializer`; Vue ordinary submissions currently omit it. `is_time_expired` uses accumulated time without advancing the clock for inactive sessions (`:226`).

Reproduction: start an exam with remaining time, pause it, then POST an answer/navigation request for its session without `expected_index`. The answer is saved while the session remains paused; repeated requests can fill the exam without consuming active time. Study/recall writes can likewise mutate paused state and navigation can commit learning evidence. Resume and finish have separate state handling, so ownership and row locking alone do not close this gap.

Reject inactive writes unconditionally under the session lock, before answer/navigation work. Keep optional legacy preconditions separate from required lifecycle invariants. Android's ordinary writes generally provide the index; the backend must still protect older/current web and direct callers.

### L4 — P2: ordinary navigation accepts invalid actions and unbounded next indices

`apps/exams/serializers/exam_serializers.py:84` declares `action` as unrestricted text and does not validate action/target combinations. `apps/exams/services/exam_service.py:542` increments `current_index` for every `next` without a ceiling. Further submissions at/past the end can write answer slots without any corresponding question and move still farther. `get_question` then returns no question. `ExamSession` has no index validation hook.

Reproduction: in a one-question study session, submit `next`, then submit `next` again. The index becomes 2 for one question, and the question endpoint returns 404. This is especially relevant to the existing web uncertain-write/retry gap. An unknown action can also save an answer while silently ignoring requested navigation.

Validate the action enum and target combinations; define the supported terminal index and enforce its bounds under the lock before mutations. Preserve valid final-question behavior and return an explicit conflict/recovery response for stale navigation.

## Existing coordinated finding confirmed

Ordinary expiry and stale-progress exceptions still share an untyped 409 (`apps/exams/views/session_views.py:345`). Vue treats every exam 409 as forced finish (`frontend/src/features/testCommon/composables/useTestQuestionController.js:107`) and omits expected-index/slot guards. This is already queued in the frontend plan; adding backend guards without semantic reasons and matching recovery handling would expose that client defect more often.

## Learning behavior traced without a new confirmed defect

- Study/recall first-answer evidence is flushed on navigation, pause, replacement, discard and finish; final editable choices are retained separately. Timed ordinary/master exams record learning at completion. These are distinct policies, not interchangeable paths.
- Learning-event identity is independent of deletable history. Planner/activity credit uses newly created events, and current-content fingerprints gate live counters/SRS. Offline identical receipts return before first-commit revalidation.
- Delayed matching-content evidence rebuilds question SRS in occurrence/receipt/ID order; early correct practice cannot extend the due date or exit relearning. Mastery includes confidence, successful repetitions and concept breadth.
- Planner scope history and read-time projection preserve historical scope counts after midnight; current explicit resets differ from taxonomy changes. Streak reads account for elapsed inactive days.
- Standalone offline uploads support declared answer/completion occurrence times. Downloaded ordinary answers retain server submission chronology; local answers do not establish server learning credit. Offline packs currently omit error-reason reflection from both Android DTO and backend serializer; this is a functionality limit, not a newly demonstrated loss of a supported field.

## Verification limits

Production-source/control-flow and caller inspection only. No test-suite inspection or execution, migrations, setup, database access, HTTP requests, builds/compilation/packaging, versions, deployment or production-code edits. Reproduction sequences above are derived from current source, not executed observations. Actual concurrency, deployed schema, browser/device behavior and performance remain unverified.

## Source corrections

Follow-up review found B1 (completion blocked by overlapping master withholding), introduced by this batch's finish guard. It is now [source-corrected with B2–B4](2026-10-17-backendMajorReview.md#source-corrections): completion commits while question review may remain withheld. Earlier descriptions below record the initial correction batch; the follow-up contract supersedes its finish guard. Runtime verification remains in workPlan.

Implemented after the user's explicit fix request on 2026-10-17:

- L1: shared `ANSWERS_WITHHELD` enforcement for ordinary study/recall start, individual/bundle reads and writes; overlapping ordinary finish/result/history delivery and offline receipt reads also withhold material. An ordinary exam excludes its own live session from its finish check. Starts, ordinary question reads and answer feedback serialize on the learner lock. No new study write or result is produced by rejected requests; committed offline receipts remain stored and readable after the overlapping exam finishes. Already delivered/downloaded content cannot be recalled.
- L2: knowledge-object queries omit concepts linked to unfinished exams before answer searches/counts; detail/update reads return semantic withholding. Both frozen assessed and current live concept links are protected. Global knowledge visibility outside closed-book restrictions and existing management permissions remain unchanged.
- L3: the locked service rejects paused writes regardless of omitted index/slot preconditions, using `SESSION_PAUSED`.
- L4: serializer/service action and target validation precedes mutation. `len(question_ids)` remains a supported terminal position; writes beyond real questions reject with `SESSION_POSITION_INVALID`. Explicit answer-free previous/goto can recover terminal/legacy invalid positions without creating ghost answers.
- Coordinated Vue: ordinary writes include the retained index/slot baseline; successful responses add `saved_slot`; errors preserve `details.code` (`TIME_EXPIRED`, `SESSION_PROGRESS_CHANGED`, `SESSION_PAUSED`, `SESSION_POSITION_INVALID`). Only typed expiry triggers forced exam finish. Other failed attempts remain memory-only, disable conflicting actions and protect navigation until explicit server-state review. Review never resends a mutation; an explicit retry requires the same original question and unchanged baseline. Confirmed progress, paused/completed/missing sessions and withheld/unavailable pages have explicit discard/use-server paths. Account scope/generation checks discard stale async results; reset/logout clears private drafts. Older servers without `saved_slot` use a follow-up read without replaying the confirmed write.

Backend-first deployment is required for matching Vue semantics. Android already retains downloaded drafts and handles ordinary failures through recovery; its optional baseline fields and unknown-field-compatible decoding need no change for this batch. Its existing locally downloaded material remains subject to the documented inability to recall previously supplied answers.

Checks: changed production Python ASTs, JavaScript and extracted Vue-script syntax, bilingual JSON key/placeholder parity, source/caller/acknowledgement tracing and whitespace. Vue SFC parser unavailable; templates are source-reviewed only. No suites inspected/run, migrations/schema/setup/database/HTTP, builds/compilation/packaging, versions, deployment or live concurrency/browser/device verification. Earlier findings/reproduction sequences remain historical source evidence, not claims that fixes were exercised at runtime.
