# Data extraction instructions

Produce source-faithful records and useful delivery files. Keep extraction, editorial decisions, translation, and application export distinguishable. Adapt the structure to the actual book and consumer rather than imposing a previous project's schema.

## Establish the source and destination

- Read applicable project instructions and current work records; inspect existing utilities and outputs before replacing anything.
- Locate supplied source files, including nested source folders. Inspect edition, page count, embedded text, layout, and a few representative pages. Do not ask the user to transcribe material that is available locally.
- Verify current source availability and retained-copy hashes. A historical manifest path is provenance, not proof that the original still exists; report unavailable originals separately from verified staged copies.
- Determine scope: source-faithful extraction, translation, explicitly edited study edition, or a combination. Translation alone does not authorize changing source answer keys or inventing case facts.
- For app imports, inspect the current importer, validators, models, and relevant language/case consumers. Establish required fields, types, limits, encodings, answer-index convention, relationships, and duplicate/update behavior. If the consumer is unavailable, label the output a proposed schema and state what is unverified.

Reuse a verified retained extraction before running OCR or extracting the book again. When navigation needs improvement, section the existing text with physical-page anchors and a small machine-readable index; retain readable text rather than assuming the entire book should become JSON. Verify page coverage, reconstruction and index offsets for the units actually used (bytes or Unicode characters). This checks navigation integrity, not medical content or image-only material.

## Recover records before translating

- Prefer embedded PDF text when reliable. For scans, use available local OCR; render difficult pages and inspect the image. Local OCR is source recognition, not a translation engine. Do not upload sources or use external services without authorization.
- Respect columns, gutters, continuation pages, captions, tables, and question/answer sections. Recover reading order before joining paragraphs. Verify table columns and row boundaries explicitly.
- Check small high-impact marks against images: negation, inequality direction, decimal points, fractions, minus signs, units, subscripts, Greek letters, gene names, and answer letters. A normalized text match that removes these marks cannot establish their accuracy.
- Preserve an identifiable original source and its hash, physical PDF page, printed page, and relevant column/section. Keep raw recognition evidence where it materially supports repairs; do not create redundant historical delivery copies.
- Reconcile source IDs, chapter sequences, question counts, duplicate appearances, and guide labels. A preface count can disagree with the complete numbered sequence; report the discrepancy instead of dropping records to match it.
- Store an evidence-backed extraction patch when correcting recognition errors. Ensure the actual extraction path applies it, so regeneration cannot erase verified corrections.
- Repair Arabic ligature/reading-order defects in context. Broad character substitutions can corrupt valid words or negation; retain raw recognition and the specific repaired fields.

## Structure and export

Read [Assessment data](#assessment-data-structures-and-difficult-cases) for question banks, shared cases, incomplete recall notes, repeated source collections, matching/multi-select conversions, or answer-guide conflicts. Skip that reference for unrelated material.

- Use stable source IDs to connect raw records, translations, editorial notes, exports, and coverage records. Keep source values distinct from approved edited values.
- Preserve established question, case, category, and knowledge IDs. Correcting text must not silently create new identities when an existing exporter hashes case text; retain explicit identity overrides or another supported stable mapping.
- Keep source/target language fields separate and preserve case translations and meaningful source metadata. Do not stuff provenance or review status into schema fields that the app does not support.
- Make export deterministic and offline from saved reviewed content. A missing translation should be recorded, not silently filled by a newly introduced translation service.
- Generate the formats the user needs. Keep supporting review files out of the import file set; document exactly which folders/files to upload.
- Honor the requested delivery location for source copies, crops, authoring records and exports. When relocation is requested, verify the destination copies before removing task-owned originals; preserve unrelated files.
- Preserve the user's project isolation. Identify mixed exam collections from printed headings/content rather than filenames alone; split distinct exams or consolidate confirmed repeats into their existing projects, retaining path aliases and provenance.

## Verify and finish

Use existing lightweight artifact checks where available. Validate observable invariants rather than assuming a script's successful exit proves correctness:

1. Coverage and mappings: source sequences, ordinary and converted answer mappings, converted-record traceability, and no unintended omissions or duplicates.
2. Structure: parse all delivery files; check field types, limits in every language, legal choice counts, metadata, case links, and semantic CSV/JSON equality.
3. Preservation: compare with a pre-edit snapshot for IDs, keys, unchanged English, relationships, and unrelated rows. Explicitly scope any authorized differences.
4. Regeneration: ensure the exporter consumes the intended saved wording and all extraction/identity patches actually reach output.

Keep source evidence, translated-field review, data validation, and live application verification separate. Counts of overrides or OCR-read pages are not counts of reviewed questions or visually inspected pages. Follow project restrictions on suites, builds, migrations, and database writes; artifact validation does not authorize a live import. Existing UUIDs may be skipped rather than updated.

Finish the authorized collection, update concise coverage/issue records, and report exact remaining limitations. Request user input only for evidence or editorial decisions that cannot be resolved from available sources and authorization.

Report source processing, import-ready rows, deferred records and review completion separately. An empty staging queue means all staged sources were processed; it does not establish that every question is complete, importable or reviewed.

## Assessment data: structures and difficult cases

### Discover the import contract

Inspect actual production code or a supplied schema. Record the source answer convention and destination convention independently: a source letter, zero-based index, one-based index, and multi-select set are different representations. Never assume the convention from a field name alone.

Typical concerns include question/case length, choices and translations, tags, category names, source references, required identifiers, upload limits, and empty versus omitted fields. Check CSV quoting, multiline cells, BOM expectations, and fields containing serialized JSON. CSV and JSON should decode into the same import records.

A review note belongs in a sidecar unless the app supports it. JSON objects containing a source manifest or review ledger are not automatically question-import files.

### Preserve the assessment unit

Read the vignette, final question, all choices, key, and explanation together. Preserve who did what, chronology, durations, units, uncertainty, exclusions, and whether the question asks for a diagnosis, a provisional possibility, a mechanism, or a next step.

Shared cases must retain order and links. Correcting one case must not duplicate it or detach its other questions. English case stems need their own language representation when the consumer separates the prompt from the case.

Recall notes, title-only prompts, placeholder distractors and a named answer without a complete option bank are not complete MCQs. Preserve them as source records, deferring required missing fields rather than inventing choices or a key. Record missing question numbers, partial continuations and inferred numbering explicitly. Separate supporting answer-guide/book-excerpt pages from the requested exam's assessment count.

### Recovering incomplete recalls from other collections

Inspect the actual record shapes before searching. Banks may store a flat question/choice list, nested original/selected items, or choices keyed by letters. Handle those shapes explicitly; report unread or missing fields rather than silently treating them as empty and claiming coverage. Distinguish the original printed bank from an approved edited rendition of another collection.

Use keywords, Arabic normalization and similarity to retrieve candidates, then compare complete directives, cases, choices and key authority. A shared topic or high similarity score cannot identify an unspecified question. An affirmative “all of the above” bank cannot fill an EXCEPT recall. Count searched source appearances separately from unique questions, repeated imports and genuinely read candidates; describe the bounded search rather than claiming no fuller source exists anywhere.

A matching incomplete note may corroborate wording without recovering any missing options. Read annotations such as “we guessed” or “nobody knew”: agreement with a student guess does not create an authoritative key. Save this evidence and keep unsupported claims deferred rather than carrying confidence from a cleaner copy.

If an edited study edition is authorized, a surviving supported statement may become a useful true/false item. Distinguish three outcomes: recovered original, reduced bank of actual source choices, and new edited study exercise. The latter does not recover the original stem, absent exception or key. Where a decision is needed, present the exact proposed wording, choices, answer, explanation and references before applying it; reuse existing authorization rather than adding a new approval gate. Preserve the incomplete original and mark the derived exercise explicitly. Dropping placeholders is not permission to invent their replacements or guess which missing option was correct.

### Answer guides

Compare the question's choices with both the guide letter and named answer caption. If they disagree, inspect the actual source pages before deciding. Record the printed letter, caption, selected mapping, and evidence separately. Use a named-caption mapping only when the evidence supports that interpretation; do not make it a universal rule.

An incorrect distractor is expected. A source problem is different: missing correct choice, multiple valid best answers, contradiction within a case, a key unsupported by the explanation, or a factual assertion requiring an editorial correction. Read the exact wording before declaring an ambiguity.

When several answer signals exist, record their provenance and the user's chosen priority: an approximate text key, a printed official key and a handwritten circle need not carry the same authority. A user reading a blurred option aloud clarifies its text; it does not select that option as the answer. Keep the raw key, selected answer and reason separately recoverable.

Before recovering a key from a repeated copy, compare the whole prompt/directive and option bank, including negation, numbers and units; map reordered options by their text rather than transferring a letter. Conflicting circles or a changed exception/distractor can leave the variant unresolved. A clear handwritten selection establishes the annotation, not an official key or clinical validity.

### Repeated source collections

Distinguish duplicate files, repeated page content and repeated assessment units. Hash equality proves identical bytes; decoded-pixel equality can identify image copies differing only in metadata. Similarity/OCR matches nominate candidates, not deletion decisions. Check complete page boundaries, continuations and handwritten annotations before choosing a clearer copy; a sharper page may omit unique notes or a cropped choice.

For a confirmed repeated assessment, reuse the canonical ID and preserve each source occurrence, variant wording, alternate key and source-to-canonical option mapping. Similar topics or materially different case facts/distractors are insufficient. Canonical wording shown for navigation must be labelled as a reference rendition, not a verbatim transcription of a blurred or partial photo.

Honor approved canonical wording/answers when adding source copies. Retain collection membership/tags in the source mappings; account for importers that skip existing IDs instead of merging tags or updating rows. If a source-faithful export intentionally keeps repeated numbers, make the recommended unique import selection explicit without discarding the required original records.

If source cleanup is authorized, record removed/retained paths, hashes, comparison method and retained unique information before removing a copy. Keep uncertain comparisons and unique annotations; identifying a duplicate does not itself authorize deletion.

### Metadata and deferred records

Save collection tags and other approved metadata in the authoring inputs so regeneration preserves them. Use the consumer's supported representations in every format, and check decoded CSV/JSON equality; do not turn a serialized array into a comma-split string when that changes tag identity.

A deferred item remains a source record even when excluded from import. If a later decision includes or excludes it, regenerate membership, answer mappings, readable status, review queues and delivery counts together. Keep its stable ID, original multiple-answer key and superseded decision history. Derive counts from the selected set rather than hard-coding a previous delivery total.

Reconcile source appearances, distinct assessments, import rows, duplicate references, deferred units and unseen source gaps separately. Do not count an inferred continuation as a fully recovered question, or missing numbers as transcribed records. Publish an exact import-file list that excludes empty/deferred-only exports and supporting sidecars; keep extracted and independently reviewed statuses distinct.

### Conversions when the destination cannot represent the source

First confirm the user's desired representation and the consumer's capabilities. Reuse native matching/multi-select support when available. If conversion is necessary and within scope:

- Preserve the complete original item and correct set in source/provenance.
- Keep a deterministic link from each derived item to its original ID.
- For a single-choice combination item, preserve the complete correct set; verify the answer position and every candidate set. Do not accidentally create two equivalent correct choices.
- For matching/glossary material, keep definitions and terms aligned, with distinct meaningful distractors. Review generated distractors; deterministic generation alone does not establish educational quality.
- Count original exercises and derived import rows separately. Reconcile every extra row to a documented conversion rather than presenting the larger total as extra source questions.

### Applying decisions and refreshing delivery

Keep the earliest source record and raw key immutable. Do not rerun a temporary assembly script that copies the current edited item into its “original” fields or resets prior decisions. Apply the approved field changes, retain unrelated reviewed wording, and recheck source-backed recognition patches when a whole-item proposal could restore an older typo.

When a selected key changes, show the current answer clearly. A retained original letter must be labeled as historical source evidence and must not masquerade as the answer to a new option bank. An absent original key stays absent; the key of an approved new exercise is a separate value.

Update authoring, actual exports, explanations, deferred/duplicate queues, decision records and current manifests together. Recompute counts from current membership; keep initial extraction counts as dated history. For added exercises, verify that existing import rows remain unchanged unless an additional edit was authorized. Refresh validation after the last content change and verify deterministic regeneration from the saved inputs.

A reviewed collection may still contain inventoried, incomplete records. Report review completion, retained qualifications, pending decisions and importable coverage separately. Move a collection only within the authorized organization workflow; verify preservation, retain old-path aliases, and update current pointers without rewriting the meaning of past relocation/hash checks.

### An adaptable intermediate representation

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
