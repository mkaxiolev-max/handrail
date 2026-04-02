# Copyright © 2026 Axiolev. All rights reserved.
"""
Semantic Feedback Binder — execution metabolism layer.
Every execution run produces:
  1. operational receipt (Alexandria ledger — already done)
  2. semantic update candidate (this layer — NEW)

Architecture law: meaning controls action, action produces reality,
reality corrects meaning. Outcomes flow back to semantics.
"""
from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

_SEM_SSD  = Path("/Volumes/NSExternal/ALEXANDRIA/semantic")
_SEM_FALL = Path.home() / ".axiolev" / "semantic"

def _sem_root() -> Path:
    if Path("/Volumes/NSExternal/ALEXANDRIA").exists():
        return _SEM_SSD
    return _SEM_FALL

def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

OP_DOMAIN_MAP: dict[str, str] = {
    "fs":"file_system_capability","git":"version_control_capability",
    "http":"network_capability","sys":"system_capability",
    "proc":"process_capability","docker":"container_capability",
    "slack":"communication_capability","email":"communication_capability",
    "stripe":"financial_capability","schedule":"scheduling_capability",
    "env":"environment_capability","window":"ui_capability",
    "input":"input_capability","vision":"vision_capability",
    "ns":"intelligence_capability","san":"legal_territorial_capability",
    "fundraising":"capital_program_capability","hiring":"talent_program_capability",
    "partner":"partnership_program_capability","ma":"acquisition_program_capability",
    "advisor":"advisor_program_capability","cs":"customer_success_capability",
    "feedback":"product_feedback_capability","gov":"governance_capability",
    "knowledge":"knowledge_ingestion_capability","program":"program_meta_capability",
}

CONFIDENCE_DELTA = {
    "success":+0.01,"failure":-0.05,"policy_denial":-0.10,
    "semantic_failure":-0.08,"temporal":-0.03,"unknown":-0.05,
}

@dataclass
class ExecutionOutcome:
    run_id: str
    ops_executed: list[str]
    success: bool
    latency_ms: float
    failure_class: str | None
    ts: str = ""

@dataclass
class SemanticImpactReport:
    run_id: str
    lexicon_terms_touched: list[str]
    assumptions_held: list[str]
    assumptions_failed: list[str]
    confidence_delta: float
    ts: str = ""

@dataclass
class MeaningRefinementCandidate:
    id: str
    term: str
    current_definition: str
    proposed_refinement: str
    evidence_run_ids: list[str]
    confidence: float
    ts: str = ""

@dataclass
class CanonCommitProposal:
    proposal_id: str
    candidate_id: str
    term: str
    requires_quorum: bool
    auto_promote_if_confidence_above: float
    ts: str = ""


class SemanticFeedbackBinder:
    def __init__(self):
        self._rolling: dict[str, list[float]] = {}

    def _dir(self, sub: str) -> Path:
        d = _sem_root() / sub
        d.mkdir(parents=True, exist_ok=True)
        return d

    def bind(self, outcome: ExecutionOutcome) -> SemanticImpactReport:
        domains: set[str] = set()
        for op in outcome.ops_executed:
            ns = op.split(".")[0] if "." in op else op
            domains.add(OP_DOMAIN_MAP.get(ns, f"{ns}_capability"))
        failure_class = outcome.failure_class or "success"
        held = list(domains) if outcome.success else []
        failed = list(domains) if not outcome.success else []
        delta = CONFIDENCE_DELTA.get(failure_class.lower() if not outcome.success else "success", -0.02)
        for domain in domains:
            self._rolling.setdefault(domain, [])
            self._rolling[domain] = (self._rolling[domain] + [delta])[-20:]
        return SemanticImpactReport(
            run_id=outcome.run_id, lexicon_terms_touched=sorted(domains),
            assumptions_held=held, assumptions_failed=failed,
            confidence_delta=delta, ts=_ts(),
        )

    def propose_refinement(self, impact: SemanticImpactReport) -> list[MeaningRefinementCandidate]:
        candidates = []
        for term in impact.assumptions_failed:
            accumulated = sum(self._rolling.get(term, []))
            if accumulated < -0.2:
                cid = str(uuid.uuid4())[:8]
                c = MeaningRefinementCandidate(
                    id=cid, term=term,
                    current_definition=f"Current definition of {term}",
                    proposed_refinement=(
                        f"Refine {term}: accumulated delta {accumulated:.3f} "
                        f"over {len(self._rolling.get(term,[]))} runs."
                    ),
                    evidence_run_ids=[impact.run_id],
                    confidence=max(0.0, 1.0 + accumulated), ts=_ts(),
                )
                (self._dir("candidates") / f"{cid}.json").write_text(json.dumps(asdict(c), indent=2))
                candidates.append(c)
        return candidates

    def propose_canon_commit(self, candidate: MeaningRefinementCandidate) -> CanonCommitProposal:
        pid = str(uuid.uuid4())[:8]
        prop = CanonCommitProposal(
            proposal_id=pid, candidate_id=candidate.id, term=candidate.term,
            requires_quorum=not (candidate.confidence > 0.85 and len(candidate.evidence_run_ids) >= 3),
            auto_promote_if_confidence_above=0.9, ts=_ts(),
        )
        (self._dir("proposals") / f"{pid}.json").write_text(json.dumps(asdict(prop), indent=2))
        return prop

    def promote_to_canon(self, proposal_id: str, approved_by: str = "founder") -> dict:
        p = self._dir("proposals") / f"{proposal_id}.json"
        if not p.exists():
            return {"ok": False, "error": f"proposal {proposal_id} not found"}
        proposal = json.loads(p.read_text())
        cp = self._dir("candidates") / f"{proposal['candidate_id']}.json"
        candidate = json.loads(cp.read_text()) if cp.exists() else {}
        canon_entry = {
            "proposal_id": proposal_id, "term": proposal.get("term",""),
            "refinement": candidate.get("proposed_refinement",""),
            "approved_by": approved_by, "promoted_at": _ts(),
            "evidence_run_ids": candidate.get("evidence_run_ids",[]),
        }
        (self._dir("canon") / f"{proposal.get('term', proposal_id)}.json").write_text(
            json.dumps(canon_entry, indent=2))
        return {"ok": True, "promoted": proposal.get("term",""), "ts": _ts()}

    def list_candidates(self) -> list[dict]:
        return [json.loads(f.read_text()) for f in sorted(self._dir("candidates").glob("*.json"))]

    def list_proposals(self) -> list[dict]:
        return [json.loads(f.read_text()) for f in sorted(self._dir("proposals").glob("*.json"))]

    def run_full_cycle(self, outcome: ExecutionOutcome) -> dict:
        report = self.bind(outcome)
        candidates = self.propose_refinement(report)
        proposals = [self.propose_canon_commit(c) for c in candidates]
        return {
            "run_id": outcome.run_id,
            "domains_touched": len(report.lexicon_terms_touched),
            "confidence_delta": report.confidence_delta,
            "candidates_generated": len(candidates),
            "proposals_generated": len(proposals),
        }


_binder: SemanticFeedbackBinder | None = None

def get_binder() -> SemanticFeedbackBinder:
    global _binder
    if _binder is None:
        _binder = SemanticFeedbackBinder()
    return _binder
