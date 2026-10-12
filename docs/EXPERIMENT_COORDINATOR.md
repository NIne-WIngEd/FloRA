# Registered experiment coordinator

`RegisteredExperimentCoordinator` connects the selected experiment infrastructure without building personality, MFM, FBM, or a substitute judge. It starts from an **already registered cohort, recipe, original histories, shared questions, and complete paired plan**. It does not invent experiment material or outcomes.

This version coordinates **prepared before/after histories**. The full plan already includes the after history and intervention. It does not claim to preregister an unknown future outcome; the separate pilot lifecycle handles live update custody.

## What it freezes

- One actual host, namespace, XTDB connection, Kurrent log, encrypted object plane and owner permission policy across cohort, comparison, evidence and assessment controllers.
- The exact registered cohort and limited-builder recipe. The protocol must bind the recipe's actual encrypted content digest.
- The complete case × before/after × three-arm binding matrix. Both native arms have explicit frozen native plans, distinct archive identities, invocation IDs, actual context plans, worker headers and checkpoint bindings.
- The exact local cohort entry sequence behind each original history, plus the original source for each shared question. `authorized_history` and `question` are the admitted intake roles; private targets and rubrics have no inference intake route.
- Predeclared comparator task IDs, so retries cannot silently create another paid request under a different name.
- The actual selected phase router configuration. Header hashes describe configuration; actual historical artifacts, producer phase/update proofs and current owner/source authority establish use eligibility.

Foreign cohort sources stay private typed dependencies. Their IDs are not fabricated as local canonical parents, and local capture permission cannot create another host's consent.

## Concrete stages

| Call | Durable result | Meaning |
| --- | --- | --- |
| `prepare()` | Exact encrypted coordinator binding | Registered infrastructure configuration |
| `readiness(adapters=...)` | Fresh encrypted preflight with sanitized missing-port reasons | `preflight_blocked` or actual supplied ports are currently usable; no inference |
| `await execute(adapters=...)` | Running marker, then actual paired run and completion control | Six attempts per case retained, including failures; custody mechanics |
| `recover_interrupted()` | Exact existing interrupted control or metadata reconciliation | Preserves provisional native/provider receipts; never reruns inference |
| `bind_sealed_assessment(collection_id=...)` | Exact run, blind-pack, supplied spec and independently authenticated seal references | `externally_sealed`; **not an accepted Part 1 result** |
| `recover_stage(artifact_id=...)` | Dedicated current-authority private recovery | Controls cannot open through generic comparison/history routes |

Actual assessment rubrics, thresholds, assignments, reviewer signatures and result qualification remain supplied independently. The coordinator does not choose favorable thresholds or infer behavioral scores. A seal is necessary custody evidence, not proof that FloRA's claim succeeded. Accepted Part 1 material must still pass the independent typed result qualification in [experiment manifests](EXPERIMENT_MANIFEST_CUSTODY.md).

## Required supplied services

- Two actual `NativeArmAdapter` instances matching the frozen native plans, each with its independently qualified process worker, producer codec, concrete owned selected read service and independent meter.
- An actual `SelectedPhaseLineageRouter` resolving each native case/phase/arm through actual historical selected authority and producer proofs. Build an original-history evidence policy first, then the router, then execution evidence using that router; identical Python policy objects are not required for that construction sequence.
- An actual `GeneralMemoryArmAdapter` with exact frozen configuration, actual selected recorder and independently enrolled signed provider-attempt ledger. External transfer, local attempt capture and private audit permissions remain separate. No native feature-packet encoder or privacy guarantee is invented here.
- Actual owner grants for the original phase evaluation sources, cohort/recipe reading, and the separate `coordinator_purpose(experiment_id, run_id, "capture"|"read")` on relevant registered controls and their actual local parent closure. Registration creates no grant. New parent controls require explicit authorized grants before later stages.

Missing dependencies produce blocked preflight; there is no default general model or fake native judgment. The coordinator never obtains credentials, downloads models or initiates an API request on its own.

## Current authority and interruptions

- Every private coordinator read checks exact immutable metadata, actual cohort/recipe dependencies, original evaluation grants, independent control purpose and relevant current phase qualification. Checks surround the actual ciphertext backend access and run before AEAD decryption.
- Phase qualification uses copied router/runtime/qualification/owner-proof planes with the same current cohort fence. Slow qualification cannot open bytes after a foreign cohort dependency was withdrawn.
- Concrete native read services use a fenced factory on their exclusively owned, bounded SELECT-only connection. Cohort/recipe/source metadata is rebound onto that connection before the owned runtime and phase resolver open private bytes. The shared encrypted plane is never mutated. Cohort dependencies on separate databases remain blocked until separately owned backend read ports are supplied.
- Selected comparison writes use copied guarded planes and a canonical append guard after clock, revision and slow dependency checks. Current authority is not an allow cache.
- Starting a run records a unique nonce under an immutable running identity before inference. A second call cannot rerun the same frozen invocation or erase failed receipts. An interrupted run requires explicit recovery.
- Cancellation propagates and performs no further inference, raw reads or writes in its cancelled continuation. The existing running marker and independently captured native/provider custody remain available to a later authorized reconciliation.
- Error controls contain machine reason codes and registered receipt IDs, not exception messages, prompts or private payloads. Lost source/capture authority may prevent final control writes; existing canonical receipts are retained rather than bypassing consent.

## Validation boundary

Local tests use fictional selected row/log ports and real local encryption. They verify denied plaintext access, withdrawal during actual ciphertext fetch, final preappend checks, exact physical controller identity, source-role mapping, owned metadata reads, missing ports, cancellation and immutable interrupted recovery. One explicitly marked mechanical fixture retains six unavailable attempts and proves no behavioral result.

`tests/integration/test_selected_experiment_coordinator.py` prepares actual XTDB/Kurrent/encrypted-object registration, signed owner grants, blocked preflight and private recovery. Its physical CI result remains separate from model qualification or experiment success. No learned model, consumer latency measurement, independently accepted Part 1 result or FBM transfer result is produced by this work.

### October4 test-purpose audit and next connected case

The frozen goal requires relevant correction/outcome change, irrelevant stability,
a serious general-model-with-memory comparison, same-evidence attribution and
isolated builder transfer. The current physical cases cover subsets of that
infrastructure. A green suite is not a completed behavioral experiment.

The two-stage preregistration test performs actual BEFORE sealing, changed Claim,
state and artifact heads, qualified AFTER capture and four native routes. Its
fictional signed producer proves the interfaces and chronology, not a learned
update. Finalization rejects unequal captured context digests across full FloRA
and ablation. The paired runner's separate contract test independently asserts
equal actual context digests and all six attempts. The physical coordinator case
supplies no adapters and asserts blocked preflight; it does not execute that
same two-stage case through the three-arm runner. Do not combine these separate
passes into a claim that this complete connection has been verified.

The next bounded integration case should retain one actual registered two-stage
history and its final authority, then supply the existing two NativeArmAdapter
ports and GeneralMemoryArmAdapter to RegisteredExperimentCoordinator. Use actual
owned selected readers, process/codec/meter contracts, the enrolled provider-attempt
ledger and explicit independently scoped grants. Supplied fictional outputs must
remain labeled transport/contract fixtures; no general-purpose fake judge or
permission bypass may replace these ports.

| Check | Independent observable assertion | Meaning of a failure |
| --- | --- | --- |
| Setup/control | Exact sources and signed purposes authenticate; unchanged operation succeeds before an adversarial callback | Setup refusal is not the target regression |
| Chronology | BEFORE uses original immutable heads; update follows its seal/gate; AFTER full uses changed heads and ablation retains original judgment checkpoint | Frozen phase or treatment routing defect |
| Comparison | Same original history and task per phase; byte/content-equivalent selected context for full/ablation; baseline selects from equal authorized originals | Unequal evidence invalidates attribution |
| Execution | Two phases × three arms produce six persisted attempts, including refused, unavailable, invalid and timed-out outcomes | Omitted attempt invalidates denominators |
| Recovery | Exact attempt identities and payloads recover without inference, new provider dispatch or replayed writes | Passive recovery or idempotency defect |
| Withdrawal/tampering | Passing authorized control first; exact mutation point is reached; independently revoke H or C; no later forbidden private read/dispatch/append | Concrete authority-boundary defect; do not infer it from setup alone |
| Qualification | Fixture results remain contract evidence; behavioral scoring waits for qualified external producers, pilot/frozen cohort and blind assessment | A fixture pass cannot establish learning or baseline superiority |

Every negative variant must use a fresh declared case/run identity; it must not
retry an already completed inference under the same frozen identity. Keep source,
cohort and ancestry separation, current independent H/C checks, exact final binding
and all frozen response/deadline budgets. Relevant, irrelevant and outcome quality,
baseline competence, uncertainty and builder transfer require their own actual
producer/evaluation evidence; this first connected case must not impersonate them.

A source/read-only Linux discovery audit also found the new callback-owner module
collects19 cases: its one new H regression plus nine imported and nine inherited
fixture tests already covered in phase snapshots. This is repeated suite work,
not19 new coverage cases or a runtime latency diagnosis. Keep the current CI source
frozen; isolate the single new regression in the next test change without modifying
its successful control, mutation trigger or protected-effect assertions.
