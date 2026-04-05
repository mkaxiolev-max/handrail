"""
Role Router — deterministic role selection from state + trigger + policy.
Role routing is policy-valid and deterministic. No LLM reasoning at this layer.
Active speaker token enforced: one role owns the turn.
"""
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

def ts(): return datetime.now(timezone.utc).isoformat()
def sid(s): return hashlib.sha256((s+ts()).encode()).hexdigest()[:8]

# Commercial role-state map (authoritative)
COMMERCIAL_ROLE_STATE_MAP = {
    "elaine_access_operator":       ["S0_IDENTIFY","S1_OPEN","S2_FRAME","S3_QUALIFY","S4_CHAMPION"],
    "heidi_validation_operator":    ["S4_CHAMPION","S5_VALIDATION"],  # only when skepticism trigger
    "stewart_negotiation_operator": ["S4_CHAMPION","S5_VALIDATION","S6_NEGOTIATION","S7_CLOSE","S8_COMMIT"],
    "legal_operator":               ["S7_CLOSE","S8_COMMIT"],
    "founder":                      ["S5_VALIDATION","S6_NEGOTIATION","S7_CLOSE"],  # selective only
}

# Trigger → role override map
TRIGGER_ROLE_MAP = {
    "pricing_discussion":    "stewart_negotiation_operator",
    "structure_discussion":  "stewart_negotiation_operator",
    "term_pushback":         "stewart_negotiation_operator",
    "skepticism":            "heidi_validation_operator",
    "regulatory_challenge":  "heidi_validation_operator",
    "clinical_question":     "heidi_validation_operator",
    "legal_review":          "legal_operator",
    "founder_requested":     "founder",
    "escalation":            "founder",
}

# Role priority for speaker token arbitration (lower = higher priority)
ROLE_PRIORITY = {
    "founder": 1,
    "legal_operator": 2,
    "stewart_negotiation_operator": 3,
    "heidi_validation_operator": 4,
    "elaine_access_operator": 5,
}

class RoleRouter:
    def get_default_role(self, state: str) -> str:
        """Get the default (non-trigger) role for a state."""
        for role, states in COMMERCIAL_ROLE_STATE_MAP.items():
            if state in states and role != "founder":  # founder is never default
                return role
        return "elaine_access_operator"

    def route(self, state: str, trigger: Optional[str] = None,
              policy_bundle: str = "commercial_policy_v1") -> dict:
        """
        Deterministic role routing.
        Trigger overrides take precedence over state-default if policy allows.
        """
        # Trigger-based override
        if trigger and trigger in TRIGGER_ROLE_MAP:
            candidate = TRIGGER_ROLE_MAP[trigger]
            # Verify candidate is allowed in this state
            allowed_states = COMMERCIAL_ROLE_STATE_MAP.get(candidate, [])
            if state in allowed_states or candidate == "founder":
                return {
                    "selected_role": candidate,
                    "routing_basis": "trigger_override",
                    "trigger": trigger,
                    "state": state,
                    "priority": ROLE_PRIORITY.get(candidate, 5),
                }

        # State-default routing
        default = self.get_default_role(state)
        return {
            "selected_role": default,
            "routing_basis": "state_default",
            "trigger": trigger,
            "state": state,
            "priority": ROLE_PRIORITY.get(default, 5),
        }

    def get_handoff(self, current_role: str, next_role: str, state: str) -> Optional[str]:
        if current_role == next_role:
            return None
        return f"HANDOFF: {current_role} → {next_role} at {state}"

    def is_role_allowed(self, role: str, state: str) -> bool:
        allowed = COMMERCIAL_ROLE_STATE_MAP.get(role, [])
        return state in allowed or role == "founder"

    def acquire_speaker_token(self, program_run_id: str, role: str, ttl: int = 300) -> dict:
        """
        Acquire active speaker token. One role owns the turn.
        Higher priority roles can preempt lower priority.
        """
        return {
            "token_id": f"SPK-{sid(program_run_id+role)}",
            "program_run_id": program_run_id,
            "active_role": role,
            "acquired_at": ts(),
            "ttl_seconds": ttl,
            "priority": ROLE_PRIORITY.get(role, 5),
        }
