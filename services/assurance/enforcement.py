# Copyright © 2026 AXIOLEV Holdings LLC. All rights reserved.
"""
NS-AL AssuranceLayer — runtime enforcement decorator.

@assured(contract=...) intercepts a state transition and:
  1. Evaluates contract preconditions before execution.
  2. Evaluates contract postconditions after execution.
  3. Dispatches the artifact bundle to VerificationDispatcher.
  4. REJECTS (raises AssuranceViolation) if:
       - dispatch returns a REJECTED VerificationReceipt, OR
       - dispatch returns a PENDING ObligationArtifact (no receipt yet), OR
       - dispatch returns neither receipt nor obligation.

The caller catches AssuranceViolation, inspects exc.obligation, runs the
compensating_action, then retries with the RESOLVED obligation as an artifact.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, List, Optional

from .dispatcher import VerificationDispatcher
from .types import (
    ComputationContract,
    ObligationArtifact,
    ObligationStatus,
    VerificationReceipt,
    Verdict,
)


class AssuranceViolation(Exception):
    """
    Raised when a state transition violates Constitutional Invariant 11.
    If violation is obligation-driven, exc.obligation carries the pending artifact
    so the caller can perform the compensating_action and retry.
    """

    def __init__(self, message: str, obligation: Optional[ObligationArtifact] = None) -> None:
        super().__init__(message)
        self.obligation = obligation


def assured(
    contract:         ComputationContract,
    artifacts_fn:     Optional[Callable[[Any], List[Any]]] = None,
    yubikey_verified: bool = False,
    prev_hash:        Optional[str] = None,
) -> Callable:
    """
    Decorator enforcing NS-AL Invariant 11 on a state transition.

    Parameters
    ----------
    contract         : ComputationContract specifying pre/post conditions, risk tier.
    artifacts_fn     : Called with the function's return value; must return a list of
                       ProofArtifact / CertificateArtifact / BoundedClaim /
                       ObligationArtifact instances.  If None, the empty list is used.
    yubikey_verified : True only when YubiKey 26116460 OTP has been validated upstream.
                       Required for R4 canon-touching contracts.
    prev_hash        : subject_hash of the preceding VerificationReceipt — enables
                       cross-layer receipt chain integrity.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            _check_preconditions(contract, args, kwargs)
            result = fn(*args, **kwargs)
            _check_postconditions(contract, result)

            artifacts = artifacts_fn(result) if artifacts_fn is not None else []
            receipt, obligation = VerificationDispatcher().dispatch(
                contract, artifacts, yubikey_verified, prev_hash
            )

            if receipt is not None and receipt.verdict == Verdict.REJECTED:
                raise AssuranceViolation(
                    f"I11:receipt_rejected — {receipt.evidence_refs}",
                )

            if receipt is None and obligation is not None:
                raise AssuranceViolation(
                    f"I11:obligation_pending — {obligation.compensating_action}",
                    obligation=obligation,
                )

            if receipt is None and obligation is None:
                raise AssuranceViolation("I11:no_receipt_and_no_obligation")

            # VERIFIED receipt — transition accepted
            return result

        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_preconditions(
    contract: ComputationContract, args: tuple, kwargs: dict
) -> None:
    inputs = {"args": args, "kwargs": kwargs}
    for pre in contract.preconditions:
        if callable(pre) and not pre(inputs):
            raise AssuranceViolation(f"I11:precondition_failed — {getattr(pre, '__name__', repr(pre))}")


def _check_postconditions(contract: ComputationContract, result: Any) -> None:
    for post in contract.postconditions:
        if callable(post) and not post(result):
            raise AssuranceViolation(f"I11:postcondition_failed — {getattr(post, '__name__', repr(post))}")
