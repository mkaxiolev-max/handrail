"""CI-5 SilenceAbstention — privileged dignity-preserving 'I do not know' response.

Never a refusal. Always an abstention with explicit reason.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class SilenceAbstention:
    def evaluate(self, candidate: dict) -> Optional[Dict[str, Any]]:
        """If candidate triggers silence conditions, return abstention envelope.

        Conditions:
        - candidate explicitly marks silence: {"silence": true}
        - candidate has no evidence and no receipts
        - op is None or empty
        """
        op = candidate.get("op", "")
        evidence = candidate.get("evidence", "__present__")
        receipts = candidate.get("receipts", "__present__")

        if candidate.get("silence"):
            return self._abstain("explicit_silence_requested")

        if not op:
            return self._abstain("no_op_specified")

        if evidence is None:
            return self._abstain("no_evidence_anchor")

        return None  # no silence triggered

    def _abstain(self, reason: str) -> Dict[str, Any]:
        return {
            "abstain": True,
            "reason": reason,
            "dignity_preserved": True,
            "message": f"Silence abstention: {reason}. Dignity preserved.",
        }
