# Backend

- Start at [docs/README.md](docs/README.md), then use `docs/workPlan.md` and `docs/workDone.md`; production serializers/views define contracts for Vue and Android.
- Preserve capability gates, actual ownership, account scoping, transactions and supported revision checks. Do not equate list visibility with management permission or invent idempotency guarantees.
- Keep omitted fields distinct from explicit clears; preserve exact tag identity and export selection/order. Coordinate PDF themes/options with frontend. Record contract limits and pending runtime checks.
- Follow [Agents.md](Agents.md) for startup behavior: fresh SQLite initial migrations differ from incremental model migrations; agent-run migration/setup work still needs an explicit request.
