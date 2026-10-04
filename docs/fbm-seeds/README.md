# FloRA builder seeds

FloRA captures one compact, reusable process trace per material infrastructure or experiment-design step. These rows follow A.L.I.C.E.'s [FBM trace schema v0.1](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/fable-builder-model/docs/fable-builder/TRACE_SCHEMA_v0.1.md). FloRA is the source of these seeds; the builder workstream can refer to them here when it needs them.

Each trace records an observable operation, safe references, constraints, validation, and a failure lesson. It is a seed for later FBM training or evaluation, not FBM weights and not a claim that FloRA can already build itself. Private host content, credentials, hidden reasoning, and raw model output stay out of this public record.

Capture new milestones in the same schema as work proceeds. A failed test and its repair should remain linked. Logging must not delay the actual build.

Run `python docs/fbm-seeds/validate_traces.py` from the repository root to check required fields, unique IDs, UTC timestamps and schema values. This validates record shape; it does not certify a trace's claims, privacy, or eligibility as a training case.

The schema's linked-case boundary also requires concrete eligible inputs, permission roles, a choice set, an independently checkable target or unresolved state, authority and outcome records, and source/generator split lineage before a procedure seed becomes a supervised or evaluable FBM example. Those linked cases and the actual builder remain separate work. The [readiness audit](../EXPERIMENT_READINESS_AUDIT.md) records the seed-field repair and the remaining experiment boundary.

## Latest construction records — 2026-10-03

The corpus now contains **130 validated procedure traces**. This count describes
schema-valid records; it does not certify their claims or training eligibility.
New material construction, failure and recovery steps continue to be captured here.

| Record | Observable operation |
| --- | --- |
| [Private CI access restoration](2026-10-03_private_ci_read_access_restoration.jsonl) | Restore authorized read-only pinned dependency checkout;26 new checkout steps succeed, full gates pending. |
| [Frontier branch applicability](2026-10-03_frontier_branch_applicability.jsonl) | Read current Alice intakes and primary methods; preserve source-index and independent outcome boundaries within FloRA scope. |
| [Completed private dependency failure](2026-10-03_completed_private_dependency_failure.jsonl) | Recover26 exact source trees and retain zero tests executed in completed checkout-failure runs. |
| [Query interface research](2026-10-04_query_interface_research.jsonl) | Inspect pinned XTDB caches and SQL/XTQL execution; separate derived-work patterns from authority and transport hypotheses. |
| [Owned assembly metadata](2026-10-04_owned_assembly_metadata_composition.jsonl) | Compose current assembly with existing H/C views, fresh private fences and expiry; 115 final cases pass at unchanged source; scoped review clear, physical qualification pending. |
| [Completed invocation gates](2026-10-04_completed_minimal_composition_gates.jsonl) | Recover1000 passing components per run; retain response failures/incomplete cases and locate native prepare. |
| [Minimal owned judgment composition](2026-10-03_minimal_owned_judgment_composition.jsonl) | Reuse actual prepared material for delivery; retain live rights, correct two reproduced callback edges, and preserve pending physical qualification. |
| [Completed older CI recovery](2026-10-03_completed_contract_cost_ci_recovery.jsonl) | Recover exact run checkouts and retain component/physical failures. |
| [Single fresh binding walk](2026-10-03_single_fresh_context_binding_walk.jsonl) | Remove measured duplicate traversal while retaining fresh own checks. |
| [Full components](2026-10-03_full_binding_components_and_publication.jsonl) | Verify 978 final cases after the retained worker failure and warning-bearing repeat. |
| [Published source and dispatch](2026-10-03_published_binding_walk_and_physical_dispatch.jsonl) | Bind the reviewed runtime to exact blobs and once-dispatched gates. |
| [Completed current CI](2026-10-03_completed_binding_ci_recovery.jsonl) | Verify all 26 jobs and retain the separate failed restart process. |
| [Unobserved cost and stack sampling](2026-10-03_unobserved_cost_and_owned_stack_sampler.jsonl) | Discriminate observer bias before another runtime change. |
| [Published sampling and one dispatch](2026-10-03_published_stack_sampler_and_dispatch.jsonl) | Verify exact published source, retain line-ending provenance and bind the pending diagnostic. |
| [Completed owned-stack sampling](2026-10-03_completed_owned_stack_sampling.jsonl) | Verify the actual artifact archive and117/116 source blobs; preserve failed fixture and healthy sampling. |
| [Bounded scope attribution](2026-10-03_bounded_owned_stack_scope_attribution.jsonl) | Attribute physical samples to fixed H/C callers before choosing the serving repair. |
| [Published scope sampling and one dispatch](2026-10-03_published_owned_stack_scope_and_dispatch.jsonl) | Bind reviewed exact source to the pending H/C scope diagnostic. |
| [Source recovery and owner architecture reset](2026-10-03_source_recovery_and_owner_architecture_reset.jsonl) | Recover the completed scope result and stop local trial/diagnostic drift; restore the narrow invocation-boundary design. |
| [Failed diagnostic and partial CI](2026-10-03_source_verified_binding_diagnostic.jsonl) | Verify loaded source, preserve failed response/process outcomes and avoid misleading timing comparisons. |

The latest result and unfinished gates are in the
[October 3 checkpoint](../VERIFICATION_CHECKPOINT_2026-10-03.md). Earlier records
remain linked snapshots; new outcomes do not rewrite an earlier failure or pending dispatch.
