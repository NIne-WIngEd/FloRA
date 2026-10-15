# Shared Alice/FloRA storage decision — 15 October 2026

Owner-approved direction: prototype the continuity kernel in FloRA; keep PE and MFM in their own workstreams. Subsequent owner correction: choose the storage foundation for Alice, exercise that same implementation in FloRA, and do not discard the responsibilities previously served by separate engines. SQLite is rejected as the implementation target. Its isolated candidate remains at `Rayan/flora-sqlite-reference`, commit `dae5766`; eight component tests passed, no connected loop or learned claim passed.

## Decision

Use **RocksDB TransactionDB, WriteCommitted**, as the canonical storage substrate beneath the Alice-owned continuity kernel. First native pin: upstream **v11.8.1**, commit `abeebd9630f11bd08c28b7bd43c7bdfc62050654`. FloRA and the intended Alice core use the same semantic API, record format and commit protocol. This is an implementation choice to test, not a measured performance win or full-Alice qualification.

Keep **encrypted original-object storage, Qdrant and Ladybug** as separate specialist planes. Keep existing **NATS ingress and Temporal/PostgreSQL reconciliation** modules and their valid tests. Deploy them when the corresponding workflow is exercised. No old module is deleted or relabeled as replaced by the presence of a RocksDB library.

RocksDB is chosen over LMDB for the intended growing mutable corpus and native transaction/concurrency options. LMDB is a credible simpler alternative, not incapable; Alice's actual throughput/volume requirements remain unmeasured. RocksDB costs native deployment, compaction resources, key/index design and application-owned temporal semantics. The intentional per-owner publication fence remains initially; changing engine does not remove it.

## Responsibility conservation

| Existing plane | Required capability | Successor placement and proof obligation |
| --- | --- | --- |
| KurrentDB | Scoped event identity, expected revision, order, durable acknowledgement, replay, committed time | Kernel semantic event log in RocksDB. Explicit sequence, commit time and retry receipts; engine WAL is not the event history. Old physical positions require an explicit migration map. |
| XTDB | Claims, two time axes, exact predecessors, permissions, independent approval and state activation | Versioned kernel records, temporal indexes and accepted-state heads in the same transaction as event/lineage changes. Neither a latest-value map nor RocksDB snapshots replace bitemporal history. |
| Ladybug | Evidence/claim relations, graph discovery, authority-checked hydration and obsolete-index cleanup | Retained derived graph. Canonical typed edges and dependency indexes are kernel records; graph hits are candidates. |
| Qdrant | Semantic retrieval for current claims and original-history comparator | Retained derived vector retrieval. Preserve the strong comparator's lexical/correction/ancestry behavior and equal evidence opportunity. |
| NATS JetStream | Device buffering, durable delivery/deduplication, canonical commit before acknowledgement | Retain existing ingress module. Direct local input may bypass transport; that does not qualify multi-device delivery. |
| Temporal + PostgreSQL | Durable workflows, retries, restart and exact-head graph/vector cleanup | Retain exercised reconciliation/workflow capability and its supported persistence. A kernel outbox publishes work atomically; it is not a replacement workflow engine. |
| Valkey / NebulaGraph | Optional shared cache / distributed graph placement in full Alice | Not implemented FloRA stores today. Preserve roles; no claim this prototype replaces or qualifies them. |
| Encrypted object plane | Authenticated original bytes and artifacts | Retain separate staging before canonical reference publication. Storage snapshots cannot atomically commit external files; deletion/backup handling requires explicit lifecycle work. |

The intended consolidation is **two canonical authorities into one coherent publication boundary**, not every specialist responsibility into one key/value engine. All planes can run under owner control; using their software does not require hosted vendor accounts.

## Shared commit contract

1. Stage authenticated evidence durably before publishing its reference. Capture event and pending formation work together.
2. Materialize actual authorized content from a consistent view; retain source roots, stream/state revisions, permission/lifecycle epochs and query coverage. Release engine handles before model inference.
3. Begin a short native transaction. `GetForUpdate` the owner generation, authority/lifecycle generations and exact predecessor keys. Compare the complete bound read basis. An ordinary `Get`, iterator or snapshot alone is insufficient.
4. Apply accepted records, typed edges, temporal indexes, heads, exact approval, semantic event/sequence, idempotency receipt and outbox changes atomically. Update every affected generation.
5. Keep WAL enabled and synchronous authoritative commits. Failure returns no accepted state. A successful external action still needs independent observed consequences; unknown effects are reconciled instead of blindly repeated.
6. Qdrant/Ladybug publish coverage watermarks. Missing projection coverage requires an authoritative tail read, catch-up or explicit incompleteness. Fresh returned hits alone cannot rule out an omitted new contradiction.

Owner-generation locking is deliberately conservative: unrelated writes can reject inference. Predicate-level concurrency is later work requiring proof of coverage. No distributed atomicity, full unlearning, automatic replication or free engine substitution is claimed.

## Implementation and verification boundary

Use the official native C API through a bounded CFFI adapter, with the native library pinned above. It exposes actual TransactionDB transactions, tracked reads, snapshots and checkpoints. Do not substitute RocksDict `WriteBatch` for conditional transactions. Bind native handle ownership, buffer lengths, errors and destructor lifetimes explicitly.

The binding has a bounded lock-wait configuration for conflict resolution, not an end-to-end response deadline. Its process-death test covers exit before/after completed commit, not power loss or interruption inside a native commit. Its checkpoint test covers database records, not external objects or lifecycle-safe restore.

Initial execution target: existing local Docker Linux ARM64. Native Windows ARM64 packaging is unverified; Linux development execution does not establish desktop release support. The model and storage API remain the same. No external compute job or provider-control script is required.

First checks on this actual engine: atomic multi-record commit/reopen; rollback and process death; stable retry identity; stale predecessor; new-record insertion race; permission/deletion race; correct historical/current time queries; consistent projection gaps; durable effect ambiguity and recovery. Then the comic-derived mixed-outcome episode with actual content and external model ports. Synthetic model doubles prove mechanics only.

Before a behavioral claim, connect qualified PE/MFM artifacts, preserve their full native packets and current schema semantics, and execute the outcome/irrelevance/representation controls and separate personalized-Gemma comparison. FloRA supports only the exercised slice of Alice; larger-scale and distributed behavior remain separate qualifications.

## Evidence

- Source responsibility audit: `docs/research/backbone-2026-10-15/current-architecture.md`, with correction: Temporal also owns real index-cleanup workflow in `src/flora/selected/derived_reconciliation.py:23-88`, not merely a restart probe.
- Requirements: `docs/research/backbone-2026-10-15/requirements.md`; original approved hypothesis in the same directory. This document supersedes their provisional physical-engine choices, not their semantic commitments.
- [RocksDB transaction semantics](https://github.com/facebook/rocksdb/wiki/Transactions), [atomic column-family updates](https://github.com/facebook/rocksdb/wiki/Column-Families), [durability](https://github.com/facebook/rocksdb/wiki/Basic-Operations).
- [Pinned native API](https://github.com/facebook/rocksdb/blob/abeebd9630f11bd08c28b7bd43c7bdfc62050654/include/rocksdb/c.h), [platform requirements](https://github.com/facebook/rocksdb/wiki/Platform-Requirements), [backup and restore](https://github.com/facebook/rocksdb/wiki/How-to-backup-RocksDB).
- [LMDB alternative and its reader/writer constraints](https://lmdb.readthedocs.io/en/latest/), [RocksDB write stalls](https://github.com/facebook/rocksdb/wiki/Write-Stalls).

Research establishes feasible primitives and costs. No Alice-scale benchmark has been reproduced and no storage choice has proved the cognitive hypothesis.
