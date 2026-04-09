"""
HIC Engine — Human Intent Classification with USDL gate enforcement.

60 HIC patterns across 8 USDL gates (G1-G8).
Verdicts: R0 (allow), R1 (flag/log), VETO (block + never-event).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


# ── Verdict ───────────────────────────────────────────────────────────────────

class HICVerdict(str, Enum):
    R0 = "R0"       # Allow — clean intent
    R1 = "R1"       # Flag — proceed but log for review
    VETO = "VETO"   # Block — never-event or prohibited pattern


# ── USDL Gates ────────────────────────────────────────────────────────────────

@dataclass
class USDLGate:
    gate_id: str          # G1–G8
    name: str
    verdict: HICVerdict   # Default verdict when this gate triggers
    description: str


USDL_GATES: dict[str, USDLGate] = {
    "G1": USDLGate("G1", "dignity_invariant",        HICVerdict.VETO, "Actions violating human dignity"),
    "G2": USDLGate("G2", "self_destruct",            HICVerdict.VETO, "Irreversible system destruction"),
    "G3": USDLGate("G3", "auth_bypass",              HICVerdict.VETO, "Authentication or authorization bypass"),
    "G4": USDLGate("G4", "policy_override",          HICVerdict.VETO, "CPS policy gate override without quorum"),
    "G5": USDLGate("G5", "bulk_mutation",            HICVerdict.R1,   "Mass data writes without chain proof"),
    "G6": USDLGate("G6", "external_exfiltration",    HICVerdict.R1,   "Sending internal state to external surface"),
    "G7": USDLGate("G7", "privilege_escalation",     HICVerdict.R1,   "Requesting higher access than role allows"),
    "G8": USDLGate("G8", "temporal_manipulation",    HICVerdict.R1,   "Attempts to alter receipt timestamps or logs"),
}


# ── Pattern ───────────────────────────────────────────────────────────────────

@dataclass
class HICPattern:
    pattern_id: str
    label: str
    gate: str            # G1–G8
    keywords: list[str]
    regex: Optional[str] = None

    def matches(self, text: str) -> bool:
        t = text.lower()
        if any(kw in t for kw in self.keywords):
            return True
        if self.regex and re.search(self.regex, t, re.IGNORECASE):
            return True
        return False


# ── 60 Patterns ──────────────────────────────────────────────────────────────

HIC_PATTERNS: list[HICPattern] = [
    # G1 — dignity (10 patterns)
    HICPattern("G1-01", "dehumanize_user",        "G1", ["dehumanize", "strip rights", "remove dignity"]),
    HICPattern("G1-02", "coerce_consent",          "G1", ["force consent", "override consent", "no choice"]),
    HICPattern("G1-03", "mass_surveillance",       "G1", ["spy on all", "track everyone", "bulk surveillance"]),
    HICPattern("G1-04", "discriminatory_filter",   "G1", ["filter by race", "exclude by religion", "gender block"]),
    HICPattern("G1-05", "identity_destruction",    "G1", ["delete user identity", "erase account permanently", "purge all user data"]),
    HICPattern("G1-06", "nonconsensual_broadcast", "G1", ["broadcast without permission", "publish private data", "expose personal"]),
    HICPattern("G1-07", "manipulation_pattern",    "G1", ["psychologically manipulate", "coerce user", "exploit vulnerability"]),
    HICPattern("G1-08", "child_safety",            "G1", ["csam", "minor explicit", "child exploitation"]),
    HICPattern("G1-09", "slavery_pattern",         "G1", ["force labor", "compelled service", "unpaid forced"]),
    HICPattern("G1-10", "threats_physical",        "G1", ["threaten harm", "physical threat", "intimidate user"]),

    # G2 — self-destruct (8 patterns)
    HICPattern("G2-01", "wipe_all_data",           "G2", ["wipe everything", "delete all data", "format all"]),
    HICPattern("G2-02", "drop_database",           "G2", ["drop database", "drop table", "truncate all"]),
    HICPattern("G2-03", "kill_all_services",       "G2", ["kill all services", "shut everything down", "terminate all"]),
    HICPattern("G2-04", "destroy_receipts",        "G2", ["delete receipts", "erase audit log", "purge chain"]),
    HICPattern("G2-05", "revoke_all_keys",         "G2", ["revoke all keys", "cancel all auth", "invalidate all tokens"]),
    HICPattern("G2-06", "burn_alexandria",         "G2", ["delete alexandria", "erase knowledge base", "wipe memory store"]),
    HICPattern("G2-07", "remove_backups",          "G2", ["delete backups", "remove snapshots", "purge archives"]),
    HICPattern("G2-08", "self_destruct_trigger",   "G2", ["self destruct", "sys.self_destruct", "initiate shutdown sequence"]),

    # G3 — auth bypass (8 patterns)
    HICPattern("G3-01", "skip_auth",              "G3", ["skip authentication", "bypass auth", "no auth check"]),
    HICPattern("G3-02", "hardcode_token",          "G3", ["hardcode token", "embed secret", "inline credential"]),
    HICPattern("G3-03", "impersonate_founder",     "G3", ["act as founder", "impersonate admin", "pretend to be owner"]),
    HICPattern("G3-04", "yubikey_bypass",          "G3", ["skip yubikey", "bypass otp", "no yubikey check"]),
    HICPattern("G3-05", "session_hijack",          "G3", ["hijack session", "steal token", "forge session"]),
    HICPattern("G3-06", "zero_auth_endpoint",      "G3", ["open endpoint", "unauthenticated route", "public admin"]),
    HICPattern("G3-07", "credential_exposure",     "G3", ["log password", "print secret", "expose credential"]),
    HICPattern("G3-08", "token_forgery",           "G3", ["forge token", "fake jwt", "create fake auth"]),

    # G4 — policy override (6 patterns)
    HICPattern("G4-01", "cps_policy_skip",         "G4", ["skip policy", "bypass policy gate", "ignore cps"]),
    HICPattern("G4-02", "override_dignity_kernel", "G4", ["override kernel", "bypass dignity", "skip never-event"]),
    HICPattern("G4-03", "quorum_bypass",           "G4", ["skip quorum", "no conciliar", "bypass governance"]),
    HICPattern("G4-04", "risk_tier_downgrade",     "G4", ["lower risk tier", "change to r0", "downgrade risk"]),
    HICPattern("G4-05", "force_allow",             "G4", ["force allow", "override denial", "approve anyway"]),
    HICPattern("G4-06", "policy_delete",           "G4", ["delete policy", "remove constraint", "erase rule"]),

    # G5 — bulk mutation (8 patterns)
    HICPattern("G5-01", "bulk_atom_write",         "G5", ["write all atoms", "bulk insert atoms", "mass update atoms"]),
    HICPattern("G5-02", "bulk_feed_generate",      "G5", ["generate all feed", "bulk feed", "mass feed insert"]),
    HICPattern("G5-03", "mass_receipt_write",      "G5", ["write receipts in bulk", "mass receipt", "batch receipt"]),
    HICPattern("G5-04", "schema_migration_prod",   "G5", ["migrate production", "alter table prod", "schema change live"]),
    HICPattern("G5-05", "batch_delete",            "G5", ["delete where", "bulk delete", "mass remove rows"]),
    HICPattern("G5-06", "reindex_all",             "G5", ["reindex everything", "rebuild all indexes", "vacuum full"]),
    HICPattern("G5-07", "bulk_canon_promote",      "G5", ["promote all candidates", "mass canon commit", "bulk promote"]),
    HICPattern("G5-08", "overwrite_store",         "G5", ["overwrite store", "replace all entries", "reset all state"]),

    # G6 — external exfiltration (6 patterns)
    HICPattern("G6-01", "email_dump",              "G6", ["email the database", "send all data", "mail dump"]),
    HICPattern("G6-02", "webhook_leak",            "G6", ["send to webhook", "post to external", "notify third party"]),
    HICPattern("G6-03", "slack_internal_state",    "G6", ["post internal state to slack", "share system state publicly"]),
    HICPattern("G6-04", "cloud_upload",            "G6", ["upload to s3", "push to cloud", "sync externally"]),
    HICPattern("G6-05", "receipt_export",          "G6", ["export receipts", "share audit log", "send chain data"]),
    HICPattern("G6-06", "atom_dump_external",      "G6", ["export atoms", "send knowledge base", "share memory externally"]),

    # G7 — privilege escalation (7 patterns)
    HICPattern("G7-01", "root_request",            "G7", ["run as root", "sudo everything", "escalate to root"]),
    HICPattern("G7-02", "admin_claim",             "G7", ["grant admin", "make admin", "escalate privileges"]),
    HICPattern("G7-03", "role_override",           "G7", ["change my role", "set role to admin", "upgrade access"]),
    HICPattern("G7-04", "policy_profile_claim",    "G7", ["set policy_profile founder", "claim founder role"]),
    HICPattern("G7-05", "docker_host_mount",       "G7", ["mount docker socket", "access host filesystem", "privileged container"]),
    HICPattern("G7-06", "kernel_access",           "G7", ["access kernel", "kernel module", "load kernel driver"]),
    HICPattern("G7-07", "cross_tenant",            "G7", ["access other tenant", "cross account", "jump to different org"]),

    # G8 — temporal manipulation (7 patterns)
    HICPattern("G8-01", "backdate_receipt",        "G8", ["backdate receipt", "change timestamp", "alter created_at"]),
    HICPattern("G8-02", "replay_attack",           "G8", ["replay request", "reuse token", "replay old hash"]),
    HICPattern("G8-03", "clock_skew",              "G8", ["set system clock", "change system time", "fake timestamp"]),
    HICPattern("G8-04", "audit_log_edit",          "G8", ["edit audit log", "modify receipt", "alter chain entry"]),
    HICPattern("G8-05", "receipt_hash_override",   "G8", ["override hash", "replace hash", "fake receipt hash"]),
    HICPattern("G8-06", "created_at_override",     "G8", ["set created_at", "update created_at", "backfill dates"]),
    HICPattern("G8-07", "log_retroactive_change",  "G8", ["retroactively change log", "fix historical entry", "patch old record"]),
]

assert len(HIC_PATTERNS) == 60, f"Expected 60 HIC patterns, got {len(HIC_PATTERNS)}"


# ── Decision ──────────────────────────────────────────────────────────────────

@dataclass
class HICDecision:
    verdict: HICVerdict
    matched_patterns: list[HICPattern]
    gates_triggered: list[str]
    input_text: str
    rationale: str


# ── Engine ────────────────────────────────────────────────────────────────────

class HICEngine:
    """
    Evaluate input text against all 60 HIC patterns.
    Returns HICDecision with the most restrictive verdict.
    """

    def evaluate(self, text: str) -> HICDecision:
        matched: list[HICPattern] = []
        for pattern in HIC_PATTERNS:
            if pattern.matches(text):
                matched.append(pattern)

        if not matched:
            return HICDecision(
                verdict=HICVerdict.R0,
                matched_patterns=[],
                gates_triggered=[],
                input_text=text,
                rationale="No HIC patterns matched — intent classified clean",
            )

        gates_triggered = list({p.gate for p in matched})

        # Most restrictive verdict wins
        verdicts = [USDL_GATES[g].verdict for g in gates_triggered]
        if HICVerdict.VETO in verdicts:
            final_verdict = HICVerdict.VETO
        elif HICVerdict.R1 in verdicts:
            final_verdict = HICVerdict.R1
        else:
            final_verdict = HICVerdict.R0

        labels = [p.label for p in matched]
        rationale = f"Matched {len(matched)} pattern(s): {', '.join(labels[:5])}"
        if len(labels) > 5:
            rationale += f" (+{len(labels)-5} more)"

        return HICDecision(
            verdict=final_verdict,
            matched_patterns=matched,
            gates_triggered=gates_triggered,
            input_text=text,
            rationale=rationale,
        )

    def gate_summary(self) -> dict:
        return {gid: {"name": g.name, "default_verdict": g.verdict, "description": g.description}
                for gid, g in USDL_GATES.items()}

    def pattern_count(self) -> int:
        return len(HIC_PATTERNS)


_engine = HICEngine()

def get_hic_engine() -> HICEngine:
    return _engine
