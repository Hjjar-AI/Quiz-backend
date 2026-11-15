# Question content limits

Updated 2026-11-04 for matching Django, Vue and Android source.

| Field | Limit |
| --- | --- |
| Question text | 4,000 characters |
| Explanation | 4,000 characters |
| Shared case stem | 4,000 characters |
| Each choice | 500 characters |
| Choices per question | 2–15 |
| Questions per import file | 5,000 (unchanged) |

The same content limits apply to English/Arabic translations. Translated choices retain the base count/order. Answers remain a single one-based index into the actual choices; widening the bank does not add multiple-answer grading.

Backend model constants in `apps/questions/models.py` govern serializers, translations, cases and imports. `MAX_CHOICES = 15` and `MAX_IMPORT_QUESTIONS = 5000` live in `config/settings.py`; public config, validation, flat import/export and master-exam answer bounds use that ceiling. CSV supports `choice_1` through `choice_15`; JSON supports the `choices` array. Actual choice counts still bound grading, including frozen sessions. Knowledge-object text retains its separate 3,000-character limit.

Vue shares editor maxima through `src/utils/constants.js`; CSV/numbered-JSON previews retain all 15 positions. Numeric answer shortcuts remain keys 1–9; all choices remain available through the question controls. Android shares editor/default-config limits through `QuestionContentLimits.kt`, including ordinary/translated questions, case editing and embedded master drafts. Android validation counts Unicode code points.

Deploy the matching backend before refreshed Vue/Android clients. Existing imported UUIDs are skipped rather than updated: regenerated book files do not repair already-imported rows automatically. No live import or database update was performed. Model metadata changed; migration inspection, schema setup and rollout verification were not authorized or performed.

## Evidence and remaining verification

Python AST, Vue SFC parsing/JavaScript syntax, Android Kotlin lexical/XML/resource checks and whitespace checks pass. These are source checks, not application execution or compilation.

The [PreTest delivery](../verification/pretestPsychiatry14Extraction.md) passes the offline artifact verifier at the new limits: 500 bilingual rows, 58 complete restored banks and seven full restored shared explanations. All 1,718 protected source/translation/other-book files and ten unrelated Android files retained their hashes; 31 generated files repeat byte-identically.

The subsequent [DSM/Kaplan limit review](../verification/bookLimitReview.md) passes all 1,147 rows. Restored DSM `4.4`'s full English choice E; all other row fields remain unchanged. Their exporters/verifiers now read current production limits and emit 15 choice columns. No remaining field overflow was found.

Focused boundary tests require milestone approval: 4,000/4,001 question/explanation/case characters, 500/501 choice characters, translated fields, 2/15/16 choices, fifteenth-answer acceptance, 15-column import/export and unchanged 5,000-row policy. Browser/device/RTL/focus and live HTTP/import/rendering remain unverified. No suites, Gradle/builds/compilation, packaging or versions were changed or run for this milestone.
