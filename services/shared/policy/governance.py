"""Governance policy — never-event definitions."""
from shared.models.enums import NeverEventCode

NEVER_EVENTS = {
    NeverEventCode.NE1: {
        "code": "NE1",
        "name": "dignity_violation",
        "description": "Any action violating human dignity invariants",
        "trigger": "dignity.never_event",
        "severity": "FATAL",
    },
    NeverEventCode.NE2: {
        "code": "NE2",
        "name": "self_destruct",
        "description": "Irreversible system destruction",
        "trigger": "sys.self_destruct",
        "severity": "FATAL",
    },
    NeverEventCode.NE3: {
        "code": "NE3",
        "name": "auth_bypass",
        "description": "Authentication or authorization bypass",
        "trigger": "auth.bypass",
        "severity": "FATAL",
    },
    NeverEventCode.NE4: {
        "code": "NE4",
        "name": "policy_override",
        "description": "CPS policy gate override without conciliar quorum",
        "trigger": "policy.override",
        "severity": "FATAL",
    },
    NeverEventCode.NE5: {
        "code": "NE5",
        "name": "bulk_irreversible_ops",
        "description": "Bulk irreversible operations without quorum approval",
        "trigger": "ops.bulk_irreversible",
        "severity": "HIGH",
    },
    NeverEventCode.NE6: {
        "code": "NE6",
        "name": "data_exfiltration",
        "description": "External data exfiltration beyond authorized scope",
        "trigger": "data.exfiltrate",
        "severity": "HIGH",
    },
    NeverEventCode.NE7: {
        "code": "NE7",
        "name": "quorum_override",
        "description": "Override of YubiKey quorum requirement",
        "trigger": "quorum.override",
        "severity": "FATAL",
    },
}


def get_never_events() -> list[dict]:
    return list(NEVER_EVENTS.values())
