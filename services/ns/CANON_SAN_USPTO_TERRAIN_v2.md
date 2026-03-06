# SAN∞ USPTO Terrain Initialization — Final Architecture v2.0
# NS∞ / AXIOLEV Holdings Canon Document
# Classification: CANON | Tier: FOUNDER | Version: 2.0 | Date: 2026-02-19
# Source: SAN_USPTO_Terrain_Init_Final_Architecture_v2.pdf
# Position: SAN domain constitution → USPTO terrain layer
# Relation to NS: NS primitives → STL axioms → SAN∞ constitution → USPTO terrain

---

## CORE POINT

USPTO ingestion is terrain initialization.

Not data import. Not database loading. Terrain initialization.

A claim-centric, graph-native legal topology that turns patent corpus into a
computable substrate for:
  - Novelty detection
  - White-space mapping
  - Competitor intelligence
  - Claim strategy optimization
  - Lexicon anchoring synchronized with Alexandria

---

## CANONICAL DEFINITIONS

| Term | Definition |
|------|-----------|
| Terrain initialization | Converting USPTO publications into a computable legal topology: CPC hierarchy, citations, families, and claim coordinates with versioned snapshots |
| Publication (pub_id) | A patent grant or application document treated as a node in legal space |
| Claim coordinate | Normalized claim representation: type (independent/dependent), dependency tree, element segmentation — used for similarity and novelty scoring |
| Element | Decomposed unit of claim language: preamble, transitional phrase, body elements — used for element-level similarity and mapping |
| Legal topology | Connected structure of publications via CPC membership, citation edges, and family/priority chains |
| Snapshot | Versioned, replayable build artifact: (raw_version, parse_version, index_version, embedding_version) with signed manifests |
| Delta | Weekly change set of new and corrected publications plus derived edges and embeddings |
| Novelty check | Low-latency query returning nearest legal neighbors (claim/text/CPC) and collision risk signals for a SAN primitive |
| White-space query | Query identifying under-occupied regions in CPC + semantic space given time, assignee pressure, and claim pattern density |

---

## THREE-LAYER LEGAL SUBSTRATE

Each layer is queryable independently and together via hybrid retrieval.

### Layer 1 — Topology
  CPC hierarchy, citation graph, family/priority chains,
  assignee/inventor resolution, temporal edges

### Layer 2 — Claim Coordinates
  Normalized claims (independent/dependent), element breakdown,
  dependency tree, semantic vectors (selective)

### Layer 3 — Signal
  Continuation density, assignee pressure, time-burst behavior,
  prosecution velocity proxies (Phase 2 with prosecution data)

---

## FORMAL OBJECT MODEL (v2)

```
Patent(
  pub_id: str,
  kind: grant|app,
  dates: dict,
  assignee_ids: list[str],
  inventor_ids: list[str],
  family_id: str,
  cpc_codes: list[str]
)

Claim(
  claim_id: str,
  pub_id: str,
  claim_no: int,
  independent: bool,
  text: str,
  dep_on: list[str],
  elements: list[Element]
)

Element(
  type: preamble|transition|body,
  text: str,
  roles: list[str]
)

CPC(pub_id: str, cpc_code: str, version: str)

CitationEdge(
  src_pub_id: str,
  dst_pub_id: str,
  edge_type: citing|cited|family
)

Family(
  family_id: str,
  members: list[str],
  priority_chain: list[str]
)

LexiconAnchor(
  term_id: str,
  claim_id: str,
  confidence: float,
  snapshot_id: str
)
```

Materialized views (Parquet tables):
  patents, claims, elements, cpc, citations, families, assignees, inventors

Edge tables:
  cite_edges, family_edges, cpc_membership, claim_deps

---

## PIPELINE ARCHITECTURE

```
Immutable Raw (S3 or append-only FS)
  → Signed manifest (checksums + signatures)
  ↓
Stage B: Parse (streaming XML)
  → Staging Parquet (patents, claims, CPC, citations)
  ↓
Stage C: Normalize (IDs, families, entity resolution)
  → Clean Parquet + edge tables
  ├── Text Index (BM25 on candidates)
  └── Vector Index (independent claims + abstracts; lazy queue for long spec)
  ↓
Stage F: Delta + Snapshot
  (SHA diff on claim/CPC/cite blocks; no full rebuild)
  ↓
SAN∞ Terrain APIs
  (novelty, white-space, competitor pressure, lexicon anchors)
```

---

## SUCCESS METRICS (TWO-TIER)

### Tier 1 — Terrain (do this first, tonight)
  Metadata + claim text + indexes
  Target: 24-48h for scoped CPC region on 32-core/256GB + local NVMe
  In practice: scope to target CPC subtree + 2-hop citations

### Tier 2 — Semantic (batch, GPU preferred)
  Embeddings generated as separable batch job
  Target: 24-72h depending on scope
  Can run independently after Tier 1 completes

Query targets (after both tiers):
  Novelty p95 < 150ms (hybrid candidate set)
  White-space p95 < 500ms on CPC subtree with precomputed membership

---

## DEFAULT STACK (lowest ops burden)

| Surface | Choice |
|---------|--------|
| Immutable raw | S3 or local append-only FS; signed manifests |
| Columnar analytics | Parquet + DuckDB (dev) / ClickHouse (prod) |
| Edges/graph | Parquet adjacency + materialized neighborhood tables |
| Text search | BM25 (candidate-set only, keep index small) |
| Vector search | Qdrant or LanceDB; HNSW; quantized vectors |
| Orchestration | Airflow or Dagster; weekly delta DAGs |
| Graph DB | Not in default. Add Neo4j only for interactive investigator UX |

---

## ENGINEERING OPTIMIZATIONS (COST DISCIPLINE)

1. No Neo4j by default — Parquet edge tables + precomputed neighborhood sets
2. Candidate-set BM25 — run only on narrowed candidates (CPC subtree + semantic cluster)
3. Tiered embeddings — embed independent claims + abstracts first; defer full spec
4. Delta everywhere — SHA blocks for claim text, CPC, citations; re-embed only changed
5. Polars + DuckDB for single-node builds; Spark only when scale requires cluster
6. Entity resolution staged: deterministic → fuzzy → top-assignee alias table → ML for long tail
7. Precompute CPC subtree membership for fast white-space and novelty filters

---

## SECURITY MODEL (NS INVARIANTS ALIGNMENT)

  Immutable raw store + signed manifest (WORM preferred)
  Separate compute workspace from canon outputs
  Append-only snapshots — no in-place edits
  Least-privilege access; secrets out of code

These are NS primitives (Lineage Preservation, Snapshot Authority) applied
to the patent data domain. Same primitive, new state space.

---

## 90-DAY BUILD PLAN

| Gate | Weeks | Acceptance Criteria |
|------|-------|---------------------|
| Gate 1 | 1-3 | Terrain usable for novelty: CPC + claims + BM25; scoped to target CPC + 2-hop |
| Gate 2 | 4-6 | White-space queries: membership precompute; competitor pressure heatmaps |
| Gate 3 | 7-9 | Embeddings for independent claims + abstracts; vector search integrated; hybrid novelty |
| Gate 4 | 10-12 | Weekly deltas: SHA diff, re-embed changed only, signed snapshot replay test passes |

---

## STARLINK / BANDWIDTH CONSTRAINTS

For overnight ingest under bandwidth caps:

Priority 1 (smallest, highest value): PatentsView normalized tables (pre-parsed Parquet)
  - Assignees, inventors, CPC, citations already normalized
  - ~20-40GB compressed for full corpus
  - Download first, builds terrain skeleton without XML parsing

Priority 2 (large, required for claims): USPTO Bulk PTGRXML grant files
  - Full text XML including claim language
  - ~100GB+ per year of grants
  - Download scoped CPC subtree only, not full corpus
  - Use USPTO ODP API for targeted pulls rather than bulk zip

Priority 3 (optional): Application XML (APPXML)
  - Required for pending application landscape
  - Defer to next bandwidth window

Bandwidth schedule:
  Late night window → bulk download (PatentsView Parquet + targeted XML)
  Morning → parse + normalize (CPU-bound, no bandwidth)
  Day → query + iterate (no bandwidth)

---

## DATA SOURCES

- USPTO Bulk Data: data.uspto.gov/bulkdata
- USPTO XML Resources + DTDs: uspto.gov/learning-and-resources/xml-resources
- PatentsView normalized tables: patentsview.org/downloads

---

## RELATION TO NS PRIMITIVES

This document instantiates NS primitives in the patent domain:

  Recursive Refinement → Delta architecture (SHA diff, never full rebuild)
  State Spaces → Legal topology (CPC, citations, families, claims)
  Commit Events → Snapshot (signed manifest, versioned, replayable)
  Snapshot Authority → Materialized Parquet tables as operative terrain
  Lineage Preservation → Immutable raw + append-only snapshots

SAN∞ terrain is not a new architecture. It is NS primitives applied to legal space.

---

# END CANON_SAN_USPTO_TERRAIN_v2.0
