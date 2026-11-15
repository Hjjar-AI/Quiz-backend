# PreTest Psychiatry 14 — extraction completion

The authorized offline extraction, direct Arabic translation and chapter delivery are **complete as of 2026-11-04**. After the requested application-limit increase, all source option banks and full shared explanations reach the exports. The offline verifier passes the current files.

## Delivery and source

- [Delivery instructions and review links](../../import_data/pretest_psychiatry14_ar/README.md): 500 questions in 13 chapter JSONs and 13 matching UTF-8 BOM CSVs. Upload one format only; source/review/manifest files are not imports.
- Psychiatry: PreTest Self-Assessment and Review, 14th edition (2016), supplied at `/home/mhmmd/Downloads/Pretest psychiatry 14.pdf` and retained in the book's `source/` folder. PDF SHA-256: `03f393ef6f26aba1efdcac650d3218b2a727b839cec4b9b602b71ed7e72ba30b`.
- Reflowed ebook: 314 physical PDF pages, without reliable printed folios. `source_page` and provenance use one-based physical PDF pages; question/answer start and continuation pages remain available.
- User authorized Arabic/English output and parallel agents for direct chapter translation. The later 2–15-choice and 4,000-character limits supersede the previously authorized eight-choice reductions. No translation engine, external service or independent current medical/legal research was used.

## Content and review coverage

Embedded-text recovery covers all 500 source IDs, 369 unique answer blocks, 51 groups including 31 matching banks, 1,755 ordinary choices and 227 distinct bank choices. Seven content images were directly inspected and transcribed: Q17 choices, Q29 diagnostic data, Q71 development skills, Q408 screening signs, A29 diagnostic matrix and two A76 Erikson tables. Their retained evidence and saved transcriptions reach the extraction path. Whole-book visual certification is not claimed.

Direct Arabic authoring/review covers all original questions, choices, bank instructions and nonempty answer blocks: 2,882 nonempty source fields. Root authored chapters 1–2; a separate agent reviewed all 92 units there and corrected eight translation issues. The other chapter agents authored and reviewed their assigned complete units. All 124 digit-comparison flags received contextual per-field dispositions, with no additional quantity edits required. Counts of source fields and reviewed questions remain separate from image checks and independent clinical evidence.

The import contains 25 shared cases linking 53 questions. Fifty-eight previously reduced matching items now retain all original choices, up to 14 per delivered question. Q106's c-or-g guide still uses one combined c+g choice because grading accepts one index. Original question counts and import rows both remain 500.

The complete shared English explanation for Q289–295 (3,624 characters) and its saved full Arabic now reach all seven import rows. No excerpt substitution or omitted source options remain. Question/explanation/case limits are 4,000 characters, choices 500 characters, banks 2–15; the per-file import ceiling remains 5,000. See the [application contract](../contracts/questionContentLimits.md).

The exporter-consumed source ledger contains 19 issue/context records, including 11 bilingual learner-note records applying to 13 questions. Targeted source checking distinguishes confirmed printed wording/number/unit discrepancies from retained clinical claims. Full-context checking retired the broad Q251 omission flag. Source keys/claims remain preserved; notes do not independently validate ambiguous grading answers. Detailed evidence is linked from the book README.

## Final verification on 2026-11-04

Commands run from backend:

```bash
python3 scripts/content/export_pretest_psychiatry14.py
python3 scripts/content/verify_pretest_psychiatry14_artifacts.py
```

The local content verifier passed all 500 current rows: complete chapter sequences/source coverage, source and combined-answer mappings, preserved English/options, saved Arabic and bilingual-note propagation, UUID/text uniqueness, case identities/order, production field limits, 2–15 choices, CSV BOM/quoting and CSV/JSON semantic equality. Q408's plus/minus signs and Q79's original duplicate label are checked explicitly. [Machine-readable artifact report](../../import_data/pretest_psychiatry14_ar/review/verification.json).

The latest baseline comparison confirms **58 banks restored**, with corresponding correct positions, English choices and removal of the reduced-bank tag; **Q289–295 also regain full bilingual explanations**. These seven are within the same 58 changed rows. All other row fields, question text, UUIDs, case relationships and source-answer semantics remain identical. All 1,718 protected source/translation/existing DSM/Kaplan files and ten unrelated Android files retain their SHA-256 hashes. The previously completed Arabic title-prefix edit remains preserved.

A second export confirmed all **26 delivery files plus five manifest/derived-support files regenerate byte-identically**, with final delivery hashes still matching the passing verifier report. [Preservation and determinism report](../../import_data/pretest_psychiatry14_ar/review/finalization.json).

Matching backend models/config/validation/import/export, Vue editors/import previews/manuals and Android editors/default config now use the requested limits. Python AST, Vue SFC/JavaScript syntax, Kotlin lexical and bilingual XML/resource checks pass. Existing UUIDs are skipped rather than updated. These are local source/artifact checks, not deployed import, compilation or runtime evidence.

## Remaining limits

- Live application import and Arabic/English/RTL/Markdown-table display were not performed.
- Independent current clinical/legal evidence review and editorial changes to source-conflicted grading items remain separate scopes.
- Application limits were updated under the later explicit request. No database writes, application suite work, builds/compilation, packaging, migration inspection/changes or version changes were performed. Existing DSM/Kaplan files were preserved; no commit was made.
- `import_data/` and `scripts/content/` are ignored by Git and remain local artifacts. Canonical extract/export/verify scripts and all saved inputs are retained; temporary authoring helpers are unnecessary for regeneration.
