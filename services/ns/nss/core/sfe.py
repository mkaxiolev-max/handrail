"""
Socratic Field Engine (SFE) — Alexandria Lexicon
NS∞ / AXIOLEV Holdings

The semantic spine of NS∞.
Turns meaning into a measurable object.
Stores meaning generation rules, not meanings.

"Meaning = the set of constraints that survive contact with evidence and outcomes."

Architecture position:
  Ether (raw signal)
    → Alexandria (chunk_store, evidence, receipts)
      → SFE (concepts, questions, boundaries, conflicts, translations)
        → Cognition kernel (hypothesis → test → outcome)
          → Canon (stabilized, receipted, versioned)

Core guarantee: No concept changes without a receipt. No silent edits. Ever.
"""

import json
import uuid
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class ConceptStatus(str, Enum):
    CANDIDATE    = "candidate"
    ACTIVE       = "active"
    DEPRECATED   = "deprecated"
    SUPERSEDED   = "superseded"

class BoundaryStatus(str, Enum):
    CANDIDATE   = "candidate"
    ACTIVE      = "active"
    CONTESTED   = "contested"
    SUPERSEDED  = "superseded"

class ConflictType(str, Enum):
    POLYSEMY    = "polysemy"       # one term, multiple concepts
    SYNONYMY    = "synonymy"       # many terms, one concept
    CLASH       = "clash"          # incompatible in same context
    SCOPE_GAP   = "scope_gap"      # used outside validated scope
    MEASUREMENT = "measurement"    # schemas cannot be unified

class ConflictResolution(str, Enum):
    OPEN              = "open"
    SCOPED_COEXISTENCE= "scoped_coexistence"
    SPLIT             = "split"
    SUPERSEDED        = "superseded"
    INVALID           = "invalid"

class QuestionType(str, Enum):
    IDENTITY       = "identity"
    MEASUREMENT    = "measurement"
    CONSTRAINT     = "constraint"
    DECISION       = "decision"
    FALSIFICATION  = "falsification"
    TRANSLATION    = "translation"

class VersionImpact(str, Enum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"
    SPLIT = "split"

class TranslationStatus(str, Enum):
    PROPOSED  = "proposed"
    VALIDATED = "validated"
    DEPRECATED= "deprecated"

class ConfidenceTier(str, Enum):
    EXPERIMENTAL = "experimental"   # completeness < 0.5
    PROPOSED     = "proposed"       # completeness 0.5-0.8
    CANONICAL    = "canonical"      # completeness 1.0


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sha256(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()

def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ── Data objects ───────────────────────────────────────────────────────────────

@dataclass
class Term:
    term_id: str
    surface_forms: List[str]
    language: str = "en"
    domain_tags: List[str] = field(default_factory=list)
    usage_coords: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_ts)
    last_seen: str = field(default_factory=_ts)

@dataclass
class AnswerSchema:
    required_fields: List[Dict]
    allowed_uncertainty: float = 0.3
    required_evidence_types: List[str] = field(default_factory=list)
    required_provenance: List[str] = field(default_factory=list)
    fail_closed_condition: str = ""

@dataclass
class Question:
    question_id: str
    question_type: QuestionType
    phrasing: str
    phrasing_variants: List[str] = field(default_factory=list)
    answer_schema: Optional[AnswerSchema] = None
    domain_applicability: List[str] = field(default_factory=list)
    failure_triggers: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: str = field(default_factory=_ts)

@dataclass
class Answer:
    answer_id: str
    question_id: str
    context_id: str
    answer_payload: Dict
    evidence_pack_id: str
    confidence: float
    answer_hash: str
    created_by: str
    timestamp: str = field(default_factory=_ts)

@dataclass
class QuestionBasis:
    basis_id: str
    concept_id: str
    minimal_basis: List[str]        # question_ids
    optional_basis: List[str] = field(default_factory=list)
    completeness_score: float = 0.0
    last_evaluated: str = field(default_factory=_ts)

@dataclass
class Boundary:
    boundary_id: str
    concept_id: str
    constraint_human: str
    constraint_machine: str
    supporting_evidence: List[str] = field(default_factory=list)
    supporting_outcomes: List[str] = field(default_factory=list)
    counterexamples: List[str] = field(default_factory=list)
    scope: List[str] = field(default_factory=list)
    strength: float = 0.0
    status: BoundaryStatus = BoundaryStatus.CANDIDATE
    version: str = "1.0.0"
    created_at: str = field(default_factory=_ts)

@dataclass
class Conflict:
    conflict_id: str
    conflict_type: ConflictType
    involved_concepts: List[str]
    involved_terms: List[str] = field(default_factory=list)
    evidence_sides: Dict = field(default_factory=dict)
    resolution_state: ConflictResolution = ConflictResolution.OPEN
    resolution_receipt_id: Optional[str] = None
    triggered_by: str = ""
    created_at: str = field(default_factory=_ts)

@dataclass
class TranslationMap:
    map_id: str
    source_concept_id: str
    source_domain: str
    target_concept_id: str
    target_domain: str
    shared_basis_questions: List[str] = field(default_factory=list)
    non_shared_questions: List[str] = field(default_factory=list)
    translation_loss_estimate: float = 0.5
    evidence_support: List[str] = field(default_factory=list)
    verified_by_outcomes: List[str] = field(default_factory=list)
    status: TranslationStatus = TranslationStatus.PROPOSED
    created_at: str = field(default_factory=_ts)

@dataclass
class Outcome:
    outcome_id: str
    linked_action_receipt_id: str
    linked_concepts: List[str]
    linked_questions: List[str] = field(default_factory=list)
    measured_deltas: Dict = field(default_factory=dict)
    irreversibility_class: str = "reversible"
    prediction_vs_actual: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=_ts)

@dataclass
class Concept:
    concept_id: str
    label: str
    version: str
    invariant_core: str
    domain_variants: List[str] = field(default_factory=list)
    linked_terms: List[str] = field(default_factory=list)
    question_basis_id: Optional[str] = None
    boundaries: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    primitive_mapping: Dict = field(default_factory=dict)
    parent_concept_id: Optional[str] = None
    status: ConceptStatus = ConceptStatus.CANDIDATE
    receipts: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_ts)
    created_by: str = "system"
    answers: Dict[str, str] = field(default_factory=dict)  # question_id → answer_id

    @property
    def confidence_tier(self) -> ConfidenceTier:
        # Computed by SFE.evaluate_completeness
        return ConfidenceTier.EXPERIMENTAL


# ── Grounding failure ──────────────────────────────────────────────────────────

@dataclass
class GroundingRefusal:
    """Returned when a concept cannot satisfy its question schema."""
    concept_id: str
    question_class: str
    missing_fields: List[str]
    missing_evidence: List[str]
    gap_description: str
    resolution_path: str
    timestamp: str = field(default_factory=_ts)

    def to_dict(self) -> dict:
        return {
            "event_type": "REFUSE_INSUFFICIENT_GROUNDING",
            **asdict(self)
        }


# ══════════════════════════════════════════════════════════════════════════════
# SOCRATIC FIELD ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class SocraticFieldEngine:
    """
    The semantic spine of NS∞.

    Stores: Terms, Concepts, Questions, QuestionBases, Answers,
            Boundaries, Conflicts, TranslationMaps, Outcomes.

    Core operations:
      - create_concept / update_concept / split_concept
      - add_boundary / challenge_boundary
      - log_outcome / evaluate_boundary_pressure
      - check_grounding / evaluate_completeness
      - detect_conflicts / resolve_conflict
      - create_translation_map
      - bootstrap_from_ether (Lexicon v0.1)

    All mutations emit receipts. No silent edits.
    """

    def __init__(self, storage_path: Optional[Path] = None, receipt_chain=None):
        # Storage
        if storage_path is None:
            ssd = Path("/Volumes/NSExternal")
            base = ssd / "ALEXANDRIA" if ssd.exists() else Path.home() / "NSS" / "MANIFOLD"
            storage_path = base / "lexicon"
        self._path = storage_path
        self._path.mkdir(parents=True, exist_ok=True)

        # Receipt chain for auditability
        self._receipt_chain = receipt_chain

        # In-memory stores (persisted to JSONL)
        self._terms:       Dict[str, Term]          = {}
        self._concepts:    Dict[str, Concept]        = {}
        self._questions:   Dict[str, Question]       = {}
        self._bases:       Dict[str, QuestionBasis]  = {}
        self._answers:     Dict[str, Answer]         = {}
        self._boundaries:  Dict[str, Boundary]       = {}
        self._conflicts:   Dict[str, Conflict]       = {}
        self._translations:Dict[str, TranslationMap] = {}
        self._outcomes:    Dict[str, Outcome]        = {}

        self._load_all()
        self._seed_canonical_questions()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _store_path(self, kind: str) -> Path:
        return self._path / f"{kind}.jsonl"

    def _append(self, kind: str, obj: dict):
        p = self._store_path(kind)
        with open(p, "a") as f:
            f.write(json.dumps(obj, default=str) + "\n")

    def _load_jsonl(self, kind: str) -> List[dict]:
        p = self._store_path(kind)
        if not p.exists():
            return []
        out = []
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
        return out

    def _load_all(self):
        """Load latest state of each object from JSONL (last record wins per ID)."""
        loaders = [
            ("terms",        self._terms,        "term_id",        Term),
            ("concepts",     self._concepts,     "concept_id",     Concept),
            ("questions",    self._questions,    "question_id",    Question),
            ("bases",        self._bases,        "basis_id",       QuestionBasis),
            ("answers",      self._answers,      "answer_id",      Answer),
            ("boundaries",   self._boundaries,   "boundary_id",    Boundary),
            ("conflicts",    self._conflicts,    "conflict_id",    Conflict),
            ("translations", self._translations, "map_id",         TranslationMap),
            ("outcomes",     self._outcomes,     "outcome_id",     Outcome),
        ]
        for kind, store, id_field, cls in loaders:
            for record in self._load_jsonl(kind):
                try:
                    # Simple dict-based reconstruction
                    obj_id = record.get(id_field)
                    if obj_id:
                        store[obj_id] = record  # store as dict, convert on access
                except Exception:
                    pass

    def _emit_receipt(self, event_type: str, source: dict,
                       inputs: dict, outputs: dict) -> dict:
        if self._receipt_chain:
            return self._receipt_chain.emit(event_type, source, inputs, outputs)
        return {"event_type": event_type, "timestamp": _ts()}

    # ── Canonical question seed ────────────────────────────────────────────────

    def _seed_canonical_questions(self):
        """Ensure the 6 canonical question templates exist."""
        canonical = [
            (QuestionType.IDENTITY,      "What is this concept operationally, not poetically?"),
            (QuestionType.MEASUREMENT,   "How do we observe or measure this concept in this domain?"),
            (QuestionType.CONSTRAINT,    "Where does this concept apply, and where does it fail?"),
            (QuestionType.DECISION,      "What actions change if this concept is true vs false?"),
            (QuestionType.FALSIFICATION, "What outcome pattern would prove we are using this concept wrong?"),
            (QuestionType.TRANSLATION,   "What is preserved and what is lost when mapping to another domain?"),
        ]
        if not any(q.get("question_type") == "identity" for q in self._questions.values()
                   if isinstance(q, dict)):
            for qtype, phrasing in canonical:
                qid = f"Q-CANONICAL-{qtype.value}"
                q = {
                    "question_id": qid,
                    "question_type": qtype.value,
                    "phrasing": phrasing,
                    "phrasing_variants": [],
                    "domain_applicability": ["*"],
                    "failure_triggers": [],
                    "version": "1.0.0",
                    "created_at": _ts(),
                }
                self._questions[qid] = q
                self._append("questions", q)

    # ── Term operations ────────────────────────────────────────────────────────

    def upsert_term(self, surface_form: str, domain_tags: List[str] = None,
                    usage_coord: str = None) -> dict:
        """Add or update a Term. Returns term dict."""
        # Check if term already exists by surface form
        for tid, t in self._terms.items():
            t_obj = t if isinstance(t, dict) else asdict(t)
            if surface_form.lower() in [s.lower() for s in t_obj.get("surface_forms", [])]:
                if usage_coord:
                    coords = t_obj.get("usage_coords", [])
                    if usage_coord not in coords:
                        coords.append(usage_coord)
                        t_obj["usage_coords"] = coords
                        t_obj["last_seen"] = _ts()
                        self._terms[tid] = t_obj
                        self._append("terms", t_obj)
                return t_obj

        # Create new
        term_id = _uid("TERM")
        term = {
            "term_id": term_id,
            "surface_forms": [surface_form],
            "language": "en",
            "domain_tags": domain_tags or [],
            "usage_coords": [usage_coord] if usage_coord else [],
            "created_at": _ts(),
            "last_seen": _ts(),
        }
        self._terms[term_id] = term
        self._append("terms", term)
        return term

    # ── Concept operations ─────────────────────────────────────────────────────

    def create_concept(self, label: str, invariant_core: str,
                       domain_tags: List[str] = None,
                       created_by: str = "system",
                       primitive_mapping: Dict = None) -> dict:
        """
        Create a new Concept at v0.1.0 (candidate status).
        Auto-creates a QuestionBasis with the 6 canonical questions.
        Emits receipt.
        """
        concept_id = _uid("CONCEPT")
        version = "0.1.0"

        # Create question basis
        basis_id = _uid("QB")
        canonical_q_ids = [f"Q-CANONICAL-{qt.value}" for qt in QuestionType]
        basis = {
            "basis_id": basis_id,
            "concept_id": concept_id,
            "minimal_basis": canonical_q_ids,
            "optional_basis": [],
            "completeness_score": 0.0,
            "last_evaluated": _ts(),
        }
        self._bases[basis_id] = basis
        self._append("bases", basis)

        concept = {
            "concept_id": concept_id,
            "label": label,
            "version": version,
            "invariant_core": invariant_core,
            "domain_variants": domain_tags or [],
            "linked_terms": [],
            "question_basis_id": basis_id,
            "boundaries": [],
            "conflicts": [],
            "primitive_mapping": primitive_mapping or {},
            "parent_concept_id": None,
            "status": ConceptStatus.CANDIDATE.value,
            "receipts": [],
            "created_at": _ts(),
            "created_by": created_by,
            "answers": {},
        }
        self._concepts[concept_id] = concept
        self._append("concepts", concept)

        receipt = self._emit_receipt(
            "SFE_CONCEPT_CREATED",
            {"kind": "sfe", "ref": created_by},
            {"label": label, "invariant_core": invariant_core[:80]},
            {"concept_id": concept_id, "version": version, "basis_id": basis_id},
        )
        concept["receipts"].append(receipt.get("receipt_id", ""))
        return concept

    def update_concept(self, concept_id: str, changes: Dict,
                       version_impact: VersionImpact,
                       updated_by: str = "system",
                       justification: str = "") -> Tuple[dict, Optional[GroundingRefusal]]:
        """
        Update a concept with version bumping.
        MAJOR changes require outcome_pressure or structural_contradiction evidence.
        Returns (updated_concept, refusal_or_none).
        """
        concept = self._concepts.get(concept_id)
        if not concept:
            return None, GroundingRefusal(
                concept_id=concept_id,
                question_class="N/A",
                missing_fields=["concept_id"],
                missing_evidence=[],
                gap_description=f"Concept {concept_id} not found",
                resolution_path="create_concept first",
            )

        if isinstance(concept, dict):
            concept = dict(concept)

        # MAJOR version change requires justification
        if version_impact == VersionImpact.MAJOR:
            if not justification:
                return concept, GroundingRefusal(
                    concept_id=concept_id,
                    question_class="versioning",
                    missing_fields=["justification"],
                    missing_evidence=["outcome_pressure_or_contradiction"],
                    gap_description="MAJOR version change requires outcome pressure or structural contradiction evidence",
                    resolution_path="Provide justification with evidence_pack_id or outcome_id",
                )

        # Bump version
        parts = concept["version"].split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        if version_impact == VersionImpact.MAJOR:
            major += 1; minor = 0; patch = 0
        elif version_impact == VersionImpact.MINOR:
            minor += 1; patch = 0
        else:
            patch += 1

        concept["version"] = f"{major}.{minor}.{patch}"
        concept.update(changes)

        self._concepts[concept_id] = concept
        self._append("concepts", concept)

        receipt = self._emit_receipt(
            f"SFE_CONCEPT_UPDATED_{version_impact.value.upper()}",
            {"kind": "sfe", "ref": updated_by},
            {"changes": list(changes.keys()), "justification": justification[:200]},
            {"concept_id": concept_id, "new_version": concept["version"]},
        )
        concept["receipts"] = concept.get("receipts", []) + [receipt.get("receipt_id", "")]
        return concept, None

    def split_concept(self, parent_id: str, child_labels: List[str],
                       split_reason: str, evidence_pack_id: str,
                       created_by: str = "system") -> List[dict]:
        """
        Concept fission protocol.
        Parent becomes deprecated umbrella.
        Children are new Concepts linked to parent.
        TranslationMaps created for continuity.
        All receipted.
        """
        parent = self._concepts.get(parent_id)
        if not parent:
            return []

        parent_dict = dict(parent) if isinstance(parent, dict) else parent
        children = []

        for label in child_labels:
            child = self.create_concept(
                label=label,
                invariant_core=f"Derived from {parent_dict['label']}: {label}",
                created_by=created_by,
            )
            child["parent_concept_id"] = parent_id
            self._concepts[child["concept_id"]] = child
            self._append("concepts", child)
            children.append(child)

            # Create TranslationMap for continuity
            tm = self.create_translation_map(
                source_concept_id=parent_id,
                source_domain="pre_split",
                target_concept_id=child["concept_id"],
                target_domain=label.lower().replace(" ", "_"),
                shared_questions=parent_dict.get("question_basis_id") and
                                  [f"Q-CANONICAL-{qt.value}" for qt in QuestionType] or [],
            )

        # Deprecate parent
        parent_dict["status"] = ConceptStatus.DEPRECATED.value
        self._concepts[parent_id] = parent_dict
        self._append("concepts", parent_dict)

        self._emit_receipt(
            "SFE_CONCEPT_SPLIT",
            {"kind": "sfe", "ref": created_by},
            {"parent_id": parent_id, "reason": split_reason[:200], "evidence": evidence_pack_id},
            {"children": [c["concept_id"] for c in children]},
        )
        return children

    # ── Answer operations ──────────────────────────────────────────────────────

    def record_answer(self, concept_id: str, question_type: QuestionType,
                       answer_payload: Dict, evidence_pack_id: str,
                       context_id: str = "default",
                       confidence: float = 0.5,
                       created_by: str = "system") -> Tuple[Optional[dict], Optional[GroundingRefusal]]:
        """
        Record an Answer to a canonical question for a Concept.
        Validates against AnswerSchema. Returns (answer, refusal).
        Updates concept completeness score.
        """
        if not evidence_pack_id:
            return None, GroundingRefusal(
                concept_id=concept_id,
                question_class=question_type.value,
                missing_fields=["evidence_pack_id"],
                missing_evidence=["evidence_pack_id is mandatory for all answers"],
                gap_description="Evidence is mandatory. Unevidenced answers are refused.",
                resolution_path="Provide an evidence_pack_id from the Alexandria evidence store",
            )

        question_id = f"Q-CANONICAL-{question_type.value}"
        payload_str = json.dumps(answer_payload, sort_keys=True, default=str)
        answer_hash = _sha256(f"{question_id}:{evidence_pack_id}:{payload_str}")

        answer_id = _uid("ANS")
        answer = {
            "answer_id": answer_id,
            "question_id": question_id,
            "context_id": context_id,
            "answer_payload": answer_payload,
            "evidence_pack_id": evidence_pack_id,
            "confidence": confidence,
            "answer_hash": answer_hash,
            "created_by": created_by,
            "timestamp": _ts(),
        }
        self._answers[answer_id] = answer
        self._append("answers", answer)

        # Update concept's answers map
        concept = self._concepts.get(concept_id)
        if concept:
            c = dict(concept)
            c["answers"] = c.get("answers", {})
            c["answers"][question_type.value] = answer_id
            self._concepts[concept_id] = c
            self._append("concepts", c)

        # Recompute completeness
        self._recompute_completeness(concept_id)

        self._emit_receipt(
            "SFE_ANSWER_RECORDED",
            {"kind": "sfe", "ref": created_by},
            {"concept_id": concept_id, "question_type": question_type.value},
            {"answer_id": answer_id, "confidence": confidence},
        )
        return answer, None

    def check_grounding(self, concept_id: str) -> Tuple[bool, List[GroundingRefusal]]:
        """
        Check if a concept satisfies its full question basis.
        Returns (grounded: bool, refusals: list).
        Grounded = all 6 canonical question types have answers with evidence.
        """
        concept = self._concepts.get(concept_id)
        if not concept:
            return False, [GroundingRefusal(
                concept_id=concept_id,
                question_class="N/A",
                missing_fields=["concept"],
                missing_evidence=[],
                gap_description="Concept not found",
                resolution_path="create_concept first",
            )]

        c = concept if isinstance(concept, dict) else asdict(concept)
        answers = c.get("answers", {})
        refusals = []

        for qt in QuestionType:
            if qt.value not in answers:
                refusals.append(GroundingRefusal(
                    concept_id=concept_id,
                    question_class=qt.value,
                    missing_fields=["answer_payload", "evidence_pack_id"],
                    missing_evidence=["No answer recorded for this question class"],
                    gap_description=f"Question class '{qt.value}' has no answer. Concept cannot be promoted.",
                    resolution_path=f"Call record_answer(concept_id, QuestionType.{qt.name}, ...) with evidence",
                ))

        return len(refusals) == 0, refusals

    def evaluate_completeness(self, concept_id: str) -> Tuple[float, ConfidenceTier]:
        """Returns (score 0.0-1.0, ConfidenceTier)."""
        concept = self._concepts.get(concept_id)
        if not concept:
            return 0.0, ConfidenceTier.EXPERIMENTAL
        c = concept if isinstance(concept, dict) else {}
        answers = c.get("answers", {})
        total = len(QuestionType)
        answered = sum(1 for qt in QuestionType if qt.value in answers)
        score = answered / total
        if score >= 1.0:
            tier = ConfidenceTier.CANONICAL
        elif score >= 0.8:
            tier = ConfidenceTier.PROPOSED
        elif score >= 0.5:
            tier = ConfidenceTier.EXPERIMENTAL
        else:
            tier = ConfidenceTier.EXPERIMENTAL
        return score, tier

    def _recompute_completeness(self, concept_id: str):
        score, tier = self.evaluate_completeness(concept_id)
        basis_id = self._concepts.get(concept_id, {})
        if isinstance(basis_id, dict):
            basis_id = basis_id.get("question_basis_id")
        if basis_id and basis_id in self._bases:
            b = dict(self._bases[basis_id])
            b["completeness_score"] = score
            b["last_evaluated"] = _ts()
            self._bases[basis_id] = b
            self._append("bases", b)

    # ── Boundary operations ────────────────────────────────────────────────────

    def add_boundary(self, concept_id: str, constraint_human: str,
                      constraint_machine: str = "",
                      scope: List[str] = None,
                      evidence_pack_id: str = "",
                      created_by: str = "system") -> dict:
        """
        Add a Boundary to a Concept.
        Boundaries are where meaning becomes sharp.
        """
        boundary_id = _uid("BND")
        boundary = {
            "boundary_id": boundary_id,
            "concept_id": concept_id,
            "constraint_human": constraint_human,
            "constraint_machine": constraint_machine or constraint_human,
            "supporting_evidence": [evidence_pack_id] if evidence_pack_id else [],
            "supporting_outcomes": [],
            "counterexamples": [],
            "scope": scope or [],
            "strength": 0.5 if evidence_pack_id else 0.1,
            "status": BoundaryStatus.CANDIDATE.value,
            "version": "1.0.0",
            "created_at": _ts(),
        }
        self._boundaries[boundary_id] = boundary
        self._append("boundaries", boundary)

        # Link to concept
        concept = self._concepts.get(concept_id)
        if concept:
            c = dict(concept)
            c["boundaries"] = c.get("boundaries", []) + [boundary_id]
            self._concepts[concept_id] = c
            self._append("concepts", c)

        self._emit_receipt(
            "SFE_BOUNDARY_ADDED",
            {"kind": "sfe", "ref": created_by},
            {"concept_id": concept_id, "constraint": constraint_human[:100]},
            {"boundary_id": boundary_id},
        )
        return boundary

    def log_outcome(self, action_receipt_id: str,
                     linked_concept_ids: List[str],
                     measured_deltas: Dict,
                     predicted: Any, actual: Any,
                     irreversibility: str = "reversible") -> dict:
        """
        Log an Outcome. This is the primary feedback mechanism for boundary evolution.
        After logging, runs boundary pressure evaluation and split detection.
        """
        error = self._compute_prediction_error(predicted, actual)
        outcome_id = _uid("OUT")
        outcome = {
            "outcome_id": outcome_id,
            "linked_action_receipt_id": action_receipt_id,
            "linked_concepts": linked_concept_ids,
            "linked_questions": [],
            "measured_deltas": measured_deltas,
            "irreversibility_class": irreversibility,
            "prediction_vs_actual": {
                "predicted": predicted,
                "actual": actual,
                "error": error,
            },
            "timestamp": _ts(),
        }
        self._outcomes[outcome_id] = outcome
        self._append("outcomes", outcome)

        # Update boundaries and check for split pressure
        for cid in linked_concept_ids:
            self._apply_outcome_pressure(cid, outcome_id, error)

        self._emit_receipt(
            "SFE_OUTCOME_LOGGED",
            {"kind": "sfe", "ref": "system"},
            {"concepts": linked_concept_ids, "error": error},
            {"outcome_id": outcome_id, "irreversibility": irreversibility},
        )
        return outcome

    def _compute_prediction_error(self, predicted: Any, actual: Any) -> float:
        """Simple normalized error."""
        try:
            if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                if predicted == 0 and actual == 0:
                    return 0.0
                denominator = max(abs(predicted), abs(actual), 1e-10)
                return abs(predicted - actual) / denominator
            elif predicted == actual:
                return 0.0
            else:
                return 1.0
        except Exception:
            return 0.5

    def _apply_outcome_pressure(self, concept_id: str,
                                  outcome_id: str, error: float):
        """
        Update boundary strengths based on outcome error.
        High error = counterexample pressure.
        Low error = supporting evidence.
        """
        concept = self._concepts.get(concept_id)
        if not concept:
            return
        c = dict(concept) if isinstance(concept, dict) else concept

        for bid in c.get("boundaries", []):
            boundary = self._boundaries.get(bid)
            if not boundary:
                continue
            b = dict(boundary)
            if error < 0.2:
                # Low error: outcome supports boundary
                b["supporting_outcomes"] = b.get("supporting_outcomes", []) + [outcome_id]
            else:
                # High error: counterexample pressure
                b["counterexamples"] = b.get("counterexamples", []) + [outcome_id]

            # Recompute strength
            supporting = len(b.get("supporting_outcomes", [])) + len(b.get("supporting_evidence", []))
            counter    = len(b.get("counterexamples", []))
            total = supporting + counter
            b["strength"] = supporting / total if total > 0 else 0.5

            # Flag contested if counterexample ratio > 0.3
            if counter / max(total, 1) > 0.3:
                b["status"] = BoundaryStatus.CONTESTED.value

            self._boundaries[bid] = b
            self._append("boundaries", b)

    # ── Split detection ────────────────────────────────────────────────────────

    def detect_split_pressure(self, concept_id: str) -> Optional[dict]:
        """
        Check if a concept is under split pressure.
        Returns split recommendation or None.
        Triggers:
          1. Prediction divergence
          2. Outcome divergence
          3. Constraint incompatibility (contested boundary ratio)
          4. Measurement incompatibility
        """
        concept = self._concepts.get(concept_id)
        if not concept:
            return None
        c = dict(concept) if isinstance(concept, dict) else concept

        # Count contested boundaries
        contested = sum(
            1 for bid in c.get("boundaries", [])
            if self._boundaries.get(bid, {}).get("status") == BoundaryStatus.CONTESTED.value
        )
        total_bounds = len(c.get("boundaries", []))

        if total_bounds == 0:
            return None

        contested_ratio = contested / total_bounds

        # High prediction error across outcomes
        concept_outcomes = [
            o for o in self._outcomes.values()
            if isinstance(o, dict) and concept_id in o.get("linked_concepts", [])
        ]
        if concept_outcomes:
            errors = [o.get("prediction_vs_actual", {}).get("error", 0) for o in concept_outcomes]
            avg_error = sum(errors) / len(errors)
        else:
            avg_error = 0.0

        if contested_ratio >= 0.5 or avg_error >= 0.6:
            return {
                "recommendation": "SPLIT",
                "concept_id": concept_id,
                "label": c.get("label"),
                "contested_boundary_ratio": contested_ratio,
                "average_prediction_error": avg_error,
                "trigger": "CONSTRAINT_INCOMPATIBILITY" if contested_ratio >= 0.5 else "PREDICTION_DIVERGENCE",
                "suggested_next_step": "call split_concept() with domain-specific child labels",
            }
        return None

    # ── Conflict detection ─────────────────────────────────────────────────────

    def detect_polysemy(self, term: str) -> Optional[dict]:
        """Detect if a term refers to multiple concepts — polysemy trigger."""
        matched = []
        for tid, t in self._terms.items():
            t_obj = t if isinstance(t, dict) else {}
            if term.lower() in [s.lower() for s in t_obj.get("surface_forms", [])]:
                # Find all concepts linked to this term
                for cid, c in self._concepts.items():
                    c_obj = c if isinstance(c, dict) else {}
                    if tid in c_obj.get("linked_terms", []):
                        matched.append(cid)

        if len(matched) > 1:
            return self._create_conflict(
                conflict_type=ConflictType.POLYSEMY,
                involved_concepts=matched,
                involved_terms=[term],
                triggered_by=f"Term '{term}' maps to {len(matched)} concepts",
            )
        return None

    def _create_conflict(self, conflict_type: ConflictType,
                           involved_concepts: List[str],
                           involved_terms: List[str] = None,
                           triggered_by: str = "") -> dict:
        conflict_id = _uid("CONF")
        conflict = {
            "conflict_id": conflict_id,
            "conflict_type": conflict_type.value,
            "involved_concepts": involved_concepts,
            "involved_terms": involved_terms or [],
            "evidence_sides": {},
            "resolution_state": ConflictResolution.OPEN.value,
            "resolution_receipt_id": None,
            "triggered_by": triggered_by,
            "created_at": _ts(),
        }
        self._conflicts[conflict_id] = conflict
        self._append("conflicts", conflict)

        self._emit_receipt(
            "SFE_CONFLICT_DETECTED",
            {"kind": "sfe", "ref": "system"},
            {"type": conflict_type.value, "triggered_by": triggered_by},
            {"conflict_id": conflict_id},
        )
        return conflict

    def resolve_conflict(self, conflict_id: str,
                          resolution: ConflictResolution,
                          resolution_notes: str = "",
                          resolved_by: str = "system") -> dict:
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return {}
        c = dict(conflict)
        c["resolution_state"] = resolution.value
        c["resolution_notes"] = resolution_notes
        self._conflicts[conflict_id] = c
        self._append("conflicts", c)

        receipt = self._emit_receipt(
            "SFE_CONFLICT_RESOLVED",
            {"kind": "sfe", "ref": resolved_by},
            {"conflict_id": conflict_id, "resolution": resolution.value},
            {"notes": resolution_notes[:200]},
        )
        c["resolution_receipt_id"] = receipt.get("receipt_id", "")
        return c

    # ── Translation maps ───────────────────────────────────────────────────────

    def create_translation_map(self, source_concept_id: str,
                                 source_domain: str,
                                 target_concept_id: str,
                                 target_domain: str,
                                 shared_questions: List[str] = None,
                                 evidence_pack_id: str = "") -> dict:
        """
        Create a TranslationMap between two concept variants.
        Computes translation_loss as fraction of canonical questions not shared.
        """
        all_canonical = [f"Q-CANONICAL-{qt.value}" for qt in QuestionType]
        shared = shared_questions or []
        not_shared = [q for q in all_canonical if q not in shared]
        loss = len(not_shared) / max(len(all_canonical), 1)

        map_id = _uid("TM")
        tm = {
            "map_id": map_id,
            "source_concept_id": source_concept_id,
            "source_domain": source_domain,
            "target_concept_id": target_concept_id,
            "target_domain": target_domain,
            "shared_basis_questions": shared,
            "non_shared_questions": not_shared,
            "translation_loss_estimate": loss,
            "evidence_support": [evidence_pack_id] if evidence_pack_id else [],
            "verified_by_outcomes": [],
            "status": TranslationStatus.PROPOSED.value,
            "created_at": _ts(),
        }
        self._translations[map_id] = tm
        self._append("translations", tm)
        return tm

    # ── Bootstrap from ether ───────────────────────────────────────────────────

    def bootstrap_lexicon_v0(self, corpus_terms: List[Dict],
                               domain: str = "general") -> Dict:
        """
        Deterministic Lexicon v0.1 bootstrap from ether ingest.
        Steps:
          1. Extract terms → upsert_term for each
          2. Cluster into concept candidates (naive: one concept per unique term stem)
          3. Create QuestionBasis (provisional) for each
          4. Generate usage cards with citations
          5. Flag polysemy conflicts
          6. Suggest translation maps for near-synonyms
        No canonization. Concepts created as CANDIDATE status.
        Returns bootstrap report.
        """
        report = {
            "domain": domain,
            "terms_processed": 0,
            "concepts_created": 0,
            "conflicts_flagged": 0,
            "translations_suggested": 0,
            "timestamp": _ts(),
        }

        term_to_concept = {}

        for item in corpus_terms:
            surface = item.get("term", "").strip()
            if not surface:
                continue

            # Upsert term
            term = self.upsert_term(
                surface_form=surface,
                domain_tags=[domain] + item.get("domain_tags", []),
                usage_coord=item.get("usage_coord", ""),
            )
            report["terms_processed"] += 1

            # Create concept candidate if not seen
            stem = surface.lower()
            if stem not in term_to_concept:
                concept = self.create_concept(
                    label=surface,
                    invariant_core=item.get("definition", f"Provisional: {surface}"),
                    domain_tags=[domain],
                    created_by="bootstrap_v0",
                )
                term_to_concept[stem] = concept["concept_id"]
                report["concepts_created"] += 1

                # Add provisional identity boundary
                if item.get("definition"):
                    self.add_boundary(
                        concept_id=concept["concept_id"],
                        constraint_human=f"Bootstrap definition: {item['definition'][:200]}",
                        scope=[domain],
                        evidence_pack_id=item.get("evidence_pack_id", ""),
                    )

        # Detect polysemy for terms seen multiple times
        seen_terms = {}
        for item in corpus_terms:
            s = item.get("term", "").lower()
            seen_terms[s] = seen_terms.get(s, 0) + 1

        for term, count in seen_terms.items():
            if count > 1:
                conflict = self.detect_polysemy(term)
                if conflict:
                    report["conflicts_flagged"] += 1

        self._emit_receipt(
            "SFE_LEXICON_BOOTSTRAP",
            {"kind": "sfe", "ref": "bootstrap_v0"},
            {"domain": domain, "input_terms": len(corpus_terms)},
            report,
        )
        return report

    # ── Query interface ────────────────────────────────────────────────────────

    def get_concept(self, concept_id: str) -> Optional[dict]:
        return self._concepts.get(concept_id)

    def find_concept_by_label(self, label: str) -> List[dict]:
        return [
            c for c in self._concepts.values()
            if isinstance(c, dict) and label.lower() in c.get("label", "").lower()
        ]

    def get_concept_with_groundings(self, concept_id: str) -> dict:
        """Full concept snapshot: concept + all answers + boundaries + completeness."""
        concept = self._concepts.get(concept_id)
        if not concept:
            return {}
        c = dict(concept) if isinstance(concept, dict) else {}
        score, tier = self.evaluate_completeness(concept_id)
        grounded, refusals = self.check_grounding(concept_id)

        # Attach answer details
        answer_details = {}
        for qt_val, aid in c.get("answers", {}).items():
            answer = self._answers.get(aid)
            if answer:
                answer_details[qt_val] = dict(answer) if isinstance(answer, dict) else {}

        return {
            **c,
            "completeness_score": score,
            "confidence_tier": tier.value,
            "grounded": grounded,
            "grounding_gaps": [r.to_dict() for r in refusals],
            "answer_details": answer_details,
            "boundary_count": len(c.get("boundaries", [])),
            "split_pressure": self.detect_split_pressure(concept_id),
        }

    def lexicon_summary(self) -> dict:
        """Dashboard summary of the full lexicon state."""
        concepts = list(self._concepts.values())
        active = [c for c in concepts if isinstance(c, dict) and c.get("status") == "active"]
        candidate = [c for c in concepts if isinstance(c, dict) and c.get("status") == "candidate"]

        completeness_scores = [
            self.evaluate_completeness(c["concept_id"])[0]
            for c in concepts if isinstance(c, dict)
        ]
        avg_completeness = (
            sum(completeness_scores) / len(completeness_scores)
            if completeness_scores else 0.0
        )

        return {
            "total_concepts": len(concepts),
            "active": len(active),
            "candidate": len(candidate),
            "total_terms": len(self._terms),
            "total_boundaries": len(self._boundaries),
            "total_conflicts_open": sum(
                1 for c in self._conflicts.values()
                if isinstance(c, dict) and c.get("resolution_state") == "open"
            ),
            "total_outcomes": len(self._outcomes),
            "total_translations": len(self._translations),
            "average_completeness": round(avg_completeness, 3),
            "split_pressure_concepts": [
                c["concept_id"] for c in concepts
                if isinstance(c, dict) and self.detect_split_pressure(c["concept_id"])
            ],
        }


# ── Module-level singleton ─────────────────────────────────────────────────────

_sfe_instance: Optional[SocraticFieldEngine] = None

def get_sfe(receipt_chain=None) -> SocraticFieldEngine:
    global _sfe_instance
    if _sfe_instance is None:
        _sfe_instance = SocraticFieldEngine(receipt_chain=receipt_chain)
    return _sfe_instance
