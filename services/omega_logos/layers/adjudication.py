"""Adjudication layer — canon + dignity gate decision surface.
AXIOLEV Holdings LLC © 2026. (Maps to I₆.C2 — invariant_violation_rate.)"""
from dataclasses import dataclass
from typing import Dict, Any

NEVER_EVENTS = {"NE1","NE2","NE3","NE4","NE5","NE6","NE7"}

@dataclass
class Decision:
    allow: bool
    code: str
    reason: str

def adjudicate(action: Dict[str, Any]) -> Decision:
    """Return DENY on any never-event or live-key leak in args; ALLOW otherwise."""
    args_text = str(action.get("args", "")).lower()
    if "sk_live_" in args_text:
        return Decision(False, "DIGNITY_KERNEL_VIOLATION", "live secret in args (NE3)")
    if action.get("never_event") in NEVER_EVENTS:
        return Decision(False, "NEVER_EVENT", f"never_event {action['never_event']} triggered")
    if action.get("action") == "canon.promote" and action.get("subject") == "anon":
        return Decision(False, "CANON_PROMOTION_DENIED", "anonymous promotion")
    return Decision(True, "ALLOW", "policy checks passed")
