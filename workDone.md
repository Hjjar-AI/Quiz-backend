# Work Done

## 2026-10-06

- Normalized Excel/CSV import headings for whitespace, BOMs, and capitalization
  so recognized choice columns through `choice_8` are not silently missed.
- Rejected heading normalization collisions and added source row numbers to
  flat-file question validation errors. The correct answer must still refer to
  a filled choice; the reported limit reflects that row's actual choice count.
- Verified import changes with Python syntax parsing and diff whitespace checks;
  no builds, compilation tasks, test suites, or migration work were performed.
- The reported spreadsheet failure still needs confirmation using the original
  file; heading differences are a possible cause, not a confirmed diagnosis.
- Reviewed the application data model and PDF export pipeline.
- Added safeguards against cyclic tag hierarchies in model writes, serializers,
  imports, and tag merges.
- Added question lifecycle, verification, counter, and version constraints.
- Added master-exam timing, weight, version, and unique question-order constraints.
- Made master-exam reordering safe while unique order constraints are active.
- Corrected the bundled Arabic font filename used by PDF export.
- Added graceful handling for unavailable WeasyPrint native dependencies.
- Added configurable PDF question/image limits and a PDF-specific rate limit.
- Updated PDF deployment documentation.
- Verified Python compilation, Django model checks, font resolution, and diff
  whitespace checks.
- Did not create or review migration files.
- Added a comprehensive backend README covering SQLite/MariaDB setup,
  configuration, API layout, operations, deployment, and troubleshooting.
