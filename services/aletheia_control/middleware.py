"""Dual-mode middleware. Mode 1 (default): observation-only peer service.
Mode 2 (ALETHEIA_CONTROL_ENFORCE=1): hard gate on Handrail/Ether/Storytime.
"""
from __future__ import annotations
import os
from typing import Callable, Any
from .service import AletheiaControlService

ENFORCE_ENV = "ALETHEIA_CONTROL_ENFORCE"

def is_enforcing() -> bool:
    return os.environ.get(ENFORCE_ENV, "0") == "1"

class AletheiaControlMiddleware:
    def __init__(self, svc: AletheiaControlService):
        self.svc = svc

    def gate(self, op: str, ctx: dict, proceed: Callable[[], Any]) -> Any:
        # always observe
        observed = {"op": op, "input_id": ctx.get("input_id"), "actor": ctx.get("actor","self")}
        if not is_enforcing():
            return proceed()
        # enforcement: require a ControlClassification receipt for this input
        iid = ctx.get("input_id")
        if not any(c.input_id == iid for c in self.svc.classifications):
            raise PermissionError(f"aletheia-control: no classification receipt for {iid}")
        return proceed()
