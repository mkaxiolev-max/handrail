from enum import Enum


class SystemTier(str, Enum):
    ACTIVE = "active"
    ISOLATED = "isolated"
    SUSPENDED = "suspended"


class RiskTier(str, Enum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"


class ProgramState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class ProgramNamespace(str, Enum):
    COMMERCIAL = "commercial"
    FUNDRAISING = "fundraising"
    HIRING = "hiring"
    PARTNERSHIP = "partnership"
    MA = "ma"
    ADVISOR_SAN = "advisor_san"
    CUSTOMER_SUCCESS = "customer_success"
    PRODUCT_FEEDBACK = "product_feedback"
    GOVERNANCE = "governance"
    KNOWLEDGE_INGESTION = "knowledge_ingestion"


class IntentClass(str, Enum):
    VOICE_QUICK = "voice_quick"
    VOICE_ACTION = "voice_action"
    STRATEGY = "strategy"
    HIGH_RISK = "high_risk"
    DEFAULT = "default"


class VoiceMode(str, Enum):
    AMBIENT = "ambient"
    ACTIVE = "active"
    MUTED = "muted"


class NeverEventCode(str, Enum):
    NE1 = "NE1"  # dignity violation
    NE2 = "NE2"  # self-destruct
    NE3 = "NE3"  # auth bypass
    NE4 = "NE4"  # policy override
    NE5 = "NE5"  # bulk irreversible ops
    NE6 = "NE6"  # external data exfiltration
    NE7 = "NE7"  # quorum override


class ReceiptType(str, Enum):
    BOOT = "boot"
    INTENT = "intent"
    CPS_OP = "cps_op"
    PROGRAM = "program"
    GOVERNANCE = "governance"
    KERNEL = "kernel"
    MODEL = "model"


class ConferenceState(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"


class OpDecision(str, Enum):
    OK = "OK"
    POLICY_DENIAL = "POLICY_DENIAL"
    NEVER_EVENT = "NEVER_EVENT"
    SKIP = "SKIP"
    ERROR = "ERROR"
