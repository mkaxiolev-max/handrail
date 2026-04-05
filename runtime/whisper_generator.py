"""
Whisper Generator — NS whispers to humans. Proving ground before direct voice.
"If whisper mode is weak, direct autonomy will be fraudulent." — Architecture doc
Every whisper packet is receipted. Every line is policy-checked before display.
"""
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

RECEIPTS_PATH = Path("/Volumes/NSExternal/.run/whisper_receipts.jsonl")

def ts(): return datetime.now(timezone.utc).isoformat()
def wid(s): return f"WP-{hashlib.sha256((s+ts()).encode()).hexdigest()[:8]}"

WHISPER_TEMPLATES = {
    "S0_IDENTIFY":   {"signal":"Pre-contact. Goal: confirm target fit before outreach.","move":"Score prospect against ICP. Do not contact without fit confirmation.","line":"[Internal only — no outreach yet]","risk":"LOW"},
    "S1_OPEN":       {"signal":"Opening established. Goal: earn discovery call.","move":"Ask one open question about their current challenge.","line":"We've built something a few organizations in your space found surprisingly useful — worth 20 minutes to compare notes?","risk":"LOW"},
    "S2_FRAME":      {"signal":"Framing. Goal: establish problem definition before solution.","move":"Reflect their challenge back. Ask what solving it would be worth.","line":"So if I'm hearing correctly, the core issue is [X]. Is that what matters most right now, or is there a layer beneath it?","risk":"LOW"},
    "S3_QUALIFY":    {"signal":"Qualification. Goal: identify internal owner and decision process.","move":"Ask directly who owns this problem and what a decision looks like.","line":"Typically there's one person who owns this kind of decision — is that you, or is there someone else I should speak with?","risk":"MEDIUM"},
    "S4_CHAMPION":   {"signal":"Champion identified. Goal: equip champion to carry internally.","move":"Give champion one-pager they can forward without your help.","line":"Here's a one-pager designed so you can share it without needing to explain it yourself — does that make it easier?","risk":"LOW"},
    "S5_VALIDATION": {"signal":"Skepticism or credibility challenge active. Heidi window.","move":"Let Heidi provide brief clinical validation. Max 3 sentences.","line":"[Heidi validates — no commercial framing. Clinical scope only.]","risk":"HIGH"},
    "S6_NEGOTIATION":{"signal":"Pricing/structure discussion. Stewart leads.","move":"Stewart holds value. No discounting without scope change.","line":"We've put together a structure that reflects what we heard — [scope] at [terms]. Does this match your thinking?","risk":"HIGH"},
    "S7_CLOSE":      {"signal":"Alignment signal present. Close window open.","move":"Confirm verbal commitment path. Do not rush.","line":"It sounds like we're aligned. What does next steps look like on your side to get this formalized?","risk":"HIGH"},
    "S8_COMMIT":     {"signal":"Verbal commit received. Legal/contract phase.","move":"Hand to legal operator. Founder available on request.","line":"[Legal operator takes contract review. Founder available if requested.]","risk":"MEDIUM"},
    "S9_ARCHIVE":    {"signal":"Deal closed or dead. Archive and memory update.","move":"Log outcome, update Alexandria, close loop.","line":"[Archive — no active outreach in this state]","risk":"LOW"},
}

class WhisperGenerator:
    def __init__(self, policy_guard=None):
        self.policy_guard = policy_guard

    def generate(self, program_runtime: dict, trigger: Optional[str] = None,
                 prospect_signal: str = "") -> dict:
        from runtime.role_router import RoleRouter
        from runtime.memory_scope import MemoryScope

        state = program_runtime["state"]
        router = RoleRouter()
        routing = router.route(state, trigger)
        active_role = routing["selected_role"]

        template = WHISPER_TEMPLATES.get(state, {
            "signal": "State transition. Await next signal.",
            "move": "Hold position. Do not act without signal.",
            "line": "[Await NS guidance]",
            "risk": "MEDIUM",
        })

        suggested_line = template["line"]

        # Policy check the line before displaying
        policy_result = {"result": "ALLOW", "violations": []}
        if self.policy_guard:
            policy_result = self.policy_guard.check_line(active_role, suggested_line, state)

        # Handoff signal
        current_role = program_runtime.get("active_role", active_role)
        handoff = router.get_handoff(current_role, active_role, state) if current_role != active_role else None

        packet_id = wid(state + active_role + program_runtime["program_run_id"])
        packet = {
            "packet_id": packet_id,
            "program_run_id": program_runtime["program_run_id"],
            "program_id": program_runtime["program_id"],
            "state": state,
            "signal": prospect_signal or template["signal"],
            "risk": template["risk"],
            "move": template["move"],
            "suggested_line": suggested_line,
            "policy_result": policy_result,
            "handoff": handoff,
            "active_role": active_role,
            "routing_basis": routing["routing_basis"],
            "trigger": trigger,
            "approved": policy_result["result"] == "ALLOW",
            "timestamp": ts(),
        }

        # Receipt every whisper — this is training data
        self._receipt(packet)
        return packet

    def _receipt(self, packet: dict):
        RECEIPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RECEIPTS_PATH, "a") as f:
            f.write(json.dumps(packet) + "\n")
