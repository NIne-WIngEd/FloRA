# FloRA builder seeds

FloRA captures one compact, reusable process trace per material infrastructure or experiment-design step. These rows follow A.L.I.C.E.'s [FBM trace schema v0.1](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/fable-builder-model/docs/fable-builder/TRACE_SCHEMA_v0.1.md). FloRA is the source of these seeds; the builder workstream can refer to them here when it needs them.

Each trace records an observable operation, safe references, constraints, validation, and a failure lesson. It is a seed for later FBM training or evaluation, not FBM weights and not a claim that FloRA can already build itself. Private host content, credentials, hidden reasoning, and raw model output stay out of this public record.

Capture new milestones in the same schema as work proceeds. A failed test and its repair should remain linked. Logging must not delay the actual build.

Run `python docs/fbm-seeds/validate_traces.py` from the repository root to check required fields, unique IDs, UTC timestamps and schema values. This validates record shape; it does not certify a trace's claims, privacy, or eligibility as a training case.

The schema's linked-case boundary also requires concrete eligible inputs, permission roles, a choice set, an independently checkable target or unresolved state, authority and outcome records, and source/generator split lineage before a procedure seed becomes a supervised or evaluable FBM example. Those linked cases and the actual builder remain separate work. The [readiness audit](../EXPERIMENT_READINESS_AUDIT.md) records the seed-field repair and the remaining experiment boundary.

## Latest construction records — 2026-10-07

The corpus now contains **161 validated procedure traces**. This count describes
schema-valid records; it does not certify their claims or training eligibility.
New material construction, failure and recovery steps continue to be captured here.

| Record | Observable operation |
| --- | --- |
| [First capture admission diagnosis](2026-10-07_phase_capture_admission_diagnosis.jsonl) | Separate functional claims from reuse counts; validate actual progress and locate the first admission refusal before repair. |
| [Failed observer and numeric journal](2026-10-07_setup_observer_failure_and_journal.jsonl) | Preserve incomplete signal-failed observation, trace coherent capture stack and repair only the measurement mechanism before architecture attribution. |
| [Completed physical failure and functional priority](2026-10-07_completed_physical_and_functional_priority.jsonl) | Validate1 pass/2 budget failures, audit uncalibrated cutoffs, retain old verdicts and rejoin the owner-authorized connected functional build. |
| [Copied-consumer observer diagnosis](2026-10-05_terminal_copy_observer_diagnosis.jsonl) | Preserve a failed control whose observer required the original consumer instead of custody's copy; correct only test ancestry binding and retry control/basis denial on unchanged runtime, with no architecture verdict yet. |
| [Terminal correction and basis discrimination](2026-10-05_terminal_completion_candidate.jsonl) | Freeze four unverified runtime changes and a strict saved-metadata-port test; dispatch only the same-source control/basis diagnostic before another correction, with broader regressions and physical pipeline pending. |
| [Completed v2 diagnostic and observation recovery](2026-10-05_completed_v2_terminal_diagnostic.jsonl) | Recover a viable actual-v2 fallback control and reached terminal-denial failure from unchanged logs; preserve the runner's parser-failure verdict separately and proceed to exact terminal revalidation on issued/fallback paths. |
| [Actual-v2 control/denial diagnostic](2026-10-05_v2_control_terminal_discrimination.jsonl) | Build a comparable registered capture control and passive branch probe; frozen offline Linux result pending. |
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

- [Capture-copy observer diagnosis](2026-10-05_terminal_copy_observer_diagnosis.jsonl): preserve the false control verdict and retry only the observer on identical runtime source.

- [Finite lineage basis diagnosis](2026-10-05_finite_lineage_basis_diagnosis.jsonl): validate matched controls, reuse finite prepared bindings, preserve lifetime and proof-coverage limits.

- [Temporal restoration fixture diagnosis](2026-10-05_temporal_restoration_fixture_diagnosis.jsonl): validate setup and pinned row contracts, reuse coherent fixtures, retain unaffected evidence.

- [Completed terminal verification and pipeline continuation](2026-10-05_completed_terminal_pipeline_continuation.jsonl):18 source-bound component passes, exact frozen publication, coverage limits and return to ordinary physical CI.

- [Source-bound physical latency diagnosis](2026-10-06_source_bound_latency_diagnosis.jsonl): validate budget claims and unfinished jobs, source-check measured amplification, dispatch one unchanged-runtime stage diagnostic before choosing a correction.

- [Finite pure verification composition](2026-10-06_finite_pure_verification_composition.jsonl): source-bound worker evidence overturns storage speculation; share graph observations while preserving independent expectations and fresh authority.

- [Finite binding pass candidate](2026-10-06_finite_binding_pass_candidate.jsonl): prove alias work before repair, preserve independent expectations and getter/meta fallback, verify callback-free graph bounds before original physical tests.

- [Binding components and original physical verification](2026-10-07_binding_components_and_physical_verification.jsonl):81 exact-source functional passes, preserved observation-timer limit, five-path publication and one uninstrumented physical dispatch before reconnecting the causal workflow.

Current October7:158 validated public procedure seeds after connected functional construction. Physical and learned results remain pending.

October7 current:159 validated public methods; shared physical construction stopped before its oracles. One source-bound observation is the next diagnostic.

October7 current:160 methods; one numeric-journal observation is next, not a runtime repair or qualification.

October7 current:161 methods; admission discriminator pending, no functional/model/latency qualification.
