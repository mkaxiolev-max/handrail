"""Bridge normalization — ns_bridge always emits ReturnBlock.v2.

Non-conforming upstream responses are logged to Alexandria for audit.
Never returns None; never returns a dict without return_block_version.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("ns.bridge.normalize")

_DIGNITY = "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_rb(ok: bool, rc: int, operation: str) -> Dict[str, Any]:
    return {
        "return_block_version": 2,
        "ok": ok,
        "rc": rc,
        "operation": operation,
        "failure_reason": None,
        "artifacts": [],
        "checks": [],
        "state_change": None,
        "warnings": [],
        "receipt_id": str(uuid.uuid4()),
        "timestamp": _now_iso(),
        "dignity_banner": _DIGNITY,
    }


def wrap_response(
    upstream: Any,
    operation: str = "bridge.upstream",
    ok: Optional[bool] = None,
) -> Dict[str, Any]:
    """Wrap any upstream value in ReturnBlock.v2.

    If upstream is already v2-shaped, return it unchanged.
    Otherwise, place it in artifacts[0].
    """
    if isinstance(upstream, dict) and upstream.get("return_block_version") == 2:
        return upstream

    # Non-conforming upstream — wrap and log for Alexandria audit
    if isinstance(upstream, dict) and upstream.get("return_block_version") not in (None, 2):
        logger.warning("bridge: non-v2 return_block_version from %s — wrapping", operation)

    rb = _base_rb(ok=True if ok is None else ok, rc=0, operation=operation)
    rb["artifacts"] = [upstream] if upstream is not None else []
    if not rb["ok"]:
        rb["rc"] = 1
    return rb


def normalize_bridge_response(
    upstream: Any,
    operation: str = "bridge.upstream",
    exc: Optional[Exception] = None,
) -> Dict[str, Any]:
    """Normalize: on exception emit ok=False; otherwise wrap upstream."""
    if exc is not None:
        logger.error("bridge exception for %s: %s", operation, exc)
        rb = _base_rb(ok=False, rc=1, operation=operation)
        rb["failure_reason"] = str(exc)
        return rb

    return wrap_response(upstream, operation=operation)
