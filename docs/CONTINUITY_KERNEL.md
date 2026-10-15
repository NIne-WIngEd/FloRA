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

## Verification and its limits

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
python -B -m unittest discover -s tests/continuity -p 'test_*.py' -v
```

The optional `continuity` dependency supplies CFFI. The pinned native build is in
`config/continuity-native.Dockerfile`; its existing base image and pinned source
archive are required. This is a local development build, not portable release
packaging or a new GitHub CI qualification. Runtime duration is not a latency gate.

## Next integration boundary

`FormationPort` and `JudgmentPort` are transport envelopes, not substitutes for
the native model schemas. Merely putting a native packet under `native_output`
does not preserve its meaning in active state. Real adapters remain to connect.

Read-only producer inspection on October 15 found:

- PE at `247612ea38bce6711e91fe0bf7192a16549697f7` requires a validated
  `CognitiveFrameDocument`, actual `ProducedFrame`, closed feature session and
  checkpoint lineage. `DecisionConsumer.respond` returns expressive decisions
  and construction receipts, but only a digest of the complete native tensor
  packet. Full packet custody must be supplied by the integration route; no hash
  or selected response can stand in for the native judgment. Its chat still
  reports the cumulative N1/N2 result pending and full capability unqualified.
- MFM at `2b0e8e936b357fe71eaf5b09dbe3302e49f474f6` retains the 1.5 base and
  additive 1.6 proposal semantics: anchors, subject, time, epistemic status,
  dispositions and other typed values. Its existing P2 bridge explicitly rejects
  richer semantics and is not a reusable complete FloRA adapter. The model chat
  reports full-source export/training still in progress.

Next: bind the actual producer artifacts and current source/feature/output
contracts to this kernel; validate semantic conversion against those artifacts.
Preserve unsupported/unknown output as unresolved rather than invent a state
update. Keep PE/MFM development in their chats. An unqualified artifact may support
explicitly labeled integration construction; it cannot support a qualification claim.

Then finish the exact-evidence/flat-relation controls and held-out behavioral
protocol before B (backbone contribution) and P (separate personalized-Gemma
comparison). Add specialist retrieval only for scenarios that exercise discovery,
with coverage and cleanup verified. The 35 passes do not make full FloRA complete.
