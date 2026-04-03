"""USDL Decoder — biological gate evaluator, DNA→USDL isomorphism."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Gate types (DNA isomorphism) ──────────────────────────────────────────────
# promoter   → enables execution (always-open unless conditions block)
# enhancer   → amplifies execution priority
# silencer   → inhibits execution
# operator   → blocks execution
# riboswitch → sensor-driven (reads state capsule signal, gates on threshold)
# miRNA      → post-execution validator (runs after, can veto commit)

GATE_TYPES = {"promoter", "enhancer", "silencer", "operator", "riboswitch", "miRNA"}

# ── Seed genome — 5 real AXIOLEV gates ───────────────────────────────────────
SEED_GENOME = [
    {
        "id": "gate_1",
        "type": "promoter",
        "name": "cps_execution_enabled",
        "description": "Enables CPS execution unless capability gap is saturated",
        "conditions": {"capability_gap": {"op": "<", "value": 0.8}},
        "priority": 100,
        "action": "enable_execution",
    },
    {
        "id": "gate_2",
        "type": "silencer",
        "name": "governance_block",
        "description": "Blocks execution when risk score is critical",
        "conditions": {"risk_score": {"op": ">", "value": 0.9}},
        "priority": 200,
        "action": "block_execution",
    },
    {
        "id": "gate_3",
        "type": "riboswitch",
        "name": "semantic_drift_detector",
        "description": "Triggers canon review when semantic drift exceeds threshold",
        "conditions": {"semantic_drift": {"op": ">", "value": 0.3}},
        "priority": 150,
        "action": "trigger_canon_review",
        "signal": "semantic_drift",
        "threshold": 0.3,
    },
    {
        "id": "gate_4",
        "type": "enhancer",
        "name": "high_value_target",
        "description": "Amplifies execution priority for high-gap, low-risk operations",
        "conditions": {
            "capability_gap": {"op": ">", "value": 0.5},
            "risk_score": {"op": "<", "value": 0.5},
        },
        "priority": 120,
        "action": "amplify_priority",
    },
    {
        "id": "gate_5",
        "type": "miRNA",
        "name": "post_exec_validator",
        "description": "Post-execution validator — checks outcome against canon",
        "conditions": {},
        "priority": 50,
        "action": "validate_against_canon",
        "fires_post_execution": True,
    },
    {
        "id": "gate_6",
        "type": "operator",
        "name": "dignity_block",
        "description": "Blocks execution if dignity kernel never-events are at risk",
        "conditions": {"risk_score": {"op": ">", "value": 0.95}},
        "priority": 250,
        "action": "block_execution",
    },
    {
        "id": "gate_7",
        "type": "enhancer",
        "name": "sovereignty_boost",
        "description": "Amplifies priority for sovereignty-critical operations",
        "conditions": {
            "constraint_pressure": {"op": ">", "value": 0.7},
            "capability_gap": {"op": "<", "value": 0.5},
        },
        "priority": 130,
        "action": "amplify_priority",
    },
    {
        "id": "gate_8",
        "type": "riboswitch",
        "name": "founder_presence_sensor",
        "description": "Gates high-risk ops on founder session presence",
        "conditions": {"ATP_level": {"op": ">", "value": 0.6}},
        "priority": 175,
        "action": "conditional_enable",
    },
]

# ── Storage ───────────────────────────────────────────────────────────────────
def _lineage_path() -> Path:
    ssd = Path("/Volumes/NSExternal/ALEXANDRIA/usdl")
    if ssd.parent.exists():
        d = ssd
    else:
        d = Path.home() / ".axiolev" / "usdl"
    d.mkdir(parents=True, exist_ok=True)
    return d / "lineage.jsonl"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ── Decoder ───────────────────────────────────────────────────────────────────
class USDLDecoder:
    """Evaluate USDL gates against a live state capsule."""

    def __init__(self, genome: Optional[list] = None,
                 state_capsule: Optional[dict] = None):
        self.genome = genome if genome is not None else list(SEED_GENOME)
        self.state_capsule = state_capsule or {}

    def _eval_condition(self, field: str, rule: dict) -> bool:
        val = self.state_capsule.get(field)
        if val is None:
            return False
        op = rule.get("op", "==")
        threshold = rule.get("value", 0)
        if op == "<":
            return val < threshold
        if op == "<=":
            return val <= threshold
        if op == ">":
            return val > threshold
        if op == ">=":
            return val >= threshold
        if op == "==":
            return val == threshold
        if op == "!=":
            return val != threshold
        return False

    def eval_gate(self, gate: dict) -> bool:
        """Evaluate all conditions for a gate — returns True if gate fires."""
        conditions = gate.get("conditions", {})
        if not conditions:
            # miRNA and conditionless gates always fire (post-exec)
            return True
        return all(
            self._eval_condition(field, rule)
            for field, rule in conditions.items()
        )

    def get_applicable_gates(self) -> list[dict]:
        """Return gates that would fire given current state capsule."""
        applicable = []
        for gate in self.genome:
            if self.eval_gate(gate):
                applicable.append({**gate, "_fires": True})
        return sorted(applicable, key=lambda g: g.get("priority", 0), reverse=True)

    def execute(self) -> dict:
        """Find applicable gates, rank, fire, log lineage."""
        applicable = self.get_applicable_gates()
        fired_ids = [g["id"] for g in applicable]
        blocked = any(g["type"] in ("silencer", "operator") for g in applicable)
        promoters = [g for g in applicable if g["type"] == "promoter"]
        enhancers = [g for g in applicable if g["type"] == "enhancer"]
        post_validators = [g for g in applicable if g["type"] == "miRNA"]

        result = {
            "execution_id": str(uuid.uuid4()),
            "state_capsule": self.state_capsule,
            "gates_fired": len(applicable),
            "blocked": blocked,
            "enabled": len(promoters) > 0 and not blocked,
            "amplified": len(enhancers) > 0,
            "post_validation_required": len(post_validators) > 0,
            "fired_gates": [{"id": g["id"], "type": g["type"],
                             "name": g["name"], "action": g["action"]}
                            for g in applicable],
            "actions": list({g["action"] for g in applicable}),
            "ts": _now(),
        }
        # Log lineage
        try:
            with open(_lineage_path(), "a") as f:
                f.write(json.dumps(result) + "\n")
        except Exception:
            pass
        return result

    def get_lineage(self, n: int = 20) -> list[dict]:
        """Recent gate firing history."""
        path = _lineage_path()
        if not path.exists():
            return []
        entries = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        return list(reversed(entries[-n:]))


# ── Singleton (with default genome) ──────────────────────────────────────────
_decoder: Optional[USDLDecoder] = None

def get_decoder(state_capsule: Optional[dict] = None) -> USDLDecoder:
    """Return decoder — always refreshes state capsule if provided."""
    global _decoder
    if _decoder is None:
        _decoder = USDLDecoder()
    if state_capsule is not None:
        _decoder.state_capsule = state_capsule
    return _decoder
