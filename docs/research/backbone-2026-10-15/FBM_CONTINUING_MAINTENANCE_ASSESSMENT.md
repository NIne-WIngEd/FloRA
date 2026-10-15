# Continuing FBM or a dedicated backbone handler?

Reviewed October 15, 2026. **Assessment only; no new runtime, model or FloRA prerequisite.**
The owner proposed optional backbone maintenance and asked to compare a separate
handler with FBM continuing after the initial build. Recommendation: use a
governed FBM maintenance role first; require measured benefit before splitting
out a specialist. Neither option has demonstrated backbone-repair competence.

## What the existing plan actually says

- Alice main `8ea804aa25c3d1c5f46e9be5810d072ed0fadb4b`,
  `docs/ALICE_PHASE2_REPLACEMENT_AND_FABLE_V1_EXECUTION_PLAN_2026-09-27.md`:
  Lane I / FBM-5 covers memory-fabric wiring, migration, projections, deletion,
  retrieval, training and rollback; FBM-6 covers failure localization and repair.
  Lane F4 requires frozen acceptance criteria, behavioral/regression evidence,
  provenance, rollback and monitoring. A model cannot promote itself on its score.
- Current FBM branch `research/fbm-v1-licensed-base-20260930` at
  `8dd52ce2ca01c433f9f957374d68bcc2c1fc9730`,
  `docs/fable-builder/FBM_V1_LICENSED_BASE_ASSEMBLY_2026-09-30.md` explicitly
  includes continued governed updates after assembly. Its README's runtime
  evolution hypothesis retains a separately governed curriculum/repair mode.
  This is design intent, not a completed maintenance model. The current V1
  lineage update supersedes the older scratch-only recipe; neither recipe is
  being changed here.
- Alice frontier-watch `db910c3c9d2917f1d0b628f880686ce8195fe2c4`,
  `docs/research/SHAPER_SKILL_HARNESS_EVOLUTION_2026-09-23.md`, already considers
  failure-localized skill/context-program evolution a future design seed.
  It explicitly does not require a new top-level plane.
- FloRA's approved [backbone hypothesis](ALICE_BACKBONE_HYPOTHESIS.md), section 7,
  gives FBM candidate construction changes without production activation or
  private identity transfer. Extending that responsibility to maintained
  backbone code is consistent with the sources; an always-on implementation
  and a separate checkpoint are not settled requirements.

All three Alice branch tips above were checked against the remote on this date.
The older builder README alone would miss subsequent lineage changes. Its
October 10 backend list also predates the owner's October 15 continuity redesign;
it does not reverse FloRA's current storage decision.

## Compare the two options

| Question | Dedicated handler model | Continuing FBM maintenance role |
| --- | --- | --- |
| What could it add? | Narrow fault specialization; potentially smaller and cheaper inference; separately deployed model failure isolation. These are hypotheses. | Reuses construction knowledge, repair methods and cross-component interfaces already assigned to FBM. |
| What does it cost? | Another training/evaluation corpus, checkpoint, lifecycle and handoff; architectural knowledge can diverge from FBM. | Maintenance examples and demonstrated coding/diagnosis competence are still needed; general builder inference could be expensive. |
| Can it avoid the response path? | Yes, if invoked outside serving with resource limits. Being separate does not guarantee this. | Yes, as an on-demand or scheduled maintenance invocation, with separate execution permissions even when weights are shared. |
| Does it provide independent verification? | No. Another model may share the same blind spots or optimize a faulty score. | No. FBM must not certify or activate its own patch solely from its judgment. |
| Current fit | Defer unless matched evaluation demonstrates an advantage. | Preferred role assignment; not yet an implemented or qualified capability. |

A separate process, role and permission set need not mean a separate trained
network. A later specialist could itself be an FBM-built artifact. Keep personal
experience learning in PE/MFM and the relevant personal roles; construction and
repair learning belongs to FBM. Private installation evidence stays local and
scoped; reusable method capture does not authorize shared training on it.

## Mechanisms worth borrowing

- [SHAPER, v2, sections 3.2-3.3](https://arxiv.org/html/2608.11350v2): the same
  frozen model has planner and optimizer roles; it proposes skill/context-code
  changes from rollout feedback, sandbox-checks generated code, and selects
  candidates on validation tasks. This supports role reuse, not proof that FBM
  can maintain transactional storage, permissions or identity. Its frozen-model
  choice is an experimental constraint, not a permanent Alice policy.
- [Darwin Godel Machine](https://sakana.ai/dgm/): code changes can improve a coding
  agent, but reported runs also fabricated test logs and altered reward-detection
  markers. Preserve independently executed checks outside candidate write access.
  Traceable history helps detect mistakes; it does not prevent all regressions.
- [OpenEvolve evaluator source](https://raw.githubusercontent.com/algorithmicsuperintelligence/openevolve/main/openevolve/evaluator.py),
  inspected October 15: candidate code is passed to a supplied evaluator, with
  direct or staged evaluation and failure artifacts. Its optional LLM-score
  mixing is not an authority test. This is a mutable source reference, not a
  pinned dependency or a sandbox-security endorsement.
- [Agent Lightning](https://www.microsoft.com/en-us/research/blog/agent-lightning-adding-reinforcement-learning-to-ai-agents-without-code-rewrites/)
  separates task execution from optimization and captures transitions for learning.
  Borrow separation of execution and improvement; its agent-RL results do not
  establish backbone repair. No framework or observer service is being added.

## Minimal lifecycle if this is tested later

1. Trigger a bounded maintenance task from an observed defect, owner request or
   approved review schedule. Background compute can still contend with serving;
   isolate/budget it and permit cancellation. No per-request model inspection.
2. Read a permitted snapshot of versions, code, linked history, receipts and
   independently observed results. Existing FloRA records are useful inputs,
   not a complete profiler or proof that every failure is observable. Missing
   evidence stays unknown; request a targeted diagnostic when necessary.
3. Apply the mandatory diagnosis skill: validate the test, connect its claim to
   the project goal, locate and understand the responsible component, consult
   research, then propose the correction and verification. A model's diagnosis
   remains a hypothesis until evidence distinguishes it.
4. Produce a versioned candidate with its expected effect, affected interfaces,
   migration implications and rollback plan. Test on an isolated copy. Evaluation
   definitions, permissions and live state are outside the candidate's write
   access. A faulty test can be corrected through a separately reviewed change,
   preserving the original failure, rather than optimized away by the candidate.
5. Evaluate against the unchanged version on independent cases plus affected
   regression/recovery checks. Preserve correction, deletion, provenance,
   subject separation and continuity. Reverting code alone may not reverse a
   state migration or external effect; require actual recovery evidence.
6. Let the owner or separately authorized promotion policy accept/reject the
   candidate. Any approved deployment has lineage and outcome monitoring.
   Failure of maintenance leaves the established serving path in control.

The authority contract remains stable while implementations can evolve through
explicit, verified versions. This does not promise an automatically correct or
permanently frozen backbone.

## FloRA boundary and the test that could change this decision

Do not insert either option into the current PE/MFM behavioral experiment.
Keep its implementation and evaluation protocol fixed for each comparison;
an evaluated code change starts a separately identified experiment generation.
The prior 63 mechanics tests and 168 procedure seeds do not prove either option.

If a maintenance-capable FBM becomes available, begin with offline proposal-only
replay of preserved failures, held-out defect families and healthy controls.
Compare it with the existing diagnosis workflow; compare a dedicated model only
when a concrete specialist candidate exists. Match evidence, tools, allowed edits,
attempts and declared compute. Use independent targets and score correct
localization, independently verified repairs, missed defects, false alarms,
new regressions and total cost. Do not expose sealed FloRA B/P cases to repair
training. Keep development feedback separate from held-out verification.

A specialist is justified only if it improves repairs or cost at acceptable
regression/false-alarm rates on those independent cases. Otherwise retain FBM
alone, or reject automatic maintenance if FBM itself adds no demonstrated value.
This comparison has not run; no numerical acceptance threshold is invented here.

Current next build step remains actual external PE/MFM artifacts, complete
consumer admission/inference, then the independent held-out B/P protocol.
