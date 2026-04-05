"""
Atomlex Graph Engine v4.0
==========================
Constraint-based semantic graph engine. Words are nodes. Constraints propagate.

Architecture: language = constraint propagation on directed graph
  Root nodes: canonical, fully analyzed, no parent
  Derived nodes: inherit parent constraints + add role-specific constraints
  Edges: semantic relationships (derived_from, constrains, grounds, limits)

ACPT (Algebraic Constraint Propagation Theory) drift scoring:
  severity = 0.5 × normalized_weighted_drift
           + 0.3 × conserved_loss
           + 0.2 × contradiction_score

  0.00-0.19: STABLE — variation within meaning
  0.20-0.39: SPECIALIZATION — domain narrowing
  0.40-0.59: TRANSFORMATION — heavy change
  0.60-0.79: DRIFT — concerning
  0.80-1.00: METAMORPHOSIS — critical, system failure

Semantic vector encoding (10 dimensions):
  [authority, responsibility, truth, dignity, constraint, freedom,
   relationship, knowledge, power, covenant]
  Each dimension: -1.0 (absent/inverted) to 1.0 (fully present)
"""

import json, os, logging, hashlib, random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

_log = logging.getLogger("atomlex.graph")

WORKSPACE = Path(os.environ.get("HR_WORKSPACE", "/Users/axiolevns/axiolev_runtime"))
_LEXICON_PATHS = [
    Path("/Volumes/NSExternal/.run/lexicon_seeds.jsonl"),
    WORKSPACE / ".run" / "lexicon_seeds.jsonl",
]
_GRAPH_PERSIST_PATH = WORKSPACE / ".run" / "atomlex_graph.json"

# ── Semantic vector dimensions ──────────────────────────────────────────────
VECTOR_DIMS = ["authority", "responsibility", "truth", "dignity", "constraint",
               "freedom", "relationship", "knowledge", "power", "covenant"]

# ── Drift thresholds (ACPT) ──────────────────────────────────────────────────
DRIFT_THRESHOLDS = {
    "STABLE": (0.0, 0.19),
    "SPECIALIZATION": (0.20, 0.39),
    "TRANSFORMATION": (0.40, 0.59),
    "DRIFT": (0.60, 0.79),
    "METAMORPHOSIS": (0.80, 1.0),
}


@dataclass
class ConstraintBundle:
    preconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=list)
    role_specific: Dict[str, List[str]] = field(default_factory=dict)

    def merge_with_parent(self, parent: "ConstraintBundle") -> "ConstraintBundle":
        """Propagate parent constraints. Child role_specific overrides, parent invariants are inherited."""
        return ConstraintBundle(
            preconditions=list(set(self.preconditions + parent.preconditions)),
            invariants=list(set(self.invariants + parent.invariants)),
            forbidden=list(set(self.forbidden + parent.forbidden)),
            role_specific={**parent.role_specific, **self.role_specific},
        )

    def check_contradiction(self) -> Tuple[bool, List[str]]:
        """Detect if any invariant is also in forbidden — that is a constraint collapse."""
        violations = [i for i in self.invariants if i in self.forbidden]
        return len(violations) > 0, violations


@dataclass
class SemanticNode:
    word: str
    status: str  # "canonical" | "derived" | "provisional"
    tier: int    # 1-5 from Gnoseogenic Lexicon
    parent: Optional[str]
    children: List[str]
    meaning: Dict[str, str]  # {canonical, root_act, ns_mapping}
    constraints: ConstraintBundle
    vector: List[float]  # 10-dimensional semantic vector
    pie_root: str
    semitic: str
    engine_component: str
    failure_mode: str
    drift: Optional[Dict[str, Any]]  # ACPT drift analysis
    edges: List[Dict[str, str]]  # [{to, type, weight}]
    priority: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def effective_constraints(self, graph: "SemanticGraph") -> ConstraintBundle:
        """Return constraints with parent propagation applied."""
        if self.parent and self.parent in graph.nodes:
            parent_node = graph.nodes[self.parent]
            parent_cb = parent_node.effective_constraints(graph)
            return self.constraints.merge_with_parent(parent_cb)
        return self.constraints

    def drift_score(self, graph: "SemanticGraph") -> Dict[str, Any]:
        """Compute ACPT drift score against root ancestor."""
        if self.status == "canonical" or not self.parent:
            return {"score": 0.0, "level": "STABLE", "details": "root node — no drift"}
        root = graph.get_root_ancestor(self.word)
        if not root or root.word == self.word:
            return {"score": 0.0, "level": "STABLE", "details": "no root found"}
        # Vector distance as drift proxy
        v1, v2 = self.vector, root.vector
        if len(v1) == len(v2) == 10:
            weighted_drift = sum(abs(a - b) * (1.0 / (i + 1)) for i, (a, b) in enumerate(zip(v1, v2)))
            normalized = weighted_drift / 10.0
            # Conserved loss: invariants in root but not in this node
            root_inv = set(root.constraints.invariants)
            self_inv = set(self.constraints.invariants)
            conserved_loss = len(root_inv - self_inv) / max(len(root_inv), 1)
            # Contradiction score
            has_contradiction, _ = self.constraints.check_contradiction()
            contradiction_score = 1.0 if has_contradiction else 0.0
            score = 0.5 * normalized + 0.3 * conserved_loss + 0.2 * contradiction_score
            level = next(
                (k for k, (lo, hi) in DRIFT_THRESHOLDS.items() if lo <= score <= hi),
                "METAMORPHOSIS"
            )
            return {
                "score": round(score, 4),
                "level": level,
                "normalized_weighted_drift": round(normalized, 4),
                "conserved_loss": round(conserved_loss, 4),
                "contradiction_score": contradiction_score,
                "root_ancestor": root.word,
            }
        return {"score": 0.0, "level": "STABLE", "details": "vector mismatch"}


class SemanticGraph:
    def __init__(self):
        self.nodes: Dict[str, SemanticNode] = {}
        self.edges: List[Dict[str, str]] = []
        self._load_canonical_nodes()

    def _load_canonical_nodes(self):
        """Seed the graph with the 12 canonical root nodes (the constitutional vocabulary backbone)."""
        canonical = [
            SemanticNode(
                word="authority", status="canonical", tier=4, parent=None, children=["allow","deny","law","guarantee"],
                meaning={"canonical": "decision-making power grounded in responsibility and accountability",
                         "root_act": "the right to direct action when bound by truth and responsibility",
                         "ns_mapping": "X-Founder-Key header + YubiKey quorum. Authority is the gate."},
                constraints=ConstraintBundle(
                    preconditions=["requires accountability", "requires truth-binding"],
                    invariants=["must imply responsibility", "cannot violate dignity", "requires accountability"],
                    forbidden=["bare power without responsibility", "authority without accountability"],
                    role_specific={"governance": ["must respect constitutional constraint"], "system": ["requires YubiKey quorum"]}
                ),
                vector=[1.0, 1.0, 0.9, 0.8, 0.7, 0.4, 0.7, 0.8, 0.9, 0.9],
                pie_root="*h₂ew- (to perceive, to guarantee)",
                semitic="סמכות (samkhut)",
                engine_component="output",
                failure_mode="constraint_collapse",
                drift={"status": "HIGH", "pattern": "authority → bare power", "signal": "responsibility_dropped"},
                edges=[{"to": "dignity", "type": "limited_by"}, {"to": "truth", "type": "grounded_in"}, {"to": "constraint", "type": "requires"}],
                priority="P1",
            ),
            SemanticNode(
                word="dignity", status="canonical", tier=4, parent=None, children=["responsibility","covenant"],
                meaning={"canonical": "the inherent gravitational mass of personhood; worth that cannot be conditional",
                         "root_act": "weight that makes a person resistant to arbitrary reduction",
                         "ns_mapping": "DignityKernel. H = eta·φ - beta·V. kavod = 'weight, honor'."},
                constraints=ConstraintBundle(
                    preconditions=["person exists"],
                    invariants=["cannot be conditional on performance", "applies universally", "grounds all other constraints"],
                    forbidden=["dignity contingent on behavior", "dignity as reward"],
                    role_specific={"system": ["H above block_threshold required for execution", "never-events protect dignity absolutely"]}
                ),
                vector=[0.6, 0.9, 0.8, 1.0, 0.9, 0.7, 0.9, 0.5, 0.2, 1.0],
                pie_root="*dek- (to take, receive; to be fitting)",
                semitic="כבוד (kavod — weight, honor)",
                engine_component="gradient_source",
                failure_mode="mismatch",
                drift={"status": "MODERATE", "pattern": "dignity → self-esteem", "signal": "universality_dropped"},
                edges=[{"to": "authority", "type": "limits"}, {"to": "shalom", "type": "required_for"}],
                priority="P1",
            ),
            SemanticNode(
                word="truth", status="canonical", tier=4, parent=None, children=["evidence","verification"],
                meaning={"canonical": "a state that corresponds to reality and bears load without deforming",
                         "root_act": "the load-bearing property of a statement — it holds when weight is applied",
                         "ns_mapping": "ABI freeze_hash. SHA256 of schema = the emet. Immutable, verifiable."},
                constraints=ConstraintBundle(
                    preconditions=["claim can be verified", "reality accessible"],
                    invariants=["must be verifiable", "cannot be merely asserted", "must be consistent across contexts"],
                    forbidden=["assertion without verification", "truth contingent on convenience"],
                    role_specific={"system": ["ABI schemas are frozen truth", "proof_registry is truth ledger"]}
                ),
                vector=[0.5, 0.8, 1.0, 0.7, 0.8, 0.3, 0.5, 1.0, 0.4, 0.8],
                pie_root="*deru- (oak, firm, solid — load-bearing)",
                semitic="אמת (emet — faithfulness, reliability)",
                engine_component="conversion",
                failure_mode="degradation",
                drift={"status": "MODERATE", "pattern": "truth → subjective experience", "signal": "verifiability_dropped"},
                edges=[{"to": "authority", "type": "grounds"}, {"to": "evidence", "type": "requires"}],
                priority="P1",
            ),
            SemanticNode(
                word="constraint", status="canonical", tier=5, parent=None, children=["law","rule","boundary"],
                meaning={"canonical": "a condition that limits the space of valid transitions; the boundary that makes action coherent",
                         "root_act": "binding — the act of tying a thing to its proper domain",
                         "ns_mapping": "The 9 frozen ABI schemas. The policy_profile on CPS. The dignity kernel H threshold."},
                constraints=ConstraintBundle(
                    preconditions=["action space is defined", "domain is specified"],
                    invariants=["must be explicit", "must be enforceable", "cannot be arbitrary"],
                    forbidden=["implicit constraint", "unenforced constraint", "constraint without basis"],
                    role_specific={"system": ["ABI validation at every boundary", "CPS policy_profile enforces at execution"]}
                ),
                vector=[0.4, 0.6, 0.9, 0.8, 1.0, 0.1, 0.5, 0.8, 0.3, 0.7],
                pie_root="*leig- (to bind, to tie)",
                semitic="אילוץ (ilus)",
                engine_component="meta_constraint",
                failure_mode="collapse",
                drift={"status": "LOW", "pattern": "constraint → restriction", "signal": "basis_dropped"},
                edges=[{"to": "logos", "type": "governed_by"}, {"to": "law", "type": "gives_rise_to"}],
                priority="P1",
            ),
            SemanticNode(
                word="logos", status="canonical", tier=5, parent=None, children=["engine","feedback_loop"],
                meaning={"canonical": "the gathering principle — the force that collects disparate elements into ordered, coherent structure",
                         "root_act": "gathering: to collect scattered things into unity that can speak and act as one",
                         "ns_mapping": "The Constitutional Regulation Engine. Logos is what makes all organs into one bloodstream."},
                constraints=ConstraintBundle(
                    preconditions=["elements exist to be gathered", "order is possible"],
                    invariants=["gathering must produce coherence", "cannot destroy what it gathers", "must be expressible"],
                    forbidden=["logos as mere logic", "logos as only speech", "gathering without ordering"],
                    role_specific={"system": ["NS∞ = logos made executable", "CPS chain = logos in action", "proof_registry = logos as memory"]}
                ),
                vector=[0.8, 0.9, 1.0, 0.9, 0.9, 0.6, 1.0, 1.0, 0.7, 1.0],
                pie_root="*leg- (to gather, to collect into order)",
                semitic="לוגוס (logos, borrowed; root: לקח — to take/gather)",
                engine_component="meta_constraint",
                failure_mode="all_modes_simultaneously",
                drift={"status": "HIGH", "pattern": "logos → pure logic / speech", "signal": "gathering_function_dropped"},
                edges=[{"to": "constraint", "type": "orders"}, {"to": "shalom", "type": "enables"}],
                priority="P1",
            ),
            SemanticNode(
                word="shalom", status="canonical", tier=5, parent=None, children=["wholeness","completeness"],
                meaning={"canonical": "structural wholeness: every component present, every relationship intact, nothing missing and nothing broken",
                         "root_act": "completion — the state where every part is in its right place and the whole functions as one",
                         "ns_mapping": "The system target state: sovereign=true, 29/29 ops, dignity enforced, quorum satisfied. Nothing missing, nothing broken."},
                constraints=ConstraintBundle(
                    preconditions=["all components present", "all relationships intact"],
                    invariants=["requires completeness", "requires nothing broken", "positive presence not merely absence of conflict"],
                    forbidden=["peace as mere absence of conflict", "shalom as passivity", "partial shalom"],
                    role_specific={"system": ["boot_mission_graph 29/29 = shalom", "sovereign=true + dignity_enforced = shalom"]}
                ),
                vector=[0.7, 1.0, 0.9, 1.0, 0.8, 1.0, 1.0, 0.8, 0.5, 1.0],
                pie_root="*sol- (whole, complete, uninjured)",
                semitic="שלום (shalom — completeness, wholeness, welfare)",
                engine_component="meta_constraint",
                failure_mode="collapse",
                drift={"status": "CRITICAL", "pattern": "shalom → absence of conflict", "signal": "completeness_replaced_by_negation"},
                edges=[{"to": "dignity", "type": "requires"}, {"to": "logos", "type": "produced_by"}],
                priority="P1",
            ),
            SemanticNode(
                word="allow", status="derived", tier=4, parent="authority", children=[],
                meaning={"canonical": "to grant permission for an action when the governing authority's constraints are satisfied",
                         "root_act": "opening the gate when conditions are met",
                         "ns_mapping": "The CPS execution path when policy_profile allows. dignity_enforced=True + quorum satisfied = allow."},
                constraints=ConstraintBundle(
                    preconditions=["authority exists", "constraints checked and satisfied"],
                    invariants=["grant requires authority's scope to be respected", "inherited: must imply responsibility"],
                    forbidden=["allow without checking constraints", "allow that violates dignity"],
                    role_specific={"system": ["ABI gate passed", "dignity kernel H above block_threshold", "quorum verified if boot.runtime"]}
                ),
                vector=[0.9, 0.9, 0.8, 0.7, 0.8, 1.0, 0.7, 0.7, 0.8, 0.8],
                pie_root="*h₂elu- (to free, to release)",
                semitic="להתיר (lehatir — to permit, to release a binding)",
                engine_component="output",
                failure_mode="blockage",
                drift=None,
                edges=[{"to": "authority", "type": "derived_from"}, {"to": "constraint", "type": "requires_satisfaction"}],
                priority="P1",
            ),
            SemanticNode(
                word="deny", status="derived", tier=4, parent="authority", children=[],
                meaning={"canonical": "to refuse permission when governing constraints are violated or authority scope exceeded",
                         "root_act": "closing the gate when conditions fail",
                         "ns_mapping": "400 abi_violation, 403 quorum_required, 422 dignity_violation. The system's deny is always principled."},
                constraints=ConstraintBundle(
                    preconditions=["authority exists", "constraint violation detected or scope exceeded"],
                    invariants=["denial must cite the violated constraint", "inherited: must imply responsibility", "must be reversible when constraint satisfied"],
                    forbidden=["arbitrary denial", "denial without explanation", "permanent denial without appeal"],
                    role_specific={"system": ["HTTP 400/403/422 with specific reason", "abi_violation or dignity_violation flags must be set"]}
                ),
                vector=[0.8, 0.8, 0.9, 0.8, 0.9, 0.0, 0.5, 0.7, 0.7, 0.7],
                pie_root="*ne- (not) + *gʷen- (to know)",
                semitic="לאסור (la'asor — to forbid, to bind up)",
                engine_component="output",
                failure_mode="blockage",
                drift=None,
                edges=[{"to": "authority", "type": "derived_from"}, {"to": "constraint", "type": "enforces"}],
                priority="P1",
            ),
            SemanticNode(
                word="evidence", status="derived", tier=3, parent="truth", children=[],
                meaning={"canonical": "a visible, verifiable artifact that grounds a claim in observable reality",
                         "root_act": "making truth visible — the act of producing what can be seen and verified",
                         "ns_mapping": "ProofEntry. Every boot emits a BootProofReceipt. Every schema freeze has a fingerprint. Evidence is the proof_id."},
                constraints=ConstraintBundle(
                    preconditions=["observable artifact exists", "claim is being made"],
                    invariants=["must be observable", "must be verifiable independently", "inherited: must be consistent across contexts"],
                    forbidden=["assertion presented as evidence", "unfalsifiable evidence"],
                    role_specific={"system": ["SHA256 fingerprint is evidence", "ProofEntry.proof_id is evidence", "boot receipt = sovereign evidence"]}
                ),
                vector=[0.3, 0.6, 1.0, 0.6, 0.7, 0.3, 0.4, 0.9, 0.3, 0.6],
                pie_root="*weid- (to see, to know by seeing)",
                semitic="עדות (edut — testimony, witness)",
                engine_component="feedback",
                failure_mode="blockage",
                drift=None,
                edges=[{"to": "truth", "type": "derived_from"}, {"to": "authority", "type": "grounds"}],
                priority="P1",
            ),
            SemanticNode(
                word="covenant", status="derived", tier=4, parent="dignity", children=[],
                meaning={"canonical": "a binding mutual agreement where both parties accept constraints that protect the other's dignity",
                         "root_act": "cutting — the act of creating a boundary both parties commit to honor",
                         "ns_mapping": "YubiKey enrollment. Serial 26116460 = the covenant token. Physical hardware as covenantal binding."},
                constraints=ConstraintBundle(
                    preconditions=["two parties with dignity", "mutual agreement possible", "constraints accepted by both"],
                    invariants=["mutual dignity protection", "both parties bound", "inherited: applies universally"],
                    forbidden=["one-sided covenant", "covenant without dignity protection", "covenant as mere contract"],
                    role_specific={"system": ["slot_1 serial = covenant binding", "X-Founder-Key = covenant token", "quorum = covenant fulfilled"]}
                ),
                vector=[0.5, 0.9, 0.8, 1.0, 0.8, 0.6, 1.0, 0.6, 0.3, 1.0],
                pie_root="*leig- (to bind, to tie — same root as 'league')",
                semitic="ברית (brit — covenant, cutting)",
                engine_component="output",
                failure_mode="blockage",
                drift=None,
                edges=[{"to": "dignity", "type": "derived_from"}, {"to": "authority", "type": "constrains"}],
                priority="P1",
            ),
            SemanticNode(
                word="law", status="derived", tier=4, parent="constraint", children=["rule","canon"],
                meaning={"canonical": "a gathered set of constraints that governs a domain — not restriction but instruction",
                         "root_act": "gathering rules into a system that directs action toward flourishing",
                         "ns_mapping": "The 9 frozen ABI schemas. The CPS policy_profile. Torah (instruction) not restriction."},
                constraints=ConstraintBundle(
                    preconditions=["domain defined", "authority to establish constraints exists", "purpose clear"],
                    invariants=["must be consistent", "must be enforceable", "inherited: must be explicit", "must be grounded in dignity"],
                    forbidden=["arbitrary law", "law without grounding", "law that destroys dignity"],
                    role_specific={"system": ["ABI is the law of the execution layer", "dignity kernel is the law of the constitutional layer"]}
                ),
                vector=[0.6, 0.7, 0.9, 0.8, 1.0, 0.2, 0.6, 0.8, 0.4, 0.9],
                pie_root="*leǵ- (to gather, collect — same root as logos)",
                semitic="תורה (Torah — instruction, direction) / דין (din — judgment, law)",
                engine_component="conversion",
                failure_mode="overload",
                drift=None,
                edges=[{"to": "constraint", "type": "derived_from"}, {"to": "logos", "type": "structured_by"}],
                priority="P1",
            ),
            SemanticNode(
                word="responsibility", status="derived", tier=4, parent="dignity", children=[],
                meaning={"canonical": "the obligation to respond appropriately to the dignity and needs of others, arising from one's own dignity",
                         "root_act": "responding — being the one who must answer when another calls",
                         "ns_mapping": "The Founder Console authority verbs: Approve Boot, Enroll YubiKey. Acts of responsibility."},
                constraints=ConstraintBundle(
                    preconditions=["other party exists with needs/dignity", "capacity to respond exists"],
                    invariants=["must be voluntarily accepted to be real", "inherited: applies universally", "cannot be forced without becoming duty"],
                    forbidden=["responsibility without capacity", "forced responsibility", "responsibility that destroys own dignity"],
                    role_specific={"system": ["X-Founder-Key = founder taking responsibility", "boot approval = responsibility for system state"]}
                ),
                vector=[0.4, 1.0, 0.7, 0.9, 0.7, 0.5, 0.9, 0.6, 0.3, 0.9],
                pie_root="*spend- (to make a libation, to make a solemn promise)",
                semitic="אחריות (achrayut — responsibility, accountability)",
                engine_component="output",
                failure_mode="blockage",
                drift=None,
                edges=[{"to": "dignity", "type": "derived_from"}, {"to": "authority", "type": "grounds"}],
                priority="P1",
            ),
        ]
        for node in canonical:
            self.nodes[node.word] = node
        self._build_edge_index()

    def _build_edge_index(self):
        self.edges = []
        for word, node in self.nodes.items():
            for e in node.edges:
                self.edges.append({"from": word, "to": e["to"], "type": e["type"]})

    def add_node(self, node: SemanticNode):
        self.nodes[node.word] = node
        self._build_edge_index()

    def get_root_ancestor(self, word: str) -> Optional[SemanticNode]:
        node = self.nodes.get(word)
        visited = set()
        while node and node.parent and node.parent not in visited:
            visited.add(node.word)
            node = self.nodes.get(node.parent, node)
        return node

    def get_subtree(self, word: str, depth: int = 3) -> List[str]:
        result = []
        def _walk(w, d):
            if d <= 0 or w not in self.nodes:
                return
            result.append(w)
            for child in self.nodes[w].children:
                _walk(child, d - 1)
        _walk(word, depth)
        return result

    def query(self, word: str) -> Optional[Dict[str, Any]]:
        """Full constraint propagation query — the core engine operation."""
        node = self.nodes.get(word.lower())
        if not node:
            return None
        effective_cb = node.effective_constraints(self)
        has_contradiction, violations = effective_cb.check_contradiction()
        drift = node.drift_score(self)
        parent_chain = []
        n = node
        while n.parent:
            parent_chain.append(n.parent)
            n = self.nodes.get(n.parent, n)
            if n.word in parent_chain:
                break
        return {
            "word": node.word,
            "status": node.status,
            "tier": node.tier,
            "priority": node.priority,
            "meaning": node.meaning,
            "constraints": {
                "effective": asdict(effective_cb),
                "own": asdict(node.constraints),
                "contradiction": has_contradiction,
                "violations": violations,
            },
            "vector": node.vector,
            "vector_dims": VECTOR_DIMS,
            "pie_root": node.pie_root,
            "semitic": node.semitic,
            "engine_component": node.engine_component,
            "failure_mode": node.failure_mode,
            "drift": drift,
            "parent_chain": parent_chain,
            "children": node.children,
            "edges": node.edges,
            "parent": node.parent,
        }

    def similarity(self, word1: str, word2: str) -> Optional[Dict[str, Any]]:
        """Cosine similarity between two word vectors."""
        n1 = self.nodes.get(word1.lower())
        n2 = self.nodes.get(word2.lower())
        if not n1 or not n2:
            return None
        v1, v2 = n1.vector, n2.vector
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = sum(a**2 for a in v1) ** 0.5
        mag2 = sum(b**2 for b in v2) ** 0.5
        cos_sim = dot / (mag1 * mag2) if mag1 and mag2 else 0.0
        return {
            "word1": word1, "word2": word2,
            "cosine_similarity": round(cos_sim, 4),
            "interpretation": "highly related" if cos_sim > 0.85 else "related" if cos_sim > 0.65 else "loosely related" if cos_sim > 0.4 else "weakly related"
        }

    def graph_status(self) -> Dict[str, Any]:
        tier_dist = dict(Counter(n.tier for n in self.nodes.values()))
        status_dist = dict(Counter(n.status for n in self.nodes.values()))
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "tier_distribution": {str(k): v for k, v in sorted(tier_dist.items())},
            "status_distribution": status_dist,
            "canonical_roots": [w for w, n in self.nodes.items() if n.status == "canonical"],
            "priority_p1": sum(1 for n in self.nodes.values() if n.priority == "P1"),
        }

    def seed_from_lexicon(self) -> int:
        """Expand graph from Gnoseogenic Lexicon file on disk. Adds provisional nodes for any new words."""
        added = 0
        for path in _LEXICON_PATHS:
            if not path.exists():
                continue
            try:
                for line in path.read_text().splitlines():
                    if not line.strip():
                        continue
                    e = json.loads(line)
                    word = e.get("word", "").lower().replace(" ", "_")
                    if not word or word in self.nodes:
                        continue
                    node = SemanticNode(
                        word=word,
                        status="provisional",
                        tier=e.get("tier", 3),
                        parent=None,
                        children=[],
                        meaning={
                            "canonical": e.get("cognitive_act", ""),
                            "root_act": e.get("cognitive_act", ""),
                            "ns_mapping": e.get("ns_mapping", ""),
                        },
                        constraints=ConstraintBundle(
                            preconditions=[],
                            invariants=[f"engine_component: {e.get('engine_component','')}"],
                            forbidden=[f"failure_mode: {e.get('failure_mode','')}"],
                        ),
                        vector=[0.5] * 10,
                        pie_root=e.get("pie_root", ""),
                        semitic=e.get("semitic", ""),
                        engine_component=e.get("engine_component", "conversion"),
                        failure_mode=e.get("failure_mode", "blockage"),
                        drift=None,
                        edges=[],
                        priority=e.get("priority", "P3"),
                    )
                    self.add_node(node)
                    added += 1
                _log.info("seed_from_lexicon: added %d provisional nodes from %s", added, path)
                return added
            except Exception as ex:
                _log.warning("seed_from_lexicon failed: %s", ex)
        return added


# Module-level singleton
_GRAPH: Optional[SemanticGraph] = None

def get_graph() -> SemanticGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = SemanticGraph()
        _GRAPH.seed_from_lexicon()
    return _GRAPH
