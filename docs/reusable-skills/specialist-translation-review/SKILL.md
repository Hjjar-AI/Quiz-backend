---
name: specialist-translation-review
description: Translate or repair technical and medical book content through direct contextual editorial reasoning, including English-Arabic questions, cases, choices, and explanations. Use for faithful specialist-language translation or proofreading, rather than machine-translation pipeline development.
---

# Specialist translation review

Read [translation-review-instructions.md](references/translation-review-instructions.md) before performing the review. It is also a standalone instruction file the user can copy into another project.

Author and review the translation directly. Use available subject knowledge to understand meaning, but distinguish translation repair from changes to the source's clinical facts, answer keys, or historical assumptions. This is editorial work, not independent specialist certification.

Default to the user's established preference: no external services and no local or remote translation engines unless explicitly requested. Existing local OCR can help read a source. Scripts may assemble and validate already reviewed text; they must not substitute glossary replacement or a new translation backend for contextual review.

Establish the requested languages, edition, scope, and destination. Resolve routine choices from available context and continue the authorized work; ask only when a missing decision materially affects the result. Read supplied source files before asking for transcription or calling an extracted defect a printed-source error.

For long collections, track coverage by stable source ID and field. Correct retained wording counts as reviewed only after it has actually been read in context. Reuse existing correct translations; producing more changed strings is not an objective.

Validate both preservation and delivery: saved per-question wording must reach actual exports; source/target content must remain aligned; corrected case text must preserve established relationships. Report translation coverage separately from source conflict resolution, schema checks, and live application verification.
