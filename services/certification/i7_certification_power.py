"""
I7 Certification Power — real, artifact-backed certification report.

Scores are derived from discoverable evidence in the repo (test files,
proof artifacts, policy docs, ontology data).  No score is asserted
statically without a corresponding evidence item.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

Status = Literal["complete", "partial", "absent"]
Band = Literal[
    "not_certifiable",
    "provisional",
    "audit_ready_internal",
    "external_certification_ready",
    "theoretical_max",
]


@dataclass
class CertificationEvidence:
    description: str
    artifact_path: str | None = None
    verified: bool = True


@dataclass
class CertificationCategory:
    id: str
    name: str
    score_0_to_10: float
    evidence_items: list[CertificationEvidence] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    receipts: list[str] = field(default_factory=list)
    status: Status = "absent"

    def __post_init__(self) -> None:
        if self.score_0_to_10 > 10:
            raise ValueError(f"Category {self.id} score {self.score_0_to_10} exceeds 10")
        if self.score_0_to_10 < 0:
            raise ValueError(f"Category {self.id} score {self.score_0_to_10} is negative")


@dataclass
class CertificationReport:
    schema: str
    run_id: str
    generated_at_utc: str
    categories: list[CertificationCategory]
    total_score_0_to_100: float
    complete_categories: int
    partial_categories: int
    absent_categories: int
    blocking_gaps: list[str]
    certification_band: Band
    ontology_link: str | None
    claim_to_artifact_mapping: dict[str, str]

    def __post_init__(self) -> None:
        if self.total_score_0_to_100 > 100:
            raise ValueError("total_score_0_to_100 exceeds 100")
        # Refuse max score if any category absent
        if self.absent_categories > 0 and self.total_score_0_to_100 >= 100:
            raise ValueError("Cannot award max score with absent categories")


# ---------------------------------------------------------------------------
# Evidence discovery helpers
# ---------------------------------------------------------------------------

def _exists(*parts: str) -> bool:
    return (ROOT / Path(*parts)).exists()


def _glob_count(pattern: str) -> int:
    return len(list(ROOT.glob(pattern)))


def _test_count_in(pattern: str) -> int:
    """Count test functions matching a glob of Python files."""
    count = 0
    for p in ROOT.glob(pattern):
        try:
            text = p.read_text(errors="ignore")
            count += text.count("\ndef test_")
        except OSError:
            pass
    return count


def _proof_files() -> list[Path]:
    d = ROOT / "proofs"
    return list(d.glob("*.json")) if d.exists() else []


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------
# Category builders
# ---------------------------------------------------------------------------

def _governance() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    if _exists("policies"):
        ev.append(CertificationEvidence("Policy directory present", "policies/"))
    if _exists("POLICY_HIERARCHY.md"):
        ev.append(CertificationEvidence("Policy hierarchy documented", "POLICY_HIERARCHY.md"))
    if _exists("canon", "axioms"):
        ev.append(CertificationEvidence("Canon axioms present", "canon/axioms/"))
    t = _test_count_in("tests/certification/test_T060_governance.py")
    if t:
        ev.append(CertificationEvidence(f"Governance tests: {t}", "tests/certification/test_T060_governance.py"))
        receipts.append("tests/certification/test_T060_governance.py")
    if not ev:
        gaps.append("No governance evidence found")

    score = min(10.0, len(ev) * 2.5)
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory("governance", "Governance", score, ev, gaps, receipts, status)


def _risk() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    if _exists("KNOWN_EXTERNAL_GATES.json"):
        ev.append(CertificationEvidence("External gates registry", "KNOWN_EXTERNAL_GATES.json"))
    if _exists("tests/brokerage"):
        ev.append(CertificationEvidence("Brokerage risk tests", "tests/brokerage/"))
        receipts.append("tests/brokerage/")
    t = _test_count_in("tests/certification/test_T061_risk.py")
    if t:
        ev.append(CertificationEvidence(f"Risk tests: {t}", "tests/certification/test_T061_risk.py"))
        receipts.append("tests/certification/test_T061_risk.py")
    if _exists("services/ns", "nss", "kernel", "dignity.py"):
        ev.append(CertificationEvidence("Dignity Kernel never-event enforcement", "services/ns/nss/kernel/dignity.py"))
    if not ev:
        gaps.append("No risk evidence found")
    if len(ev) < 2:
        gaps.append("Weak risk coverage — add external verifier bundle")

    score = min(10.0, len(ev) * 2.5)
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory("risk", "Risk", score, ev, gaps, receipts, status)


def _lineage() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    proofs = _proof_files()
    if proofs:
        ev.append(CertificationEvidence(f"{len(proofs)} proof artifacts in proofs/", "proofs/"))
        receipts.extend([_rel(p) for p in proofs[:5]])
    if _exists("services", "alex_merkle"):
        ev.append(CertificationEvidence("Alexandria Merkle proof service", "services/alex_merkle/"))
    t = _test_count_in("tests/certification/test_T062_lineage.py")
    if t:
        ev.append(CertificationEvidence(f"Lineage tests: {t}", "tests/certification/test_T062_lineage.py"))
        receipts.append("tests/certification/test_T062_lineage.py")
    if not ev:
        gaps.append("No lineage artifacts found")

    score = min(10.0, len(ev) * 2.5 + (2.5 if len(proofs) > 10 else 0))
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory("lineage", "Lineage", min(10.0, score), ev, gaps, receipts, status)


def _transparency() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    if _exists("tla", "NSInvariants.tla"):
        ev.append(CertificationEvidence("TLA+ invariant spec", "tla/NSInvariants.tla"))
    if _exists("docs"):
        count = _glob_count("docs/**/*.md")
        ev.append(CertificationEvidence(f"Documentation: {count} markdown files", "docs/"))
    t = _test_count_in("tests/certification/test_T063_transparency.py")
    if t:
        ev.append(CertificationEvidence(f"Transparency tests: {t}", "tests/certification/test_T063_transparency.py"))
        receipts.append("tests/certification/test_T063_transparency.py")
    if _exists("ARCHITECTURE_TRUTH.md"):
        ev.append(CertificationEvidence("Architecture truth document", "ARCHITECTURE_TRUTH.md"))
    if not ev:
        gaps.append("No transparency evidence found")

    score = min(10.0, len(ev) * 2.5)
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory("transparency", "Transparency", score, ev, gaps, receipts, status)


def _safety() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    if _exists("dignity_kernel"):
        ev.append(CertificationEvidence("Dignity Kernel present", "dignity_kernel/"))
    if _exists("canon", "axioms"):
        ev.append(CertificationEvidence("Canon axioms", "canon/axioms/"))
    t = _test_count_in("tests/certification/test_T064_safety.py")
    if t:
        ev.append(CertificationEvidence(f"Safety tests: {t}", "tests/certification/test_T064_safety.py"))
        receipts.append("tests/certification/test_T064_safety.py")
    if _glob_count("services/ns_core/test_adversarial.py"):
        ev.append(CertificationEvidence("Adversarial test suite", "services/ns_core/test_adversarial.py"))
        receipts.append("services/ns_core/test_adversarial.py")
    if not ev:
        gaps.append("No safety evidence found")

    score = min(10.0, len(ev) * 2.5)
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory("safety", "Safety", score, ev, gaps, receipts, status)


def _bias() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    t = _test_count_in("tests/certification/test_T065_bias.py")
    if t:
        ev.append(CertificationEvidence(f"Bias tests: {t}", "tests/certification/test_T065_bias.py"))
        receipts.append("tests/certification/test_T065_bias.py")
    cal = _test_count_in("tests/test_calibration.py")
    if cal:
        ev.append(CertificationEvidence(f"Calibration tests: {cal}", "tests/test_calibration.py"))
        receipts.append("tests/test_calibration.py")
    hormetic = _glob_count("tests/test_hormetic*.py")
    if hormetic:
        ev.append(CertificationEvidence("Hormetic robustness tests present"))
    if not ev:
        gaps.append("Bias/fairness tests not found — add calibration and bias validation suite")

    score = min(10.0, len(ev) * 3.3)
    status: Status = "complete" if score >= 6.6 else ("partial" if score > 0 else "absent")
    return CertificationCategory("bias", "Bias / Fairness", score, ev, gaps, receipts, status)


def _security() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    if _exists(".gitleaks.toml"):
        ev.append(CertificationEvidence("Gitleaks config present", ".gitleaks.toml"))
    if _exists(".gitleaksignore"):
        ev.append(CertificationEvidence("Gitleaks ignore list present", ".gitleaksignore"))
    t = _test_count_in("tests/certification/test_T066_security.py")
    if t:
        ev.append(CertificationEvidence(f"Security tests: {t}", "tests/certification/test_T066_security.py"))
        receipts.append("tests/certification/test_T066_security.py")
    if _exists("proofs", "yubikey_binding_proof.json"):
        ev.append(CertificationEvidence("YubiKey binding proof", "proofs/yubikey_binding_proof.json"))
        receipts.append("proofs/yubikey_binding_proof.json")
    if not ev:
        gaps.append("No security evidence found")

    score = min(10.0, len(ev) * 2.5)
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory("security", "Security", score, ev, gaps, receipts, status)


def _runtime() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    if _exists("boot.sh"):
        ev.append(CertificationEvidence("Boot script present", "boot.sh"))
    if _exists("proofs", "ns_boot_proof.json"):
        ev.append(CertificationEvidence("Boot proof artifact", "proofs/ns_boot_proof.json"))
        receipts.append("proofs/ns_boot_proof.json")
    t = _test_count_in("tests/certification/test_T067_runtime.py")
    if t:
        ev.append(CertificationEvidence(f"Runtime tests: {t}", "tests/certification/test_T067_runtime.py"))
        receipts.append("tests/certification/test_T067_runtime.py")
    if _exists("services", "continuum"):
        ev.append(CertificationEvidence("Continuum append-only event store", "services/continuum/"))
    if not ev:
        gaps.append("No runtime evidence found")

    score = min(10.0, len(ev) * 2.5)
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory("runtime", "Runtime / Drift", score, ev, gaps, receipts, status)


def _auditability() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    if _exists("services", "continuum"):
        ev.append(CertificationEvidence("Continuum append-only audit log", "services/continuum/"))
    if _exists("proofs", "replay_contract_proof.json"):
        ev.append(CertificationEvidence("Replay contract proof", "proofs/replay_contract_proof.json"))
        receipts.append("proofs/replay_contract_proof.json")
    t = _test_count_in("tests/certification/test_T068_auditability.py")
    if t:
        ev.append(CertificationEvidence(f"Auditability tests: {t}", "tests/certification/test_T068_auditability.py"))
        receipts.append("tests/certification/test_T068_auditability.py")
    if _exists("tests", "meta", "test_ns_test_ontology.py"):
        ev.append(CertificationEvidence("Test ontology meta-tests", "tests/meta/test_ns_test_ontology.py"))
        receipts.append("tests/meta/test_ns_test_ontology.py")
    if not ev:
        gaps.append("No auditability evidence found")

    score = min(10.0, len(ev) * 2.5)
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory("auditability", "Auditability", score, ev, gaps, receipts, status)


def _continuous_improvement() -> CertificationCategory:
    ev: list[CertificationEvidence] = []
    gaps: list[str] = []
    receipts: list[str] = []

    phase_count = _glob_count("tests/test_phase_*.py")
    if phase_count:
        ev.append(CertificationEvidence(f"{phase_count} phase system tests", "tests/test_phase_*.py"))
        receipts.append("tests/test_phase_*.py")
    if _exists("tests", "test_master_v32.py"):
        ev.append(CertificationEvidence("Master v3.2 score test", "tests/test_master_v32.py"))
        receipts.append("tests/test_master_v32.py")
    t = _test_count_in("tests/certification/test_T069_continuous.py")
    if t:
        ev.append(CertificationEvidence(f"CI tests: {t}", "tests/certification/test_T069_continuous.py"))
        receipts.append("tests/certification/test_T069_continuous.py")
    if _exists("CHANGELOG.md"):
        ev.append(CertificationEvidence("Changelog present", "CHANGELOG.md"))
    if not ev:
        gaps.append("No continuous improvement evidence found")

    score = min(10.0, len(ev) * 2.5)
    status: Status = "complete" if score >= 7.5 else ("partial" if score > 0 else "absent")
    return CertificationCategory(
        "continuous_improvement", "Continuous Improvement", score, ev, gaps, receipts, status
    )


# ---------------------------------------------------------------------------
# Band computation
# ---------------------------------------------------------------------------

REQUIRED_CATEGORIES = {
    "governance", "risk", "lineage", "transparency", "safety",
    "bias", "security", "runtime", "auditability", "continuous_improvement",
}


def _band(score: float) -> Band:
    if score < 70:
        return "not_certifiable"
    if score < 85:
        return "provisional"
    if score < 92:
        return "audit_ready_internal"
    if score < 97:
        return "external_certification_ready"
    return "theoretical_max"


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_i7_certification_report(
    run_id: str,
    generated_at_utc: str,
    ontology_link: str | None = None,
) -> CertificationReport:
    from datetime import timezone, datetime

    categories = [
        _governance(),
        _risk(),
        _lineage(),
        _transparency(),
        _safety(),
        _bias(),
        _security(),
        _runtime(),
        _auditability(),
        _continuous_improvement(),
    ]

    # Validate all required categories present
    found_ids = {c.id for c in categories}
    missing = REQUIRED_CATEGORIES - found_ids
    if missing:
        raise ValueError(f"Missing required categories: {missing}")

    total = sum(c.score_0_to_10 for c in categories)
    complete = sum(1 for c in categories if c.status == "complete")
    partial = sum(1 for c in categories if c.status == "partial")
    absent = sum(1 for c in categories if c.status == "absent")

    blocking_gaps: list[str] = []
    for c in categories:
        blocking_gaps.extend(f"[{c.id}] {g}" for g in c.gaps)

    # Absent categories cap the total — treat absent as 0
    if absent > 0 and total >= 100:
        total = min(total, 99.9)

    claim_to_artifact: dict[str, str] = {}
    for c in categories:
        for ev in c.evidence_items:
            if ev.artifact_path:
                claim_to_artifact[f"{c.id}.{ev.description[:40]}"] = ev.artifact_path

    return CertificationReport(
        schema="axiolev.ns.i7_certification_power/v1",
        run_id=run_id,
        generated_at_utc=generated_at_utc,
        categories=categories,
        total_score_0_to_100=round(total, 2),
        complete_categories=complete,
        partial_categories=partial,
        absent_categories=absent,
        blocking_gaps=blocking_gaps,
        certification_band=_band(total),
        ontology_link=ontology_link,
        claim_to_artifact_mapping=claim_to_artifact,
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _serialize(obj):
    if isinstance(obj, (CertificationReport, CertificationCategory, CertificationEvidence)):
        return asdict(obj)
    raise TypeError(f"Not serializable: {type(obj)}")


def export_i7_certification_report(report: CertificationReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    path = out_dir / "I7_CERTIFICATION_REPORT.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from datetime import datetime, timezone

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".run/i7_cert")
    run_id = out.name
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = build_i7_certification_report(run_id, ts)
    path = export_i7_certification_report(report, out)
    print(f"score={report.total_score_0_to_100}")
    print(f"band={report.certification_band}")
    print(f"complete={report.complete_categories}")
    print(f"partial={report.partial_categories}")
    print(f"absent={report.absent_categories}")
    print(f"blocking_gaps={len(report.blocking_gaps)}")
    print(f"report={path}")
