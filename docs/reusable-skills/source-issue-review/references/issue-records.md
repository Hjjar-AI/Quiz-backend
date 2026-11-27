# Evidence and issue records

Use separate states for source verification and content disposition. Avoid a single ambiguous status called reviewed.

| Concern | Useful states |
| --- | --- |
| Source access/check | pending, unavailable, verified by embedded text, verified by local OCR, verified by image |
| Finding | extraction defect, translation defect, mapping discrepancy, false alarm, printed contradiction, insufficient vignette support, historical claim |
| Editorial disposition | no content change, extraction patched, translation repaired, retained with qualification, edited within scope, excluded within scope, decision pending |
| Delivery | not regenerated, regenerated, artifact checks passed, live import/render verified |

A confirmed printed contradiction can have **source check complete** and **editorial decision pending** at the same time. A checked historical claim can remain unverified as current guidance. A source-correct letter can still name a medically questionable answer.

For repeated copies, distinguish recognition confidence, agreement between source versions, and answer authority. Record the canonical ID, each supplied key/annotation, option-order mapping and any changed directive or choice; clearer pixels alone do not supersede an approved answer. Missing/partial source material can be fully inventoried while its question remains deferred. Report processed collections, importable questions and unresolved source gaps separately so an empty extraction queue is not presented as complete grading or content review.

## Editorial choices and follow-up replies

Ask in the user's preferred language and manageable batches. Include the question, relevant choices, supplied key, specific problem and recommended disposition. Distinguish the original from the proposed replacement, especially when explaining why a newly proposed distractor is false. Offer meaningful alternatives such as an edited item, retention with a precise warning, or deferral when the source supports those choices.

Persist each decision by stable question ID. Reuse explicit choices instead of asking again without new evidence or a request to revisit them. A later reply can supersede an earlier deferral or retention; record that history and update the active queue. Treat photo requests, factual questions and option transcriptions as clarification, not approval of a rewrite or answer key. An “I don't know” response does not authorize a proposed edit: follow any established preservation policy and record the remaining clinical uncertainty.

For an approved rewrite, assess the prompt, every option and answer together. Preserve the intended distinction without creating another valid exception or changing an association into an exclusive claim. Keep the original and selected keys explicit in the learner's explanation; replace stale pending or deferred language after the decision changes.

Report editorial disposition separately from clinical validity. “All decisions recorded” may include an intentionally retained disputed key or deferred item; it does not certify every graded item. Distinguish those deliberate choices from questions still awaiting a decision, and offer follow-up on uncertain retained items when the user requests remaining issues.

A “wait” reply keeps the affected mutation on hold while independent work continues. A request to recheck is authorization to investigate, not acceptance of the proposed replacement. After rechecking, withdraw a disproven proposal; if the user chooses retention with a qualification, record that as a final disposition rather than leaving it pending. Keep optional new study conversions separate from the completed review of the existing bank.

Use the final selected wording to regenerate explanations and current status. Remove obsolete hold language, unsupported source-error claims and rejected alternatives from the active delivery; keep the decision history in provenance. Do not leave an earlier “not applied” proposal list or a pre-change validation report presented as the current result.

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

## Independent evidence records

For externally checked claims, record the exact claim, source URL/PMID, publication or guidance version, review date, finding, applicability and remaining editorial decision. State whether the evidence was read as full text, abstract or indexed passage; a blocked full text is not a completed full-text review. Distinguish primary findings from the reviewer's inference. A newer paper alone does not settle a question framed for another population, jurisdiction or purpose.

Separate confirmed errors from conditional recommendations, incomplete support and source-only contradictions. A treatment exception after failed alternatives may preserve a conditional answer; it does not establish universal safety. An outside paper cannot recover the author's intended age, chronology or medication history when the book contradicts itself. Do not invent those details or substitute a new key without support.

Keep each substantive correction/qualification visible in the delivered explanation, with the same meaning and applicable references in all delivered languages. Retain raw source wording separately; clearly label any superseded text retained for comparison. Update stale warnings, manifests and current review metadata to reflect the bounded evidence pass without rewriting historical provenance. Count external-evidence items separately from source-only checks; neither count certifies the entire book.

## Comparing requested references without manufacturing agreement

Attach evidence to the claim it actually addresses: diagnostic criteria, symptom terminology, pharmacologic classification, indication, adverse-effect possibility, comparative risk or historical theory are different tasks. Read the relevant context within a source and record genuine disagreements rather than treating any named book or website as infallible. An absence from approved indications is not proof that a drug never appears in a broader classification; a possible effect is not proof of a standard treatment indication.

PubMed indexes articles; it is not itself a primary clinical finding. Identify the article and whether it is a trial, case report, consensus, review or theoretical account. NCBI Bookshelf hosts multiple publishers: identify StatPearls by the actual chapter, and do not count its PubMed listing as independent corroboration. A page title or bibliography alone is a lead, not evidence for a detailed claim. An indexed passage can support its explicit content when direct access is blocked, but does not establish full-text review.

When the user requests several reference families, record per-item support, contradiction, context only, or no applicable support identified. A citation count is not a count of facts verified, and a topical paper cannot certify every distractor. Do not force unrelated citations onto a question to claim all sources agree. Historical models may be described accurately without being experimentally validated; case reports support possibility without establishing incidence or comparative safety.

For a cited study edition, end each explanation with the relevant textbook edition and explicitly labeled PDF or printed pages, or the website/chapter/article title and direct link (PMID when useful). Preserve the source-specific limits in the explanation when they affect grading. Keep internal file paths, approval bookkeeping and access logs in sidecars. Refresh coverage from the references actually mapped to each item, distinguishing direct support from contextual/descriptive pointers.

## What closes an issue

- A repair is closed only after the actual generated output contains it, and regeneration retains it.
- A false alarm is closed with its contextual reason; remove misleading visible warnings and stale manual-check requests.
- A printed defect has a completed source check but may still need an authorized grading/editorial decision.
- A guide letter/caption discrepancy needs evidence from both options and guide, not a rule that captions always win.
- A source scan cannot close an independent current-law or current-regulation check.

Report distinct question IDs, original exercise counts, converted-row counts, field review coverage, and remaining editorial decisions without mixing them. Never use the number of modified entries, successful parses, OCR pages, or absent error markers as a proxy for semantic review.
