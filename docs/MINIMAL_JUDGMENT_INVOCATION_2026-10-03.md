# FloRA minimal current judgment invocation

Status: authorized implementation slice; performance and learned qualification pending.

This implements the owner's October 3 scope reset. FloRA consumes qualified
external personality/MFM exports. It builds no model, memory platform or mission
scheduler. The frozen causal experiment and its existing budgets remain in force.

## Invocation contract

The foreground path is one current-context preparation, delivery of that exact
material, qualified external judgment and a decision linked to its actual
execution. Recovery is a separate, explicitly invoked operation. An outcome
observation links back to the decision; an externally proposed successor still
passes Claim/state governance before it can influence the next judgment.

| Transition | Live facts and observer | Protected use and refusal |
| --- | --- | --- |
| Experiment entry | `NativeArmAdapter._check`, actual final authority and `_phase_session` bind case, phase, question, arm, history, archive and invocation. | Refuse changed BEFORE/AFTER lineage, missing final authority or detached readers before private preparation. H authentication is explicit at this entry. |
| Selected current preparation | `FloRAExperimentRuntime._prepare_current_context` uses finite Claim/state nominations; actual registered policies, owner verifier and current metadata barriers authenticate the material. | Before/after ciphertext access, reject withdrawn C rights, changed Claim/state heads, source/raw metadata or owner proof. H evaluation rights and phase membership remain independently enforced by the current phase guard/shared frame. |
| Delivery | The same invocation-owned `PreparedCurrentContext` revalidates exact material and current authority. Delivery still authenticates cited originals, their timestamps and Experience revision. | Do not call `assemble_context` again to rediscover already prepared material. Refuse source changes/withdrawal during read or before append; the terminal joint fence still covers H and C. |
| External producer | `_execute` resolves the actual current qualified personality artifact, binds exact input, verifies the external execution independently and revalidates after callbacks. | Reject changed artifact/input, invalid proof or lost permission before inference and output acceptance. No MFM invocation or readiness prerequisite is added to judgment. |
| Decision/result acceptance | `record_decision` retains authenticated consumed-source links. Native adapter recovery, independent result proof, metering, evaluation authority and writer fences remain explicit. | Reject mismatched output or consumption lineage and current withdrawal before accepting/writing the result. A delivered-context receipt is not proof of learned attention. |
| Correction/outcome | Existing `record_outcome_observation`, governed outcome revision and external formation/admission/activation interfaces preserve decision → observation → evidence → successor. | Observation is evidence, not automatic truth or preference activation. A new judgment prepares current material after accepted successor activation. Add mission/node identifiers only when a case needs them. |

Successful permission answers are never reused. Immutable material can remain
owned by an invocation while each protected boundary observes present authority.
This slice leaves H verification inside the existing phase predicates unchanged;
its removal needs a separately demonstrated protection mapping. Consequently it
does not claim to resolve the sampled current-history bottleneck by itself.

## Source-backed rationale

At runtime `4b88946f`, `judge` already obtains an authenticated current preparation.
It then calls `record_context_delivery`, which calls `assemble_context` a second
time before authenticating delivery sources. This is an observed duplication in
the serving composition, distinct from the scoped sampler's H attribution.

Alice Memory Architecture v4.1 §3.2 calls for current materialization during
ordinary serving and explicit historical reconstruction. Existing
[research](LATENCY_RESEARCH_2026-10-02.md) inspected Graphify's exact-content reuse
and Graphiti's shared query representation. The applicable mechanism is reuse of
the same authenticated material with fresh authority, not reuse of allow answers.
No database, source cap, timing definition or arbitrary callback is replaced.

## Bounded implementation plan

- [x] Add a regression demonstrating one context assembly reaches the actual
  fixture producer with exact delivery/input/decision linkage, without requiring
  a live MFM binding. Retain denial if authority changes after preparation.
- [x] Factor delivery's existing source authentication/receipt append into a
  private helper in `src/flora/selected/context.py`. The standalone public
  delivery API keeps its reconstruction semantics.
- [x] Compose `FloRAExperimentRuntime.judge` with its owned preparation and that
  helper. Run full current owner-proof/authority validation after clock/revision callbacks and before delivery append; retain per-source reads and pre-append
  authority checks. Change no recovery, producer, governance or phase algorithm.
- [ ] Run affected runtime/context/phase-race tests, obtain a fresh scoped review,
  and run the required selected-engine invocation. Record complete/incomplete
  results separately from learned and latency qualification. Update context/FBM.

Review focus: withdrawal during delivery/codec callbacks, source mutation after
preparation, exact source/control consumption, current artifact replacement and
independently recovered output. Existing relevant tests must stay passing.

## Construction result

[Exact receipt](evidence/2026-10-03_minimal_judgment_composition.json) records **27/27 final Linux component cases**, zero errors/failures/skips, and a fresh clear review. Review reproduced two introduced edges before their corrections: owner-proof withdrawal at the delivery clock, and replacement of the original runtime policy during qualification. Full delivery revalidation and a pure original-policy identity guard now reject both. The external authority callback still executes freshly. Source reads, standalone reconstruction and recovery remain explicit.

A mixed broader local check was stopped because serving edits invalidated its loaded source identity; it has no final pass total. Physical BEFORE/AFTER and response qualification remain pending at publication. No new diagnostic, model training, GPU job or mission infrastructure was added. The unchanged H/recovery path remains a separate unresolved cost.

## Published physical gates

Published serving source `bf494970` and context snapshot `877162da` are [verified against actual Git blobs](evidence/2026-10-03_minimal_judgment_publication.json). [Push37151333895](https://github.com/NIne-WIngEd/FloRA/actions/runs/37151333895) and [PR37151335920](https://github.com/NIne-WIngEd/FloRA/actions/runs/37151335920) are in progress at capture. They are the existing standard physical/contract gates, automatically triggered once; no new diagnostic was dispatched. Only external results remain. Stop here, then recover exact completed receipts and actual timings before choosing the next bounded change. Context-branch serving files remain historical.

