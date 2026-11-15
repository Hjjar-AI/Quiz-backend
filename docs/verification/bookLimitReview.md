# DSM and Kaplan limit review — 2026-11-04

Reviewed both books against the current 4,000-character question/explanation/case limits, 500-character choices, 2–15 choices and 5,000 questions per import file. The local review is complete: **one outdated shortening was restored; no remaining field-limit violations were found in 1,147 import rows**.

## Findings and corrections

1. **DSM `4.4`, English choice E:** the old 300-character cap caused a 313-character source choice to be replaced with shorter wording. Including `E. `, the full choice is 316 characters and now fits. Restored the complete source text and removed the sole obsolete English-choice override. Embedded PDF text on physical question page 53 matches the complete saved choice; guide page 252 confirms answer **D**, which remains unchanged. Arabic wording and every other field remain unchanged.
2. **Both export pipelines:** their validation and CSV generation still used the old 3,000/300/eight-choice limits. Exporters and artifact verifiers now read the current literal model/settings constants through `scripts/content/book_content_limits.py`, without initializing Django. CSV headers cover `choice_1`–`choice_15`; chapter file counts are checked against 5,000. Checks include both languages, case translations, metadata and the separate knowledge-object limit.
3. **Current delivery READMEs:** replaced obsolete limits and linked the new contract/review. Historical dated reviews remain historical evidence.

## Coverage and measured maxima

| Book / language | Question | Explanation | Shared case | Choice |
| --- | ---: | ---: | ---: | ---: |
| DSM / Arabic | 671 | 1,407 | 1,060 | 224 |
| DSM / English | 786 | 2,086 | 1,240 | 316 |
| Kaplan / Arabic | 582 | 721 | 1,182 | 116 |
| Kaplan / English | 911 | 1,835 | 1,368 | 153 |
| Allowed | 4,000 | 4,000 | 4,000 | 500 |

Lengths include delivered source-number/choice labels. Shared cases are measured separately from question prompts. All delivered content fields, case translations, tags, source/category/case/knowledge metadata and file row counts pass their applicable limits.

- **DSM:** 476 original exercises produce 545 import rows in 24 chapter pairs; 470 ordinary MCQs plus 75 rows derived from six matching exercises. The largest chapter has 75 rows. All 26 glossary definitions remain represented; the glossary has 26 terms, which still exceeds 15, so its established five-choice per-definition conversions remain unchanged. The complete original bank is retained in source/review records.
- **Kaplan:** all 602 source questions appear in 34 chapter pairs; the largest chapter has 70 rows. No question content changed. The three multi-select exercises (`12.7`, `13.2`, `20.2`) preserve every original option in the converted question text and retain their complete correct combination. This is an existing grading representation, not lost content from a field limit. A scan of all 15,126 retained OCR lines found no option-like I–O lines beyond the extractor's source-specific A–H range; this does not claim a new visual PDF review.
- All ordinary English choices now match the complete saved source choices. Saved full English explanations, including prior bilingual evidence-review edits, reach delivery unchanged; all original raw explanation blocks are below even the former 3,000-character cap. No other limit-induced excerpt or omission was found. This does not reclassify deliberately concise Arabic wording as a new translation review.

## Verification and preservation

From the backend directory, ran both `export_dsm5.py` / `export_kaplan.py` and `verify_dsm5_artifacts.py` / `verify_kaplan_artifacts.py` under `scripts/content/`. These are offline artifact utilities, not application suites.

The verifiers pass all 1,147 rows: complete source coverage and answer mappings, fields in both languages, 15-column choice headers, BOM/CSV–JSON equality, glossary definitions, multi-select source banks, full saved English explanations, case relationships and duplicate checks. Five changed/new content scripts pass Python AST checks.

Baseline comparison proves exactly **one English choice in one DSM row changed**. All other DSM row fields and all 602 Kaplan rows remain identical, including Arabic, UUIDs, keys and case/knowledge links. All **1,627 protected file hashes** remain unchanged, including both books' sources/translation/evidence inputs and the entire PreTest tree. Repeated export reproduces **116 delivery files plus ten manifest/support files byte-identically**; final hashes match the passing verifier reports.

Detailed field measurements, source hashes, issue disposition, preservation and regeneration hashes: [DSM ledger](../../import_data/dsm5_ar/review/2026-11-04_limit_review.json) · [Kaplan ledger](../../import_data/kaplan_ar/review/2026-11-04_limit_review.json). [Shared application contract](../contracts/questionContentLimits.md).

## Remaining limits

No application code, database import/update, application test files/suites, builds/compilation, migration work or versions were changed in this review. Existing imported UUIDs are skipped rather than updated, so restoring the import file does not update an already-imported question. Live import/rendering and the existing source-conflicted grading decisions remain separate work. This was a limit-focused source/artifact review, not a new whole-book visual, translation or current clinical/legal certification.
