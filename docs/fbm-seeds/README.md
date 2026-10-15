# FloRA builder seeds

## October 15: explicit roles and continuing maintenance

Read [FloRA's FBM objectives](../FBM_ROLES_AND_OBJECTIVES.md).
The [maintenance assessment](2026-10-15_continuing_maintenance_assessment.jsonl)
and [role mapping](2026-10-15_roles_and_objectives.jsonl) are procedure-only records.
The full [170-record workstream corpus](https://github.com/NIne-WIngEd/FloRA/blob/fc6d82df8e4050ed5f0f73fe43d84b1e35463830/docs/fbm-seeds/README.md)
remains on its source revision; this merge imports these two records, not all
unmerged development history. Trace count is not learned builder competence.

FloRA captures one compact, reusable process trace per material infrastructure or experiment-design step. These rows follow A.L.I.C.E.'s [FBM trace schema v0.1](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/fable-builder-model/docs/fable-builder/TRACE_SCHEMA_v0.1.md). FloRA is the source of these seeds; the builder workstream can refer to them here when it needs them.

Each trace records an observable operation, safe references, constraints, validation, and a failure lesson. It is a seed for later FBM training or evaluation, not FBM weights and not a claim that FloRA can already build itself. Private host content, credentials, hidden reasoning, and raw model output stay out of this public record.

Capture new milestones in the same schema as work proceeds. A failed test and its repair should remain linked. Logging must not delay the actual build.

Run `python docs/fbm-seeds/validate_traces.py` from the repository root to check required fields, unique IDs, UTC timestamps and schema values. This validates record shape; it does not certify a trace's claims, privacy, or eligibility as a training case.

The schema's linked-case boundary also requires concrete eligible inputs, permission roles, a choice set, an independently checkable target or unresolved state, authority and outcome records, and source/generator split lineage before a procedure seed becomes a supervised or evaluable FBM example. Those linked cases and the actual builder remain separate work. The [readiness audit](../EXPERIMENT_READINESS_AUDIT.md) records the seed-field repair and the remaining experiment boundary.
