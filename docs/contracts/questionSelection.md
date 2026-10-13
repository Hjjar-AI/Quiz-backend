# Per-user automatic question variety

Implemented in source 2026-10-09; schema preparation and live HTTP/database/performance checks remain pending. Detailed contracts: [learning consistency](learningConsistency.md).

Automatic category/tag/bookmark and blueprint selection now uses durable user/content exposure records instead of scanning history JSON or taking newest rows repeatedly. Coverage is the default: never-presented/answered assessed content first, then lower exposure/allocation counts, diverse knowledge concepts within comparable choices, older exposure and randomized ties. Case siblings in the selected set remain together.

Both clients offer coverage, balanced and weakness-review strategies through `selection_strategy`. Balanced favors new coverage and due reviews; review favors due/weak evidence. Blueprint weights/category quotas remain authoritative, and concept diversity is shared across quota/fallback selections. Explicit IDs/order, scheduled SRS order and fixed master composition retain their contracts.

`QuestionExposure` separates allocations, first generated presentations and answers by assessed fingerprint. Ordinary/master starts record allocations; repeated reads of the same question/source do not repeatedly count a presentation. Completion records answer evidence, including synchronized offline practice. These records survive session/history deletion; question deletion removes live exposure while historical learning events retain the original ID. Generated responses cannot establish that a screen was actually viewed, and unsynchronized offline learning is unknown to the server.

Ordinary selection and allocation now share the learner transaction, so concurrent starts see the preceding committed allocations. This is a preference, not a promise of disjoint sets: sparse pools, quotas and deliberate/manual repetition still allow overlap. Concept/case grouping cannot select questions outside eligibility or exceed requested limits.

Exposure lookups are indexed and do not traverse full histories. Eligible candidate rows are still materialized to rank current assessed content; large banks need runtime measurement. These models require a matching fresh schema; no migration/setup/database action was performed by the agent.
