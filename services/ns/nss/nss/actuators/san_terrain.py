"""
SAN∞ USPTO Terrain Engine
NS∞ / AXIOLEV Holdings

Three-layer legal substrate built on NS primitives:
  Topology layer    → CPC hierarchy, citation graph, families, assignees
  Claim coordinate  → normalized claims, elements, dependency trees, vectors
  Signal layer      → continuation density, assignee pressure, time-burst

Architecture: graph-native concept, table-native implementation.
Storage: Parquet + DuckDB (dev) / ClickHouse (prod).
No Neo4j by default.

API surface:
  novelty_check(claim_text, cpc_scope)     → collision risk + nearest neighbors
  whitespace_query(cpc_code, assignee_ids) → under-occupied regions
  competitor_pressure(cpc_code)            → assignee density + burst signals
  lexicon_anchors(term_ids)               → LexiconAnchor → Claim mappings

Snapshots are NS receipts: versioned, signed, replayable.
Deltas use SHA-based change detection — no full rebuilds after baseline.
"""

import os
import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ── Formal Object Model v2 ─────────────────────────────────────────────────────

@dataclass
class Element:
    """Decomposed unit of claim language."""
    type: str           # preamble | transition | body
    text: str
    roles: List[str] = field(default_factory=list)
    element_hash: str = ""

    def __post_init__(self):
        if not self.element_hash:
            self.element_hash = _sha(self.type + self.text)


@dataclass
class Claim:
    """Claim coordinate: normalized representation for similarity + novelty."""
    claim_id: str
    pub_id: str
    claim_no: int
    independent: bool
    text: str
    dep_on: List[str] = field(default_factory=list)
    elements: List[Element] = field(default_factory=list)
    claim_hash: str = ""
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        if not self.claim_hash:
            self.claim_hash = _sha(self.text)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("embedding", None)  # Don't serialize large vectors
        return d


@dataclass
class Patent:
    """Publication node in legal space."""
    pub_id: str
    kind: str               # grant | app
    title: str = ""
    abstract: str = ""
    filing_date: str = ""
    grant_date: str = ""
    assignee_ids: List[str] = field(default_factory=list)
    inventor_ids: List[str] = field(default_factory=list)
    family_id: str = ""
    cpc_codes: List[str] = field(default_factory=list)
    claims: List[Claim] = field(default_factory=list)
    pub_hash: str = ""

    def __post_init__(self):
        if not self.pub_hash:
            self.pub_hash = _sha(self.pub_id + self.title)

    def independent_claims(self) -> List[Claim]:
        return [c for c in self.claims if c.independent]


@dataclass
class CPC:
    pub_id: str
    cpc_code: str
    version: str = ""
    section: str = ""     # First char of code (A-H, Y)
    subclass: str = ""    # e.g. G06F


@dataclass
class CitationEdge:
    src_pub_id: str
    dst_pub_id: str
    edge_type: str        # citing | cited | family


@dataclass
class Family:
    family_id: str
    members: List[str] = field(default_factory=list)
    priority_chain: List[str] = field(default_factory=list)


@dataclass
class LexiconAnchor:
    """Links an NS lexicon term to a specific patent claim."""
    term_id: str
    claim_id: str
    pub_id: str
    confidence: float
    snapshot_id: str
    anchor_text: str = ""
    created_at: str = field(default_factory=_ts)


@dataclass
class TerrainSnapshot:
    """Versioned, replayable build artifact — NS receipt equivalent."""
    snapshot_id: str
    raw_version: str
    parse_version: str
    index_version: str
    embedding_version: str = ""
    cpc_scope: List[str] = field(default_factory=list)
    pub_count: int = 0
    claim_count: int = 0
    edge_count: int = 0
    signed_manifest: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=_ts)
    tier: str = "terrain"  # terrain | semantic


@dataclass
class NoveltyResult:
    """Result of a novelty check query."""
    query_claim_hash: str
    nearest_neighbors: List[Dict[str, Any]]  # pub_id, claim_id, score, cpc
    collision_risk: float         # 0.0 (clear) → 1.0 (high collision)
    risk_level: str               # CLEAR | LOW | MODERATE | HIGH | BLOCKING
    cpc_overlap: List[str]        # CPC codes with density
    query_latency_ms: float = 0.0
    snapshot_id: str = ""

    @property
    def risk_label(self) -> str:
        if self.collision_risk < 0.2:   return "CLEAR"
        elif self.collision_risk < 0.4: return "LOW"
        elif self.collision_risk < 0.65: return "MODERATE"
        elif self.collision_risk < 0.85: return "HIGH"
        else: return "BLOCKING"


@dataclass
class WhitespaceResult:
    """Result of a white-space query."""
    cpc_code: str
    sparse_regions: List[Dict[str, Any]]  # region, density_score, assignee_pressure
    under_occupied: List[str]             # CPC sub-codes with low density
    assignee_pressure_map: Dict[str, float]
    time_burst_signals: List[Dict[str, Any]]
    query_latency_ms: float = 0.0


# ── Terrain Storage ────────────────────────────────────────────────────────────

class TerrainStorage:
    """
    Parquet-native storage layer for the terrain.
    Dev mode: JSON files (zero deps).
    Prod mode: Parquet + DuckDB (install duckdb + pyarrow).
    """

    def __init__(self, terrain_dir: Path):
        self.root = terrain_dir
        self.patents_dir = terrain_dir / "patents"
        self.claims_dir = terrain_dir / "claims"
        self.edges_dir = terrain_dir / "edges"
        self.indexes_dir = terrain_dir / "indexes"
        self.snapshots_dir = terrain_dir / "snapshots"
        self.anchors_dir = terrain_dir / "anchors"

        for d in [self.patents_dir, self.claims_dir, self.edges_dir,
                  self.indexes_dir, self.snapshots_dir, self.anchors_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self._patent_index: Dict[str, dict] = self._load_index("patents")
        self._claim_index: Dict[str, dict] = self._load_index("claims")
        self._cpc_index: Dict[str, List[str]] = self._load_index("cpc")

    def _load_index(self, name: str) -> dict:
        p = self.indexes_dir / f"_{name}.json"
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                return {}
        return {}

    def _save_index(self, name: str, data: dict):
        p = self.indexes_dir / f"_{name}.json"
        p.write_text(json.dumps(data, indent=2))

    # ── Write ──────────────────────────────────────────────────────────────

    def store_patent(self, patent: Patent) -> bool:
        """Store patent. Returns True if new, False if existing hash matches."""
        existing = self._patent_index.get(patent.pub_id, {})
        if existing.get("pub_hash") == patent.pub_hash:
            return False  # No change

        doc = {
            "pub_id": patent.pub_id, "kind": patent.kind,
            "title": patent.title, "abstract": patent.abstract[:2000],
            "filing_date": patent.filing_date, "grant_date": patent.grant_date,
            "assignee_ids": patent.assignee_ids,
            "cpc_codes": patent.cpc_codes,
            "family_id": patent.family_id,
            "pub_hash": patent.pub_hash,
            "claim_count": len(patent.claims),
            "independent_claim_count": len(patent.independent_claims()),
        }

        (self.patents_dir / f"{patent.pub_id}.json").write_text(
            json.dumps(doc, indent=2))

        self._patent_index[patent.pub_id] = {
            "pub_hash": patent.pub_hash,
            "kind": patent.kind,
            "cpc_codes": patent.cpc_codes,
        }
        self._save_index("patents", self._patent_index)

        # Store claims separately (delta-friendly)
        for claim in patent.claims:
            self.store_claim(claim)

        return True

    def store_claim(self, claim: Claim) -> bool:
        existing = self._claim_index.get(claim.claim_id, {})
        if existing.get("claim_hash") == claim.claim_hash:
            return False

        (self.claims_dir / f"{claim.claim_id}.json").write_text(
            json.dumps(claim.to_dict(), indent=2))

        self._claim_index[claim.claim_id] = {
            "claim_hash": claim.claim_hash,
            "pub_id": claim.pub_id,
            "independent": claim.independent,
            "text_preview": claim.text[:100],
        }
        self._save_index("claims", self._claim_index)
        return True

    def store_edge(self, edge: CitationEdge):
        edge_id = _sha(edge.src_pub_id + edge.dst_pub_id + edge.edge_type)
        (self.edges_dir / f"{edge_id}.json").write_text(
            json.dumps(asdict(edge)))

    def store_anchor(self, anchor: LexiconAnchor):
        (self.anchors_dir / f"{anchor.term_id}_{anchor.claim_id}.json").write_text(
            json.dumps(asdict(anchor), indent=2))

    def store_snapshot(self, snap: TerrainSnapshot):
        # Sign the manifest
        snap.signed_manifest = {
            "pub_count": str(snap.pub_count),
            "claim_count": str(snap.claim_count),
            "cpc_scope": json.dumps(snap.cpc_scope),
            "signature": _sha(snap.snapshot_id + str(snap.pub_count) +
                               str(snap.claim_count)),
        }
        (self.snapshots_dir / f"{snap.snapshot_id}.json").write_text(
            json.dumps(asdict(snap), indent=2))

    # ── Read ───────────────────────────────────────────────────────────────

    def get_patent(self, pub_id: str) -> Optional[dict]:
        p = self.patents_dir / f"{pub_id}.json"
        if p.exists():
            return json.loads(p.read_text())
        return None

    def get_claims_for_pub(self, pub_id: str) -> List[dict]:
        claims = []
        for k, v in self._claim_index.items():
            if v.get("pub_id") == pub_id:
                p = self.claims_dir / f"{k}.json"
                if p.exists():
                    claims.append(json.loads(p.read_text()))
        return claims

    def get_patents_by_cpc(self, cpc_prefix: str) -> List[str]:
        """Get pub_ids for patents matching a CPC prefix."""
        results = []
        for pub_id, meta in self._patent_index.items():
            for code in meta.get("cpc_codes", []):
                if code.startswith(cpc_prefix):
                    results.append(pub_id)
                    break
        return results

    def stats(self) -> dict:
        snapshots = list(self.snapshots_dir.glob("*.json"))
        latest_snap = None
        if snapshots:
            latest = max(snapshots, key=lambda p: p.stat().st_mtime)
            try:
                latest_snap = json.loads(latest.read_text())
            except Exception:
                pass
        return {
            "patents": len(self._patent_index),
            "claims": len(self._claim_index),
            "edges": len(list(self.edges_dir.glob("*.json"))),
            "snapshots": len(snapshots),
            "anchors": len(list(self.anchors_dir.glob("*.json"))),
            "latest_snapshot": latest_snap,
            "terrain_dir": str(self.root),
        }


# ── Terrain API ────────────────────────────────────────────────────────────────

class SANTerrainEngine:
    """
    Production API for SAN∞ terrain queries.
    Novelty, white-space, competitor pressure, lexicon anchors.
    """

    RISK_THRESHOLDS = {
        "CLEAR": 0.2, "LOW": 0.4, "MODERATE": 0.65, "HIGH": 0.85
    }

    def __init__(self, terrain_dir: Path, receipt_chain=None):
        self._store = TerrainStorage(terrain_dir)
        self._receipt_chain = receipt_chain
        self._query_cache: Dict[str, Any] = {}

    @property
    def storage(self) -> TerrainStorage:
        return self._store

    def novelty_check(self, claim_text: str,
                      cpc_scope: List[str] = None,
                      top_k: int = 10) -> NoveltyResult:
        """
        Check novelty of a claim against terrain.
        Returns nearest legal neighbors + collision risk.
        Target: p95 < 150ms on scoped terrain.
        """
        t0 = time.time()
        query_hash = _sha(claim_text)

        # Candidate set from CPC scope (fast filter before BM25)
        candidates: List[str] = []
        if cpc_scope:
            for cpc_prefix in cpc_scope:
                candidates.extend(self._store.get_patents_by_cpc(cpc_prefix))
        else:
            candidates = list(self._store._patent_index.keys())

        # BM25-style keyword scoring on candidate set
        query_terms = set(claim_text.lower().split())
        scored: List[Tuple[float, str, str]] = []  # (score, pub_id, claim_id)

        for pub_id in candidates[:500]:  # cap at 500 for latency
            claims = self._store.get_claims_for_pub(pub_id)
            for cl in claims:
                if not cl.get("independent", False):
                    continue
                claim_terms = set(cl.get("text", "").lower().split())
                if not claim_terms:
                    continue
                overlap = len(query_terms & claim_terms)
                union = len(query_terms | claim_terms)
                jaccard = overlap / union if union else 0.0
                if jaccard > 0.05:
                    scored.append((jaccard, pub_id, cl.get("claim_id", "")))

        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]

        # Collision risk from top neighbor scores
        collision_risk = 0.0
        if top:
            collision_risk = min(1.0, top[0][0] * 2.5)

        # CPC overlap from top neighbors
        cpc_overlap = []
        for _, pub_id, _ in top[:5]:
            meta = self._store._patent_index.get(pub_id, {})
            cpc_overlap.extend(meta.get("cpc_codes", []))
        cpc_overlap = list(set(cpc_overlap))[:10]

        result = NoveltyResult(
            query_claim_hash=query_hash,
            nearest_neighbors=[
                {
                    "pub_id": pub_id,
                    "claim_id": cid,
                    "similarity_score": round(score, 4),
                    "risk_contribution": round(score * 2.5, 4),
                    "patent": self._store.get_patent(pub_id) or {},
                }
                for score, pub_id, cid in top
            ],
            collision_risk=round(collision_risk, 4),
            risk_level=self._risk_level(collision_risk),
            cpc_overlap=cpc_overlap,
            query_latency_ms=round((time.time() - t0) * 1000, 1),
        )

        if self._receipt_chain:
            self._receipt_chain.emit(
                "TERRAIN_NOVELTY_CHECK",
                {"kind": "san_terrain", "ref": "api"},
                {"query_hash": query_hash, "cpc_scope": cpc_scope or []},
                {"risk_level": result.risk_level,
                 "collision_risk": result.collision_risk,
                 "neighbors_found": len(top),
                 "latency_ms": result.query_latency_ms}
            )

        return result

    def whitespace_query(self, cpc_code: str,
                          assignee_filter: List[str] = None) -> WhitespaceResult:
        """
        Find under-occupied regions in CPC + semantic space.
        Target: p95 < 500ms on subtree with precomputed membership.
        """
        t0 = time.time()

        # Get all patents in this CPC subtree
        pubs = self._store.get_patents_by_cpc(cpc_code)

        # Assignee density map
        assignee_counts: Dict[str, int] = {}
        for pub_id in pubs:
            meta = self._store._patent_index.get(pub_id, {})
            for assignee in meta.get("assignee_ids", []):
                assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1

        # Pressure map (normalize)
        total = max(sum(assignee_counts.values()), 1)
        pressure_map = {a: round(c / total, 4)
                        for a, c in sorted(assignee_counts.items(),
                                           key=lambda x: -x[1])[:20]}

        # Find sub-CPC codes and their densities
        sub_cpc_counts: Dict[str, int] = {}
        for pub_id in pubs:
            meta = self._store._patent_index.get(pub_id, {})
            for code in meta.get("cpc_codes", []):
                if code.startswith(cpc_code):
                    sub = code[:len(cpc_code) + 4]  # one level deeper
                    sub_cpc_counts[sub] = sub_cpc_counts.get(sub, 0) + 1

        # Under-occupied: sub-codes with < 5% of max density
        max_density = max(sub_cpc_counts.values()) if sub_cpc_counts else 1
        under_occupied = [
            code for code, count in sub_cpc_counts.items()
            if count / max_density < 0.05
        ]

        sparse_regions = [
            {"cpc": code, "patent_count": count,
             "density_ratio": round(count / max_density, 4),
             "opportunity": "HIGH" if count / max_density < 0.02 else "MODERATE"}
            for code, count in sorted(sub_cpc_counts.items(), key=lambda x: x[1])[:10]
        ]

        return WhitespaceResult(
            cpc_code=cpc_code,
            sparse_regions=sparse_regions,
            under_occupied=under_occupied[:20],
            assignee_pressure_map=pressure_map,
            time_burst_signals=[],  # Phase 2: prosecution velocity signals
            query_latency_ms=round((time.time() - t0) * 1000, 1),
        )

    def competitor_pressure(self, cpc_code: str) -> dict:
        """Assignee density + filing burst signals for a CPC region."""
        pubs = self._store.get_patents_by_cpc(cpc_code)
        assignee_counts: Dict[str, int] = {}
        kind_counts: Dict[str, int] = {}

        for pub_id in pubs:
            meta = self._store._patent_index.get(pub_id, {})
            for a in meta.get("assignee_ids", []):
                assignee_counts[a] = assignee_counts.get(a, 0) + 1
            kind = meta.get("kind", "unknown")
            kind_counts[kind] = kind_counts.get(kind, 0) + 1

        top_assignees = sorted(assignee_counts.items(),
                                key=lambda x: -x[1])[:10]

        return {
            "cpc_code": cpc_code,
            "total_publications": len(pubs),
            "top_assignees": [
                {"assignee": a, "pub_count": c,
                 "market_share": round(c / max(len(pubs), 1), 4)}
                for a, c in top_assignees
            ],
            "kind_breakdown": kind_counts,
            "hhi": sum((c / max(len(pubs), 1)) ** 2
                       for c in assignee_counts.values()),  # market concentration
        }

    def lexicon_anchors_for_term(self, term_id: str) -> List[dict]:
        """Get all LexiconAnchors for an NS lexicon term."""
        anchors = []
        for f in self._store.anchors_dir.glob(f"{term_id}_*.json"):
            try:
                anchors.append(json.loads(f.read_text()))
            except Exception:
                pass
        return sorted(anchors, key=lambda x: -x.get("confidence", 0))

    def create_lexicon_anchor(self, term_id: str, claim_text: str,
                               claim_id: str, pub_id: str,
                               confidence: float,
                               snapshot_id: str = "current") -> LexiconAnchor:
        """Link an NS lexicon term to a specific patent claim."""
        anchor = LexiconAnchor(
            term_id=term_id,
            claim_id=claim_id,
            pub_id=pub_id,
            confidence=confidence,
            snapshot_id=snapshot_id,
            anchor_text=claim_text[:200],
        )
        self._store.store_anchor(anchor)

        if self._receipt_chain:
            self._receipt_chain.emit(
                "LEXICON_ANCHOR_CREATED",
                {"kind": "san_terrain", "ref": "lexicon"},
                {"term_id": term_id, "claim_id": claim_id},
                {"confidence": confidence, "pub_id": pub_id}
            )
        return anchor

    def take_snapshot(self, cpc_scope: List[str] = None,
                       tier: str = "terrain") -> TerrainSnapshot:
        """Create a versioned, signed snapshot of current terrain state."""
        stats = self._store.stats()
        snap_id = _sha(f"{tier}_{_ts()}")
        snap = TerrainSnapshot(
            snapshot_id=snap_id,
            raw_version=_sha("raw_" + _ts()),
            parse_version=_sha("parse_" + _ts()),
            index_version=_sha("index_" + _ts()),
            cpc_scope=cpc_scope or [],
            pub_count=stats["patents"],
            claim_count=stats["claims"],
            edge_count=stats["edges"],
            tier=tier,
        )
        self._store.store_snapshot(snap)

        if self._receipt_chain:
            self._receipt_chain.emit(
                "TERRAIN_SNAPSHOT",
                {"kind": "san_terrain", "ref": "snapshot"},
                {"snapshot_id": snap_id, "tier": tier},
                {"pub_count": snap.pub_count, "claim_count": snap.claim_count}
            )
        return snap

    def stats(self) -> dict:
        return self._store.stats()

    def _risk_level(self, risk: float) -> str:
        if risk < 0.2:   return "CLEAR"
        elif risk < 0.4: return "LOW"
        elif risk < 0.65: return "MODERATE"
        elif risk < 0.85: return "HIGH"
        else:            return "BLOCKING"


# ── Singleton ──────────────────────────────────────────────────────────────────

_engine: Optional[SANTerrainEngine] = None

def get_terrain_engine(receipt_chain=None) -> SANTerrainEngine:
    global _engine
    if _engine is None:
        from nss.core.storage import ALEXANDRIA_ROOT
        terrain_dir = ALEXANDRIA_ROOT / "terrain" / "uspto"
        terrain_dir.mkdir(parents=True, exist_ok=True)
        _engine = SANTerrainEngine(terrain_dir, receipt_chain=receipt_chain)
    elif receipt_chain and _engine._receipt_chain is None:
        _engine._receipt_chain = receipt_chain
    return _engine
