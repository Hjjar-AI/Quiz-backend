# Assessment data: structures and difficult cases

## Discover the import contract

Inspect actual production code or a supplied schema. Record the source answer convention and destination convention independently: a source letter, zero-based index, one-based index, and multi-select set are different representations. Never assume the convention from a field name alone.

Typical concerns include question/case length, choices and translations, tags, category names, source references, required identifiers, upload limits, and empty versus omitted fields. Check CSV quoting, multiline cells, BOM expectations, and fields containing serialized JSON. CSV and JSON should decode into the same import records.

A review note belongs in a sidecar unless the app supports it. JSON objects containing a source manifest or review ledger are not automatically question-import files.

## Preserve the assessment unit

Read the vignette, final question, all choices, key, and explanation together. Preserve who did what, chronology, durations, units, uncertainty, exclusions, and whether the question asks for a diagnosis, a provisional possibility, a mechanism, or a next step.

Shared cases must retain order and links. Correcting one case must not duplicate it or detach its other questions. English case stems need their own language representation when the consumer separates the prompt from the case.

## Answer guides

Compare the question's choices with both the guide letter and named answer caption. If they disagree, inspect the actual source pages before deciding. Record the printed letter, caption, selected mapping, and evidence separately. Use a named-caption mapping only when the evidence supports that interpretation; do not make it a universal rule.

An incorrect distractor is expected. A source problem is different: missing correct choice, multiple valid best answers, contradiction within a case, a key unsupported by the explanation, or a factual assertion requiring an editorial correction. Read the exact wording before declaring an ambiguity.

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
