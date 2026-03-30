from __future__ import annotations

OPCODE_TABLE = {
    "φ:ns:boot": {
        "task_type": "ops_status_check",
        "objective": "semantic opcode status check",
        "payload": {}
    }
}

def parse_opcode(text: str) -> dict:
    raw = (text or "").strip()

    if raw not in OPCODE_TABLE:
        raise ValueError(f"unsupported_opcode:{raw}")

    entry = OPCODE_TABLE[raw]

    return {
        "instruction": raw,
        "task_type": entry["task_type"],
        "objective": entry["objective"],
        "payload": entry.get("payload", {})
    }
