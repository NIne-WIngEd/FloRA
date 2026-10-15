# Current FloRA architecture: implementation audit for a backbone rethink

Audit date: 15 October 2026. Read-only source review; no code changes, backend changes, job observations, cancellations, dispatches, or remote mutations. The occupied `work/FloRA` checkout and index were left unchanged.

## Judgment

FloRA is not an arbitrary collection of databases. Its logical decomposition is coherent: original evidence, ordered experience, accepted Claims, approved personal state, retrieval projections, model proposals, and actual judgments have different responsibilities. The code often preserves these distinctions carefully. Those responsibilities are worth retaining.

It is not yet a demonstrated coherent personal cognitive system. Much of the working composition concerns proving source, permission, artifact, and experimental-route custody. The actual external MFM/personality interfaces and the decision → outcome → governed revision → fresh judgment loop remain incomplete. More backend passes cannot supply the missing semantic computation. The current canonical positive test deliberately supplies fictional producer outputs; even a completed pass would establish its mechanical claim, not personal judgment or outcome learning.

The service topology is also more distributed than the minimum local experiment requires. Its source repeatedly names and inspects concrete Kurrent/XTDB implementations. Therefore “we own the logical contract” is defensible; “we own the backend implementation,” “the stores are freely interchangeable,” and “the connected personal system is already demonstrated” are not.

The right reuse boundary is the semantic contract and its adversarial cases. Preserve the current implementation and results as an explicit reference. A new compact local authority can be evaluated as a successor design without inheriting every process, wrapper, and Python implementation-identity check as a permanent product requirement.

## Source and evidence boundary

- Frozen executable source: FloRA [`692a5b2d3f7a86b481fc73828607f432b2c29cdf`](https://github.com/NIne-WIngEd/FloRA/tree/692a5b2d3f7a86b481fc73828607f432b2c29cdf), locally at `work/connected-placement-20261009/full-source-package/source`; Alice contract source `4f287a488bc908bd04f99255ee01b794bacba50b`.
- Current remote-tracking documentary refs observed locally: shared-source [`7beca501b11b18b29771dae6b6e637e96e6c6361`](https://github.com/NIne-WIngEd/FloRA/tree/7beca501b11b18b29771dae6b6e637e96e6c6361) and context `d0371fd25018536a017cd253d2689cc504785bdb`. There is no `src`/`tests` diff between the frozen source and this shared-source head. Nine central audited files were additionally compared byte-for-byte by Git blob identity with the frozen commit: runtime, Experience log, context guard, formation admission, decision/outcome, outcome revision, registered fixture, runtime test, and Compose definition; all matched.
- Local continuation: `work/connected-placement-20261009/semantic-loop-next-step-20261011.md` and `resume-state.json`. The state file contains dated historical fields as well as later updates; the current documentary entry and semantic next-step note are needed to interpret it.
- [Current continuation](https://github.com/NIne-WIngEd/FloRA/blob/7beca501b11b18b29771dae6b6e637e96e6c6361/docs/FLORA_CONTEXT.md#L3-L30) says Magnolia 577259 stopped during bootstrap before the strict test. Job 577260 was only initially observed running in the retained record. This audit did not refresh it. Kaggle 138146053 reached readiness and original-input registration but ended at the provider cap without a strict result. None of these facts establishes a defective cognitive architecture or a particular database startup cause.
- [Frozen experiment goal](https://github.com/NIne-WIngEd/FloRA/blob/692a5b2d3f7a86b481fc73828607f432b2c29cdf/docs/EXPERIMENT_GOAL.md): relevant correction/outcome influence, unrelated stability, competent equal-history baseline, same-evidence ablation, builder transfer, and later real-host evidence are separate claims. Any successor hypothesis or evaluation must be explicitly versioned; old results retain their original interpretation.

## What the implementation connects

| Stage | Concrete implementation and authority | Present limit |
| --- | --- | --- |
| Exact original bytes | `selected/object_store.py:26-97`: `OpaqueObjectBackend`, atomic local object placement, host-held key and encrypted content-addressed plane | This is a real narrow project-owned storage abstraction; it does not establish encryption of every other store. |
| Ordered experience | `selected/experience.py:183-207,250-278`: scoped stream, expected revision, committed physical position, server recording time, exact event binding | Canonical event ownership is distinct from Claim truth. Implementation is Kurrent-specific and explicitly disclaims cross-plane atomicity. |
| Semantic proposal | `selected/experiment_runtime.py:135-172,695-725`; `formation_candidates.py:224-265` | External adapter/codec must compute the proposal. Registering an output or authenticating its source does not interpret or learn its meaning. |
| Accepted knowledge | `formation_admission.py:51-65,239-279`; `claims.py:240-301` | External semantic interpretation and independently verified adjudication precede Claim authority. Synthetic ancestry remains experimental. |
| Personal state | `personal_state.py:344-407` | A candidate requires exact independent approval and expected-predecessor activation. Accepted Claims do not automatically become an updated personal model. |
| Recollection | `context.py:92-150,153-184`: actual content bytes, exact Claim/state routes, optional vector/graph nominations | Receipt hashes identify consumed material; hashes are not the semantic input itself. Count sufficiency is only the declared mechanical minimum. |
| Native judgment | `experiment_runtime.py:863-923`: context delivery, exact artifact/input/output, execution verifier, decision record | An interface exists, but the fixture codec supplies receipt-only context and a constant output. Real PE consumption remains to be connected. |
| Feedback | `decision_outcome.py:108-143`; `outcome_revision.py:23-84` | Independent observation, causal time order, predecessor/generation and candidate registration exist. Semantic revision is supplied externally; activation is separate. |

The assembled `run_cycle` at [`experiment_runtime.py:973-992`](https://github.com/NIne-WIngEd/FloRA/blob/692a5b2d3f7a86b481fc73828607f432b2c29cdf/src/flora/selected/experiment_runtime.py#L973) ends after formation, admission, activation and the **first judgment**. It does not then observe an outcome, propose a new state, adjudicate/activate it and obtain a later judgment. This is the central missing capability, not a missing database name.

The existing outcome contract is usefully conservative: [`record_outcome_observation`](https://github.com/NIne-WIngEd/FloRA/blob/692a5b2d3f7a86b481fc73828607f432b2c29cdf/src/flora/selected/decision_outcome.py#L108) explicitly says an observed outcome is not an automatic preference update, reward, or verdict that the decision was good. Keep that distinction for mixed consequences and predictions whose relevance is goal-specific.

## Backend, local process, and external service are different questions

The integration configuration runs KurrentDB 26.1.1, XTDB 2.1.0, NATS 2.12.15, Qdrant 1.18.3 and Temporal 1.32.0. Temporal additionally requires PostgreSQL, schema setup and namespace setup. Ladybug 0.21.0 is an embedded dependency rather than another Compose service. See [`compose.integration.yml`](https://github.com/NIne-WIngEd/FloRA/blob/692a5b2d3f7a86b481fc73828607f432b2c29cdf/compose.integration.yml) and `pyproject.toml:13-26`.

| Component | What it contributes | Minimum experiment assessment |
| --- | --- | --- |
| KurrentDB | Canonical event append/replay/commit metadata | Preserve its semantics or explicitly migrate them. A distinct server process is not the semantic requirement. |
| XTDB | Claim versions/current heads; permissions, state, artifact and experimental custody records | Temporal/versioned authority matters. Splitting every typed record into a separate service does not. Current code depends on XTDB transactions and assertions. |
| Qdrant | Derived Claim search and comparator memory retrieval | Useful when discovery is exercised. Keep a serious comparator; exact lookup in a bounded semantic scenario need not start every retrieval engine. |
| Ladybug | Derived evidence graph | Its hits are checked against Claim authority and source evidence. Instantiate only for graph questions in the declared experiment. |
| NATS | Device/edge buffering before canonical commit | `edge_ingress.py:1-6` explicitly treats it as transport. A local single-ingress prototype need not add this hop. |
| Temporal | Durable workflow/recovery machinery | `temporal_recovery_probe.py:1-5` is a synthetic restart test, not the cognitive loop. Durable effect recovery can be a required behavior without requiring this deployment in the first local scenario. |
| Local objects | Exact encrypted originals and model/private artifacts | Essential meaning/provenance boundary; local implementation already exists. |
| External feature provider | Replaceable authorized generation/comparison work | Distinct from native personal computation. The current connected fixture makes no actual provider inference. |

These can be self-hosted on one machine. Local network calls do not by themselves imply cloud dependence. Conversely, localhost deployment does not imply implementation ownership, zero egress, protected production configuration, or universal encryption. Compose is an integration configuration, including explicitly insecure Kurrent transport and fixture credentials; it is not a shipped security profile.

One concrete privacy boundary: `claims.py:294` writes `ClaimVersion.metadata_record()` into XTDB `record_json`. The pinned Alice `claim_contracts.py:234-253,720-743` includes the actual typed value in that record. The encrypted raw-object plane therefore does not establish that all personal semantic values are encrypted at rest. Any successor must specify which records/indexes contain personal meaning and where their encryption and keys live.

## The model seam is real work

`QualifiedProducerCodec` and `ExternalRuntimeAdapter` give useful integration points. `_execute` verifies exact invocation/input/artifact/output bindings and calls the supplied adapter (`experiment_runtime.py:534-593`). That is the right place to connect actual model computation and preserve the complete native decision packet.

The currently tested codec deliberately serializes `context.receipt_record()` rather than the actual `LocalContextItem.content`, and accepts exactly `{"fixture_only":"no learned verdict"}`. Its adapter supplies that output. See [`tests/test_selected_experiment_runtime.py:49-103`](https://github.com/NIne-WIngEd/FloRA/blob/692a5b2d3f7a86b481fc73828607f432b2c29cdf/tests/test_selected_experiment_runtime.py#L49). Production context contains bytes; therefore this is a missing integration seam, not proof that the architecture cannot carry meaning.

The inspected PE consumer is Alice [`1f22bc0c636840a50f9360064a074a41260ad9b0`, `identity/consumer.py:94`](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/1f22bc0c636840a50f9360064a074a41260ad9b0/src/alice_personality/identity/consumer.py#L94). It requires an actual document, produced features, and a matching closed-session receipt. A valid adapter must preserve those source/model bindings; renaming a FloRA receipt to PE input is insufficient. This is an inspected dated consumer, not a claim about final model readiness.

FloRA's pinned `formation_contracts.py:23` declares schema **1.2.0** and proposals use `value_ref`. The inspected MFM source at Alice [`d48c97a51cca57d40b4bd656cc994849cc0b18c2`](https://github.com/NIne-WIngEd/A.L.I.C.E/tree/d48c97a51cca57d40b4bd656cc994849cc0b18c2) declares formation schema **1.5.0**, adds `value_text` and anchors, and has companion `formation_semantics_v16.py` semantics. Calling all of that a single “1.6 ABI” would be inaccurate. The consumer needs an explicit versioned meaning-preserving mapping, including subject, source, time, contradiction and correction semantics. Do not silently downgrade it or replace every Alice contract just to make imports pass.

## What the canonical positive test can prove

The test at `tests/integration/test_selected_connected_functional_comparison.py:1-6,59-110` accurately declares fictional transport outputs and a mechanical three-arm comparison. Its useful obligations include before/after chronology, independent authority, matching histories/context, correct artifact routing, persisted attempts and fresh-controller recovery.

However, [`registered_functional_case_fixture.py:864-899`](https://github.com/NIne-WIngEd/FloRA/blob/692a5b2d3f7a86b481fc73828607f432b2c29cdf/tests/registered_functional_case_fixture.py#L864) computes the supplied judgments during construction and then prohibits subsequent model calls. Its worker program at lines 913-916 relays the bound output event ID. Its provider at lines 1031-1041 returns `Supplied fictional output. No model inference occurred.` This is legitimate transport/custody testing. It cannot measure semantic feedback, a strong baseline, or learned architecture advantage.

Preserve the incomplete physical outcomes without calling them failed behavioral hypotheses. The latest source-backed continuation explicitly leaves full mechanics and real model/outcome integration unqualified. A positive result should lead to the reached withdrawal controls; it should not be promoted to personal-learning evidence.

## Necessary complexity versus avoidable coupling

**Necessary product semantics:** isolated subjects/hosts, original evidence, uncertainty and provenance, proposal/adjudication separation, revisions and effective/system time, independent approval, consumed evidence, correction/deletion, coherent causal outcome links, idempotent commits, and recovery from an interrupted durable operation. Eliminating these would change the product claim.

**Necessary experimental semantics:** frozen held-out material, equal authorized history, honest baseline, same-evidence ablation, before/after chronology, leakage controls, reproducible artifacts, outcome-specific scoring and preserved failures. These belong in a bounded evaluation harness; they need not define the entire ordinary serving path.

**Current implementation choices:** separate event and Claim servers; repeated replay and reassembly inside nested guards; exact Python class/function/code identity checks; capture-slot publication plumbing; per-arm phase restoration; process readers/writers and synthetic-owner brokers. Some protect real boundaries in this implementation, but none is itself a learned personal capability or a universal cognitive requirement.

The coupling is concrete. Phase capture checks full `context_lineage` at lines 625, 661, 681 and 700 of [`phase_snapshots.py`](https://github.com/NIne-WIngEd/FloRA/blob/692a5b2d3f7a86b481fc73828607f432b2c29cdf/src/flora/selected/phase_snapshots.py#L620), around further head/source reads, archival objects and durable intent. The coordinator adds checks around adapter preparation/execution (`experiment_coordinator.py:543-591`). `context_guard.py:26-48` captures class layouts and Python code identity, while `experience.py:265-301` requires exact installed native receiver/SDK behavior for a physical-row proof. These are strong evidence that the implementation boundary is narrower than its apparently generic injected-client APIs.

This supports redesigning composition; it does not establish an exclusive performance cause. The retained October 7 evaluation audit documents repeated reconstruction and finite work in specific controls, while explicitly rejecting unbounded-recursion and whole-backend-causation claims. Magnolia bootstrap failures occurred before this path. Do not use those failures to justify a storage replacement.

## Defensible reuse and deliberate replacement

| Retain | Adapt for a successor | Leave outside the minimum loop |
| --- | --- | --- |
| Typed evidence/event/Claim/state distinctions; original-byte custody; subject boundaries; exact input/output/artifact receipts | Engine-facing classes into project-owned capability contracts; replace physical Kurrent positions with an explicitly mapped canonical sequence if storage changes | Multi-device NATS route until exercised |
| Expected predecessor, idempotency, provenance/source closure, independent permission and approval semantics | Single coherent semantic commit where possible; explicit durable intent/effect status where external work cannot share that transaction | Temporal deployment unless the scenario needs its workflow guarantees |
| Relevant/irrelevant/withheld-approval controls; deletion and stale-authority counterexamples | Current guards into checks over committed readsets, predicate generations and separate permission epochs, with actual equivalence tests | Graph/vector services on an exact-evidence scenario where they add no tested discovery capability |
| Current implementation, raw failures and strict tests as historical references | Real MFM/PE codec adapters; full decision packet; typed outcome and revision orchestration | Phase experiment machinery on every ordinary personal turn |
| Source/artifact authentication at meaningful boundaries | Replace Python object/code-identity defenses only after the new trust boundary is explicit and tested | Repeated bootstrap/observer wrapper layers without a demonstrated missing requirement |

Do not remove guards individually to make the existing test green. A successor transaction/read contract must protect the same meaningful invariant. A captured evidence readset alone is insufficient if a newly inserted relevant Claim could change the query result; query/predicate generations matter. Permission withdrawal is a different dimension from content version and must invalidate an operation independently. Replay and archived evidence must not restore revoked authority.

The current type-specific owners can become typed records under one local semantic commit authority without making proposals, observations, accepted Claims and judgments interchangeable. “One authority” should mean coherent commit ownership, not one undifferentiated truth table or one model that authorizes itself. An engine has not been selected by this audit.

## Minimum coherent prototype for the revised hypothesis

Construct one isolated fictional host, one small decision family, and one explicit goal with mixed observable consequences. Keep PE and MFM as external workstreams. The prototype needs a single complete causal path:

1. Commit authorized original evidence and current typed state with a stable source boundary.
2. Obtain a real native decision from actual content and model features. Record the chosen action, goal-specific predicted consequences and uncertainty as explicit data where the model supports them; do not invent missing model predictions in a wrapper.
3. Record an independently sourced later observation, including both benefit and cost where applicable. Preserve the original prediction and observed outcome separately.
4. Ask the external formation/revision component to propose a scoped update grounded in that observation and earlier decision. A failure to produce the required proposal is a model/integration result, not a reason for a scripted desired answer.
5. Independently adjudicate and atomically activate the permitted successor state with exact predecessor/version links. Withheld approval excludes that candidate from active judgment while preserving any separately authorized observation evidence.
6. Run a fresh held-out decision through the same actual consumer; measure warranted changed behavior, unrelated stability, source/reason accuracy and uncertainty. Use paired worlds where outcomes differ without supplying the desired preference or answer.
7. Compare against a competent model with the same authorized history, plus a same-evidence control that withholds the tested personal update. Keep model/backbone differences and evidence-selection differences explicit.

For the first implementation, a local transactional core plus encrypted objects, two genuine model adapters and the bounded evaluation harness is a coherent shape. It still needs causal ordering, expected versions, current authority, interrupted-operation recovery and derivative invalidation. It does not need every full Alice service to exist first.

Before model availability, an on-call deterministic synthetic producer may test sequencing only if it reads actual authorized bytes and derives its output. Its result must remain labeled synthetic mechanics. Predetermined phase answers cannot demonstrate the proposed behavioral connection. Builder transfer and real-host value remain later independent claims; none follows from this one-host prototype.

## Decision for the main synthesis

Keep the responsibilities; challenge the topology and hot-path composition. Use the existing sources and adversarial tests to define what must survive a compact local successor. Prioritize actual semantic model interfaces and the complete outcome loop over further experimental-wrapper expansion. Retain the current physical run and historical failures under their own contracts; do not reinterpret a new prototype as retroactive qualification of them.
