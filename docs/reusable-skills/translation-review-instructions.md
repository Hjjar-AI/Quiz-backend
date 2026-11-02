# Translation review instructions

Use these instructions for a new book or project by supplying its source files, source/target languages, desired scope, and output location. The default method is direct contextual translation and review using subject knowledge, with no translation engine or external service. Authorized external evidence research is distinct from translation-service use; follow the session's authorization and access restrictions. Respect the user's explicit preferences and the project's applicable instructions.

## 1. Establish what is being produced

Identify whether the task is faithful translation, repair of existing wording, or an explicitly edited edition. Inspect the supplied original, retained extraction, current translations, and actual output contract before changing them. The default is source-faithful language correction; changing a graded answer, adding clinical facts, deleting a question, or modernizing a historical claim requires that scope to be authorized.

Use available source documents yourself. Search the source folder and inspect the relevant question and answer-guide pages before asking the user to retype content. Keep physical PDF and printed page numbering distinct.

## 2. Read the complete unit, then translate its meaning

For assessments, the unit is the case, prompt, every choice, answer key, and explanation. For prose, use the paragraph and surrounding argument; for tables, use headers, row labels, units, and footnotes. Do not translate a term without establishing its role in that unit.

Preserve:

- People, relationships, gender, speaker, and agent of each action.
- Negation, exceptions, quantifiers, comparison direction, and uncertainty.
- Onset, duration, recurrence, temporal relationships, and drug start/stop history.
- Numbers, denominators, decimal marks, units, dose versus concentration, routes, formulations, and frequency.
- Observed facts versus patient reports, interpretations, provisional possibilities, and confirmed findings.
- Distinctions such as symptom versus disorder, association versus causation, and supportive finding versus sufficient criterion.

Keep intentionally false distractors false while translating them accurately. Do not repair their medical content merely because they are incorrect choices. Do not turn a provisional or best-fitting possibility into an established diagnosis, or flag every concise vignette because it does not reproduce a full assessment.

## 3. Use subject knowledge to repair meaning, not invent evidence

Resolve literal mistranslations, malformed syntax, abbreviations, omitted clauses, and semantic reversals. Think through the complete case before changing the wording.

When the source itself seems wrong, distinguish:

1. Recognition/extraction error: correct against the printed source and preserve the evidence.
2. Translation error: correct the target wording without changing source facts.
3. Printed-source conflict: explain the discrepancy and retain a precise issue record; do not silently invent a replacement key, timeline, measurement, or treatment.
4. Historical context: identify the source edition and avoid presenting its regulations, prevalence figures, legal rules, or treatment assumptions as independently verified current guidance.

If an edited edition is authorized, revise the prompt, choices, key, and explanation coherently in all supported languages. Preserve the original source separately in provenance. A warning does not make an invalid graded answer valid; unresolved graded items require an explicit editorial disposition, not a claim that translation has solved them.

### Independent evidence and visible corrections

When fact-checking is in scope, use primary research, official diagnostic criteria, product labels and applicable guidelines. Record URLs/PMIDs, evidence date/version, access level (full text, abstract or indexed passage), and population or jurisdiction limits. Do not claim that a service or full article was consulted when it was unavailable. Research access does not authorize uploading source books or using translation engines.

State every substantive correction or qualification in the affected explanation in all delivered languages, with concise citations. Distinguish confirmed errors, conditional answers, unsupported claims and unresolved ambiguities. Evidence may qualify a recommendation without invalidating it in a refractory or otherwise exceptional case. It cannot supply an author's missing intended age, timeline or medication history.

Preserve raw source wording separately. If superseded wording remains visible for comparison, label it clearly so it does not appear endorsed. Keep the full clinical teaching content unless an edited or summarized explanation is authorized. Update stale current warnings and evidence metadata, then verify the correction reaches every canonical output. Report externally checked claims separately from source-only contradictions and overall translation coverage; do not certify the whole book from a selected pass.

## 4. English-Arabic practice

Write clear Modern Standard Arabic with familiar, precise medical terminology. Prefer a natural complete sentence over English word order. Keep terms consistent within a book while respecting their meaning in each context.

- Expand an ambiguous abbreviation from context; do not translate it as an unrelated everyday object or diagnosis.
- Distinguish clinical senses from everyday senses: affect versus effect, motor restlessness versus insomnia, behavioral cycling versus cycling as a sport, and devaluation of a person versus currency devaluation.
- Preserve Latin letters when they are the assessed speech sound, literacy example, gene name, or answer label. An example involving Latin b/d must not become a different Arabic-letter task.
- Retain drug/gene names and technical symbols when needed for identification. Check similar glyphs in the source image, such as 1/I/l, r/7, and >/≥. Do not claim the book misprinted a symbol merely because OCR did.
- Preserve patient gender, kinship, pronouns, who said each statement, and who is receiving an intervention.
- Translate stopping, withdrawal, refusal, permission, suicide prevention, and other action-sensitive wording carefully; a missing negative can reverse the meaning.
- Keep source and target languages in their respective fields. Retain English terms only when they serve a concrete purpose, rather than repeating whole English paragraphs inside Arabic.
- Preserve meaningful question/table labels. Check mixed Arabic/Latin text and inequalities for readable order; do not reverse the mathematical relationship to make a line look right in RTL.

A glossary supports consistency but is not a translation algorithm. Do not use global find/replace to decide the meaning of an ambiguous word. Prefer a scoped whole-field correction or per-record override when the same source phrase has different valid renderings.

## 5. Revise conservatively and retain detail

Keep existing wording that is accurate and natural. Repair complete sentences when patching individual words would leave broken grammar or duplicate fragments.

Do not omit clinically relevant source details for fluency. Unless summarization is requested, preserve the complete explanation and meaningful qualifications. When a shorter rendering is necessary, disclose the scope, retain the full source-language text, and do not count a summary as a full translation without qualification.

Keep patient-facing or study content focused on learning. Put OCR mechanics, extraction history, internal status, and evidence paths in review records. Add a short visible note only when a source conflict affects understanding or grading.

## 6. Save corrections so they survive regeneration

Use stable record IDs and the project's existing content pipeline. Reuse working per-record overrides rather than inventing another translation engine.

Make the precedence of contextual overrides, exact-source overrides, and retained wording explicit. Confirm that the exporter consumes the intended layer. Updating a review JSON that does not reach delivered CSV/JSON is incomplete work.

Preserve question/case/knowledge identities and relationships. If a case ID derives from text, retain its established identity explicitly when correcting spelling or translation. Do not assume a repeat import updates existing rows; inspect duplicate/update behavior before making that claim.

Keep one canonical delivery set. Prune obsolete entries that are demonstrably superseded when within scope; preserve necessary source/provenance and unrelated edits. Do not create duplicate old/new deliveries unless requested.

## 7. Track real review coverage

For long jobs, track each source ID and relevant fields: case, prompt, every choice, and explanation. Record empty source explanations and derived exercises separately.

Use unambiguous statuses such as authored/revised, reviewed and retained, pending, and source conflict. Record source verification separately from translation review. A field does not become reviewed merely because it has an override, lacks an obvious error marker, or passes a validator.

Count original exercises separately from converted import rows. Count changed strings separately from reviewed questions. For each pass, state what was read, changed, retained, and still unresolved. Retire stale flags after checking context; do not repeatedly ask the user to verify issues already resolved from supplied files.

## 8. Validate and report honestly

Use permitted lightweight content checks to verify parsing, language-field alignment, field limits, option counts/order, answer representation, CSV/JSON equality, and case links. Compare stable IDs, keys, English text, metadata, and unrelated records with a pre-edit snapshot, allowing only intended changes.

Inspect actual exported wording, especially whole cases and recently patched sentences. Check for duplicated clauses, cross-question warning leakage, lost qualifiers, and stale source-error notes.

Keep these conclusions separate:

- Translation fields reviewed in context.
- Source transcription verified, with the actual text/OCR/image method stated.
- Printed-source clinical/key issue resolved or still open.
- Data compatible with the inspected consumer contract.
- Import, bilingual rendering, and runtime behavior actually verified.

Do not claim every scanned word was visually inspected when OCR or normalized text comparison was used. Structural validation is not proof of semantic correctness, current medical/legal accuracy, or specialist certification. State the remaining limit precisely and continue all independent authorized work.
