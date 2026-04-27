from services.pap.canon_bridge import can_promote_to_canon_via_pap

def can_write_canon(claim, logos_decision, canon_decision,
                    ldr_score, omega_gnoseo_score, pap_score):
    ok, reason = can_promote_to_canon_via_pap(
        logos_decision, canon_decision,
        ldr_score, omega_gnoseo_score, pap_score,
    )
    return ok
