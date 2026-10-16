# Remaining logic/model review — 2026-10-17

Reviewed current production source after the B1–B4 corrections, preserving those uncommitted changes. Findings below are source-derived reachable sequences, not runtime reproductions. This pass changes documentation only.

## C1 — High: learning objectives escape closed-book withholding

`apps/questions/serializers/question_read.py:28–32,102–111` always serializes the linked knowledge title/objective. Its withholding branch clears only the correct answer, explanation and translated explanations. `apps/learning/knowledge_map.py:11–18,86–94` separately returns active public-linked knowledge objects and their learning objectives without consulting the frozen/current closed-book knowledge policy.

An objective can explicitly state the fact being assessed; the model accepts free text. Start an exam containing a public question linked to such an object, then read its question detail or knowledge map. The dedicated knowledge detail rejects access, but these alternate representations return the same objective. A public sibling sharing a withheld knowledge object also needs policy review; hiding only the exact question ID does not cover that relation. Vue `features/knowledge/views/KnowledgeMap.vue` and Android `ui/knowledge/KnowledgeMapScreen.kt` display this field directly. Both clients are affected; this is an omission in the earlier L2 correction.

Apply the shared frozen/current knowledge withholding policy to all assessed knowledge representations, including nested question fields and the map; preserve non-sensitive mastery summaries where possible.

## C2 — High: draft deletion bypasses fresh ownership/usage and breaks unfinished attempts

`apps/master_exams/views/drafts_views.py:207–235` fetches a draft, checks its owner and checks blocking exam usage before entering a transaction. Inside the transaction it deletes every question membership and the question without locking/rechecking the draft or the relevant exams. A composer can attach an initially orphan draft after the blocking check; deletion then removes that new attachment from an exam the caller was told should be protected. Publication can similarly turn the fetched draft into public bank content before deletion uses its stale instance.

A sequential failure also exists: begin an attempt, cancel its exam, then delete one of its draft questions. Cancellation does not finish attempts; the draft delete explicitly permits cancelled attachments. The attempt still has question IDs and a grading snapshot, but `apps/master_exams/services/master_exam_attempt_service/question_flow.py:65–75` returns no question when the live row is absent, before reading the snapshot. The current-question API returns 404. Ordinary PROTECT usually prevents this deletion; this handler explicitly removes that protection by deleting through rows first.

Vue and Android draft libraries call this same DELETE; neither can make the server's check/write interval atomic. Coordinate fresh authorization, draft identity and exam usage under the established lock order, and retain usable frozen attempt content or explicitly resolve unfinished attempts before deleting their dependencies.

## C3 — High: draft edits bypass question revisions and silently overwrite newer content

`apps/master_exams/serializers/draft.py:31–40` omits `Question.version`; its write serializer accepts no expected revision. `apps/master_exams/views/drafts_views.py:153–204` takes a row lock but writes the submitted complete question content and calls `draft.save()` without checking or advancing the version. `Question` has invariant hooks but no automatic revision increment.

Two draft editors reading the same baseline can both save successfully; the second overwrites the first. More subtly, the normal question editor may read version N, a draft-library editor changes that row without advancing N, then the normal editor's `QuestionService.update_question` CAS (`apps/questions/services/question_service.py:250–267`) accepts its stale baseline and overwrites the draft change. Row locking serializes writes but cannot detect this stale intent.

Vue `features/masterExams/views/MasterExamDrafts.vue:198–233` sends no revision. Android `data/remote/MasterExamService.kt:115–117` has the same contract; `ui/masterexams/ExamDraftLibrary.kt` explicitly recognizes that its preflight leaves a read/write gap. Expose/check the baseline and advance the shared question revision on draft mutations; coordinate both clients and preserve their drafts on conflict. Audit other direct question writers separately rather than claiming all model saves already bump revisions.

## C4 — Medium: bank publication accepts draft/cancelled lifecycle states

`apps/master_exams/services/master_exam_service/lifecycle.py:354–372` rejects only an already-bank-published exam or an unclosed window. It never requires a published/completed source state. The create serializer validates relative opening/closing/duration but permits past windows. Therefore an overdue never-published draft, or an overdue cancelled exam, can transition directly to `published_to_bank`, promoting its private questions to public bank content.

The endpoint still requires management and bank-publication capabilities, so this is a lifecycle error, not a capability escalation. Vue's results control and Android's review screen require completed status. Android's editor `ui/masterexams/MasterExamEditorViewModel.kt:235–236` instead mirrors the weaker server condition, and its lifecycle buttons make this reachable through normal native controls. Validate the allowed source states under the exam lock and align all native/web controls with that contract.

## Scope and limits

Traced model hooks, ordinary question revisions, draft callers, cancellation/publication, attempt snapshots, knowledge-map delivery and planner reconstruction. The initial suspicion of unrestricted ordinary deletion of master-exam questions is narrowed by `MasterExamQuestion.question=PROTECT`; C2 identifies the explicit detach/delete path that bypasses it. Planner reconstruction was not promoted to a concurrency finding without a proved interleaving.

No production fixes in this pass. No suites inspected/run, migrations inspected/changed, database/HTTP access, builds/compilation/packaging, versions or deployment. Previous source checks do not verify these new sequences or exhaustive backend correctness.

## Extended findings and source corrections

Implemented after the subsequent request to check further and fix the findings:

- **C1:** maps exclude withheld concepts; nested question titles/objectives redact the frozen/current concept set, including visible siblings, with request memoization.
- **C2:** DELETE requires the displayed revision and rechecks draft identity/ownership/attachments atomically. Lock order: actor, discovered exams by PK, structural gate, question, memberships. Unknown new exam links conflict before deletion. Composition/creation, publication and admin attachments coordinate the gate; creation rechecks visibility. Terminal cleanup remains supported. Master pages render frozen snapshots before consulting live rows, preserving snapshot-backed display/answer/grading after deletion; legacy missing snapshots remain a limit.
- **C3:** reads expose Question `version`; PUT requires body `expected_version`, DELETE its query value. Direct saves track editable/ownership/verification revisions; SQL CAS writers increment explicitly. FK comparisons use stored IDs and names/attnames. Publication advances question revisions. Vue guards writes and retains uncertain/conflicted intent for explicit read-only comparison/use-server/keep-draft/discard; Android sends its selected revision after existing preflight and checks versions on restore. No automatic replay. Old clients reject safely without revisions; matching rollout required.
- **C4:** bank publication requires published/completed stored state and closure under lock. Native editor eligibility matches; capabilities unchanged.

Three additional evidenced defects were corrected:

- **C5 — explanation search oracle (high):** explanation matching preceded redaction, revealing hidden phrases via list membership/counts. The predicate now excludes hidden IDs from explanation matches. Public list/count and ordinary/SRS/blueprint selection pass answer-policy identity separately from public visibility; offline catalogue uses the predicate. Permitted question/source/tag matching and privileged admin exports retain their contracts.
- **C6 — planner admin scope drift (medium):** date-only saves left old scope/revision, so learning used old dates while UI/queue used new ones. Admin captures old scope under lock, advances revision and records final scalar/M2M scope. Derived daily ledgers are read-only; previously accepted manual changes could be ignored/overwritten by scope projection. Historical scopes and API chronology remain authoritative.
- **C7 — exposure foreign-key race (medium):** allocation/presentation checked live question existence without holding its row through dependent inserts. Deletion between check and insert could raise IntegrityError and fail session start/page delivery. Both helpers now lock learner then live questions (allocation in PK order) through the writes. Ordinary replacement locks old/new question rows before recording pending learning, avoiding new question locks after old assessed-parent locks. A deleted question is skipped for exposure while its frozen page remains usable. Existing event/grading identities and counters are unchanged.

Also fixed draft choice-count changes with retained translations reaching model ValueError/500: the API now returns structured field validation without silently deleting translations. Coordinated translation edits remain available in the ordinary editor.

Checks: 33 changed production Python ASTs including prior work, revision-field names, changed JavaScript/extracted Vue scripts, local imports, bilingual JSON, native service/callers and whitespace. Vue parser unavailable; templates/Kotlin source-reviewed without compilation. No suites inspected/run, migrations/schema/setup/database/HTTP/concurrency, builds/packaging, dependency/version changes or deployment. This bounded closure does not establish exhaustive correctness or total deadlock freedom.
