import json

REPLAY_SEMANTICS = {
    "APPLY": "apply to state",
    "INDEX_ONLY": "index/log",
    "SIDE_EFFECT_PROOF": "use stored proof only",
    "NOOP": "skip",
}

STANDARD_KINDS = {
    "session_start": {"schema": {"context": (str, 1024)}, "replay_semantics": "APPLY"},
    "turn_complete": {"schema": {"input": (str, 4096), "output": (str, 4096)}, "replay_semantics": "APPLY"},
    "summary_generated": {"schema": {"summary_text": (str, 8192)}, "replay_semantics": "INDEX_ONLY"},
    "identity_linked": {"schema": {"person_id": (str, 64), "link_reason": (str, 256)}, "replay_semantics": "APPLY"},
    "action_requested": {"schema": {"action_id": (str, 64), "action_spec": (str, 8192)}, "replay_semantics": "INDEX_ONLY"},
    "action_approved": {"schema": {"action_id": (str, 64), "approval_reason": (str, 1024)}, "replay_semantics": "INDEX_ONLY"},
    "action_started": {"schema": {"action_id": (str, 64), "start_params": (str, 8192)}, "replay_semantics": "INDEX_ONLY"},
    "action_completed": {"schema": {"action_id": (str, 64), "result": (str, 16384), "exit_code": (int, None)}, "replay_semantics": "SIDE_EFFECT_PROOF"},
    "action_failed": {"schema": {"action_id": (str, 64), "error": (str, 16384), "exit_code": (int, None)}, "replay_semantics": "SIDE_EFFECT_PROOF"},
    "action_canceled": {"schema": {"action_id": (str, 64), "cancel_reason": (str, 1024)}, "replay_semantics": "NOOP"},
    "repair_applied": {"schema": {"old_session_id": (str, 128), "reason": (str, 1024)}, "replay_semantics": "NOOP"},
}

MAX_PAYLOAD_BYTES = 256 * 1024

def validate_payload(kind: str, payload: dict) -> None:
    if kind not in STANDARD_KINDS:
        raise ValueError(f"Unknown kind: {kind}")
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    if len(raw.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("Payload too large")
    schema = STANDARD_KINDS[kind]["schema"]
    for field, (typ, max_len) in schema.items():
        if field not in payload:
            raise ValueError(f"Missing field: {field}")
        if typ is int:
            if not isinstance(payload[field], int):
                raise ValueError(f"Wrong type for {field}: expected int")
        else:
            if not isinstance(payload[field], typ):
                raise ValueError(f"Wrong type for {field}: expected {typ.__name__}")
            if typ is str and max_len is not None and len(payload[field]) > max_len:
                raise ValueError(f"{field} too long")
