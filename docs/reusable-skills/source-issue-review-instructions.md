# Source issue review instructions

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

Use [Evidence and issue records](#evidence-and-issue-records) for persistent review states, evidence, and coverage. Keep PDF verification, editorial disposition, and delivery validation independent.

## Verify closure

Save corrections at the layer actually used by extraction/export. Preserve stable IDs, including existing case identities when corrected text would change a content hash. Regenerate affected outputs and check mappings, relationships, bilingual alignment, and unchanged records with permitted lightweight checks.

Finish all source checks available locally. Ask for a missing page or transcription only if that source cannot actually be accessed; identify the exact missing evidence. Once the printed source is confirmed, ask only for a genuinely necessary editorial decision, not another reading of the same PDF. Keep resolved recognition errors out of the remaining manual list.

## Evidence and issue records

Use separate states for source verification and content disposition. Avoid a single ambiguous status called reviewed.

| Concern | Useful states |
| --- | --- |
| Source access/check | pending, unavailable, verified by embedded text, verified by local OCR, verified by image |
| Finding | extraction defect, translation defect, mapping discrepancy, false alarm, printed contradiction, insufficient vignette support, historical claim |
| Editorial disposition | no content change, extraction patched, translation repaired, retained with qualification, edited within scope, excluded within scope, decision pending |
| Delivery | not regenerated, regenerated, artifact checks passed, live import/render verified |

A confirmed printed contradiction can have **source check complete** and **editorial decision pending** at the same time. A checked historical claim can remain unverified as current guidance. A source-correct letter can still name a medically questionable answer.

### Minimal evidence

Record source ID, edition/document hash, question and answer PDF pages, printed pages where available, disputed field, actual observation, verification method, result, and remaining limitation. Store the original extraction or enough evidence to reconstruct the change; a per-ID patch should not erase provenance.

Example of a small internal ledger entry:

```json
{
  "source_id": "chapter.item",
  "source_check": "complete",
  "method": "direct page-image inspection",
  "question_pdf_page": 12,
  "answer_pdf_page": 19,
  "finding": "extraction_defect",
  "observation": "The scan prints an inclusive comparator; OCR lost its horizontal bar.",
  "disposition": "extraction_patched",
  "editorial_decision_pending": false,
  "delivery_status": "artifact_checks_passed"
}
```

This is a sidecar example, not a runtime import schema. Adapt fields to existing records. Do not add review metadata to application records unless supported.

### What closes an issue

- A repair is closed only after the actual generated output contains it, and regeneration retains it.
- A false alarm is closed with its contextual reason; remove misleading visible warnings and stale manual-check requests.
- A printed defect has a completed source check but may still need an authorized grading/editorial decision.
- A guide letter/caption discrepancy needs evidence from both options and guide, not a rule that captions always win.
- A source scan cannot close an independent current-law or current-regulation check.

Report distinct question IDs, original exercise counts, converted-row counts, field review coverage, and remaining editorial decisions without mixing them. Never use the number of modified entries, successful parses, OCR pages, or absent error markers as a proxy for semantic review.
