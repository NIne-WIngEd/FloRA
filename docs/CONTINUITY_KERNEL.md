# Continuity kernel: connected mechanical slice

15 October 2026. Candidate on `Rayan/flora-continuity-core`; no cutover of the
old FloRA runtime, no model training and no Alice ratification.

## What changed

The redesign makes memory, missions and experience views of one linked history.
`ContinuityKernel` owns transitions between their distinct record types;
`ContinuityStore` publishes related records, state heads, history, retry receipts
and pending work in one native transaction. RocksDB supplies durability and
conditional transactions; it does not decide what an observation means.

The connected path is now implemented:

1. Stage authenticated original bytes; atomically publish evidence and formation work.
2. Recollect actual authorized content, typed history and current state. Seal its
   generation, permission epoch and valid-time interval; close native read handles.
3. Call an external formation port. Retain its complete JSON packet and proposed
   subject-specific changes. A proposal cannot activate itself.
4. Independently approve the exact proposal/predecessors. Publish all accepted
   changes, approval, activation and projection work together.
5. Give an external personality port the current content/state; retain its full
   supplied packet. Recheck freshness and authority before publishing judgment.
6. Record owner-authorized action separately from judgment. Persist an uncertain
   effect before returning work to an executor. An ambiguous effect is not blindly
   dispatched again after restart.
7. Capture independent post-dispatch evidence bound to the exact action. Record
   separate outcomes against each mission's exact criterion. Actor success is not
   completion; the observer remains responsible for measuring the world.
8. Propose and approve scoped revisions from the outcome, then obtain a subsequent
   judgment from the persisted history. Original source-person state stays separate.

This closes the old runtime's missing connection after its first judgment.
The [approved hypothesis](research/backbone-2026-10-15/ALICE_BACKBONE_HYPOTHESIS.md)
still governs meaning, controls and adoption. The
[storage decision](CONTINUITY_STORAGE_DECISION.md) governs responsibility placement.

## Authority and lifecycle

- One trusted local owner process owns the store. Actor names are supplied by
  that boundary, not authenticated network identities. Models receive views,
  not authority objects. This is not an untrusted-plugin sandbox.
- Accepted claims retain valid time and recorded time. Current heads and historical
  knowledge are different queries. Future activation/expiry invalidates a consumed
  current-state view even when no database write occurs.
- Global generation checks conservatively invalidate inference after any mutation,
  including insertion of evidence absent from the consumed snapshot. This may
  reject unrelated concurrent work; no concurrency/performance advantage is claimed.
- `supports`/`uses` record declared evidence. Separate `context_from` edges record
  every item offered to a model, so an uncited copied source still participates
  in withdrawal. Full-scan exposure deliberately over-invalidates in this slice.
- Withdrawal revokes current use transitively, clears affected heads without
  resurrecting an older state, cancels pending work and requests projection cleanup.
  It is not physical erasure, model unlearning or reversal of external actions.
- Record bodies, retry receipts and original objects are encrypted. Key counts,
  record identities and access patterns are not concealed. Keys are caller-held;
  key management is not a shipped consumer implementation.
- Database checkpoints can be fenced against an externally supplied lifecycle
  floor. Durable custody of that floor and coordinated object backup/restore are
  not implemented here. Historical queries cannot rewind present permissions.

## Retrieval and retained services

This bounded episode uses a complete authorized scan with exact original bytes.
That provides explicit coverage without trusting a stale index. Pending projection
refresh/cleanup is durable, but Qdrant/Ladybug consumers are not connected to this
new kernel yet. Therefore no graph/vector cleanup, selective-retrieval quality or
scale pass is claimed. Existing modules and tests remain preserved.

Direct local intake does not exercise NATS or multi-device delivery. The effect
state machine does not replace Temporal's workflow/reconciliation responsibilities.
No old Kurrent physical positions have been migrated. No SQL-backed canonical
authority is used by this candidate.

## Earlier core verification and its limits

**35 tests passed** on the actual native RocksDB 11.8.1 library, local Linux ARM64
Docker, with networking disabled and source/contract mounts read-only:
9 native/configuration, 7 store, 15 kernel and 4 connected-episode tests.
Image ID: `sha256:3e05b07ce7c63ce0ecf734f78c616db441dce2848bd5cafec40bea29c88418dc`.
Native source: `abeebd9630f11bd08c28b7bd43c7bdfc62050654`.

The comic-derived episode executes a real file-based synthetic environment. Its
independent reader finds project success and a missed research deadline; approved
host workload and self project-value revisions change a fresh-process judgment.
Alternative consequences, irrelevant detail, withheld approval and approved no-op
controls are present. The original outcome remains available when approval is
withheld. The source-person anchor remains unchanged.

Both model doubles compute from actual content, but deliberately use simple
arithmetic. They establish sequencing, persistence and authority only. In
particular, their state-consuming policy cannot demonstrate that persistent
revision outperforms rereading raw outcomes. No B/P behavioral claim follows.

Tests also cover atomic mixed-subject rollback, retry identity, encryption/key
scope, two time axes, permission changes during inference, newly inserted
contradictions, source-person revision refusal, transitive withdrawal, stale restore
refusal and unknown-effect non-repetition. Native process death is tested before
and after completed commit, not during a commit or simulated power loss.

Review found three real gaps missed by the initial tests: uncited input exposure,
time-only state changes, and observation/action chronology. All were reproduced,
diagnosed in order, corrected and verified with positive controls. Original RED
evidence and the eight-step diagnoses remain in the local SDD ledger; the final
test output is also retained in `docs/evidence/2026-10-15_continuity_core_tests.txt`.
Primary mechanisms consulted: [Hindsight source validation](https://github.com/vectorize-io/hindsight/blob/79303b6729f573a253a5f606324ab6274ef59d97/hindsight-api-slim/hindsight_api/engine/consolidation/consolidator.py),
[XTDB time semantics](https://docs.xtdb.com/about/time-in-xtdb.html), and
[W3C provenance chronology](https://www.w3.org/TR/prov-constraints/#generation-precedes-usage).
These sources inform specific guarantees, not the entire Alice hypothesis.

Physical suites live in `tests/continuity/` and deliberately fail if invoked
without their native dependency. They are separate from the existing top-level
component CI; there is no silent alternate engine or missing-library skip.

Run inside the prepared image, with this checkout at `/flora` and the retained
Alice `4f287a488bc908bd04f99255ee01b794bacba50b` source at `/alice`:

```sh
python -B -m unittest discover -s tests/continuity -p 'test_continuity*.py' -v
```

The optional `continuity` dependency supplies CFFI. The pinned native build is in
`config/continuity-native.Dockerfile`; its existing base image and pinned source
archive are required. This is a local development build, not portable release
packaging or a new GitHub CI qualification. Runtime duration is not a latency gate.

## Native adapters and current verification

The weight-independent integration is now implemented; stopping earlier solely
because model training was unfinished was premature.

- `NativeFormationPort` builds actual MFM1.6 context, opens exact evidence bytes,
  validates the full native output, and resolves current subject/governance
  references. A trusted external runtime returns native output; optional
  `NativeFormationResult` declares newly allocated local uncertainty names.
- `capture_native` preserves explicit source role, subject, modality and sensitivity.
  `bind_native_subject` independently enrolls a domain's subject; storage scope IDs
  are not silently treated as people. `register_native_target` handles actual
  entity/scene/workspace targets; missions are already typed records.
- `form_native` stages the exact candidate. `accept_native` independently accepts
  typed memories and abstain/defer/retain-raw dispositions. Optional state bindings
  must match the enrolled subject and predecessor. Native proposal content remains
  intact. Request memories do not execute deletion/revocation commands.
- Local proposal/value/uncertainty references retain a resolved accepted-bundle
  namespace, including forward references and cycles. This bounded implementation
  withdraws the entire accepted bundle atomically if any member or its namespace
  becomes unavailable; related claims also become unavailable. This deliberately
  over-invalidates rather than claiming fine-grained independent retention.
- `NativePersonalityPort` builds a real native document from original content,
  provenance/time descriptions, current state and registered relation meanings.
  Pointer IDs stay in native metadata. Source-person identity authority is explicit;
  host/relationship/self context does not silently acquire it. Relation concepts
  follow PE's separate authority views; no evaluator-derived causal links are added.
- An external feature producer supplies real `ProducedFrame` and closed-session
  receipts; the external consumer owns optimized checkpoint admission. A temporary
  forward hook retains the full tensor packet from that same call, alongside the
  native downstream codec. The response/document/features/session digests must
  match. No second inference or model modification is used.
- Full audit custody remains encrypted in storage. A versioned semantic projection
  exposes evidence, typed decisions, uncertainty and relationships without feeding
  tensor archives or feature receipts back as model prose. Source ancestry travels
  through hidden proposal/approval history; overlapping roots are conservatively
  grouped by both adapters. This is not an independence or confidence estimator.
- Native question/candidate/label/representation configuration is snapshotted and
  bound into the operation receipt. Legacy capture retries retain their original
  fingerprint when no native policy is supplied.

**63 tests passed** in the final dedicated physical suite with pinned RocksDB11.8.1
and CPU PyTorch2.10.0, network disabled and source mounts read-only. Evidence:
[full output](evidence/2026-10-15_native_adapter_tests.txt) and
[ordered diagnoses](evidence/2026-10-15_native_adapter_diagnosis.md).
FBM168 records the reusable method, original failures and limits as a partial,
procedure-only seed. It is not admitted training data or learned FBM capability.

Coverage comprises the previous 35 native/store/kernel/episode tests plus 28 native
adapter/comparison tests. The native connected episode executes an actual synthetic
world action, independently measures project success and research failure, accepts
separate host/self proposals, reopens storage and runs native PE tensor mechanics
again. Source-person evidence stays unchanged. The previous synthetic episode also
tests fresh-process continuity and coherent alternative outcomes.

PE positives use the real upstream model/feature/document/output mechanics with
untrained tensors, a content-reading feature fixture and a fixture response shell.
Actual `DecisionConsumer.respond` negatives test corrupted feature/session refusal;
the valid control reaches its real artifact-admission boundary. **Successful
optimized consumer admission/inference has not been exercised.** MFM outputs are
explicit content-reading fixtures through real native schemas and authority gates.
No trained judgment, outcome-sensitive learning, latency, B or P pass follows.

### Reproduce the physical profile

`config/continuity-adapters.Dockerfile` extends the existing pinned native image
with CPU PyTorch. Exact contract archives, native pin and inspected image ID are in
`config/continuity-adapter-pins.json`. This is a separate explicit profile; the
legacy Alice dependency pin and old runtime remain unchanged.

Read-only mounts in the network-disabled container:

- This checkout at `/flora`.
- PE source archive at `/pe`, commit `247612ea38bce6711e91fe0bf7192a16549697f7`.
- MFM source archive at `/mfm`, commit `2b0e8e936b357fe71eaf5b09dbe3302e49f474f6`.

Run `python -B -m unittest discover -s tests/continuity -p 'test_*.py' -v`.
The image sets the source import paths. Stores and synthetic worlds live in private
container temporary directories. No missing-library skip or replacement engine is
used. This is local physical verification, not the old GitHub CI matrix or a portable
consumer release.

### Comparison preparation and remaining boundary

`matched_documents` provides B's structured/flat inputs with identical source,
concept, candidate, label and relation meaning. Only native graph edges differ.
`backbone_case` freezes both documents, the same model identity, independent rubric
digest and call budget. `comparison_case` separately freezes P's common evidence
and the distinct FloRA/Gemma model identities. The challenger remains a separate
system. `compare_results` rejects missing/duplicate arms, changed inputs/models,
wrong rubrics, invalid scores and budget mismatches; unresolved pairs remain in the
denominator. It produces descriptive counts, never a qualification verdict.

This does not execute the challenger or authenticate external evaluator assertions.
Actual consumption, matching of full prior histories/training resources, independent
scoring and calibrated held-out effect estimates remain obligations of the experiment.
The [approved protocol](research/backbone-2026-10-15/ALICE_BACKBONE_HYPOTHESIS.md)
requires coherent alternative worlds, irrelevant controls, blinded evaluation,
held-out scenario families and pilot-calibrated thresholds before sealed B/P runs.

The next meaningful integration requires external PE optimized checkpoint/feature
artifacts and the finished MFM native runtime/export, then their actual admission
and inference. Neither model is trained or replaced here. Test full native outcomes
and unresolved cases first; then pilot/freeze the held-out evaluation and run B/P.
Additional selective indexes, transport/workflow services or a conversation model
are not needed merely to run the bounded local episode. Their unexercised full-Alice
responsibilities remain explicitly unqualified, as do complete erasure/backup,
multimodal development, scalability and consumer packaging. Latency work remains
deferred under the owner's instruction.
