"""Π admissibility engine — deterministic axiom evaluation."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from abi.return_block import ReturnBlock
from pi.never_events import load_never_events

def _find_canon_root() -> str:
    """Search upward from cwd for canon/axioms/ax_core.json."""
    # Env override for container
    if os.environ.get("CANON_ROOT"):
        return os.path.join(os.environ["CANON_ROOT"], "axioms/ax_core.json")
    # Walk up from cwd
    path = os.path.abspath(os.getcwd())
    for _ in range(6):
        candidate = os.path.join(path, "canon/axioms/ax_core.json")
        if os.path.exists(candidate):
            return candidate
        path = os.path.dirname(path)
    # Fallback: relative to this file
    return os.path.join(os.path.dirname(__file__), "../../../../canon/axioms/ax_core.json")


_AXIOM_PATH = _find_canon_root()

_AXIOMS: Optional[List[Dict]] = None
_NEVER_EVENTS: Optional[List[Dict]] = None


def _load_axioms() -> List[Dict]:
    global _AXIOMS
    if _AXIOMS is None:
        with open(_AXIOM_PATH) as f:
            _AXIOMS = json.load(f)["axioms"]
    return _AXIOMS


def _load_never_event_corpus() -> List[Dict]:
    global _NEVER_EVENTS
    if _NEVER_EVENTS is None:
        _NEVER_EVENTS = load_never_events()
    return _NEVER_EVENTS


class PiCheckRequest(BaseModel):
    candidate: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class PiCheckResult(BaseModel):
    return_block_version: int = 2
    ok: bool
    rc: int = 0
    operation: str = "pi.check"
    failure_reason: Optional[str] = None
    admissible: bool
    triggered_axioms: List[str]
    triggered_never_events: List[str]
    abstention: bool
    reason: str
    artifacts: List[Dict[str, Any]] = []
    checks: List[Dict[str, Any]] = []
    state_change: Optional[Dict] = None
    warnings: List[str] = []
    receipt_id: Optional[str] = None
    timestamp: Optional[str] = None
    dignity_banner: str = "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"


def _op_matches_never_event(op: str, ne: Dict) -> bool:
    """Check if candidate op string matches a never-event pattern."""
    triggers = ne.get("trigger_ops", [])
    return any(op.startswith(t) for t in triggers)


class PiEngine:
    """Deterministic Π admissibility engine.

    Algorithm:
    1. Load ax_core.json + never_events corpus
    2. Check candidate op against never-event triggers
    3. If never-event triggered → admissible=False, abstention=False
    4. If evidence=null AND op is consequential → admissible=False, abstention=True
    5. Else → admissible=True
    """

    def check(self, request: PiCheckRequest) -> PiCheckResult:
        import uuid
        from datetime import datetime, timezone

        candidate = request.candidate
        op = str(candidate.get("op", ""))
        evidence = candidate.get("evidence", "__present__")

        axioms = _load_axioms()
        never_events = _load_never_event_corpus()

        triggered_axioms: List[str] = []
        triggered_never: List[str] = []

        # Step 1: check never-events
        for ne in never_events:
            if _op_matches_never_event(op, ne):
                triggered_never.append(ne.get("id", ne.get("name", "unknown")))
                # Map never-event to axiom ref
                ax_ref = ne.get("axiom_ref")
                if ax_ref and ax_ref not in triggered_axioms:
                    triggered_axioms.append(ax_ref)

        if triggered_never:
            return PiCheckResult(
                ok=False,
                rc=1,
                admissible=False,
                triggered_axioms=triggered_axioms,
                triggered_never_events=triggered_never,
                abstention=False,
                failure_reason="never_event_triggered",
                reason=f"Never-event triggered: {', '.join(triggered_never)}",
                receipt_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Step 2: ambiguity check — no evidence + consequential op
        _consequential_prefixes = (
            "canon.", "execute.", "wire.", "promote.", "admin.", "delete.",
        )
        is_consequential = any(op.startswith(p) for p in _consequential_prefixes)
        if evidence is None and is_consequential:
            return PiCheckResult(
                ok=False,
                rc=1,
                admissible=False,
                triggered_axioms=["AX-5"],
                triggered_never_events=[],
                abstention=True,
                failure_reason="ambiguity",
                reason="Ambiguity: consequential op with no evidence anchor — AX-5 fails closed",
                receipt_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Step 3: admissible
        return PiCheckResult(
            ok=True,
            rc=0,
            admissible=True,
            triggered_axioms=[],
            triggered_never_events=[],
            abstention=False,
            reason="No axiom violations detected",
            receipt_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
