"""Voice State Machine — 9 states + transitions"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class VoiceState(str, Enum):
    IDLE = "idle"
    READY = "ready"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    RESPONDING = "responding"
    EXECUTING = "executing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    INTERRUPTED = "interrupted"
    MUTED = "muted"
    ERROR = "error"

VALID_TRANSITIONS = {
    VoiceState.IDLE: [VoiceState.READY],
    VoiceState.READY: [VoiceState.LISTENING, VoiceState.MUTED],
    VoiceState.LISTENING: [VoiceState.TRANSCRIBING, VoiceState.MUTED],
    VoiceState.TRANSCRIBING: [VoiceState.THINKING, VoiceState.INTERRUPTED],
    VoiceState.THINKING: [VoiceState.RESPONDING, VoiceState.EXECUTING, VoiceState.ERROR],
    VoiceState.RESPONDING: [VoiceState.READY, VoiceState.INTERRUPTED, VoiceState.AWAITING_CONFIRMATION],
    VoiceState.EXECUTING: [VoiceState.RESPONDING, VoiceState.ERROR],
    VoiceState.AWAITING_CONFIRMATION: [VoiceState.EXECUTING, VoiceState.READY, VoiceState.INTERRUPTED],
    VoiceState.INTERRUPTED: [VoiceState.LISTENING, VoiceState.READY],
    VoiceState.MUTED: [VoiceState.READY],
    VoiceState.ERROR: [VoiceState.READY, VoiceState.IDLE]
}

VOICE_STATE_UI = {
    VoiceState.IDLE: {"badge": "o", "color": "gray", "spinner": False},
    VoiceState.READY: {"badge": "mic", "color": "green", "spinner": False},
    VoiceState.LISTENING: {"badge": "ear", "color": "blue", "spinner": True},
    VoiceState.TRANSCRIBING: {"badge": "pen", "color": "blue", "spinner": True},
    VoiceState.THINKING: {"badge": "brain", "color": "yellow", "spinner": True},
    VoiceState.RESPONDING: {"badge": "speak", "color": "violet", "spinner": False},
    VoiceState.EXECUTING: {"badge": "bolt", "color": "violet", "spinner": True},
    VoiceState.AWAITING_CONFIRMATION: {"badge": "hand", "color": "orange", "spinner": False},
    VoiceState.INTERRUPTED: {"badge": "pause", "color": "red", "spinner": False},
    VoiceState.MUTED: {"badge": "mute", "color": "gray", "spinner": False},
    VoiceState.ERROR: {"badge": "x", "color": "red", "spinner": False}
}

@dataclass
class VoiceSession:
    session_id: str
    state: VoiceState
    transcript_partial: str = ""
    transcript_final: list = field(default_factory=list)
    current_program: Optional[str] = None
    current_role: Optional[str] = None
    latency_ms: int = 0
    interruptible: bool = True
    awaiting_confirmation: bool = False
    error_message: Optional[str] = None

    def transition(self, new_state: VoiceState) -> bool:
        if new_state in VALID_TRANSITIONS.get(self.state, []):
            self.state = new_state
            return True
        return False
