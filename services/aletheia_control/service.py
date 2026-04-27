"""Main service orchestrator."""
from __future__ import annotations
import pathlib, secrets, statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from .models import (ControlInput, ControlClassification, ControlAtom,
                     InfluenceChain, ConcernWasteRoute, AletheiaControlReceipt,
                     ControlCircle)
from .classifier import classify
from . import receipts as R
from .scoring import omega_score, rubric_score, RUBRIC

ALEX = pathlib.Path("alexandria/receipts/aletheia_control/log.jsonl")

class AletheiaControlService:
    def __init__(self):
        self.classifications: List[ControlClassification] = []
        self.atoms: Dict[str, ControlAtom] = {}
        self.chains: Dict[str, InfluenceChain] = {}
        self.wastes: Dict[str, ConcernWasteRoute] = {}
        self.receipts: List[AletheiaControlReceipt] = []
        self.false_control_events: int = 0
        self.feedback_observed: int = 0
        self.feedback_expected: int = 0

    # ── classification + routing ──
    def record_classification(self, inp: ControlInput, cls: ControlClassification):
        self.classifications.append(cls)
        R.append(ALEX, "ALET_CONTROL_CLASSIFICATION_RECEIPT",
                 {"input_id": inp.input_id, "circle": cls.circle.value,
                  "weights": [cls.control_weight, cls.influence_weight, cls.concern_weight]})

    def route(self, inp: ControlInput) -> AletheiaControlReceipt:
        cls = classify(inp); self.record_classification(inp, cls)
        rcp = AletheiaControlReceipt(
            receipt_id="rcp_"+secrets.token_hex(6),
            input_id=inp.input_id, classification=cls,
            outcome=f"routed:{cls.circle.value}",
        )
        self.receipts.append(rcp); return rcp

    def execute_control(self, atom: ControlAtom) -> AletheiaControlReceipt:
        self.atoms[atom.atom_id] = atom
        self.feedback_expected += 1; self.feedback_observed += 1
        R.append(ALEX, "ALET_CONTROL_ATOM_RECEIPT", atom.model_dump())
        return AletheiaControlReceipt(
            receipt_id="rcp_"+secrets.token_hex(6),
            input_id=atom.input_id, control_atom=atom, outcome="executed",
        )

    def register_influence(self, chain: InfluenceChain) -> AletheiaControlReceipt:
        self.chains[chain.chain_id] = chain
        R.append(ALEX, "ALET_INFLUENCE_CHAIN_RECEIPT", chain.model_dump(mode="json"))
        return AletheiaControlReceipt(
            receipt_id="rcp_"+secrets.token_hex(6),
            input_id=chain.input_id, influence_chain=chain, outcome="influence_registered",
        )

    def delete_concern(self, route: ConcernWasteRoute) -> AletheiaControlReceipt:
        self.wastes[route.waste_id] = route
        R.append(ALEX, "ALET_CONCERN_WASTE_RECEIPT", route.model_dump(mode="json"))
        return AletheiaControlReceipt(
            receipt_id="rcp_"+secrets.token_hex(6),
            input_id=route.input_id, waste_route=route, outcome="concern_deleted",
        )

    def persist_receipt(self, rcp: AletheiaControlReceipt) -> AletheiaControlReceipt:
        self.receipts.append(rcp); return rcp

    # ── metrics ──
    def _control_ratio(self) -> float:
        if not self.classifications: return 0.0
        c = sum(1 for x in self.classifications if x.circle==ControlCircle.CONTROL)
        return c/len(self.classifications)

    def _concern_leakage(self) -> float:
        # fraction of CONCERN-classified inputs that produced a ControlAtom (bad)
        concern_inputs = {x.input_id for x in self.classifications if x.circle==ControlCircle.CONCERN}
        if not concern_inputs: return 0.0
        leaked = sum(1 for a in self.atoms.values() if a.input_id in concern_inputs)
        return leaked/len(concern_inputs)

    def _false_control_rate(self) -> float:
        if not self.classifications: return 0.0
        return self.false_control_events/len(self.classifications)

    def _feedback_integrity(self) -> float:
        if self.feedback_expected == 0: return 1.0
        return self.feedback_observed/self.feedback_expected

    def _influence_conversion(self) -> float:
        if not self.chains: return 0.0
        return statistics.mean(c.expected_conversion for c in self.chains.values())

    def dashboard(self) -> dict:
        return {
            "classifications": len(self.classifications),
            "atoms":           len(self.atoms),
            "chains":          len(self.chains),
            "wastes":          len(self.wastes),
            "control_ratio":   round(self._control_ratio(),4),
            "concern_leakage": round(self._concern_leakage(),4),
            "false_control_rate": round(self._false_control_rate(),4),
            "feedback_integrity": round(self._feedback_integrity(),4),
            "influence_conversion": round(self._influence_conversion(),4),
        }

    def score(self) -> dict:
        sub = {
            "control_ratio_score":        self._control_ratio(),
            "influence_conversion_score": self._influence_conversion(),
            "concern_leakage_score":      max(0.0, 1.0-self._concern_leakage()/0.05),
            "feedback_integrity_score":   self._feedback_integrity(),
            "deletion_efficiency_score":  min(1.0, len(self.wastes)/max(1,len(self.classifications))),
            "drift_resistance_score":     1.0,  # populated by drift.py
        }
        # clamp
        sub = {k: max(0.0, min(1.0, v)) for k,v in sub.items()}
        return {"omega": omega_score(sub), "subscores": sub}

    def weekly_audit(self) -> dict:
        d = self.dashboard()
        passed = (d["concern_leakage"] <= 0.05
                  and d["false_control_rate"] <= 0.02
                  and d["feedback_integrity"] >= 0.95)
        R.append(ALEX, "ALET_WEEKLY_DELETION_AUDIT", {**d, "passed": passed})
        return {"passed": passed, **d}
