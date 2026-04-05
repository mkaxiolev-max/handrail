"""
Receipt Writer — semantic legal objects, not just logs.
Receipts must be reconstructive: auditor can answer WHY from receipts alone.
Every exception is a governed exception receipt or it did not happen.
"""
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

RECEIPTS_PATH = Path("/Volumes/NSExternal/.run/program_receipts.jsonl")
EXCEPTION_LOG = Path("/Volumes/NSExternal/.run/exception_receipts.jsonl")

def ts(): return datetime.now(timezone.utc).isoformat()
def rid(s): return f"PR-{hashlib.sha256((s+ts()).encode()).hexdigest()[:8]}"

class ReceiptWriter:
    def write_transition(self, program_runtime: dict, prior_state: str,
                         next_state: str, trigger: str, active_role: str,
                         actions_executed: list, risk_flags: list = None,
                         approval_path: str = None, next_state_patch: dict = None,
                         memory_update_intent: list = None) -> dict:
        """Write a full semantic transition receipt."""
        run_id = program_runtime["program_run_id"]
        receipt_id = rid(run_id + prior_state + next_state)

        # Output digest — hash of actions for determinism proof
        output_digest = hashlib.sha256(json.dumps(actions_executed, sort_keys=True).encode()).hexdigest()[:12]

        receipt = {
            "receipt_id": receipt_id,
            "program_run_id": run_id,
            "program_id": program_runtime["program_id"],
            "prior_state": prior_state,
            "next_state": next_state,
            "trigger_event": trigger,
            "active_role": active_role,
            "policy_bundle": program_runtime.get("policy_bundle", "unknown"),
            "actions_executed": actions_executed,
            "output_digest": output_digest,
            "risk_flags": risk_flags or [],
            "approval_path": approval_path,
            "next_state_patch": next_state_patch or {},
            "memory_update_intent": memory_update_intent or [],
            "timestamp": ts(),
        }

        # Append to receipts log
        RECEIPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RECEIPTS_PATH, "a") as f:
            f.write(json.dumps(receipt) + "\n")

        # Append to program runtime receipts list
        program_runtime["receipts"].append(receipt_id)
        program_runtime["state"] = next_state
        program_runtime["active_role"] = active_role
        program_runtime["updated_at"] = ts()

        return receipt

    def write_exception(self, program_run_id: str, exception_type: str,
                        requested_by: str, justification: str,
                        approved_by: Optional[str] = None,
                        governance_run_id: Optional[str] = None) -> dict:
        """
        Every exception is a governed exception receipt or it did not happen.
        No informal bypasses. No 'let founder hop on just this once.'
        """
        eid = f"EX-{hashlib.sha256((program_run_id+exception_type+ts()).encode()).hexdigest()[:8]}"
        receipt = {
            "exception_id": eid,
            "program_run_id": program_run_id,
            "exception_type": exception_type,
            "requested_by": requested_by,
            "justification": justification,
            "approved_by": approved_by,
            "governance_run_id": governance_run_id,
            "timestamp": ts(),
            "_warning": "Ungoverned exceptions are constitutional violations. Route through Governance program if recurring."
        }
        EXCEPTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(EXCEPTION_LOG, "a") as f:
            f.write(json.dumps(receipt) + "\n")
        return receipt
