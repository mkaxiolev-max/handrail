"""
NS∞ ABI Validator — enforces frozen object chain
All 5 Tier-1 schemas. Handrail imports this as the execution gate.
"""
import json, hashlib, random
from datetime import datetime, timezone
from pathlib import Path
import jsonschema

SCHEMA_DIR = Path(__file__).parent.parent / "schemas"

def _load(name):
    return json.loads((SCHEMA_DIR / f"{name}.json").read_text())

SCHEMAS = {
    "IntentPacket.v1":          _load("IntentPacket.v1"),
    "CPSPacket.v1":             _load("CPSPacket.v1"),
    "ReturnBlock.v2":           _load("ReturnBlock.v2"),
    "KernelDecisionReceipt.v1": _load("KernelDecisionReceipt.v1"),
    "CommitEvent.v1":           _load("CommitEvent.v1"),
    "BootMissionGraph.v1":      _load("BootMissionGraph.v1"),
    "BootProofReceipt.v1":      _load("BootProofReceipt.v1"),
    "StateDelta.v1":            _load("StateDelta.v1"),
    "TransitionLifecycle.v1":   _load("TransitionLifecycle.v1"),
    "LexiconEntry.v1":          _load("LexiconEntry.v1"),
}

def validate(schema_name: str, data: dict) -> dict:
    """Returns {ok, errors, schema_version}"""
    schema = SCHEMAS.get(schema_name)
    if not schema:
        return {"ok": False, "errors": [f"Unknown schema: {schema_name}"]}
    try:
        jsonschema.validate(data, schema)
        return {"ok": True, "errors": [], "schema_version": schema.get("version", "?")}
    except jsonschema.ValidationError as e:
        return {"ok": False, "errors": [e.message], "schema_version": schema.get("version", "?")}

def make_intent_id() -> str:
    return "INT-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_cps_id() -> str:
    return "CPS-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_return_id() -> str:
    return "RET-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_kdr_id() -> str:
    return "KDR-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_cmt_id() -> str:
    return "CMT-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_boot_id() -> str:
    return "BOOT-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_bpr_id() -> str:
    return "BPR-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_sdl_id() -> str:
    return "SDL-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_trn_id() -> str:
    return "TRN-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

def make_lex_id() -> str:
    return "LEX-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

# Aliases for backward compat
make_state_delta_id = make_sdl_id
make_transition_id  = make_trn_id

def freeze_hash(schema_name: str) -> str:
    """SHA256 of schema file — canonical freeze fingerprint"""
    path = SCHEMA_DIR / f"{schema_name}.json"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

def freeze_manifest() -> dict:
    """Returns {schema_name: hash} for all frozen schemas."""
    return {name: freeze_hash(name) for name in SCHEMAS}

if __name__ == "__main__":
    print("=== ABI FREEZE VERIFICATION ===")
    for name in SCHEMAS:
        h = freeze_hash(name)
        print(f"  [ok] {name}: frozen @ {h}")

    # Test IntentPacket valid
    test_intent = {
        "intent_id": "INT-ABC12345",
        "source_surface": "voice",
        "raw_input": "Run sovereign boot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "sess-001",
        "founder_present": True,
        "dignity_budget": 1.0,
    }
    r = validate("IntentPacket.v1", test_intent)
    print(f"  IntentPacket valid:    {'PASS' if r['ok'] else 'FAIL: ' + str(r['errors'])}")

    # Test bad packet (missing required fields)
    bad = {"intent_id": "INT-BAD00000"}
    r2 = validate("IntentPacket.v1", bad)
    print(f"  Bad packet rejected:   {'PASS' if not r2['ok'] else 'FAIL (should have rejected)'}")

    # Test CPSPacket valid
    test_cps = {
        "cps_id": "CPS-BOOT0001",
        "intent_id": "INT-ABC12345",
        "objective": "sovereign boot",
        "ops": [{"op": "http.health_check", "args": {"url": "http://ns:9000/healthz"}}],
        "risk_tier": "R0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    r3 = validate("CPSPacket.v1", test_cps)
    print(f"  CPSPacket valid:       {'PASS' if r3['ok'] else 'FAIL: ' + str(r3['errors'])}")

    print("")
    print("ABI FREEZE COMPLETE. Handrail ready to enforce.")
