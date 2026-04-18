"""
AXIOLEV NS∞ — Brokerage compliance ops
Six deterministic gate ops. Each returns:
  {ok: bool, gate: str, evidence: dict, timestamp: str, reason?: str}
Not a substitute for counsel — a pre-action gate so any forbidden action
emits a clean FAIL_CLOSED receipt before an adapter is touched.
Owner: AXIOLEV Holdings LLC. No LLM legal claim.
"""
from datetime import datetime, timezone


def _ts(): return datetime.now(timezone.utc).isoformat()


def _receipt(ok, gate, evidence, reason=""):
    r = {"ok": ok, "gate": gate, "evidence": evidence, "timestamp": _ts()}
    if reason: r["reason"] = reason
    return r


def check_fair_housing(payload):
    text = (payload.get("text") or "").lower()
    stoplist = ["no kids","adults only","no children","christian home",
                "perfect for singles","no section 8","prefer male","prefer female",
                "ideal for families","no families","mature tenants"]
    hits = [w for w in stoplist if w in text]
    if hits:
        return _receipt(False, "fair_housing",
                        {"text_sample": text[:200], "hits": hits},
                        reason=f"stoplist hit: {hits}")
    return _receipt(True, "fair_housing", {"text_length": len(text), "hits": []})


def check_tcpa_dnc(payload):
    phone = payload.get("phone")
    consent = payload.get("consent_status")
    dnc = payload.get("dnc_status")
    if not phone:
        return _receipt(False, "tcpa_dnc", {}, reason="missing phone")
    if consent not in ("express_written","express","prior_business_relationship"):
        return _receipt(False, "tcpa_dnc", {"phone": phone, "consent": consent}, reason="consent not verified")
    if dnc not in ("clear","not_listed"):
        return _receipt(False, "tcpa_dnc", {"phone": phone, "dnc": dnc}, reason="DNC status unresolved")
    return _receipt(True, "tcpa_dnc", {"phone": phone, "consent": consent, "dnc": dnc})


def check_ca_recording_consent(payload):
    participants = payload.get("participants", [])
    disclosures = payload.get("disclosures", [])
    missing = [p for p in participants if p not in disclosures]
    if missing:
        return _receipt(False, "ca_recording_consent",
                        {"participants": participants, "missing": missing},
                        reason=f"consent not recorded for: {missing}")
    return _receipt(True, "ca_recording_consent",
                    {"participants": participants, "disclosures_count": len(disclosures)})


def check_wa_recording_announcement(payload):
    ar = payload.get("announcement_recorded", False)
    ats = payload.get("announcement_timestamp")
    if not ar:
        return _receipt(False, "wa_recording_announcement",
                        {"announcement_recorded": False}, reason="announcement not recorded")
    if not ats:
        return _receipt(False, "wa_recording_announcement",
                        {"announcement_recorded": True, "timestamp": None},
                        reason="announcement timestamp missing")
    return _receipt(True, "wa_recording_announcement",
                    {"announcement_recorded": True, "timestamp": ats})


def check_agency(payload):
    status = payload.get("agency_status")
    ack = payload.get("agency_acknowledged", False)
    if status not in ("buyer","seller","dual_disclosed"):
        return _receipt(False, "agency_check", {"agency_status": status}, reason="agency not established")
    if not ack:
        return _receipt(False, "agency_check",
                        {"agency_status": status, "acknowledged": False},
                        reason="agency not acknowledged by party")
    return _receipt(True, "agency_check", {"agency_status": status, "acknowledged": True})


def block_wire_execution(payload):
    """UNCONDITIONAL block. Never returns ok=True."""
    return _receipt(False, "wire_execution_block",
                    {"intent": payload.get("intent"),
                     "amount": payload.get("amount"),
                     "destination": payload.get("destination")},
                    reason="wire execution structurally forbidden; route to wire-safe playbook")


REGISTRY = {
    "compliance.check_fair_housing": check_fair_housing,
    "compliance.check_tcpa_dnc": check_tcpa_dnc,
    "compliance.check_ca_recording_consent": check_ca_recording_consent,
    "compliance.check_wa_recording_announcement": check_wa_recording_announcement,
    "compliance.check_agency": check_agency,
    "compliance.block_wire_execution": block_wire_execution,
}


def register(cps_registry):
    n = 0
    for name, fn in REGISTRY.items():
        if hasattr(cps_registry, "register"):
            cps_registry.register(name, fn)
        else:
            cps_registry[name] = fn
        n += 1
    return n
