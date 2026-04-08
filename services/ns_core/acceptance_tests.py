import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pytest
from isr_v2 import create_default_isr, FounderMode, ResponseShape
from violet_renderer import VioletRenderer
from voice_state_machine import VoiceSession, VoiceState

class TestISRv2:
    def test_default_isr(self):
        isr = create_default_isr()
        assert isr.current_mode == FounderMode.STRATEGIC
        assert isr.trust_posture == "full"

    def test_command_shape(self):
        isr = create_default_isr(mode=FounderMode.COMMAND)
        assert isr.recommended_response_shape() == ResponseShape.COMMAND_ACK

    def test_strategic_high_pressure(self):
        isr = create_default_isr(mode=FounderMode.STRATEGIC)
        isr.current_pressure = "high"
        assert isr.recommended_response_shape() == ResponseShape.DIRECT_THEN_DETAIL

    def test_voice_pacing(self):
        pacing = create_default_isr().voice_pacing()
        assert "pre_speak_pause_ms" in pacing
        assert "speech_rate" in pacing

class TestVioletRenderer:
    def test_render_command(self):
        isr = create_default_isr(mode=FounderMode.COMMAND)
        r = VioletRenderer().render({"decision_summary": "Feed built"}, isr)
        assert r["response_shape"] == "command_acknowledgment"
        assert "Feed built" in r["rendered_text"]

    def test_render_strategic(self):
        isr = create_default_isr(mode=FounderMode.STRATEGIC)
        r = VioletRenderer().render({"decision_summary": "Ready", "next_move": "Boot"}, isr)
        assert r["response_shape"] == "strategic_synthesis"
        assert "Boot" in r["rendered_text"]

class TestVoiceStateMachine:
    def test_valid_transition(self):
        s = VoiceSession(session_id="t", state=VoiceState.IDLE)
        assert s.transition(VoiceState.READY)

    def test_invalid_transition(self):
        s = VoiceSession(session_id="t", state=VoiceState.IDLE)
        assert not s.transition(VoiceState.LISTENING)

    def test_full_call_flow(self):
        s = VoiceSession(session_id="t", state=VoiceState.IDLE)
        for state in [VoiceState.READY, VoiceState.LISTENING, VoiceState.TRANSCRIBING,
                      VoiceState.THINKING, VoiceState.RESPONDING]:
            assert s.transition(state), f"Failed: {s.state} -> {state}"

    def test_interrupt_and_resume(self):
        s = VoiceSession(session_id="t", state=VoiceState.RESPONDING)
        assert s.transition(VoiceState.INTERRUPTED)
        assert s.transition(VoiceState.LISTENING)
