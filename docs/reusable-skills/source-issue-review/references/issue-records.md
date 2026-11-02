# Evidence and issue records

Use separate states for source verification and content disposition. Avoid a single ambiguous status called reviewed.

| Concern | Useful states |
| --- | --- |
| Source access/check | pending, unavailable, verified by embedded text, verified by local OCR, verified by image |
| Finding | extraction defect, translation defect, mapping discrepancy, false alarm, printed contradiction, insufficient vignette support, historical claim |
| Editorial disposition | no content change, extraction patched, translation repaired, retained with qualification, edited within scope, excluded within scope, decision pending |
| Delivery | not regenerated, regenerated, artifact checks passed, live import/render verified |

A confirmed printed contradiction can have **source check complete** and **editorial decision pending** at the same time. A checked historical claim can remain unverified as current guidance. A source-correct letter can still name a medically questionable answer.

## Minimal evidence

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

## What closes an issue

- A repair is closed only after the actual generated output contains it, and regeneration retains it.
- A false alarm is closed with its contextual reason; remove misleading visible warnings and stale manual-check requests.
- A printed defect has a completed source check but may still need an authorized grading/editorial decision.
- A guide letter/caption discrepancy needs evidence from both options and guide, not a rule that captions always win.
- A source scan cannot close an independent current-law or current-regulation check.

Report distinct question IDs, original exercise counts, converted-row counts, field review coverage, and remaining editorial decisions without mixing them. Never use the number of modified entries, successful parses, OCR pages, or absent error markers as a proxy for semantic review.
