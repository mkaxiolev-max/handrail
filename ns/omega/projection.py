"""
axiolev-omega-projection-v2
AXIOLEV Holdings LLC © 2026

Recovery-ordered projection engine. Six strategies tried in order.
"""
from __future__ import annotations
from typing import Callable, Dict, List, Optional

from .primitives import (
    ProjectionRequest, ProjectionResult, RecoveryStrategy,
    Recoverability, ConfidenceEnvelope,
)


RECOVERY_ORDER: List[RecoveryStrategy] = [
    RecoveryStrategy.EXACT_LOCAL,
    RecoveryStrategy.DELTA_REPLAY,
    RecoveryStrategy.SHARD_RECOVERY,
    RecoveryStrategy.ENTANGLEMENT_ASSISTED,
    RecoveryStrategy.SEMANTIC,
    RecoveryStrategy.GRACEFUL_PARTIAL,
]

StrategyFn = Callable[[ProjectionRequest], Optional[Dict]]


def project(
    request: ProjectionRequest,
    strategies: Dict[RecoveryStrategy, StrategyFn],
) -> ProjectionResult:
    attempts: List[RecoveryStrategy] = []
    payload: Optional[Dict] = None
    used: Optional[RecoveryStrategy] = None

    for strat in RECOVERY_ORDER:
        attempts.append(strat)
        fn = strategies.get(strat)
        if fn is None:
            continue
        try:
            out = fn(request)
        except Exception:
            out = None
        if out is not None:
            payload = out
            used = strat
            break

    if used == RecoveryStrategy.EXACT_LOCAL:
        rec = Recoverability.EXACT
    elif used in (RecoveryStrategy.DELTA_REPLAY, RecoveryStrategy.SHARD_RECOVERY):
        rec = Recoverability.RECONSTRUCTIBLE
    elif used in (RecoveryStrategy.ENTANGLEMENT_ASSISTED, RecoveryStrategy.SEMANTIC):
        rec = Recoverability.SEMANTIC_EQUIVALENT
    elif used == RecoveryStrategy.GRACEFUL_PARTIAL:
        rec = Recoverability.PARTIAL
    else:
        rec = Recoverability.UNRECOVERABLE

    conf = ConfidenceEnvelope(
        evidence=0.8 if payload else 0.0,
        contradiction=0.1,
        novelty=0.3,
        stability=0.8 if payload else 0.0,
    )

    return ProjectionResult(
        request_id=request.id,
        branch_id=request.branch_id,
        mode=request.mode,
        confidence=conf,
        recoverability=rec,
        order_used=attempts,
        payload=payload or {},
    )
