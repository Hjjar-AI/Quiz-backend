# DSM-5 / Kaplan Arabic import revision — updated 2026-10-18

## Current delivery and coverage

Current chapter files: [DSM-5](../../../import_data/dsm5_ar/README.md) and [Kaplan](../../../import_data/kaplan_ar/README.md). The final displayed-field continuation reviewed **all 570 remaining original questions**: 314 DSM (14 chapter file pairs) and 256 Kaplan (11 pairs). Pending prompts, clinical cases and every choice were directly reviewed; correct existing wording and prior authored fields were retained. Revised **319 exact-source entries and 351 question-specific fields**; removed **304 superseded cache entries**. Exact-source entries differing from the initial session baseline total **2846** (1042 DSM, 1804 Kaplan). Segment counts overlap and are not distinct-question counts.

**Cumulative general-medical editorial review covers all 1078 original exercises**, including all displayed prompts, cases, choices and all nonempty original explanations. No questions or explanations remain in the translation review queue. Source/key conflicts and live app verification remain separate below; the user has now confirmed the 16.12 table transcription.

| Book | Import rows | Chapter files per format | Authored / nonempty original explanations | Explanations remaining |
| --- | ---: | ---: | ---: | ---: |
| DSM-5 | 545 | 24 | 475 / 475, plus 26 glossary-derived | 0 |
| Kaplan | 602 | 34 | 602 / 602 | 0 |

DSM has 476 original exercises: 475 have standalone explanations; glossary exercise `23.1` has an empty source explanation and generates 26 explanation-bearing rows from reviewed terms/definitions. Earlier remaining totals counted this empty field as an untranslated explanation; it is now accounted for separately. The preceding batch added 180 source explanations (44 DSM, 136 Kaplan), reviewed the glossary and all displayed fields for 40 Kaplan questions in chapters 17–20.

Full displayed-field review covers every chapter in both books, including DSM introductory questions `I.1`–`I.3` and the glossary. This is direct general-medical editing against retained English, not independent specialist certification of every source key or a systematic update to current clinical, regulatory or legal guidance.

Exporters select saved question-specific Arabic without an engine. Whole-book checks confirm contextual prompts and choices reach exports and prior source warnings remain isolated. Removed obsolete English-only rules that suppressed authored Arabic for cataplexy and the historical source term autogynephilia in the preceding pass.

No translation engine/model, network or external service was used. Editorial text is authored directly against retained English and general medical knowledge. Some explanations are concise renderings; full English remains. Current Arabic is stored in `review/arabic_overrides.json`; field coverage in `review/translation_status.json`; current progress/limits in `review/current_editorial_review.json`.

The user no longer needs obsolete versions: removed both old ZIP bundles and duplicate before/after editorial files. Removed superseded lower-priority translation entries in the preceding pass: DSM 3000 cache and 406 preferred-cache entries; Kaplan 623 cache entries. The chapter 4 pass removed 219 more superseded entries (90 DSM, 129 Kaplan). The chapters 5–10 pass removed 280 more (162 DSM, 118 Kaplan). The latest continuation removed another 254 (127 per book), with no old delivery copies created. The current continuation removed another 249 superseded entries (61 DSM, 188 Kaplan). This explanation-completion pass removed 221 further superseded Kaplan cache entries. The final displayed-field pass removed 304 more superseded entries (101 DSM, 203 Kaplan). Remaining cache entries support retained wording that has now been reviewed; they are not a pending-review count. English/OCR source and provenance remain available. No new backup files were placed in the delivery folders.

Arabic and English passages remain separate, with English case translations supported by the existing app contract. Existing matching/multi-select conversions, UUIDs, answer indices, categories, source/page references, case UUID/key/order and knowledge-object UUIDs remain preserved.

## Source problems

Kaplan's [source repair record](../../../import_data/kaplan_ar/review/2026-10-17_source_repairs.json) preserves previous OCR and evidence:

- `16.12`: all six table rows A–F and answer D were confirmed by the user’s transcription on 2026-10-18. Corrected E to patient **≥16**, replacing OCR >16; C/E display N/A. Updated English extraction, persistent extraction override, Arabic and chapter CSV/JSON. This resolves the pending transcription check; no direct scan inspection is claimed. The source’s <14 cutoff remains distinguished from the clinical prepubertal-child criterion and the full diagnostic criteria.
- `21.46`: restored the lost micro prefix (`50 µg/mL`, supported by the explanation) and distinguished concentration from administered dose.
- `30.7`: removed isolated footer noise from a complete option.
- `31.1`: restored `25` from `C..25`, corroborated by answer caption and explanation.

Extraction overrides preserve those repairs; raw OCR and answer letters remain. Further explicit Arabic warnings now identify DSM `1.5` (potentially multiple false options), `1.43` (age five versus minimum six for DMDD), `2.5` (three depressive months out of six does not establish majority duration for schizoaffective disorder), and Kaplan `3.2` (metronidazole is not routine treatment for typical bacterial UTI). Source keys remain for provenance; these items require source resolution rather than treating the preserved key as medically validated. No alternative ages, durations or antibiotic were invented.

The continuation also corrected source-level explanations about genetic loci (Prader–Willi, Rubinstein–Taybi, Williams, cri-du-chat and Cornelia de Lange), sundowning versus delirium, partial/focal seizure terminology, normal routine EEG limitations, CT/fMRI/SPECT descriptions and QTc risk thresholds. Earlier notes about Hoover, aripiprazole, Huntington penetrance, bereavement and atopognosia remain. This is not a systematic update of all recommendations, epidemiology or legal assertions to current guidance.

The chapter 4 pass also corrected DMDD onset versus first-diagnosis ages (`4.8`, `4.15`), clarified that ODD criteria can overlap without recording ODD alongside DMDD (`4.19`), and corrected the PMDD core-symptom wording (`4.28`). New unresolved source issues are explicitly recorded in each book's `review/source_editorial_notes.json`:

- DSM `4.24`: the vignette does not establish MS versus interferon versus independent depression as the cause. `4.25`: five distinct PMDD symptoms are not clearly documented. `4.29`: the named patch formulation/route needs confirmation.
- Kaplan `4.2`: a prevalence fraction is unreadable in OCR and was not guessed. `4.11`: thiamine causes Wernicke disease; pellagra is due to niacin deficiency, which is absent from the options. `4.20`: personality disorder is not required for cannabis-induced psychosis. `4.30`: slow respiration is atypical for uncomplicated stimulant intoxication. `4.32`: the case does not establish every claimed contraindication, and nasal spray differs from the inhaler option. `4.37`: the prior treatment is unspecified, so treatment-caused rhabdomyolysis is not established; the blanket recommendation of activated charcoal was corrected to a qualified discussion with supportive care as the priority.

Historical legal thresholds, regulatory approvals and epidemiologic comparisons are labelled as book context, without claiming current external verification. Source answer indices and English wording remain unchanged; warnings distinguish the intended source answer from a medically established conclusion.

The chapters 5–10 pass additionally corrected or qualified:

- DSM: adult-onset separation anxiety; unexpected attacks and duration for panic disorder; physiologic causality versus adjustment; OCD versus hoarding/appearance concerns; acute-stress pool of **14 symptoms with nine required**; ICU delirium versus actual trauma; ordinary play versus traumatic reenactment; hypercapnia in asthma; positive evidence for functional neurological symptoms; confirmed versus suspected illness fabrication; and alkalosis from vomiting versus possible acidosis from laxative-related diarrhea.
- Kaplan: undefined premature-mortality comparison; schizoaffective mood/psychosis timeline; nonbizarre delusions are not mandatory; clozapine can affect the liver and book dispensing rules are not verified current rules; mania/hypomania duration makes both A and E valid in `6.1`; cyclothymia duration is missing; three months of untreated mania does not define maintenance duration; slow lamotrigine titration and valproate interaction; cognition may not fully recover after depression treatment; antidepressant taper speed must be individualized; three-month specific-phobia vignettes do not document usual six-month persistence; and delayed PTSD expression concerns completion of criteria, not absence of every early symptom.

Source keys and English remain unchanged. Question-specific notes make the intended book answer distinct from a medically established answer. Detailed question IDs and limits are in both `review/source_editorial_notes.json` files. These corrections do not establish independent specialist verification of every key or a comprehensive update to current clinical/regulatory guidance.

The chapters 11–16 continuation corrected or qualified these additional source issues:

- DSM `11.1`/`11.6`: developmental age cannot be inferred from a broad delay label. `11.8`: fecal overflow was mistranslated as urinary overflow. `12.5`: hypopnea differs from hypoventilation. `12.8`: hypoxemia alone is insufficient to establish hypoventilation. `12.18`: prognostic percentage comparator is unreadable and was not guessed. `12.21`: pregnancy/insomnia alone do not establish restless legs syndrome. `12.22`/`12.23`: source wording permits multiple associated conditions. `12.25`: withdrawal is not an automatic exclusion of all separate induced sleep diagnoses; assess delirium. `13.6`/`13.7`: no additional DSM diagnosis does not mean no medical problem, and controlled diabetes/stress do not prove psychological causation. Gender identity variation alone does not meet distress-based diagnosis criteria.
- Kaplan `11.1`/`12.3`/`12.6`: sparse symptoms or negative investigations do not prove dissociation, functional neurological disorder or deliberate illness falsification. `12.10`: old diagnostic-revision percentages are not generalized. `13.5`: no DSM 2000-kcal binge cutoff; loss of control matters. `13.8`: night eating with awareness differs from sleep-related eating with amnesia. `13.14`: bulimia key lacks documented binge/loss of control. `14.3`: surgery is not routine initial disimpaction. `14.5`: twice weekly, not two weeks. `14.9`: hyponatremic seizure and desmopressin safety context corrected. `15.6`: MSLT mean latency matters in addition to SOREM count. `15.9`: dopamine agonist augmentation risk qualified. `15.10`: pitolisant is H3 antagonist/inverse agonist. `16.9`: estrogen effects are not universal. The prior `16.12` operator uncertainty was subsequently resolved from the user’s transcription, as recorded above.

Detailed IDs, status and limits remain in `review/source_editorial_notes.json` and `review/current_editorial_review.json`. Source answer mappings and English remain unchanged; clinical corrections and source uncertainty are distinguished from independent specialist or current regulatory verification.

The latest continuation also corrected or qualified source claims about schizotypal psychotic experiences, antisocial personality and suicide risk, gender development/karyotype notation, authoritative parenting, epilepsy and violence, MAOI and prazosin mechanisms, serotonin toxicity, lithium toxicity and dose timing, clozapine historical dispensing rules, valproate pregnancy planning, lamotrigine re-titration, complex sleep behaviors, cognitive/fall effects of benzodiazepines, and ECT seizure/memory/safety claims. Detailed IDs and unresolved source conflicts are in both `review/source_editorial_notes.json` files. These are direct editorial corrections using general knowledge; no current external regulatory verification was performed.

The explanation-completion pass corrected or qualified additional source claims about osmotic diuresis for lithium toxicity (`25.22`), indiscriminate flumazenil (`25.20`), unavailable tardive-dyskinesia treatment (`25.25`), increasing drug clearance with age (`25.15`), ECG exclusion of valve prolapse (`25.23`), pediatric HIV initial-site claims (`25.27`), safety contracts and undocumented eating-disorder stability (`26.1`/`26.3`), grief limited to two months (`29.5`), Endicott replacement criteria (`29.9`), consciousness and opioid neurotoxicity (`29.10`/`29.11`), and fixed developmental milestones. The social-smile key conflicts with the explanation (`32.8`); reward pathway choices overlap (`33.16`); RR 1.2 does not mean 20% greater probability of genetic causation (`33.24`). The Twin Towers event date is corrected to 2001 in Arabic, retaining and flagging the English 2011 typo (`34.12`). Legal details and old demographic forecasts are explicitly source context, not verified current rules or statistics. Full IDs and unresolved issues are in Kaplan `review/source_editorial_notes.json`.

The displayed-field continuation corrected mistranslated confidentiality/privilege terms (`28.3`), consent withdrawal (`28.11`), judgment of legal competence versus clinical decision capacity (`28.12`), requests to hasten death rendered as execution (`29.13`), restarting medication (`30.5`), prospective study versus hypothetical association (`31.7`), maternal perception of fetal movement (`32.2`), autosomal inheritance (`32.6`), seeking approval (`32.12`), and middle childhood versus middle-aged adulthood (`32.17`). Cases now preserve grade improvements, consistent gender and meaningful drug-formulation distinctions. No new current legal or statistical verification is claimed; all source keys and English are retained.

The chapters 33–34 continuation corrected CNS ventricular enlargement (`33.1`), neuronal/glial anatomy, miRNA action on mRNA (`33.12`), lapses in responsiveness (`33.29`), medial temporal localization (`34.11`), ethology mistaken for ethics (`34.24`/`34.25`), great-aunt kinship (`34.34`) and low mood mistaken for panic (`34.36`). The table combinations in `33.18`, `34.15`, `34.18` and `34.28` name every column explicitly. Source fexofenadine/no-medications contradiction (`33.29`) and nonstandard adult BMI percentile (`33.21`) are flagged rather than resolved by invention. English, answer indices and existing explanations are unchanged; no clinical/source-key certification is inferred from clearer Arabic.

The final 570-question pass corrected IED/CD abbreviation errors, weapon bats, acute confusion, personality terms, tobacco abstinence, functional seizure descriptions, omitted exhibitionism-case consequences, nursing rounds, pressured speech, rapid cycling, medication withdrawal, weight units and a reversal of suicide-prevention meaning. Childhood cases now preserve school grades, Latin letter examples, foster-care context, observed engagement and prognostic wording. New source caveats include DSM `15.11`/`16.9`/`22.10`, Kaplan `21.60`/`21.70`, and the `FMR1` OCR correction in `2.6`. Detailed question IDs and unresolved criteria/key conflicts remain in each book’s `review/source_editorial_notes.json`.

## App compatibility

**Chapter CSV/JSON schemas are compatible with current app source.** Import only files in `json/` or `csv/`. Manifests, `source/`, `review/` and `duplicate_review/` contain supporting data, not question imports. Choose one format; matching CSV/JSON share UUIDs.

| Data | Current contract / result |
| --- | --- |
| JSON | List of objects; `choices` array; integer `correct_answer` from 1 |
| CSV | UTF-8 BOM; quoted multiline cells; `choice_1`–`choice_8`; JSON cells for tags/translations/case translations |
| Choices | 2–8; at most 300 characters each; English counts match Arabic |
| Question, explanation, case stem | At most 3000 characters, including translations |
| Category / tag / source / document | At most 100 / 50 / 200 / 500 characters |
| Cases | Stable key/UUID, title/stem/order, `case_translations` or `case_translations_json`; separate English case stem |
| Knowledge links | Existing UUID/title/objective fields supported |
| File counts/sizes | Largest chapter DSM 75 rows, Kaplan 70; largest CSV below 300 KB; current limit 5000 questions per upload |

Traced [flat importer](../../../apps/questions/services/importing/flat_import.py), [choices](../../../apps/questions/validation.py), [question translations](../../../apps/questions/translation_validation.py), [case translations](../../../apps/questions/case_validation.py), current models/settings, import capability gate and [Vue language resolution](../../../../frontend/src/utils/localizedQuestion.js). No application API change required.

Existing UUIDs are skipped: re-uploading **does not update previously imported questions** or replace populated case stems. No application database was read or changed. Updating existing imports requires a separately scoped workflow. Normal capability/upload/throttle rules still apply.

## Verification

- Regenerated 58 JSON and 58 CSV files with existing local exporters and saved editorial entries.
- Both artifact verifiers passed: all 1147 rows, coverage, original/converted answer mappings, CSV/JSON equality, unique UUID/question text, lengths and case links.
- Exercised current pure production choice/question-translation/case-translation validators in isolation with source constants, without initializing Django. This does not exercise database resolution, MIME/upload handling or HTTP transactions.
- Compared all 1147 rows against the final pre-batch snapshot: only Arabic question/choice/case text changed. All English, explanations, UUIDs, answer mappings, relationships and other metadata matched. Verified source-warning placement across both whole books and that the latest question-specific prompts and choices are actually exported. Checked current converted exercises without changing their mappings.
- Compared stable metadata with the pre-edit snapshot. No remaining `⁇` marker in delivered question/choice/explanation/case text; marker absence does not establish semantic accuracy.
- Python AST, JSON parsing and changed document/whitespace/link checks completed.

No application suites, builds/compilation, packaging, migrations/setup, database operations or browser/live HTTP imports. Obsolete ZIPs and duplicated older Arabic entries were removed at the user's request; use current chapter folders. Existing Git policy ignores `import_data/` and `scripts/content/`, so those edits remain workspace-local unless deliberately included later.

Remaining: resolve flagged source/key questions; verify actual import and bilingual rendering on the running app. No original translation fields or nonempty explanations remain unreviewed. Local data validation does not establish specialist, current legal/regulatory or runtime verification. A read-only listener query was denied by the environment; no running app was established or started.
