"""AXIOLEV NS∞ — Brokerage v1 smoke tests. Zero LLM calls, zero network."""
import json, sys
from pathlib import Path
sys.path.insert(0, ".")

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  [OK]   {name}")
    else:
        print(f"  [FAIL] {name} — {detail}")
        FAILED.append(name)


def test_jurisdiction_loader():
    print("\n· Jurisdiction loader")
    from runtime.jurisdiction import load_jurisdiction, list_available
    avail = list_available()
    check("CA+WA packs available",
          ("CA","brokerage") in avail and ("WA","brokerage") in avail, f"got {avail}")
    ca = load_jurisdiction("CA","brokerage")
    check("CA loads", ca.jurisdiction=="CA")
    check("CA all-party consent", ca.enforces("call_recording_requires_all_party_consent"))
    check("CA forbids wire.send", "wire.send" in ca.forbidden_actions)
    check("CA has statute citations", len(ca.citations) >= 2)
    wa = load_jurisdiction("WA","brokerage")
    check("WA loads", wa.jurisdiction=="WA")
    check("WA pamphlet required", wa.enforces("pamphlet_surface_required"))


def test_compliance_ops():
    print("\n· Compliance ops")
    from ops.compliance.brokerage_gates import REGISTRY
    expected = {"compliance.check_fair_housing","compliance.check_tcpa_dnc",
                "compliance.check_ca_recording_consent","compliance.check_wa_recording_announcement",
                "compliance.check_agency","compliance.block_wire_execution"}
    check("all 6 ops registered", set(REGISTRY.keys())==expected)
    r = REGISTRY["compliance.check_fair_housing"]({"text":"Adults only, no kids."})
    check("fair_housing fails on stoplist", r["ok"] is False)
    r = REGISTRY["compliance.check_fair_housing"]({"text":"Bright 3 bed, updated kitchen."})
    check("fair_housing passes on clean", r["ok"] is True)
    r = REGISTRY["compliance.block_wire_execution"]({"intent":"send","amount":500000,"destination":"x"})
    check("wire_block always ok=False", r["ok"] is False)
    r = REGISTRY["compliance.check_agency"]({"agency_status":None})
    check("agency_check fails no status", r["ok"] is False)
    r = REGISTRY["compliance.check_tcpa_dnc"]({"phone":"+15551234567","consent_status":"express_written","dnc_status":"clear"})
    check("tcpa_dnc passes with good inputs", r["ok"] is True)


def test_adapters():
    print("\n· Adapters")
    from adapters.brokerage import (MLSAdapter, DocsAdapter, OfferAdapter,
                                    EscrowAdapter, WireAdapter, CommsAdapter)
    for cls in (MLSAdapter, DocsAdapter, OfferAdapter, EscrowAdapter, WireAdapter, CommsAdapter):
        check(f"{cls.__name__} instantiates", cls() is not None)
    w = WireAdapter()
    check("WireAdapter has verify_playbook", hasattr(w,"verify_playbook"))
    check("WireAdapter has NO .send", not hasattr(w,"send"))
    r = w.verify_playbook({"wire_id":"w1"})
    check("verify_playbook executable=False", r["executable"] is False)


def test_mission_graphs():
    print("\n· Mission graphs")
    d = Path("programs/brokerage/missions")
    expected = {"mg_resi_hunter_prospect.json","mg_resi_listing_intake.json",
                "mg_resi_buyer_consult.json","mg_resi_offer_esign.json",
                "mg_resi_escrow_wire_safe.json","mg_resi_close_postcare.json"}
    present = {p.name for p in d.glob("*.json")}
    check("all 6 missions present", expected.issubset(present), f"missing: {expected-present}")
    for f in expected:
        data = json.loads((d/f).read_text())
        check(f"{f} mission_id", "mission_id" in data)
        check(f"{f} states≥1", len(data.get("states",[]))>0)
        check(f"{f} transitions≥1", len(data.get("transitions",[]))>0)


def test_program_library():
    print("\n· Program library")
    lib = json.loads(Path("programs/program_library_v1.json").read_text())
    ids = {p["program_id"] for p in lib.get("programs",[])}
    check("brokerage registered", "whisper_brokerage_residential_starter_v1" in ids)


def test_roles():
    print("\n· Role bindings")
    d = Path("programs/brokerage/roles")
    expected = {"violet_interface_operator.json","hunter_operator.json","listing_operator.json",
                "buyer_operator.json","offer_operator.json","escrow_operator.json","compliance_operator.json"}
    present = {p.name for p in d.glob("*.json")}
    check("all 7 roles present", expected.issubset(present), f"missing: {expected-present}")
    for f in expected:
        data = json.loads((d/f).read_text())
        check(f"{f} has memory_scope_spec", "memory_scope_spec" in data)


if __name__ == "__main__":
    print("═══════════════════════════════════════════════════════════════════")
    print(" BROKERAGE v1 SMOKE TESTS")
    print("═══════════════════════════════════════════════════════════════════")
    test_jurisdiction_loader()
    test_compliance_ops()
    test_adapters()
    test_mission_graphs()
    test_program_library()
    test_roles()
    print("")
    if FAILED:
        print(f"✗ {len(FAILED)} failure(s): {FAILED}")
        sys.exit(1)
    print("✓ ALL SMOKE TESTS PASSED")
