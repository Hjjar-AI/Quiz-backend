---
name: book-data-extraction
description: Extract books, PDFs, scans, tables, and question banks into traceable structured records and application-compatible CSV/JSON. Use for source recovery, book-to-data conversion, or repair of existing extraction pipelines.
---

# Book data extraction

Produce source-faithful records and useful delivery files. Keep extraction, editorial decisions, translation, and application export distinguishable. Adapt the structure to the actual book and consumer rather than imposing a previous project's schema.

## Establish the source and destination

- Read applicable project instructions and current work records; inspect existing utilities and outputs before replacing anything.
- Locate supplied source files, including nested source folders. Inspect edition, page count, embedded text, layout, and a few representative pages. Do not ask the user to transcribe material that is available locally.
- Determine scope: source-faithful extraction, translation, explicitly edited study edition, or a combination. Translation alone does not authorize changing source answer keys or inventing case facts.
- For app imports, inspect the current importer, validators, models, and relevant language/case consumers. Establish required fields, types, limits, encodings, answer-index convention, relationships, and duplicate/update behavior. If the consumer is unavailable, label the output a proposed schema and state what is unverified.

## Recover records before translating

- Prefer embedded PDF text when reliable. For scans, use available local OCR; render difficult pages and inspect the image. Local OCR is source recognition, not a translation engine. Do not upload sources or use external services without authorization.
- Respect columns, gutters, continuation pages, captions, tables, and question/answer sections. Recover reading order before joining paragraphs. Verify table columns and row boundaries explicitly.
- Check small high-impact marks against images: negation, inequality direction, decimal points, fractions, minus signs, units, subscripts, Greek letters, gene names, and answer letters. A normalized text match that removes these marks cannot establish their accuracy.
- Preserve an identifiable original source and its hash, physical PDF page, printed page, and relevant column/section. Keep raw recognition evidence where it materially supports repairs; do not create redundant historical delivery copies.
- Reconcile source IDs, chapter sequences, question counts, duplicate appearances, and guide labels. A preface count can disagree with the complete numbered sequence; report the discrepancy instead of dropping records to match it.
- Store an evidence-backed extraction patch when correcting recognition errors. Ensure the actual extraction path applies it, so regeneration cannot erase verified corrections.

## Structure and export

Read [assessment-data.md](references/assessment-data.md) for question banks, shared cases, matching/multi-select conversions, or answer-guide conflicts. Skip that reference for unrelated material.

- Use stable source IDs to connect raw records, translations, editorial notes, exports, and coverage records. Keep source values distinct from approved edited values.
- Preserve established question, case, category, and knowledge IDs. Correcting text must not silently create new identities when an existing exporter hashes case text; retain explicit identity overrides or another supported stable mapping.
- Keep source/target language fields separate and preserve case translations and meaningful source metadata. Do not stuff provenance or review status into schema fields that the app does not support.
- Make export deterministic and offline from saved reviewed content. A missing translation should be recorded, not silently filled by a newly introduced translation service.
- Generate the formats the user needs. Keep supporting review files out of the import file set; document exactly which folders/files to upload.

## Verify and finish

Use existing lightweight artifact checks where available. Validate observable invariants rather than assuming a script's successful exit proves correctness:

1. Coverage and mappings: source sequences, ordinary and converted answer mappings, converted-record traceability, and no unintended omissions or duplicates.
2. Structure: parse all delivery files; check field types, limits in every language, legal choice counts, metadata, case links, and semantic CSV/JSON equality.
3. Preservation: compare with a pre-edit snapshot for IDs, keys, unchanged English, relationships, and unrelated rows. Explicitly scope any authorized differences.
4. Regeneration: ensure the exporter consumes the intended saved wording and all extraction/identity patches actually reach output.

Keep source evidence, translated-field review, data validation, and live application verification separate. Counts of overrides or OCR-read pages are not counts of reviewed questions or visually inspected pages. Follow project restrictions on suites, builds, migrations, and database writes; artifact validation does not authorize a live import. Existing UUIDs may be skipped rather than updated.

Finish the authorized collection, update concise coverage/issue records, and report exact remaining limitations. Request user input only for evidence or editorial decisions that cannot be resolved from available sources and authorization.
