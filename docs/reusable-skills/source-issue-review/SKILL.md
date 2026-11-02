---
name: source-issue-review
description: Recheck flagged book, PDF, extraction, or answer-key discrepancies against supplied source pages and resolve false alarms or recognition errors. Use when questions, explanations, table values, or printed keys appear contradictory or unsupported.
---

# Source issue review

Close the source-verification work before handing a manual checklist back to the user. Reassess each flag against current files; an inherited note is a hypothesis, not evidence.

## Locate and read the evidence

- Find the supplied source, retained raw text/OCR, current extracted record, translated output, and any previous repair. Check edition, document hash, and physical versus printed page mapping.
- Read both the original question and guide, not just the extracted explanation. Include all choices, table headers/footnotes, continuation pages, and the precise task being asked.
- Prefer source text when reliable; use available local OCR for scans and render high-impact or ambiguous details. An OCR recognizer can repeat the same error on multiple runs, so use the image for disputed symbols and names.
- State the method actually used. Distinguish embedded-text comparison, local OCR comparison, and direct page-image inspection. Normalization that removes punctuation or comparison symbols cannot prove their fidelity.

## Decide whether the flag survives context

- **OCR/extraction defect:** repair from the source, save a reproducible extraction patch, and remove target-language notes that falsely blame the printed book.
- **Translation defect:** correct meaning and grammar in the complete unit; preserve facts and the source key.
- **Guide mapping defect:** compare printed letter, answer caption, and actual options; document the evidence for any selected mapping.
- **False alarm/context clarified:** retire the flag and explain why. Wrong distractors are intentional; a question may restrict its domain to actual categories; a provisional/suggested diagnosis need not assert that every criterion is established. Scope the issue to the actual question, not a neighboring item about a different task.
- **Printed-source problem:** mark the source check complete, describe the actual contradiction or missing support, and distinguish that from an unresolved transcription task.
- **Historical/current-guidance issue:** preserve and label edition/jurisdiction/context; the supplied textbook alone cannot independently verify today's rules, statistics, or clinical recommendations.

A missing fact is not permission to invent it. Different defensible interpretations are not automatically a transcription error. Use appropriate qualifications without turning every abbreviated teaching vignette into a defective question.

## Apply only the authorized disposition

For faithful extraction/translation, preserve source content and identifiers with precise qualifications. Do not silently rewrite keys, delete records, or update current clinical guidance outside scope.

When an edited edition is explicitly authorized, correct prompt/choices/key/explanation together in every supported language, retaining original provenance. Exclude an irreparably ambiguous graded item only when that disposition is authorized. Do not call a clinically invalid graded key resolved just because a visible warning was added.

Use [issue-records.md](references/issue-records.md) for persistent review states, evidence, and coverage. Keep PDF verification, editorial disposition, and delivery validation independent.

## Review independent evidence when in scope

Keep independent clinical verification distinct from checking what the book prints. Use relevant primary research, official criteria, product labels or guidelines when external verification is requested or required; respect the session's access restrictions. Permission to consult a public source does not imply permission to upload the book, use a translation service, or claim access to a named service that was not used.

Put every substantive correction or qualification in the affected question's explanation in each delivered language, with a concise reference. A separate review ledger alone is insufficient. Explain whether the finding is a confirmed error, conditional answer, unsupported generalization or unresolved ambiguity. Do not turn an exception-dependent answer into a categorically wrong one. Read the evidence-record guidance for access limits and population/jurisdiction applicability.

## Verify closure

Save corrections at the layer actually used by extraction/export. Preserve stable IDs, including existing case identities when corrected text would change a content hash. Regenerate affected outputs and check mappings, relationships, bilingual alignment, and unchanged records with permitted lightweight checks.

Finish all source checks available locally. Ask for a missing page or transcription only if that source cannot actually be accessed; identify the exact missing evidence. Once the printed source is confirmed, ask only for a genuinely necessary editorial decision, not another reading of the same PDF. Keep resolved recognition errors out of the remaining manual list.
