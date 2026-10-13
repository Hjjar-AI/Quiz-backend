# Optional clinical-case translations

Updated 2026-10-10. [Schema readiness](schemaReadiness.md) · [Android status](../../../Android/docs/workDone.md).

Clinical cases now carry an optional `translations` JSON object keyed by locale. Each locale can supply `title`, `stem`, or both. Example:

```json
{"translations": {"ar": {"title": "حالة سريرية", "stem": "النص المترجم للحالة"}, "en": {"stem": "Translated clinical vignette"}}}
```

Titles allow 200 characters; stems use the existing 3000-character case limit. Locale keys normalize underscores to hyphens and lowercase; duplicate normalized locales, unknown fields, nonstring values and oversized text are rejected. Blank translated fields are omitted. `{}` clears translations in the case PUT; omission preserves them. Existing stem-only updates preserve translations.

The existing case PUT accepts this field with its existing capability/actual authorship gates, row locks, expected revision and audit record. Translation edits increment the case revision. Changes to translated stems invalidate affected learning evidence and participate in learning fingerprints; title-only translations do not. Cases with no translated stem retain their previous fingerprint shape.

The shared question case block includes translations in library reads, new ordinary/master grading snapshots, previews, offline downloads and new completed results. A historical snapshot without translations remains without them; no live translation is substituted. The master runner now uses the canonical snapshot case helper, retaining title as well as translations. Previously downloaded packs must be downloaded again to obtain newly added translations.

Android's existing question reading-language selection also applies to the case. Title/stem fall back independently to their originals when missing or blank. Original disables both question and case translations. Available case languages join the existing selector, including a case-only language. No additional reader buttons or translation panels are added. Readers already following the app language apply the same case resolver. Completed result readers retain their existing original-content behavior; this extension does not add result language controls.

Android case management provides a collapsed optional Translations section with title and case-text fields. Existing permissions, encrypted draft recovery, dirty state, revision conflict review and uncertain-write reconciliation include translations. Django admin has a collapsed translation field. Vue now also localizes case title/stem through its existing question-display language, including ordinary/master/preview and export-preview readers. Its shared question editor contains a collapsed case-translation editor with independent revisioned saves and explicit review for conflicts/uncertain writes. New cases must first be created by saving the question; edits remain in memory and route/dialog guards protect them. Writes omitting translations still preserve them. No additional translation controls appear in reader screens.

JSON and CSV/XLSX flat exports/imports support nested `case.translations`, `case_translations`, or `case_translations_json` as appropriate. State JSON and the Cases worksheet's optional `translations_json` column preserve translations; old workbooks without the column remain accepted. Importing cases follows their existing fill-missing semantics: add absent translated fields, keep existing local translated fields, and do not clear them through import. Explicit case PUT is the editing/clearing surface.

Deploy a backend/database containing `ClinicalCase.translations` before using the new editor. Schema setup and Android rebuild/device checks are pending; no migration inspection, generation/application, setup, database writes or builds were performed. This feature stores supplied translations; it does not automatically translate or populate book cases.
