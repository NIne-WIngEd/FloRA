# FloRA builder seeds

FloRA captures one compact, reusable process trace per material infrastructure or experiment-design step. These rows follow A.L.I.C.E.'s [FBM trace schema v0.1](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/fable-builder-model/docs/fable-builder/TRACE_SCHEMA_v0.1.md). FloRA is the source of these seeds; the builder workstream can refer to them here when it needs them.

Each trace records an observable operation, safe references, constraints, validation, and a failure lesson. It is a seed for later FBM training or evaluation, not FBM weights and not a claim that FloRA can already build itself. Private host content, credentials, hidden reasoning, and raw model output stay out of this public record.

Capture new milestones in the same schema as work proceeds. A failed test and its repair should remain linked. Logging must not delay the actual build.

Run `python docs/fbm-seeds/validate_traces.py` from the repository root to check required fields, unique IDs, UTC timestamps and schema values. This validates record shape; it does not certify a trace's claims, privacy, or eligibility as a training case.

The schema's linked-case boundary also requires concrete eligible inputs, permission roles, a choice set, an independently checkable target or unresolved state, authority and outcome records, and source/generator split lineage before a procedure seed becomes a supervised or evaluable FBM example. Those linked cases and the actual builder remain separate work. The [readiness audit](../EXPERIMENT_READINESS_AUDIT.md) records the seed-field repair and the remaining experiment boundary.

## Latest construction records — 2026-10-05

The corpus now contains **145 validated procedure traces**. This count describes
schema-valid records; it does not certify their claims or training eligibility.
New material construction, failure and recovery steps continue to be captured here.

| Record | Observable operation |
| --- | --- |
| [Completed run and purpose-first diagnosis](2026-10-05_completed_run_purpose_first_diagnosis.jsonl) | Recover all26 source/pin-bound original logs and completed physical failures; distinguish reached Claim-read entry from downstream effects, preserve the missing connected comparison, and require a discriminating diagnostic before a coherent correction. |
| [Test purpose and connected comparison audit](2026-10-04_test_purpose_connected_comparison_audit.jsonl) | Check positive/negative controls and actual equal-evidence oracles; identify missing same-case six-attempt physical coordinator connection and repeated fixture discovery, while preserving the running source. |
| [Reviewed phase correction and pipeline continuation](2026-10-04_reviewed_phase_correction_rejoin_pipeline.jsonl) | Genuine prior-source failure,92 corrected Linux passes with711 unchanged source records; apply exact reviewed correction and resume ordinary full pipeline, with physical and learned results pending. |
| [Original factory and real history control](2026-10-04_original_factory_and_real_history_control.jsonl) | Original-function/code admission, signed real-H control, clear source review and conditional Linux verification; complete physical phase boundary remains pending. |
| [Native factory origin and history fixture plane](2026-10-04_native_factory_origin_and_history_fixture_plane.jsonl) | Recover10 component passes but retain origin admission rejection and incompatible real-H fixture refusals; dispatch isolated original-factory/live-policy correction. |
| [Completed owner components with retained RED](2026-10-04_completed_owner_components_retained_red.jsonl) | Recover63 Linux passes without skips on unchanged source; retain copied-controller review failure and actual proof-port RED; registered-H fixture setup refusal is separate. |
| [Native callback owner review and readiness](2026-10-04_native_callback_owner_review_readiness.jsonl) | Retain copied-native-owner review gap and publish complete-pipeline readiness limits; one isolated factory repair is dispatched. |
| [Finite owner-map correction recovery](2026-10-04_finite_owner_map_correction_recovery.jsonl) | Recover82 original Linux cases and a source-isolated two-file correction; final Windows5/5 and native Linux21/21 pass, review/full phase pending. |
| [Actual phase owner-map review failure](2026-10-04_actual_phase_owner_map_review_failure.jsonl) | Retain six real capture errors and omitted-controller review findings; reject publication and dispatch one isolated finite mapping repair. |
| [Actual phase connected construction](2026-10-04_actual_phase_connected_construction.jsonl) | Actual consumer handoff, retained two repaired regressions and75 progressive component passes; review/Linux/physical gates pending. |
| [Actual-owner prepared-material contract](2026-10-04_actual_owner_prepared_material_contract.jsonl) | Source-backed real-consumer protection mapping and one construction dispatch; implementation/results pending. |
| [Actual phase boundary observation](2026-10-04_actual_phase_boundary_observation.jsonl) | One read-only actual-class observation separates cold restoration, repeated open preparation and current checks; physical/anchored limits retained. |
| [Actual phase consumer reachability](2026-10-04_actual_phase_consumer_reachability.jsonl) | Reject a fixture-only owner patch before source edits; trace actual live capture, pinned restore and anchored judgment. |
| [Completed owned assembly physical failure](2026-10-04_completed_owned_assembly_physical_failure.jsonl) | Recover completed1003-case component results, physical failures and correctly attributed baseline/native timings. |
| [Whole-operation reassessment](2026-10-04_whole_operation_architecture_reassessment.jsonl) | Trace guard amplification, review current Alice/frontier originals and map the prototype protection boundaries; replacement not implemented. |
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
