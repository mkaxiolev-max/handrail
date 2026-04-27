"""Triadic Canon gating. Decree P-6."""
from typing import Optional, Tuple


def triadic_canon_check(ldr: float, omega_gnoseo: float, pap: float) -> Tuple[bool, float, Optional[str]]:
    """
    Decree P-6: require min(LDR, Omega-Gnoseo, PAP) >= 95.
    Returns (eligible, triadic_min, blocking_track).
    """
    triadic_min = min(ldr, omega_gnoseo, pap)
    eligible = triadic_min >= 95.0
    blocker: Optional[str] = None
    if not eligible:
        if ldr <= omega_gnoseo and ldr <= pap:
            blocker = "LDR"
        elif omega_gnoseo <= ldr and omega_gnoseo <= pap:
            blocker = "OMEGA_GNOSEO"
        else:
            blocker = "PAP"
    return (eligible, triadic_min, blocker)


def can_promote_to_canon_via_pap(
    logos_decision: str, canon_decision: str,
    ldr: float, omega_gnoseo: float, pap: float,
) -> Tuple[bool, str]:
    """Combined gate: Aletheion dual-ALLOW AND triadic min >= 95."""
    if logos_decision != "ALLOW":
        return (False, f"logos {logos_decision}")
    if canon_decision != "ALLOW":
        return (False, f"canon {canon_decision}")
    eligible, triadic_min, blocker = triadic_canon_check(ldr, omega_gnoseo, pap)
    if not eligible:
        return (False, f"triadic_min={triadic_min:.2f} < 95 (blocking: {blocker})")
    return (True, f"triadic_min={triadic_min:.2f}")
