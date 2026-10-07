# Agent Instructions

## Scope

- This folder contains the Django backend and owns the API/data contracts.
- Preserve service-layer transactions, capability checks, audit logging, and the
  standard API response envelope.
- Keep Arabic and English behavior consistent where localization applies.

## Working rules

- Do not review migration files or create migration files unless explicitly
  requested. The project commonly starts from a fresh database after model edits.
- Do not review test-suite files unless explicitly requested.
- Preserve unrelated user changes in a dirty worktree.
- Prefer enforcing important invariants at both the API/service boundary and the
  database-model boundary.
- Keep import and export formats backward-compatible unless the task explicitly
  authorizes a schema-version change.
- Never expose storage paths, credentials, or internal exceptions through API
  responses.

