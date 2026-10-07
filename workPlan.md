# Work Plan

## Current priorities

1. Exercise an end-to-end Arabic and English PDF export on a host with
   WeasyPrint and its native libraries installed.
2. Check small, image-heavy, filtered, verified-only, and front-matter PDF cases.
3. Monitor the default PDF limits and adjust them through environment variables
   if production worker capacity differs:
   - `PDF_EXPORT_MAX_QUESTIONS`
   - `PDF_EXPORT_MAX_TOTAL_IMAGE_BYTES`
4. Confirm fresh-database initialization creates the constraints represented by
   the current models.
5. When migration work is explicitly authorized, consider database constraints
   for the newly guarded result counts, percentages, dates, learning state,
   user counters, and planner bounds after auditing existing data.
6. Verify concurrent learner reviews and content edits against an isolated
   MariaDB instance, and exercise the knowledge/question API writes with the
   complete backend dependencies installed. SQLite scenario checks passed;
   production database locking and full API integration remain unverified.

## Verification

- Run `manage.py check` when the complete backend dependency set is installed.
- Do not inspect or run test suites unless explicitly requested.
- Do not create migration files unless explicitly requested.


## Bulk-tag Android integration — pending verification

- Verify mixed visible/inaccessible IDs and inaccessible-only selection against the
  bulk tag endpoint; keep private drafts outside the mutation/count scope.
- Verify transactional rollback includes new tags, memberships and question revisions.
- Exercise concurrent bulk tagging and ordinary editor saves on MariaDB: actual tag
  changes should trigger stale-editor conflicts, while no-op changes retain revision.
- Deploy the matching backend source before validating Android bulk tag recovery.
  Source/AST checks do not replace live API/database verification; test-suite and
  migration work still requires explicit authorization.
