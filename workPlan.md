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

## Verification

- Run `manage.py check` when the complete backend dependency set is installed.
- Do not inspect or run test suites unless explicitly requested.
- Do not create migration files unless explicitly requested.

