"""
Violet Response Renderer
Renders decisions with relational intelligence based on ISR v2
"""
from isr_v2 import InteractionStateV2, ResponseShape

class VioletRenderer:
    def render(self, decision: dict, isr: InteractionStateV2) -> dict:
        shape = isr.recommended_response_shape()
        if shape == ResponseShape.DIRECT:
            text = self._render_direct(decision)
        elif shape == ResponseShape.COMMAND_ACK:
            text = self._render_command_ack(decision)
        elif shape == ResponseShape.DIRECT_THEN_DETAIL:
            text = self._render_direct_then_detail(decision)
        elif shape == ResponseShape.STRATEGIC:
            text = self._render_strategic(decision)
        else:
            text = decision.get("decision_summary", "Ready")

        return {
            "status": "ok",
            "rendered_text": text,
            "rendered_voice_text": text,
            "response_shape": shape.value,
            "pacing": isr.voice_pacing(),
            "ui_summary": decision.get("decision_summary", ""),
            "next_move": decision.get("next_move", ""),
            "receipt_ref": decision.get("receipt_ref", "")
        }

    def _render_direct(self, d):
        return f"{d.get('decision_summary', 'Done')}."

    def _render_command_ack(self, d):
        return f"Done. {d.get('decision_summary', 'Executed')}."

    def _render_direct_then_detail(self, d):
        s = d.get("decision_summary", "Done")
        r = d.get("reasoning_summary", "")
        return f"{s}.\n\n{r}" if r else s

    def _render_strategic(self, d):
        parts = [d.get("decision_summary", "Done")]
        if d.get("reasoning_summary"):
            parts.append(f"\nWhy: {d['reasoning_summary']}")
        if d.get("next_move"):
            parts.append(f"\nNext: {d['next_move']}")
        return "\n".join(parts)
