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

Files: `src/flora/continuity/native.py`, `tests/test_continuity_native.py`, `config/continuity-native.Dockerfile`.

Interfaces: `RocksDB(path, lock_timeout_ms=1000)`; `db.transaction()` with `get(key, tracked=True)`, `put(key,value)`, `delete(key)`, `scan(prefix)`, explicit `commit`; `db.snapshot()` with `get/scan`; `db.checkpoint(path)`; checked `close`. Values are bytes. Transaction/snapshot scopes release handles deterministically. No raw base DB write handle is public.

- [ ] Add and run tests: binary values, atomic multi-key rollback/reopen, tracked missing-key conflict, stable snapshot, close-with-live-handle refusal, process death before/after commit, checkpoint reopen.
- [ ] Build pinned native library and implement only the needed official C API surface.
- [ ] Run actual Linux ARM64 tests without mocks or missing-library skips; diagnose failures in order.
- [ ] Review/commit result with exact source/library identities and limitations.

### Task 2: Semantic authority

Files: `src/flora/continuity/contracts.py`, `store.py`, `kernel.py`; `tests/test_continuity_store.py`, `test_continuity_kernel.py`.

Interfaces: actual evidence capture + formation outbox; bitemporal accepted records; typed links and current heads; consistent `ReadView` with content and generations; outside-transaction `FormationPort`/`JudgmentPort`; exact independent activation; current-authority action intent/dispatch/outcome; lifecycle propagation and restore fence.

- [ ] Test declared semantics before implementation; original valid/recorded-time and permission cases are the contract, not a latest-value approximation.
- [ ] Implement on native tracked generation reads, preserving typed values and full external packets.
- [ ] Verify competing successor/new-evidence races, duplicate request equality, atomic mixed-subject activation, no self-approval, source withdrawal and restore.
- [ ] Connect source staging/outbox and projection coverage. Retain specialists; no undeclared query capability reduction.

### Task 3: Connected mechanical episode and external handoff

Files: `tests/test_continuity_episode.py`, `docs/CONTINUITY_KERNEL.md`, context and new compact FBM seed.

- [ ] Actual content → computed synthetic formation/judgment → real synthetic environment change → independent mixed outcome → governed host/self revisions → new judgment after process restart.
- [ ] Include coherent alternative consequences, irrelevant evidence, withheld approval, false actor success, duplicate source roots, projection lag and uncertain external effects. Exact-data source baseline remains competent.
- [ ] Review entire slice; run affected unchanged specialist tests where exercised; preserve exclusions.
- [ ] Record mechanics only. Qualified PE/MFM integration and held-out behavioral comparisons remain required; do not build those models here.

Test command inside native image with repo read-only: `python -m unittest discover -s tests -p 'test_continuity*.py' -v`. Private test stores use container temporary directories, not the checkout.
