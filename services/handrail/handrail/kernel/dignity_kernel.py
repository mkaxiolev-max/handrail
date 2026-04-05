import json
import os
from typing import Dict, Any, List
from datetime import datetime
from enum import Enum

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "dignity_config.json")

def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}

class NeverEvent(Enum):
    DECISION_NULL        = "decision.allowed is None"
    EXECUTION_NULL       = "execution.all_ok is None"
    OUTPUT_NULL          = "result.output_ok is None"
    VIOLATIONS_NULL      = "violations is None"
    VIOLATIONS_NOT_LIST  = "violations is not list"
    LEDGER_TAMPER        = "merkle chain broken"
    QUORUM_FAIL          = "yubikey quorum not satisfied"

class DignityKernel:
    def __init__(self):
        cfg = _load_config()
        self.eta               = cfg.get("eta", 0.85)
        self.beta              = cfg.get("beta", 0.92)
        self.warn_threshold    = cfg.get("warn_threshold", 0.65)
        self.block_threshold   = cfg.get("block_threshold", 0.40)
        self.content_never_events = cfg.get("never_events", [])
        self.never_events      = []
        self.constitutional_state = "ACTIVE"

    def hamiltonian_dignity_score(self, context: Dict[str, Any]) -> float:
        """H_dignity = eta * phi(context) - beta * V(violations).
        Returns score in [0,1]; below block_threshold → deny."""
        phi = float(context.get("phi", 1.0))   # dignity potential (1.0 = clean)
        v   = float(context.get("violations_count", 0))
        score = self.eta * phi - self.beta * min(v * 0.1, 1.0)
        return max(0.0, min(1.0, score))

    def check_content_never_event(self, op_name: str) -> bool:
        """Returns True (blocked) if op_name matches a configured never-event."""
        return op_name in self.content_never_events

    def validate_never_event(self, rb: Dict[str, Any]) -> tuple:
        if rb.get("decision", {}).get("allowed") is None:
            return False, NeverEvent.DECISION_NULL
        if rb.get("execution", {}).get("all_ok") is None:
            return False, NeverEvent.EXECUTION_NULL
        if rb.get("result", {}).get("output_ok") is None:
            return False, NeverEvent.OUTPUT_NULL
        if rb.get("violations") is None:
            return False, NeverEvent.VIOLATIONS_NULL
        if not isinstance(rb.get("violations"), list):
            return False, NeverEvent.VIOLATIONS_NOT_LIST
        return True, None

    def enforce_dignity_invariants(self, rb: Dict[str, Any]) -> tuple:
        valid, never = self.validate_never_event(rb)
        if not valid:
            self.never_events.append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "violation": never.value if never else "UNKNOWN",
            })
            return False, f"DIGNITY_VIOLATION:{never.value if never else 'UNKNOWN'}"
        return True, "DIGNITY_ENFORCED"

    def audit_trail(self) -> List[Dict[str, Any]]:
        return self.never_events

    def config_snapshot(self) -> Dict[str, Any]:
        return {
            "eta": self.eta,
            "beta": self.beta,
            "warn_threshold": self.warn_threshold,
            "block_threshold": self.block_threshold,
            "content_never_events": self.content_never_events,
            "constitutional_state": self.constitutional_state,
        }
