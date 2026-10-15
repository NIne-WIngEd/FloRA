# Shared continuity core implementation plan

> Execute with superpowers:executing-plans; owner has approved construction and continuation. Mandatory diagonosis on any failure requiring diagnosis.

**Goal:** Implement the same proposed Alice canonical core in FloRA, then verify its bounded connected episode without constructing PE/MFM.

**Architecture:** Native RocksDB TransactionDB owns one commit boundary. The semantic kernel owns history, temporal state, permissions, linked updates and pending work. Existing objects, vector/graph specialists and exercised delivery/reconciliation responsibilities remain.

**Tech stack:** Python, CFFI and pinned upstream RocksDB 11.8.1; existing local Linux ARM64 Docker; existing encrypted object plane, Qdrant/Ladybug and optional exercised NATS/Temporal paths.

**Spec:** `docs/CONTINUITY_STORAGE_DECISION.md` and `docs/research/backbone-2026-10-15/ALICE_BACKBONE_HYPOTHESIS.md`.

## Global constraints

- Same storage/semantic implementation for intended Alice core and its FloRA slice; no temporary SQLite backend or transparent legacy-engine substitution.
- Preserve old code, failing evidence and pending Magnolia job. No provider/controller campaign.
- Models stay external. Native packet, evidence and time/subject meanings must survive integration.
- One local authority process, actual native transactions, tracked read generations, durable WAL commits. No blind write-batch substitution.
- Storage tests do not prove the cognitive hypothesis or full Alice scale. Latency qualification remains deferred.

## Review focus

- Native pointer/buffer ownership, exception cleanup and active handles during close (Task 1).
- Exact-key conflicts and a newly inserted contradiction not present in a prior snapshot (Tasks 1–2).
- Temporal correction and approval against the exact candidate/predecessor (Task 2).
- Projection coverage/cleanup and an external effect after crash (Tasks 2–3).
- Host/self revisions versus unchanged source-person; real content versus synthetic receipts (Task 3).

### Task 1: Native transaction substrate

Files: `src/flora/continuity/native.py`, `tests/continuity/test_continuity_native.py`, `config/continuity-native.Dockerfile`.

Interfaces: `RocksDB(path, lock_timeout_ms=1000)`; `db.transaction()` with `get(key, tracked=True)`, `put(key,value)`, `delete(key)`, `scan(prefix)`, explicit `commit`; `db.snapshot()` with `get/scan`; `db.checkpoint(path)`; checked `close`. Values are bytes. Transaction/snapshot scopes release handles deterministically. No raw base DB write handle is public.

- [x] Add and run tests: binary values, atomic multi-key rollback/reopen, tracked missing-key conflict, stable snapshot, close-with-live-handle refusal, process death before/after commit, checkpoint reopen.
- [x] Build pinned native library and implement only the needed official C API surface.
- [x] Run actual Linux ARM64 tests without mocks or missing-library skips; diagnose failures in order.
- [x] Review/commit result with exact source/library identities and limitations.

### Task 2: Semantic authority

Files: `src/flora/continuity/contracts.py`, `store.py`, `kernel.py`; `tests/continuity/test_continuity_store.py`, `test_continuity_kernel.py`.

Interfaces: actual evidence capture + formation outbox; bitemporal accepted records; typed links and current heads; consistent `ReadView` with content and generations; outside-transaction `FormationPort`/`JudgmentPort`; exact independent activation; current-authority action intent/dispatch/outcome; lifecycle propagation and restore fence.

- [x] Test the bounded valid/recorded-time and permission semantics before implementation.
- [x] Implement native tracked generation reads, typed records and complete supplied JSON envelopes. Actual native model-schema adapters remain below.
- [x] Verify stale proposals/new-evidence races, duplicate request equality, atomic mixed-subject activation, no self-approval, source withdrawal and stale database-restore refusal.
- [x] Connect authenticated source staging/outbox and explicit complete-scan coverage for this bounded slice.
- [ ] Connect retained specialist projection consumers with watermarks, hydration and cleanup when the experiment exercises discovery. Current complete scans do not qualify specialist behavior.
- [ ] Implement durable external lifecycle-floor custody and coordinated object restore before claiming complete lifecycle-safe backup/recovery.

### Task 3: Connected mechanical episode and external handoff

Files: `tests/continuity/test_continuity_episode.py`, `docs/CONTINUITY_KERNEL.md`, context and new compact FBM seed.

- [x] Actual content → computed synthetic formation/judgment → real synthetic environment change → independent mixed outcome → governed host/self revisions → new judgment after process restart.
- [x] Coherent alternative consequences, irrelevant evidence, withheld approval, false actor success, approved no-op and uncertain external effects. Exact outcome remains available when a revision is withheld.
- [ ] Qualify duplicate-root corroboration and selective-retrieval lag with the actual consumers. Preserved source-root labels and a complete scan alone do not prove these behavioral/discovery claims.
- [x] Review the entire implemented slice. Reproduce and diagnose three semantic gaps; verify corrections on the actual native engine. Existing object storage is exercised; no unchanged vector/graph/transport/workflow path is newly qualified.
- [x] Record mechanics only in context/FBM167. Final dedicated suite: 35 passing tests.
- [ ] Connect real PE/MFM input/features/output and typed-state conversion with actual artifacts; preserve full native meaning and unresolved results. Do not build those models here.
- [ ] Finish and execute the competent equal-evidence/flat-relation and held-out behavioral comparisons before claiming B or P.

Test command inside native image with repo and pinned Alice contracts read-only:
`python -B -m unittest discover -s tests/continuity -p 'test_*.py' -v`.
Private test stores use container temporary directories, not the checkout. These
physical tests are explicitly separate from the top-level legacy component CI;
they have no missing-library skip or fallback engine. See `docs/CONTINUITY_KERNEL.md`
for the measured result, deployment pins, remaining obligations and model handoff.

### Task 4: Native adapters before trained weights (owner continuation)

The owner explicitly requested finishing weight-independent backbone/adapter work.
Prior stopping at incomplete artifacts was premature: producer codecs already exist.
Continue the approved design inline; do not train or modify PE/MFM.

- [x] Separate native MFM memory acceptance from personal state activation. Carry
  exact 1.6 proposals, abstain/defer/retain-raw dispositions, source roles, sensitivity,
  subject, anchors, time and registered targets. Accept an exact native proposal
  independently; optional owner-reviewed state bindings retain full typed content.
- [x] Build PE documents from eligible content with explicit source-person versus
  host/relationship/self authority. Preserve native feature/session binding and
  collect the exact full packet from the same consumer call, without a second forward.
- [x] Add equal-evidence structured/flat comparison inputs, duplicate-root accounting
  and executable matched-result analysis; do not invent learned answers or thresholds.
- [x] Verify actual upstream schemas and tensor mechanics on CPU plus real native
  storage, including abstention, stale inputs, withdrawal, corrupted bindings and
  source-authority negatives. No training or synthetic behavioral qualification.
- [x] Fresh review, context/FBM update, then reassess remaining necessary prototype
  work. Vector/graph services are required only when discovery is exercised; full
  Alice delivery/restore/product packaging are not prerequisites for this local slice.

Contract test pins: PE247612ea38bce6711e91fe0bf7192a16549697f7 and
MFM2b0e8e936b357fe71eaf5b09dbe3302e49f474f6, read-only snapshots. Tests use
their real code. Production adapters require those modules explicitly; legacy
runtime dependency pins are not silently changed. Model artifacts remain external.

Task4 closure:63 physical tests passed; FBM168 seeded. Actual optimized checkpoint/runtime admission and held-out B/P execution remain incomplete, despite weight-independent adapters and result binding being implemented. New typed relation concepts preserve the PE source-view restrictions. Accepted native bundles use conservative atomic withdrawal to preserve local-reference lifetime. Original tests/failures remain retained.
