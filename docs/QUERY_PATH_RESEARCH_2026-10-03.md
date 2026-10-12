# FloRA query-path research — 2026-10-03 local / October 4 UTC

The owner asked whether SQL querying is the best design and whether the query
path explains latency. This comparison retains the narrow prototype scope.
Personality and MFM remain external producers. It introduces no serving change,
new engine, diagnostic job, model or response-budget adjustment.

## Findings and limits

SQL is the selected XTDB query interface for Claims, state and permission
metadata. It is not evidence that a new generic relational memory architecture
was introduced. Temporal's PostgreSQL workflow storage has a separate role.
There is no evidence establishing this query path as the best possible path,
or establishing SQL syntax itself as the source of FloRA's response failures.

The completed bf494970 push/PR receipts locate native cancellation during
`prepare`, before inference. The corrected assembly regression attributes
22,425 SQL calls to nested whole-H verification under pure assembly, outside
the fresh private-read barriers. That is a controlled adapter-fixture count,
not a count from the live server or a predicted speedup. It demonstrates a
composition defect: already sampled metadata was followed by original phase
predicates that repeatedly reconstructed the history.

The existing bounded candidate supplies native sampled views only during
assembly and expires them on every exit. Every actual object and independent
owner proof still passes fresh original H/C checks; the joint terminal fence
remains. Its115 relevant cases pass in901.715s at the receipt's exact hashes,
and the scoped review is clear. Physical response qualification remains open.

## Exact selected engine, not current-main assumptions

The selected image is XTDB2.1.0. GitHub's annotated tag resolves to
`ca78d5609dfa7393c465c1e1435a8f20fa3eb371`; its recursive tree was untruncated.
Original source files were retrieved at that commit, not from current main.

- [SQL parser](https://github.com/xtdb/xtdb/blob/ca78d5609dfa7393c465c1e1435a8f20fa3eb371/core/src/main/kotlin/xtdb/query/SqlParser.kt#L61)
  caches single and multi-statement parsed forms, each with4096 entries.
- [Query source](https://github.com/xtdb/xtdb/blob/ca78d5609dfa7393c465c1e1435a8f20fa3eb371/core/src/main/clojure/xtdb/query.clj#L281)
  caches plans using parsed query, relevant options and table information;
  emitted-query reuse also binds scan fields, blocks, parameter fields and timezone.
- [pgwire preparation](https://github.com/xtdb/xtdb/blob/ca78d5609dfa7393c465c1e1435a8f20fa3eb371/core/src/main/clojure/xtdb/pgwire.clj#L951)
  resolves result columns and [binding](https://github.com/xtdb/xtdb/blob/ca78d5609dfa7393c465c1e1435a8f20fa3eb371/core/src/main/clojure/xtdb/pgwire.clj#L1081)
  rejects changed result shapes. FloRA's `configure_xtdb_connection` disables
  driver automatic preparation for discovered table shapes. This does not
  disable the server caches above; cache existence also does not prove cache hits.
- The pinned [engine tour](https://github.com/xtdb/xtdb/blob/ca78d5609dfa7393c465c1e1435a8f20fa3eb371/dev/doc/high-level-tour.adoc#L108)
  says SQL and XTQL converge on the same logical-plan/execution pipeline.
  Changing the language alone would not remove application-level repeated work.

The [2.1.0 release](https://github.com/xtdb/xtdb/releases/tag/v2.1.0)
already supplies EXPLAIN ANALYZE and query tracing. These can distinguish
server scan/operator time from client reconstruction and many round trips if
completed ordinary gates leave a material query-route decision unresolved.
This research does not dispatch another diagnostic or make profiling a default.

The [2.2.0-rc0 release](https://github.com/xtdb/xtdb/releases/tag/v2.2.0-rc0),
published July21,2026, introduces Arrow ADBC/Flight SQL, reducing Arrow-to-row
conversion for bulk analytical reads. That is a new transport for SQL, not a
replacement for the work requested. It is not a drop-in feature of2.1.0, and
its bulk-read motivation is not proof that FloRA's small authority queries
would benefit. The release also lists compatibility changes. No upgrade is proposed.

## Comparable implementations and frontier memory work

| Primary source reviewed | Useful mechanism | FloRA boundary |
| --- | --- | --- |
| [Graphify cache](https://github.com/Graphify-Labs/graphify/blob/eaaec1abd99d3a7fb30301ccb49f4cc72ae34011/graphify/cache.py) | Extraction reuse is keyed to source and extractor/schema or prompt identity. | Reuse exact derived dependency work; preserve complete-byte provenance. Its Markdown hashing omits frontmatter and cannot replace FloRA's identity contract. No cached grant. |
| [Graphiti search](https://github.com/getzep/graphiti/blob/4f62cfe7a2d519e55bfdf2dc4a2fd06649dc00b3/graphiti_core/search/search.py) | One supplied/computed query vector serves enabled routes; candidates are UUID-deduplicated, with candidate and BFS-depth limits. | Bound selected evidence and share compatible derived inputs. This ranks candidates; it does not verify current source rights. |
| [MemForest](https://arxiv.org/html/2605.23986v2), sections3.1–3.3 and4 | Persistent source facts are separate from derived summaries/embeddings; local edits refresh affected paths, and queries recall scopes then descend to evidence. | Keep canonical evidence and current state linked; avoid replaying all history for normal current reads. A new forest/tree platform is unnecessary for this prototype. |
| [MAGMA](https://aclanthology.org/2026.acl-long.1709.pdf), sections3.1–3.4 | Query intent selects bounded retrieval views; fast ingestion is separate from asynchronous consolidation. | Keep response preparation bounded and separate eligible derived maintenance. Current withdrawal and terminal checks remain synchronous; inferred causal edges do not become ledger authority. |

Retrieval-Driven Memory Reconsolidation was also inspected through its
[construction and retrieval sections](https://arxiv.org/html/2609.16053).
Its adaptive graph expansion and memory evolution concern retrieval quality;
they do not establish a faster XTDB interface or license semantic rewriting of
accepted Claims. Model inference/KV optimization cannot repair a timeout that
occurs before inference; no model work is moved into FloRA.

## Decision for the existing build

1. Keep the selected XTDB adapter and version while testing the already reviewed
   composition. Do not relabel SQL as the cause or switch databases blindly.
2. Serve necessary current nominations from bounded current material within
   one invocation. Keep fresh private-read and terminal rights/source fences.
3. Keep explicit historical reconstruction separate from normal current
   preparation. Immutable proof dependencies can be shared only at exact identity.
4. Preserve separate comparator cold-construction/retrieval costs and BEFORE/AFTER
   namespaces. Neither comparator cost nor passive recovery is fixed by this change.
5. Consider a query projection, preparation lifecycle or transport change only
   when actual route-specific evidence justifies it. One snapshot or a saved
   positive permission decision cannot stand in for live withdrawal checks.

This follows Alice [Memory Performance and Reliability Standard sections4–6](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/8ea804aa25c3d1c5f46e9be5810d072ed0fadb4b/docs/MEMORY_PERFORMANCE_AND_RELIABILITY_STANDARD.md)
and the original current-materialization boundary recorded in the minimal
invocation plan. Experience/Evidence/Claim/state/judgment/correction/outcome
links remain necessary semantic connections, without adding full mission infrastructure.

## Research provenance

Exa discovery used25 candidate hits across four independent questions. The
recent-paper window was2025-10-03 through2026-10-03; older foundations and
implementation version pins are separate. Counts describe discovery, not25
complete paper reviews. Selected primary release notes, paper method sections
and original source files were fetched. Graphify/Graphiti source pins were
rechecked from the existing research record. Private fetches and source copies
remain scratch artifacts. No reported paper speedup is transferred to FloRA.

## Refreshed Alice frontier-watch — October 3 local

The owner's requested branch review fetched original
`research/frontier-watch@bd04f9c6147ab27178508f3bd45e50cffaeca19f`, advancing
froma0e6d805. Targeted current-impact remainsf813268f; canonical main remains
8ea804aa. Alice's runtime API remains4f287a. The frontier branch is a research
intake, not an adopted production contract. Its execution guardrail classifies
findings by actual applicability and rejects automatic architecture changes.

The original [October2 intake](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/bd04f9c6147ab27178508f3bd45e50cffaeca19f/docs/research/FRONTIER_WATCH_INTAKE_2026-10-02.md)
and [October3 outcome intake](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/bd04f9c6147ab27178508f3bd45e50cffaeca19f/docs/research/FRONTIER_WATCH_INTAKE_2026-10-03_VERIFIED_MISSION_STATE_AND_OUTCOME_GATED_LEARNING.md)
were read before judging the FloRA slice.

- [MemFit](https://arxiv.org/pdf/2610.00872), methods3.2–3.3, keeps exact episodes
  retrievable behind provenance-linked summaries and separates index construction
  from answering. This corroborates source-native bounded reads. Its no-delete
  policy cannot transfer to FloRA's deletion/withdrawal contract, and its selected
  retrieval constants and QA gains are not FloRA qualification.
- [StructAgent](https://arxiv.org/html/2607.11388v1), section3.1 and appendixC,
  lets actors propose progress while verification-backed decisions commit or
  invalidate it. Its boundary verification uses current task state and grounded
  postconditions. This supports compact linked state and independent outcome
  authority; it does not justify installing a new multi-model mission harness.
- The intake's LongHorizon-Harness and RSIAgent findings were reviewed as branch
  research, not independently re-qualified here. The relevant rule is to retain
  failed/unverified Experience while separating verified-success promotion.
- FOCUS, LatentHarness and retrieval-layer continual learning are future
  compression/scheduling/evaluation challengers. No such model or full workspace
  implementation is introduced into this prototype.

FloRA's actual `decision_outcome` explicitly records supplied judgment/source
lineage without certifying truth or native attention. `outcome_revision` only
registers an externally proposed candidate; activation is separate. Its
evaluation protocol says a logged link does not prove advice was followed or
caused an outcome. Preserve these limits when plugging in external producers;
add independent observed-outcome evidence for the causal claim when that run is
exercised. The current CI access failure calls for credential repair, not a new
memory design. Serving code and all existing authority boundaries are unchanged.

## October4 completed runs and new frontier delta

The [c70 completed receipts](evidence/2026-10-04_c70b9a4e_completed_ci_receipts.json)
show no demonstrated latency improvement. Baseline response failure and native
prepare timeout are distinct. Two existing automatic comparator diagnostics each
count189 combined H/disclosure checks,44403 SQL executions and4105 Kurrent reads
over the entire instrumented fixture. All14 loaded source hashes matchc70 Git
blobs. No new diagnostic was dispatched. These counts support application-level
amplification, without establishing engine query latency or current native thread
cost. The next step is the [whole-operation protection mapping](MINIMAL_JUDGMENT_INVOCATION_2026-10-03.md).

Actual frontier-watch3bea3318904ec2881d3f981d46a5b8d5bca91ba7 adds the
[October4 evolvable-memory intake](https://github.com/NIne-WIngEd/A.L.I.C.E/blob/3bea3318904ec2881d3f981d46a5b8d5bca91ba7/docs/research/FRONTIER_WATCH_INTAKE_2026-10-04_EVOLVABLE_MEMORY_PROGRAMS.md).
Original [MemCodex sections2.1–2.2](https://arxiv.org/html/2609.39765) were inspected:
bounded read routing keeps exact source links, while candidate programs remain
behind fixed runtime constraints and attributable acceptance checks. The useful
analogy is source-linked current serving with explicit boundaries; no layered
program-evolution system is required here. Append-only retention and benchmark
speed do not qualify FloRA withdrawal or predict this repair's latency. VerMem
is a future learned memory-policy training idea; it creates no model task here.
Alice main8ea804aa and runtime API4f287a remain unchanged.

## Actual phase consumer and temporal research follow-up

[The source reachability audit](evidence/2026-10-04_actual_phase_consumer_reachability.json)
rejects the session-only owner proposal. The real pinned archive runtime does
not use the current-context frame; first capture and anchored judgment must be
part of the serving design. Do not extrapolate a supplied recovery fixture's
query-count improvement to that chronology.

The pinned [Graphiti SearchFilters implementation](https://github.com/getzep/graphiti/blob/4f62cfe7a2d519e55bfdf2dc4a2fd06649dc00b3/graphiti_core/search/search_filters.py)
was read directly: exact edge IDs and separate valid/invalid/created/expired
time filters make historical selection explicit. This is an implementation
analogy for distinguishing a frozen phase view from present state. It supplies
neither FloRA Claim truth authority nor current withdrawal/evaluation permission.
Retain historical occurrence proof and freshly resolve current use rights;
adopting Graphiti's graph or its filters is not the proposed repair.

The one actual-class local observation preserves exact frozen context and27
source identities. It separates cold restore (20456 SQL calls) from open
preparation (15560 calls, zero restores) and current prepared metadata (253).
The counts support repeated phase preparation, including historical pin checks,
without measuring XTDB execution or anchored authority. This changes the next
construction decision: an archive-placement change alone cannot address all
open-use work. The physical budget and all current permission fences remain.
