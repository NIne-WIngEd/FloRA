# External memory mechanisms for an Alice/Fable backbone

Research date: 2026-10-15. Primary papers, official documentation, and pinned public source were inspected live. This is a design research note, not runtime validation or an adoption decision. No project data were sent to external services, no packages were installed, and no jobs were run.

The working objective supplied by the parent task is a locally owned, coherent personal-AI backbone, prototyped narrowly in FloRA. The historical FloRA scope and behavioral boundary were recovered from memory; the parent agent owns current project-contract verification. The external evidence below does not establish that any candidate already satisfies that contract.

## Decision and synthesis

The decision is which mechanisms let personal experience change later judgment reliably, while preserving where evidence came from, what was inferred, what changed, and what remains uncertain. Storage/retrieval success and outcome-sensitive judgment are different claims.

The strongest transferable pattern is **evidence retained separately from revisable interpretations, with a bounded working view and measured consequences of using that view**. The components are familiar research ideas; their Alice-specific composition and evaluation would be the engineering contribution. Nothing in this review supports claiming that a graph, a memory vendor, a single database, or a new label for memory is universally best.

Four competitors are useful for different reasons:

| System | Mechanism worth learning from | Main transfer limitation |
|---|---|---|
| Letta/MemGPT | Agent-operated context hierarchy; currently versioned files and selective loading | Editable memory is not verified personal belief, and tool skill depends on the host model |
| Graphiti/Zep | Source-linked temporal assertions and separate event/ingestion time | An LLM proposes contradiction and entity resolution; neither becomes truth merely by entering a graph |
| Mem0 | Preserve changing facts instead of destructive reconciliation; combine retrieval signals | Managed results differ from OSS; additive storage alone does not resolve competing assertions |
| Hindsight | Separate facts/experience from derived observations; maintain source-linked summaries off the request path | Its original headline tests deliberately suppress strong preference formation and evaluate recall |

These are responsibilities that can be expressed within one owned contract. They do not require adopting four platforms or mapping every responsibility to a separate model or database.

## Letta/MemGPT: context management, then versioned context repositories

**Original mechanism.** MemGPT moves information between active context and external memory using model-invoked tools and control-flow interrupts. This addresses finite context, with document and multi-session conversation evaluations. It is primarily external-state and in-context adaptation, not an experiment showing owner-specific weight learning. [MemGPT paper, submitted 2023-10-12; revised 2024-02-12](https://arxiv.org/abs/2310.08560).

**Current implementation differs substantially.** The current `letta-ai/letta` repository redirects active development to `letta-ai/letta-code`; the old V1 API server is in its `archive` branch. The current harness offers a local/self-hosted App Server. [Current repository](https://github.com/letta-ai/letta).

Current MemFS projects an agent's Git repository onto a computer. Root memory files enter every prompt; indexed subdirectories stay outside context until read. Ordinary file tools are the default: MemFS does not include vector search unless an optional search mod is added. Local agents commit to local repositories; cloud-backed agents synchronize commits. A real working tree, uncommitted edits, and saved versions are explicit. [MemFS docs, accessed 2026-10-15](https://docs.letta.com/concepts/memfs). The pinned `ensureLocalMemfsCheckout` implementation has a separate local initialization path, rather than always cloning a cloud repository. [Source](https://github.com/letta-ai/letta-code/blob/cc4654acc3b424a68c385bce0fe0c00edaad5d7e/src/agent/memory-filesystem.ts#L251).

**Evidence boundary.** Letta's filesystem experiment reported 74% LoCoMo with GPT-4o-mini, iterative file search, embeddings, and constrained tool ordering. This is a useful strong baseline, not proof that arbitrary plain files outperform structured memory. Letta also disputed whether competitor evaluations faithfully backfilled MemGPT. That dispute is a methodological warning; it is not an independently adjudicated verdict. [Letta benchmark report](https://www.letta.com/blog/benchmarking-ai-agent-memory/).

**Transfer hypothesis.** Give the native decision process a legible, versioned working view and familiar lookup operations. Preserve source evidence beneath those views. Compare against an iterative source-search baseline, not just one-shot vector top-k.

**Incompatibility.** Letting a generative model rewrite a persona file is insufficient authority for owner state. Git records changes, but does not determine whether a statement is supported, current, properly scoped, or an observed action rather than an assistant's claim. Those remain Alice contract requirements.

## Graphiti/Zep: temporal assertions with recoverable sources

The original Zep paper links raw episodes to extracted entities and semantic edges. It separates when something is said to be valid from when the system records or expires it. An LLM compares candidate edges with related edges and can invalidate temporally overlapping contradictions. The reported GPT-4o LongMemEval result was 71.2% versus 60.2% full context, with much smaller supplied context. Its source-traversal links were described but explicitly not directly evaluated in the paper. Its attempted LongMemEval MemGPT integration did not yield successful responses, so that is not a clean matched head-to-head result. [Paper, 2025-01-20](https://arxiv.org/html/2501.13956v1).

The current source concretely carries source episode IDs, `valid_at`, `invalid_at`, `expired_at`, and `reference_time` on entity edges. The comments distinguish future plans from future occurrence dates, and soft deadlines from invalidation times. These distinctions matter for commitments and deferred actions. [Pinned edge schema](https://github.com/getzep/graphiti/blob/5961293865a57844fe13d4eb061deb3501971fb2/graphiti_core/edges.py#L242).

**Ownership and version boundary.** OSS Graphiti currently requires a graph backend and LLM/embedding providers; the README lists Neo4j, FalkorDB, Neptune combinations, and deprecated Kuzu support. It warns that weaker models may fail structured-output ingestion. Commercial Zep now advertises a proprietary Context Graph Engine; it is not simply OSS Graphiti plus hosting. [Current repository](https://github.com/getzep/graphiti). The pinned Graphiti root license is [Apache-2.0](https://github.com/getzep/graphiti/blob/5961293865a57844fe13d4eb061deb3501971fb2/LICENSE).

**Transfer hypothesis.** Represent claims as time-scoped assertions connected to their sources; preserve old assertions when superseded. Separate an entity-match proposal from an accepted identity link. Retrieval may exploit relationships without making the graph the authority.

**Falsifier.** If out-of-order corrections, two people with similar names, or hypothetical/future statements change the wrong current judgment, temporal fields and graph links have not solved the needed problem. The extractor's decisions require validation at the point they acquire authority.

## Mem0: a useful negative result drove additive memory

The 2025 paper's pipeline extracts candidate facts and reconciles them through memory operations; its optional graph variant yielded only a modest aggregate improvement over its base method. Its LoCoMo comparison used RAG alternatives with one or two retrieved chunks, so it cannot rule out stronger iterative retrieval. [Original paper, 2025-04-28](https://arxiv.org/html/2504.19413v1).

The April 2026 algorithm, updated September 28, replaces two-pass ADD/UPDATE/DELETE reconciliation with single-pass ADD-only extraction. The authors identify overwrites and deletions as a source of lost context. Entity matching joins semantic and lexical signals. Their reported 92.5 LoCoMo and 94.4 LongMemEval scores explicitly describe the **managed platform with proprietary optimizations**, rather than exact OSS performance. Their BEAM 10M result falls to 48.6, with weak event ordering and temporal reasoning. The same report says behavioral pattern matching is planned, not already established. [Current algorithm report](https://mem0.ai/blog/mem0-the-token-efficient-memory-algorithm).

Pinned OSS source confirms recent-context lookup, retrieval of ten existing memories, one additive extraction call, batch embeddings, deduplication, and persistence. It also explicitly rejects the platform-only temporal `reference_date` search parameter. This is a concrete example of why an API name or vendor score must not be treated as the local implementation's capability. [Pinned implementation](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L839). The code is [Apache-2.0](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/LICENSE); library, self-hosted server, and managed platform are distinct deployment surfaces. [Repository](https://github.com/mem0ai/mem0).

**Transfer hypothesis.** Preserve observations and state transitions; derive a current view instead of making an LLM destructively reconcile the only copy. Support exact, semantic, and entity-oriented lookup only when each contributes on the actual workload.

**Incompatibility.** Treating an assistant's statement of a completed action as equal to an observed tool receipt would contaminate evidence. ADD-only records also accumulate contradictions and duplicates; an authority-aware current view is still needed. These are design deductions, not claims that Mem0 promises Alice's stronger contract.

## Hindsight: useful consolidation without proof of personal judgment

The original Hindsight paper separates world facts, agent experiences, neutral observations, and opinions. Retain extracts narrative facts; recall combines semantic, lexical, graph, and temporal retrieval with rank fusion, reranking, and a token budget; reflect conditions generation on retrieved memory and configurable dispositions. The paper reports 83.6% LongMemEval for GPT-OSS-20B versus 39% full context with the same backbone. Crucially, section 7.3 uses neutral dispositions and low bias precisely because the benchmarks test factual recall rather than preference-conditioned reasoning. Thus its 91.4% larger-model headline is not evidence for outcome-sensitive personal judgment. [Paper, 2025-12-14](https://arxiv.org/html/2512.12818v1).

Current documentation now emphasizes world facts, experiences, observations, and mental models. Mental models are standing answers to selected questions, synthesized in the background and returned cheaply. They retain source references, history, and a freshness signal; stale models are not intended to short-circuit deeper retrieval. Incremental edits limit drift. [Mental-model documentation](https://hindsight.vectorize.io/developer/mental-models).

The implementation has meaningful details beyond taxonomy: consolidation checks whether source rows still exist, locks them while writing a derived observation, checks source edits since reading, and does expensive model/embedding work before the final transaction. This is directly relevant to stale synthesis and deletion races. It is source inspection, not a proof that every race is covered. [Pinned consolidator](https://github.com/vectorize-io/hindsight/blob/79303b6729f573a253a5f606324ab6274ef59d97/hindsight-api-slim/hindsight_api/engine/consolidation/consolidator.py#L587).

**Local ownership.** Its MIT-licensed implementation supports local model providers. PostgreSQL supplies vectors through pgvector, text search, relational/JSON data, and recursive graph queries; development can use embedded pg0. This demonstrates that these logical views need not imply separate database products. Oracle is now an alternative; the storage documentation's older “no abstraction” rationale should not be interpreted as an exhaustive current code description. [Storage docs](https://hindsight.vectorize.io/developer/storage), [current repository](https://github.com/vectorize-io/hindsight), [license](https://github.com/vectorize-io/hindsight/blob/79303b6729f573a253a5f606324ab6274ef59d97/LICENSE).

**Transfer hypothesis.** Background synthesis can produce bounded, source-linked views with explicit versions and freshness. It should reduce repeated retrieval/synthesis, subject to measurement.

**Incompatibility.** Labels such as “fact,” “observation,” “belief,” “proof count,” or “mental model” do not establish truth or causal reliability. Repeated paraphrases can share one source; repeated assertions are not independent evidence. Disposition controls are not a learned owner model. Original paper architecture and current product taxonomy must not be conflated.

## Research closest to experience reuse and behavioral qualification

**ACE — adapting external context.** ACE stores reusable strategies as individually identified playbook entries, with helpful/harmful counters and localized delta updates merged deterministically. Generator, reflector, and curator are functional roles; this does not imply three permanent models. Its AppWorld/financial experiments support context adaptation without weight updates. The paper documents collapse under monolithic rewriting, but also warns that a weak reflector can create harmful memory. Transfer the incremental revision mechanism and outcome-linked entries; do not treat self-reported usefulness as calibrated causal credit. [ACE, 2025-10-06](https://arxiv.org/html/2510.04618v1).

**Hindsight Memory-PRM — trained memory management, a separate project from Vectorize Hindsight.** It trains an 8B memory policy using later retrieval/citation traces plus deletion-and-reanswer probes, with an auxiliary utility critic. Version chains retain old entries. Reported LoCoMo accuracy is 77.5% under a shared reader. Its own limits are essential: entry-presence credit is a proxy for action credit; schema transfer is domain-dependent; a lossless verbatim substrate under-stresses forgetting; probes depend on a closed model; deletion rights require more machinery. The counterfactual is model/prompt-relative, not general causal proof. This is genuine parameter training of a manager, not merely memory insertion; it still does not demonstrate learned personal judgment. The paper claims released caches and scripts, but this search did not verify a public repository location. [Paper, 2026-08-30](https://arxiv.org/html/2608.29605v1).

**MemoryBench — feedback is not another fact to memorize.** It evaluates accumulation of explicit and implicit simulated user feedback over varied task forms. The paper finds simple RAG competitive and memory approaches inconsistent as feedback accumulates, arguing that treating procedural feedback like declarative facts misses its role. Simulator and judge choices limit ecological validity. Its current repository has changed evaluation machinery since the initial paper, so pin the protocol before comparing. [Paper, originally 2025-10-20](https://arxiv.org/html/2510.17281), [official code](https://github.com/THUIR/MemoryBench).

**MemoryArena — action and memory must be evaluated together.** Across interdependent sessions, external memory is not universally better than long context; exact RAG can be more robust than heavier consolidation for precise intermediate constraints. The paper proposes representation and training mismatches as explanations, and finds performance decay with dependency depth. This is strong counterevidence against assuming a richer schema automatically improves action. Its results depend on the chosen agents, integrations, tasks, and versions; they do not prove external memory is intrinsically harmful. [Paper, 2026-02-18](https://arxiv.org/html/2602.16313v1).

**DolphinBench — recent action-oriented evaluation.** It supplies 600 tasks over three synthetic knowledge-work personas and verifies task construction using an agent with and without relevant history. It requires cost and latency reporting, including memory processing. This is closer to personal-assistant use than a prompted recall question. Limits include synthetic personas, a vendor-authored benchmark, and configuration-sensitive results; applying a remembered rule still does not prove learning from its consequences. [Paper, 2026-09-21](https://arxiv.org/html/2609.24971v1), [official benchmark](https://dolphinbench.ai/).

## Proposed Alice-specific composition and risks

This section is design inference for the parent agent to reconcile with current Alice contracts.

1. **Evidence first.** A decision episode should bind the situation, goal, available alternatives, selected action, pre-action assumptions and predictions, actual receipts, later outcome observations, and uncertainty. Record concise observable decision summaries; do not require hidden chain of thought.
2. **Separate assertion and observation.** “The assistant said it booked the flight” is an observed utterance, not an observed booking. “The user rejected the recommendation” is feedback, not proof of which assumption caused rejection.
3. **Versioned interpretation.** Derived preferences, working beliefs, and reusable procedures should identify supporting evidence and scope, plus contradiction/supersession relations. The authority to accept these changes must remain explicit. Learned components can propose revisions without possessing unilateral authority over every state plane.
4. **One coherent commit space.** A common version/lineage boundary could make related updates atomic and reduce coordination cost. It must not erase different authority or retention rules for user facts, assistant identity, actions, learned artifacts, and derived indexes. One transaction is a consistency mechanism, not a learning mechanism.
5. **Bounded views.** Compile task-specific context from current accepted state and exact source evidence. Indexes and summaries are replaceable projections. A dependency change invalidates only affected views; refresh and final-read checks must use the same version assumptions.
6. **Outcome-sensitive revision.** Revise a procedure or judgment rule only within the conditions supported by feedback. Keep successful, failed, ambiguous, and counterfactual cases available to appropriate training/qualification paths. The mechanism must be tested against strong memory-only inference.

Risks in the parent proposal are manageable but substantive. Outcome labels can be confounded by tool failure, changed circumstances, user mood, or an unavailable option. A prediction written after the result is hindsight leakage. A single successful episode cannot establish a general preference. Dependency tracking that misses an indirect source can preserve a stale conclusion. Shared commit space can accidentally mix authority or disclose one subject's memory to another. And a narrow event schema can discard exactly the nuance that later decisions need.

The narrow FloRA prototype should therefore exercise a few complete decision episodes with real correction/outcome semantics, not instantiate every comparator's infrastructure. Root's newer research branch findings remain a separate source of project-specific constraints; this review does not supersede them.

## Candidate hypotheses and falsification tests

| Hypothesis | Matched comparison | Result that would falsify or sharply weaken it |
|---|---|---|
| H1: source-linked versions improve correction use | Same model and evidence budget; destructive current-summary baseline versus preserved source plus versioned current view | Wrong current answer, loss of a valid historical answer, or no improvement after controlling context volume |
| H2: bounded derived views reduce latency without changing authority | Same accepted evidence/decision; fresh view versus direct source reconstruction | Lower latency achieved by omitting required evidence, using stale sources, or shifting work outside cost accounting |
| H3: outcome-bearing episodes improve later personal judgment beyond strong memory | Same host, candidates, source evidence, token/call budget; memory-only inference versus proposed judgment mechanism | Gain disappears with a strong iterative-search baseline, or is explained by the desired answer being written explicitly in memory |
| H4: revision is sensitive to the relevant cause | Change only relevant outcome/correction; separately change irrelevant wording, timestamps, or unrelated outcomes | Judgment follows superficial cues, flips on irrelevant changes, or fails to flip when the relevant evidence changes |
| H5: learned changes transfer | Held-out contexts/actions with separate development and qualification data; retained unrelated capabilities | Only paraphrases of training examples improve; unrelated behavior regresses; improvement depends on evaluation leakage |
| H6: shared commit space preserves consistency under interruption | Crash/replay and stale-projection scenarios with the same logical contract | Duplicate action, mismatched receipt/state version, orphan interpretation, or accepted output based on invalidated evidence |

H3 and H4 need more than removal of a memory entry. Removal can alter context length, retrieval competition, and evidence redundancy. Use matched replacement controls, hold the reader/retriever fixed when isolating representation, compare support clusters rather than only a single duplicate, and separately test complete removal of the relevant evidence. Randomized repeated trials are needed when generation variance can explain a flip. Candidate order and action labels should be balanced. The hidden target outcome must not appear in the retrieval query or generated evaluation cue.

For training, compare fixed weights with changed memory, changed weights with fixed memory, and both together. This identifies where the improvement resides without assuming parameter updates are always necessary. Do not credit a new backend for improvement caused by a better host model, different prompt, more context, extra inference calls, or privileged ground-truth feedback.

## Pinned implementation evidence

The following public `main` commit identities were fetched through GitHub's API on 2026-10-15. Source locations above are immutable links; documentation and vendor pages can continue changing.

| Repository | Inspected commit | Commit time UTC |
|---|---|---|
| mem0ai/mem0 | `0724291bd864cf807e88ee8981c8226644e8fb42` | 2026-10-14 15:39:50 |
| getzep/graphiti | `5961293865a57844fe13d4eb061deb3501971fb2` | 2026-10-15 14:59:36 |
| vectorize-io/hindsight | `79303b6729f573a253a5f606324ab6274ef59d97` | 2026-10-15 14:46:47 |
| letta-ai/letta-code | `cc4654acc3b424a68c385bce0fe0c00edaad5d7e` | 2026-10-15 05:01:15 |

License labels were checked at these commits: Mem0, Graphiti, and Letta Code use Apache-2.0; Hindsight uses MIT. This establishes the inspected repository labels, not blanket compatibility of every model, database, managed feature, or transitive dependency. Local deployment still requires explicitly local inference/embedding configuration and verified data paths before making zero-egress claims.

No benchmark was reproduced in this task. No competitor result is an Alice/Fable/FloRA qualification result. Graphify may assist source navigation and option discovery; this review supplies no evidence for promoting it into production memory or an authority plane.
