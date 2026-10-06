# Work Done

## 2026-10-06

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

