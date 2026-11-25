# Assessment data: structures and difficult cases

## Discover the import contract

Inspect actual production code or a supplied schema. Record the source answer convention and destination convention independently: a source letter, zero-based index, one-based index, and multi-select set are different representations. Never assume the convention from a field name alone.

Typical concerns include question/case length, choices and translations, tags, category names, source references, required identifiers, upload limits, and empty versus omitted fields. Check CSV quoting, multiline cells, BOM expectations, and fields containing serialized JSON. CSV and JSON should decode into the same import records.

A review note belongs in a sidecar unless the app supports it. JSON objects containing a source manifest or review ledger are not automatically question-import files.

## Preserve the assessment unit

Read the vignette, final question, all choices, key, and explanation together. Preserve who did what, chronology, durations, units, uncertainty, exclusions, and whether the question asks for a diagnosis, a provisional possibility, a mechanism, or a next step.

Shared cases must retain order and links. Correcting one case must not duplicate it or detach its other questions. English case stems need their own language representation when the consumer separates the prompt from the case.

Recall notes, title-only prompts, placeholder distractors and a named answer without a complete option bank are not complete MCQs. Preserve them as source records, deferring required missing fields rather than inventing choices or a key. Record missing question numbers, partial continuations and inferred numbering explicitly. Separate supporting answer-guide/book-excerpt pages from the requested exam's assessment count.

## Answer guides

Compare the question's choices with both the guide letter and named answer caption. If they disagree, inspect the actual source pages before deciding. Record the printed letter, caption, selected mapping, and evidence separately. Use a named-caption mapping only when the evidence supports that interpretation; do not make it a universal rule.

An incorrect distractor is expected. A source problem is different: missing correct choice, multiple valid best answers, contradiction within a case, a key unsupported by the explanation, or a factual assertion requiring an editorial correction. Read the exact wording before declaring an ambiguity.

When several answer signals exist, record their provenance and the user's chosen priority: an approximate text key, a printed official key and a handwritten circle need not carry the same authority. A user reading a blurred option aloud clarifies its text; it does not select that option as the answer. Keep the raw key, selected answer and reason separately recoverable.

Before recovering a key from a repeated copy, compare the whole prompt/directive and option bank, including negation, numbers and units; map reordered options by their text rather than transferring a letter. Conflicting circles or a changed exception/distractor can leave the variant unresolved. A clear handwritten selection establishes the annotation, not an official key or clinical validity.

## Repeated source collections

Distinguish duplicate files, repeated page content and repeated assessment units. Hash equality proves identical bytes; decoded-pixel equality can identify image copies differing only in metadata. Similarity/OCR matches nominate candidates, not deletion decisions. Check complete page boundaries, continuations and handwritten annotations before choosing a clearer copy; a sharper page may omit unique notes or a cropped choice.

For a confirmed repeated assessment, reuse the canonical ID and preserve each source occurrence, variant wording, alternate key and source-to-canonical option mapping. Similar topics or materially different case facts/distractors are insufficient. Canonical wording shown for navigation must be labelled as a reference rendition, not a verbatim transcription of a blurred or partial photo.

Honor approved canonical wording/answers when adding source copies. Retain collection membership/tags in the source mappings; account for importers that skip existing IDs instead of merging tags or updating rows. If a source-faithful export intentionally keeps repeated numbers, make the recommended unique import selection explicit without discarding the required original records.

If source cleanup is authorized, record removed/retained paths, hashes, comparison method and retained unique information before removing a copy. Keep uncertain comparisons and unique annotations; identifying a duplicate does not itself authorize deletion.

## Metadata and deferred records

Save collection tags and other approved metadata in the authoring inputs so regeneration preserves them. Use the consumer's supported representations in every format, and check decoded CSV/JSON equality; do not turn a serialized array into a comma-split string when that changes tag identity.

A deferred item remains a source record even when excluded from import. If a later decision includes or excludes it, regenerate membership, answer mappings, readable status, review queues and delivery counts together. Keep its stable ID, original multiple-answer key and superseded decision history. Derive counts from the selected set rather than hard-coding a previous delivery total.

Reconcile source appearances, distinct assessments, import rows, duplicate references, deferred units and unseen source gaps separately. Do not count an inferred continuation as a fully recovered question, or missing numbers as transcribed records. Publish an exact import-file list that excludes empty/deferred-only exports and supporting sidecars; keep extracted and independently reviewed statuses distinct.

## Conversions when the destination cannot represent the source

First confirm the user's desired representation and the consumer's capabilities. Reuse native matching/multi-select support when available. If conversion is necessary and within scope:

- Preserve the complete original item and correct set in source/provenance.
- Keep a deterministic link from each derived item to its original ID.
- For a single-choice combination item, preserve the complete correct set; verify the answer position and every candidate set. Do not accidentally create two equivalent correct choices.
- For matching/glossary material, keep definitions and terms aligned, with distinct meaningful distractors. Review generated distractors; deterministic generation alone does not establish educational quality.
- Count original exercises and derived import rows separately. Reconcile every extra row to a documented conversion rather than presenting the larger total as extra source questions.

## An adaptable intermediate representation

An internal record can separate these concerns without copying this shape into an unsupported application schema:

```json
{
  "source_id": "chapter.item",
  "source_location": {
    "document_id": "edition-or-document-hash",
    "question_pdf_page": 12,
    "answer_pdf_page": 19,
    "printed_question_page": "5",
    "column": 1
  },
  "original": {
    "question": "...",
    "choices": {"A": "...", "B": "..."},
    "guide_letter": "B",
    "guide_caption": "...",
    "explanation": "..."
  },
  "extraction_patches": [],
  "reviewed_translations": {},
  "editorial_decision": null,
  "export_links": []
}
```

This is an intermediate example, not a promised API. Adapt it; do not populate missing values with guesses. Keep extracted source text recoverable when an edited edition changes content.
