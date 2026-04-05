"""
State Resolver — ledger-derived first, inference-assisted second, never reverse.
State is only real if it has a valid transition receipt in the ledger.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

LEDGER_PATH = Path("/Volumes/NSExternal/.run/alexandria_ledger.jsonl")
PROG_RECEIPTS = Path("/Volumes/NSExternal/.run/program_receipts.jsonl")

def ts(): return datetime.now(timezone.utc).isoformat()

class StateResolver:
    """
    Resolves the canonical current state of a ProgramRuntime.
    Source of truth: transition receipts in Alexandria.
    LLM signals may propose state changes but cannot ratify them.
    """

    def resolve_from_ledger(self, program_run_id: str) -> Optional[dict]:
        """
        Walk the ledger and find the most recent valid transition_receipt
        for this program_run_id. Returns the canonical state.
        """
        last_state = None
        last_receipt = None

        for source in [PROG_RECEIPTS, LEDGER_PATH]:
            if not source.exists():
                continue
            with open(source) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        # Handle both direct receipts and wrapped Alexandria entries
                        payload = entry.get("payload", entry)
                        if payload.get("program_run_id") != program_run_id:
                            continue
                        if payload.get("next_state"):
                            last_state = payload["next_state"]
                            last_receipt = payload
                    except json.JSONDecodeError:
                        continue

        return {"canonical_state": last_state, "last_receipt": last_receipt} if last_state else None

    def resolve(self, program_runtime: dict) -> dict:
        """
        Full resolution: check ledger first, fall back to runtime object.
        Returns resolution with confidence flag.
        """
        run_id = program_runtime["program_run_id"]
        ledger_result = self.resolve_from_ledger(run_id)

        if ledger_result:
            canonical = ledger_result["canonical_state"]
            if canonical != program_runtime["state"]:
                # Ledger and runtime object disagree — ledger wins
                program_runtime["state"] = canonical
                program_runtime["_state_source"] = "ledger"
            else:
                program_runtime["_state_source"] = "ledger_confirmed"
            confidence = "HIGH"
        else:
            # No ledger entries — use runtime object state (startup case)
            program_runtime["_state_source"] = "runtime_object_only"
            confidence = "MEDIUM"

        # Build resolution object
        prog_id = program_runtime["program_id"]
        state_table = _load_state_table(prog_id)
        current = program_runtime["state"]
        idx = state_table.index(current) if current in state_table else -1

        return {
            "program_run_id": run_id,
            "canonical_state": current,
            "state_index": idx,
            "total_states": len(state_table),
            "next_state": state_table[idx + 1] if 0 <= idx < len(state_table) - 1 else None,
            "prior_state": state_table[idx - 1] if idx > 0 else None,
            "is_terminal": idx == len(state_table) - 1,
            "confidence": confidence,
            "state_source": program_runtime.get("_state_source"),
        }

    def validate_transition(self, program_runtime: dict, proposed_next: str, trigger: str) -> dict:
        """
        Validate a proposed state transition.
        Returns: {valid, reason, prior_state, next_state}
        """
        prog_id = program_runtime["program_id"]
        state_table = _load_state_table(prog_id)
        current = program_runtime["state"]
        transition_rules = _load_transition_rules(prog_id)

        if current not in state_table:
            return {"valid": False, "reason": f"Current state {current} not in state table"}
        if proposed_next not in state_table:
            return {"valid": False, "reason": f"Proposed state {proposed_next} not in state table"}

        current_idx = state_table.index(current)
        next_idx = state_table.index(proposed_next)

        # Must advance (no backward transitions without governance)
        if next_idx <= current_idx:
            return {"valid": False, "reason": f"Backward transition {current}→{proposed_next} requires governance program"}

        # Check transition rules if defined
        rule_key = f"{current}_to_{proposed_next}"
        if rule_key in transition_rules:
            pass  # rule exists — would evaluate against context in full impl
        elif next_idx > current_idx + 1:
            return {"valid": False, "reason": f"Cannot skip states: {current}→{proposed_next} (skipped {next_idx - current_idx - 1})"}

        return {
            "valid": True,
            "prior_state": current,
            "next_state": proposed_next,
            "trigger": trigger,
            "transition_rule_key": rule_key,
        }


def _load_state_table(program_id: str) -> list:
    lib = Path(__file__).parent.parent / "programs" / "program_library_v1.json"
    if lib.exists():
        data = json.loads(lib.read_text())
        for p in data.get("programs", []):
            if p["program_id"] == program_id:
                return p.get("states", [])
    # Commercial fallback
    return ["S0_IDENTIFY","S1_OPEN","S2_FRAME","S3_QUALIFY","S4_CHAMPION",
            "S5_VALIDATION","S6_NEGOTIATION","S7_CLOSE","S8_COMMIT","S9_ARCHIVE"]

def _load_transition_rules(program_id: str) -> dict:
    if "commercial" in program_id:
        return {
            "S1_OPEN_to_S2_FRAME": "response_received == true",
            "S2_FRAME_to_S3_QUALIFY": "engagement_score >= threshold",
            "S3_QUALIFY_to_S4_CHAMPION": "qualified == true",
            "S4_CHAMPION_to_S5_VALIDATION": "objection_type in skepticism_or_regulatory",
            "S4_CHAMPION_to_S6_NEGOTIATION": "price_or_structure_discussion == true",
            "S5_VALIDATION_to_S6_NEGOTIATION": "credibility_restored == true",
            "S6_NEGOTIATION_to_S7_CLOSE": "alignment_signal == true",
            "S7_CLOSE_to_S8_COMMIT": "verbal_commit == true",
            "S8_COMMIT_to_S9_ARCHIVE": "contract_executed == true",
        }
    return {}
