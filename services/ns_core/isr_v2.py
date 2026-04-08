"""
ISR v2: Interaction State Register
Relational intelligence for human-feel Violet responses
"""
from dataclasses import dataclass, asdict
from typing import Optional
from enum import Enum

class FounderMode(str, Enum):
    STRATEGIC = "founder_strategic"
    COMMAND = "founder_command"
    MONITORING = "monitoring"
    REFLECTIVE = "reflective"
    SIDECAR = "sidecar"
    CONFERENCE = "conference"

class ResponseShape(str, Enum):
    DIRECT = "direct"
    DIRECT_THEN_DETAIL = "direct_then_detail"
    CONTEXTUAL_THEN_DIRECT = "contextual_then_direct"
    CALM_THEN_ACTION = "calm_reassurance_then_action"
    STRATEGIC = "strategic_synthesis"
    HARD_STOP = "hard_stop"
    REFLECTIVE = "reflective"
    SIDECAR_BRIEF = "sidecar_brief"
    COMMAND_ACK = "command_acknowledgment"

@dataclass
class InteractionStateV2:
    current_mode: FounderMode
    active_program: Optional[str]
    active_role: str
    current_pressure: str
    desired_directness: str
    affect_temperature: str
    continuity_thread: Optional[str]
    unresolved_question: Optional[str]
    last_advice: Optional[str]
    last_receipt: Optional[str]
    interruption_state: str
    trust_posture: str

    def to_dict(self):
        return asdict(self)

    def recommended_response_shape(self) -> ResponseShape:
        if self.current_mode == FounderMode.COMMAND:
            return ResponseShape.COMMAND_ACK if self.desired_directness == "high" else ResponseShape.DIRECT_THEN_DETAIL
        elif self.current_mode == FounderMode.STRATEGIC:
            return ResponseShape.STRATEGIC if self.current_pressure == "low" else ResponseShape.DIRECT_THEN_DETAIL
        elif self.current_mode == FounderMode.REFLECTIVE:
            return ResponseShape.REFLECTIVE
        elif self.current_mode == FounderMode.SIDECAR:
            return ResponseShape.SIDECAR_BRIEF
        elif self.current_mode == FounderMode.CONFERENCE:
            return ResponseShape.DIRECT
        return ResponseShape.DIRECT

    def voice_pacing(self) -> dict:
        return {
            "pre_speak_pause_ms": 400 if self.current_pressure == "high" else 200,
            "clause_pause_ms": 150,
            "confirmation_pause_ms": 800,
            "speech_rate": 1.1 if self.current_pressure == "high" else 1.0,
            "backchannels": self.affect_temperature != "steady"
        }

def create_default_isr(mode: FounderMode = FounderMode.STRATEGIC) -> InteractionStateV2:
    return InteractionStateV2(
        current_mode=mode,
        active_program=None,
        active_role="founder",
        current_pressure="medium",
        desired_directness="high",
        affect_temperature="steady",
        continuity_thread=None,
        unresolved_question=None,
        last_advice=None,
        last_receipt=None,
        interruption_state="none",
        trust_posture="full"
    )
