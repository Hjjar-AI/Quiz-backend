# Django remaining work

## 2026-11-27 Ibn Rushd exam verification

- All 30 questions rechecked; initial approved edits/copyediting plus strict-recheck Q2/Q16 clarifications applied. No pending content decisions from this pass. Live import/Arabic rendering and any update of already imported rows remain unperformed and separately scoped. [Review and approved edits](../import_data/extracted_and_reviewed/ibn_rushd_exam/review/clinical_review.txt).

## 2026-11-25 additional-source verification and source gaps

- Offline extraction of all nine staged groups and bounded image/question overlap comparison are complete: [193 additional rows; recommended 350 canonical exam rows](../import_data/README.md). Each actual exam remains isolated; current collection locations and reviewed status are recorded in the index. Original 2015/2019 payloads and approved records remain unchanged; the recommended separate 2019 view selects 98 unique rows.
- The 197 remaining deferred source appearances need fuller source material, unambiguous keys or a separately requested editorial review before grading; they include 77 July 2024 recall notes. Fourth-year April 2015 lacks Q92–96, with partial Q56/Q91 and an inferred Q97 continuation. Full July 2015 has ten deferred units. No missing material/medical answers were invented. Optional live import/Arabic/RTL verification and independent clinical review remain unperformed; no application/database write, suite/build, migration or version work is authorized by this record.

## 2026-11-25 July 2015 psychiatry extraction verification

- Offline extraction/export is complete: [59 matching Mukhtabir CSV/JSON rows](../import_data/extracted_only/psychiatry_july2015_ar/README.md), tagged **امتحان الهيئة الأول 2015**, from the user-selected newer PDF. Optional live import and Arabic/RTL rendering remain unverified. Printed keys and source wording issues are preserved and documented; no independent clinical correctness is inferred.

## 2026-11-25 July 2019 psychiatry extraction verification

- All 24 requested editorial dispositions are applied; no pending selections. The [backend-only delivery](../import_data/extracted_and_reviewed/psychiatry_july2019_ar/README.md) contains 100 matching import rows and all 100 readable records; no deferred items, with approved Q83/Q99 rewrites included as D. Optional live import and Arabic/RTL rendering remain unverified. Retained-with-note items preserve their clinical limitations; see the saved English decision record and explanations.

## 2026-11-04 content-limit verification

- Verify actual DSM/Kaplan import/rendering after matching rollout, including restored DSM `4.4` choice E. [Offline limit review](verification/bookLimitReview.md) is complete; existing UUIDs skip rather than update, so any already-imported row needs a separately authorized update path.

- Source implementation and PreTest regeneration are complete. After milestone approval, verify 4,000/4,001 text boundaries, 500/501 choice boundaries, translations/cases, 2/15/16 choices, answer 15 and 15-column import/export. Deploy matching backend before refreshed clients; verify import, large/RTL text, options 10–15, keyboard/focus and actual Android/browser behavior. Existing UUIDs skip rather than update; no database repair/import was performed. [Contract and evidence](contracts/questionContentLimits.md). Suites, compilation/builds and migration work retain their separate authorization gates.

## PreTest Psychiatry 14 — remaining verification

- Offline extraction, translation, chapter exports and artifact checks are complete. Live import/bilingual/RTL/Markdown rendering and independent current clinical/legal review remain unverified; source-conflicted grading items retain their original keys. [Delivery, evidence and limits](verification/pretestPsychiatry14Extraction.md). Database writes, suites/builds and editorial key changes require their applicable authorization.

## Remaining test coverage

- Current existing suites pass completely on PostgreSQL (1053), Android (63) and Vue (951); SQLite passes 1017 with 36 intended PostgreSQL-only skips. [Current evidence](verification/pythonTests.md).
- Future Android additions: DTO parsing fixtures for analytics/admin/moderation/transfer/groups/planner, real Compose navigation/reveal/selection/restoration controls, and offline completion/sync/uncertain-write flows. Device encryption, airplane-mode connections, accessibility, actual browser/deployed proxy behavior and production capacity remain separate verification scopes. Propose concrete coverage/commands at the next milestone; do not infer full behavioral coverage or fresh coverage percentages from existing-suite results.

## 2026-10-23 Android API rollout verification

Focused database-free contracts now pass 32/32; their mocked ORM/service boundaries do not establish database or deployed HTTP behavior. [Evidence](workDone.md#2026-10-23-focused-androidbackend-regression-run).

- Deploy matching backend before Android. Verify English/Arabic errors and field fallbacks, app versus device language, CSRF token rotation/one rejected-request retry on login/writes/exports, and no retry of permission failures or unknown mutation outcomes. Verify query-based discard/master deletion and password-authorized POST user deletion (permissions/self/last-admin protections, response loss); body-based requests still used by the current Vue frontend must work.
- Verify JSON-array filters on availability, start, offline catalog and all export formats, especially tag names containing commas, empty selections and comma input still used by current Vue callers. Exercise actual HTTPS/proxy Host-with-port, forwarded scheme and trusted origins; source configuration does not establish deployment behavior. Android compilation/unit suites now pass; device/live HTTP remain unverified. No packaging/deployment authorization is inferred.

## 2026-10-18 book Arabic review

- No unreviewed original prompts/cases/choices or nonempty explanations remain: cumulative direct review covers all 476 DSM exercises and 602 Kaplan questions, with 475 DSM standalone explanations, 26 glossary-derived explanations and 602 Kaplan explanations. Both PDFs have now been used to source-check all 134 questions in the previous manual list; no PDF transcription checks remain for that list. All 30 remaining issues now have cited bilingual explanation corrections/qualifications (28 external-evidence entries, two source-only contradictions). Decide whether to rewrite ambiguous/unsupported graded items coherently or exclude them from grading; explanation warnings preserve source keys and do not resolve that editorial choice. See the [evidence report](verification/bookEvidenceReview.md). Verify actual import and bilingual rendering in the running app; existing imported UUIDs are skipped, not updated. [Coverage and limits](archive/reviews/2026-10-17-importDataReview.md). [Source-checked editorial decisions](verification/bookManualReview.md).

## 2026-10-17 logic/model correction verification

- [C1–C7 plus translation validation](archive/reviews/2026-10-17-remainingLogicReview.md#extended-findings-and-source-corrections) are source-corrected. Deploy matching draft-client contracts; verify concept/sibling withholding, explanation-only searches/counts, permitted matches, concurrent draft edit/delete/attach/publication/admin, deleted-live-row snapshot navigation/answer/finish, revisions, translated-choice rejection and client unknown-write review. Check invalid bank transitions and normal publication.
- Verify admin planner scalar/M2M scopes, current/delayed attribution, resets, revisions and read-only ledgers. Measure mixed actor/exam/gate/question locking; source checks do not establish runtime concurrency/capacity or total deadlock freedom. These records do not authorize suites/builds/migrations.

## 2026-10-17 additional major-fix verification

- [B1–B4 source corrections](archive/reviews/2026-10-17-backendMajorReview.md#source-corrections) are implemented. Verify ordinary finish/expiry with overlapping master work, exact result recovery after response loss, saved summary versus withheld/full review and failed explicit refresh on Vue/Android. Verify private/blank/shared case links, actual actor versus author, differing/equal stem hints, revisioned editor recovery, explicit detach and duplication of withheld questions.
- Verify planner/category merge and case/learning concurrency on the deployed row-locking database, including API/admin/bulk deletion, flat/Telegram/state imports, new links during parent edits, changed relationships, audit/receipt rollback and lock duration under mixed workloads. Source coordination does not establish freedom from all deadlocks or server capacity.
- Verify middleware/login/background renewal against concurrent admin disable, expiry shortening/clearing, renewal disable, bypass-capability changes and password reset. No source completion implies HTTP/database/browser/device concurrency verification. Builds/suites/migrations remain subject to explicit-request restrictions.

## 2026-10-17 learning-flow verification

- [L1–L4 and coordinated Vue recovery](archive/reviews/2026-10-17-learningFlowReview.md#source-corrections) are source-complete. Deploy backend before matching Vue; verify overlapping ordinary/master/study/recall and old study/history/receipt reads, frozen/current knowledge links and answer searches, paused writes without preconditions, invalid/terminal navigation, and typed expiry versus progress/paused conflicts. Exercise web response loss, unchanged/changed saved slots, explicit retry/discard, missing/completed/paused sessions, failed recovery reads, account switches and expired timers during review. No runtime/HTTP/database/concurrency, suites or builds verified.

## Backend strengthening verification

- Reload/deploy matching source, then verify two-stage pack capture/preparation/finalization under concurrent content/category/tag/case/knowledge/image-name changes, closed-exam start, account/capability changes and selected-download quota races. Confirm failed preparation/revalidation consumes no grants, text-only/default byte ceilings persist, and image IO/encoding is outside transactions on the deployed database.
- Verify offline receipt replay/conflict after response loss, concurrent UUID/source-session collisions and unrelated integrity failures retaining normal 500 diagnostics/rollback. Verify old receipt/revision hashes and caller payload compatibility, unchanged learning chronology and fresh answer withholding. Capture `django.server.offline` success/failure records and `X-Offline-Operation-ID` with permission, validation, changed-content, receipt and server failures; no token/body/user/image/answer data in these records. Server dispatch timing does not measure client delivery. No suite/database/HTTP runtime verification has been performed for these changes.

Updated 2026-10-10. [Current source status](workDone.md) · [Project map](../../Android/README.md).

The seven rescan and eight deeper-review findings are source-complete. Do not reopen historical unchecked items without tracing current production source. Add new defects with reproduction, affected clients/contracts and priority.

## Selected offline functionality verification

- Deploy/reload the additive offline catalogue/pack backend, then rebuild/install only when authorized. Verify permission grant/revocation and direct handler/server checks, combined filters and frozen resume/reset, old whole-bank requests, text-only omission/legacy rejection/byte limits, changed/unchanged/unavailable material and preservation of old packs. Exercise completed offline review, multiple independent pack uploads/local answers/navigation, lost responses and durable receipts, serialized storage/capacity failures and account/server cleanup. Verify ordinary Sync during new answers/revisions/navigation, conflict/latest queue merges, duplicate Sync, local study finish/restart/exit/finalize/lost finish response, and unchanged timed-exam deadlines/recall. Include RTL/large text/TalkBack; source checks do not establish compilation/concurrency/device or HTTP behavior.

## 2026-10-13 remaining presentation verification

- Deploy/reload matching PDF palette source and verify themed body/card/alternate surfaces, accents/text, tables/charts and actual exported/printed output against Android/web. Keys/aliases are retained; source AST/colour comparisons do not establish rendering.

## Pending verification

- Verify the updated study prefetch on matching Android/backend: owned study bundles include frozen keys and original/translated explanations; exam bundles withhold both; single-page study/recall reads reveal keys only alongside allowed saved feedback. Check deleted/edited snapshot questions, legacy fallback, unseen exposure, other-account rejection and explicit queued-answer sync. No schema changes; AST/source checks do not establish live HTTP/device correctness.

- Verify category merge and direct tag merge controls after matching backend/client rollout: all source links, planner targets/progress, overlapping blueprint weights, editor revisions, receipt/review recovery, concurrent changes, Arabic/English/RTL and large text. Source checks passed; HTTP, browser/device, concurrency and compilation remain unverified.


- Verify backend-first full available counts and book-specific category/tag refinements on matching clients: >200 matching questions with the unchanged session cap, combined filters, changed/cleared books, read failure/Retry, rapid switches and saved setup. Source checks passed; compilation, template/browser/device and live API verification remain pending.

- Deploy/verify ordinary owned-session `GET /exam/questions/`: frozen pages, reveal/feedback withholding, no unseen exposure, legacy/deleted questions and other-account rejection. Verify matching Android downloaded-answer sync with existing expected-index/slot writes, concurrent changes, lost responses, partial confirmation and unchanged server exam deadlines. No schema changes; source AST/resource checks do not establish live HTTP or locking correctness.

- Verify the source-complete request-read ENETUNREACH and WSGI response-send ETIMEDOUT handlers after normal reload/restart: single transport entries, immediate failed-response connection cleanup, no unread-body drain/double iterable close, preserved HTTP/HEAD/static/414/application diagnostics and socket/database cleanup. Existing read ECONNREFUSED/ETIMEDOUT guard is evidenced active; keepalive values and new runtime behavior remain unverified. The user confirms frequent Android errors, HTTP configuration and different connection types. Correlate exact client errors/failed endpoints with actual Wi-Fi/mobile/VPN routes; identify TLS-to-HTTP senders separately. Curated samples lack frequency/duration/correlation; root cause remains unresolved. Verify reduced Android sync reads and lost-response/conflict/deadline recovery after matching rebuild.

- Verify `/questions/source-books/` on the running PostgreSQL backend after reload: existing null source titles should be omitted without HTTP 500, with exact valid titles/counts still available in Vue/Android. Two regressions and the 18-test question API run pass on SQLite; no application data repair is required.

- Verify member creation/duplication defaults and individual admin exceptions on the deployed backend and refreshed Vue/Android profiles. Existing stored member role grants remain authoritative; disable these in the permissions panel if still enabled. Focused 49-test SQLite verification passed; live PostgreSQL/browser/device behavior remains unverified.

- Verify [temporary import-limit bypass](contracts/importLimits.md) on the deployed session/cache stack and both clients: correct/wrong passwords, separate sessions, expiry at ten minutes, retained hourly quota and explicit resumption after HTTP 429. Focused SQLite/frontend checks do not establish live HTTP/device behavior.

- Expand behavioral coverage beyond the passing [982-test suite and coverage report](verification/backendCoverage.md), prioritizing its measured uncovered lines/branches. PostgreSQL line/branch coverage is 71.75%/56.87%; passing suites do not verify every function or deployed behavior. The user's requested complete existing-suite run and coverage report are complete.
- Verify deployed PostgreSQL/cache/workflows against `mpsql` / `quiz_fresh`. The user reported successful bootstrap; the older `quiz` database remains separate recovery work. Follow the [PostgreSQL guide](guides/POSTGRESQL_SETUP.md).

- Prepare/verify matching [schema and coordinated clients](contracts/schemaReadiness.md); no readiness is inferred from source or database deletion.
- Execute the [shared functional matrix](../../Android/README.md#verification), especially lost responses, account/attempt switches, receipts, permissions, revisions, imports/parent locking and planner late/midnight evidence.
- Extend the passing [35-scenario PostgreSQL concurrency matrix](verification/concurrencyLimits.md) to deployed HTTP/multiple processes/production cache, sustained load and large mixed imports before claiming user capacity. Verify startup/session integration, exports/PDFs and deliberately isolated backup/restore/clear. PostgreSQL administration remains unsupported.

Builds, suites, migrations/setup, destructive operator actions and versions follow [explicit-request policies](../Agents.md). The user's Python-test authorization covered these isolated suites and test database initialization; their results do not establish complete deployed readiness.

## 2026-10-10 parity-review follow-up

All seven native gaps, smaller workflow differences and shared web defects from the latest parity review are source-complete. Verify the dedicated account set-state route, partial/unknown batch outcomes, clock-read ownership and the shared manual matrix after matching rollout. Old servers reject the new route without changing account state. Earlier completed fixes remain complete.

Optional clinical-case translations are source-complete; verify matching `ClinicalCase.translations` schema and Android rollout, snapshots, editor recovery and legacy import/export behavior. See the [contract](contracts/caseTranslations.md). No schema setup has been performed for this extension.
