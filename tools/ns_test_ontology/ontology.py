from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]


INSTRUMENTS = {
    "I1": {
        "name": "Canon Integrity / Sentinel Gate",
        "current": 88.02,
        "near": 93.0,
        "theory": 96.0,
        "w31": 0.135,
        "w32": 0.1215,
        "target": "constitutional invariants, canon promotion, doctrine determinism",
    },
    "I2": {
        "name": "Reasoning / Calibration / Abstention",
        "current": 88.36,
        "near": 96.0,
        "theory": 98.0,
        "w31": 0.185,
        "w32": 0.162,
        "target": "calibration, NVIR, abstention, adversarial and hormetic robustness",
    },
    "I3": {
        "name": "External Verifiability / Third-Party Admin",
        "current": 88.84,
        "near": 92.0,
        "theory": 95.0,
        "w31": 0.175,
        "w32": 0.162,
        "target": "validators, external verification, audit bundles, brokerage, evidence exports",
    },
    "I4": {
        "name": "Governed Proof-carrying Execution",
        "current": 95.28,
        "near": 97.0,
        "theory": 99.0,
        "w31": 0.255,
        "w32": 0.243,
        "target": "execution grounding, Handrail, RIL, Oracle, runtime, receipts",
    },
    "I5": {
        "name": "Append-only / SAQ / Attestation",
        "current": 89.00,
        "near": 96.0,
        "theory": 98.0,
        "w31": 0.145,
        "w32": 0.1215,
        "target": "append-only state, replay, reversibility, witness, Merkle, PIIC",
    },
    "I6": {
        "name": "Ω-Logos / Perception / Inquiry / Execution / Memory / Autonomy",
        "current": 88.00,
        "near": 95.0,
        "theory": 99.0,
        "w31": 0.105,
        "w32": 0.090,
        "target": "CQHML, phase systems, projection, omega primitives, semantic manifold",
    },
    "I7": {
        "name": "Certification Power Score",
        "current": 84.00,
        "near": 92.0,
        "theory": 100.0,
        "w31": 0.0,
        "w32": 0.10,
        "target": "certification, risk, transparency, bias, security, runtime, auditability",
    },
    "I8": {
        "name": "Omega-Prime / Aletheia-Ω / Self-Modification / Continuous Improvement",
        "current": 0.0,
        "near": 97.0,
        "theory": 100.0,
        "w31": 0.0,
        "w32": 0.0,
        "w33": 0.10,
        "target": "self-modification sandbox, proof-carrying execution, efficiency, aletheia loop, v3.3",
    },
}


# Order matters — more specific rules first.
RULES = [
    # Newly mapped families (previously UNMAPPED)
    ("I3", "Validator Systems", ["tests/validators/", "test_validators.py"]),
    ("I7", "Certification T060-T079", [
        "tests/certification/",
        "test_T060", "test_T061", "test_T062", "test_T063", "test_T064",
        "test_T065", "test_T066", "test_T067", "test_T068", "test_T069",
        "test_T070", "test_T071", "test_T072", "test_T073", "test_T074",
        "test_T075", "test_T076", "test_T077", "test_T078", "test_T079",
    ]),
    ("I7", "Master Score v3.2", ["test_master_v32", "master_v32"]),
    ("I7", "Assurance / T-series", ["test_assurance_"]),
    ("I6", "Phase System", ["test_phase_"]),
    ("I7", "Certification / Auditability", [
        "certification", "auditability", "external_transparency",
        "bias", "fairness", "risk_file", "claim_to_artifact",
    ]),
    ("I3", "External Verifiability", [
        "external_verifiability", "third_party", "verifier_bundle", "evidence_pack",
    ]),
    ("I7", "Meta Ontology / Score Traceability", ["tests/meta/", "test_ns_test_ontology"]),

    # Omega-Prime cycle rules (C01-C24)
    ("I8", "Self-Modification Sandbox",     ["test_self_mod_sandbox"]),
    ("I7", "Proof-Carrying Execution",      ["test_pce"]),
    ("I4", "Reversibility Registry",        ["test_reversibility_registry"]),
    ("I1", "TLA Apalache Bridge",           ["test_apalache_bridge"]),
    ("I8", "Global Efficiency Ledger",      ["test_efficiency_ledger"]),
    ("I8", "Universal Module Contract",     ["test_universal_contract"]),
    ("I8", "Continuity Daemon",             ["test_continuity_daemon"]),
    ("I8", "Autonomous Goal Formation",     ["test_goal_formation"]),
    ("I8", "Action-Outcome Loop",           ["test_action_outcome_loop"]),
    ("I8", "Shadow Score Discipline",       ["test_shadow_scorer"]),
    ("I8", "Canonical Receipts",            ["test_canonical_receipts"]),
    ("I7", "Validator Adapters",            ["test_validator_adapters"]),
    ("I7", "MITRE ATLAS Coverage",          ["test_atlas_coverage"]),
    ("I7", "Drift Monitor",                 ["test_drift_monitor"]),
    ("I7", "CPS Risk Tiering",              ["test_cps_risk_tiering"]),
    ("I7", "Math Calc Machine",             ["test_math_calc"]),
    ("I6", "PRISM-Omega Routing",           ["test_prism_omega"]),
    ("I8", "ARMS Scoring",                  ["test_arms_scoring"]),
    ("I8", "Mutation Gate",                 ["test_mutation_gate"]),
    ("I8", "Noetic Layer",                  ["test_noetic_mass", "test_noetic_fascia", "test_intent_kernel", "test_noetic"]),
    ("I6", "Reality Ingest",                ["test_reality_ingest"]),
    ("I8", "Architecture Validator",        ["test_architecture_validator"]),
    ("I8", "Aletheia Omega",                ["test_aletheia_omega"]),
    ("I8", "Score Reconciler V33",          ["test_score_reconciler_v33"]),

    # Existing canonical buckets
    ("I1", "Ring 1 constitutional", ["test_ring1_constitutional"]),
    ("I4", "Ring 2 substrate", ["test_ring2_substrate"]),
    ("I4", "Ring 3 Loom", ["test_ring3_loom"]),
    ("I1", "Ring 4 canon promotion", ["test_ring4_canon"]),
    ("I3", "Ring 5 external gates", ["test_ring5_external"]),
    ("I4", "Ring 6 G2 invariant", ["test_ring6_g2"]),
    ("I4", "Ring 7 final certification", ["test_ring7_final"]),
    ("I5", "NCOM", ["test_ncom.py"]),
    ("I5", "PIIC", ["test_piic.py"]),
    ("I4", "RIL engines", ["test_ril_engines"]),
    ("I4", "Oracle v2", ["test_oracle_v2"]),
    ("I6", "CQHML manifold", ["test_cqhml_"]),
    ("I6", "Super-Omega eval", ["tests/super_omega/"]),
    ("I2", "NVIR", ["test_nvir"]),
    ("I5", "Witness / attestation", ["witness"]),
    ("I6", "Omega projection", ["test_omega_projection"]),
    ("I5", "Governor", ["test_governor"]),
    ("I2", "Clearing / abstention", ["tests/clearing/"]),
    ("I1", "Promotion Index / PI", ["tests/pi/"]),
    ("I4", "ABI bridge", ["tests/abi/"]),
    ("I2", "Calibration", ["test_calibration"]),
    ("I2", "Adversarial", ["test_adversarial"]),
    ("I7", "UI routes / audit", ["test_ui_named_routes", "test_ui_audit", "tests/ui/"]),
    ("I2", "SAQ / selective prediction", ["test_saq", "test_selective"]),
    ("I5", "Autopoiesis", ["tests/autopoiesis/"]),
    ("I1", "Doctrine determinism", ["tests/doctrine/"]),
    ("I2", "Hormetic", ["test_hormetic"]),
    ("I4", "Omega app", ["services/omega/app/tests/"]),
    ("I3", "Brokerage", ["tests/brokerage/"]),
    ("I4", "Handrail", ["handrail"]),
    ("I6", "UG entity", ["test_ug_entity"]),
    ("I6", "Omega primitives", ["test_omega_primitives"]),
    ("I5", "Replay / reversibility", ["test_replay_soundness", "test_reversible", "test_robustness"]),
    ("I4", "Hamiltonian / conftuner / MCI / RCI", ["test_hamiltonian", "test_conftuner", "test_mci", "test_rci"]),
    ("I4", "Voice E2E", ["test_voice_e2e"]),
    ("I5", "Merkle / SLSA / TLA", ["test_merkle", "test_slsa", "test_tla", "test_invariants_coverage"]),
    ("I6", "Three realities / judge / Apollo / composite", [
        "test_three_realities", "test_judge_ensemble", "test_apollo", "test_final_composite",
    ]),
]


@dataclass(frozen=True)
class TestObject:
    nodeid: str
    file_path: str
    test_name: str
    instrument: str
    bucket: str


def classify_path(path: str) -> tuple[str, str]:
    normalized = path.replace("\\", "/")
    for instrument, bucket, needles in RULES:
        if any(needle in normalized for needle in needles):
            return instrument, bucket
    return "UNMAPPED", "Other / unclassified"


def discover_pytest_tests(root: Path = ROOT) -> list[str]:
    proc = subprocess.run(
        ["pytest", "--collect-only", "-q"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    tests = sorted({line.strip() for line in proc.stdout.splitlines() if "::" in line})
    return tests


def build_ontology(test_nodeids: Iterable[str]) -> dict:
    objects: list[TestObject] = []
    for nodeid in test_nodeids:
        file_path = nodeid.split("::", 1)[0]
        test_name = nodeid.split("::")[-1]
        instrument, bucket = classify_path(file_path)
        objects.append(TestObject(nodeid, file_path, test_name, instrument, bucket))

    bucket_totals: dict[str, int] = defaultdict(int)
    instrument_totals: dict[str, int] = defaultdict(int)
    files: dict[str, int] = defaultdict(int)
    unmapped = []

    for obj in objects:
        bucket_totals[obj.bucket] += 1
        instrument_totals[obj.instrument] += 1
        files[obj.file_path] += 1
        if obj.instrument == "UNMAPPED":
            unmapped.append(asdict(obj))

    return {
        "schema": "axiolev.ns.test_ontology/v1",
        "total": len(objects),
        "objects": [asdict(o) for o in objects],
        "bucket_totals": dict(sorted(bucket_totals.items(), key=lambda kv: (-kv[1], kv[0]))),
        "instrument_totals": dict(sorted(instrument_totals.items())),
        "file_totals": dict(sorted(files.items())),
        "unmapped": unmapped,
    }


def score_from_ontology(ontology: dict, vitest_total: int = 0, xctest_files: int = 0) -> dict:
    instrument_totals = ontology["instrument_totals"]
    unmapped_count = len(ontology["unmapped"])

    v31_raw = sum(v["current"] * v["w31"] for v in INSTRUMENTS.values())
    v32_raw = sum(v["current"] * v["w32"] for v in INSTRUMENTS.values())
    v31_near = sum(v["near"] * v["w31"] for v in INSTRUMENTS.values())
    v32_near = sum(v["near"] * v["w32"] for v in INSTRUMENTS.values())

    gaps = []
    if unmapped_count:
        gaps.append({
            "severity": "CRITICAL",
            "name": "Unmapped tests",
            "count": unmapped_count,
            "impact": "Breaks test-to-score traceability and certification auditability.",
            "close_by": "Add ontology rules or rename tests into canonical bucket paths.",
        })
    if instrument_totals.get("I7", 0) == 0:
        gaps.append({
            "severity": "CRITICAL",
            "name": "No I7 test backing",
            "impact": "Certification Power Score is not grounded.",
            "close_by": "Map certification tests and add I7 meta gates.",
        })
    if instrument_totals.get("I3", 0) < 50:
        gaps.append({
            "severity": "HIGH",
            "name": "Weak I3 external verifiability coverage",
            "count": instrument_totals.get("I3", 0),
            "target": 50,
            "impact": "Limits external certification ceiling.",
            "close_by": "Add validator, verifier bundle, evidence export, and third-party audit tests.",
        })
    if xctest_files == 0:
        gaps.append({
            "severity": "HIGH",
            "name": "No XCTest files detected",
            "impact": "Mac app runtime and UI are not verified by native tests.",
            "close_by": "Wire Swift/XCTest target or add documented Swift test manifest.",
        })

    improvements = [
        {
            "priority": 1,
            "name": "Zero unmapped tests",
            "reason": "Highest leverage: restores score traceability and makes I7 auditable.",
        },
        {
            "priority": 2,
            "name": "Ground I7 with certification meta-tests",
            "reason": "Turns Certification Power from static self-score into proof-backed score.",
        },
        {
            "priority": 3,
            "name": "Expand I3 external verification",
            "reason": "Raises external verifiability ceiling and supports third-party certification.",
        },
        {
            "priority": 4,
            "name": "Wire XCTest or Swift UI verification manifest",
            "reason": "Closes Mac sovereignty and runtime UI verification gap.",
        },
        {
            "priority": 5,
            "name": "Audit I6 density",
            "reason": "I6 is strong but may be overconcentrated; reduce redundant tests only after ontology is clean.",
        },
    ]

    return {
        "schema": "axiolev.ns.score_from_ontology/v1",
        "pytest_total": ontology["total"],
        "vitest_total": vitest_total,
        "xctest_files": xctest_files,
        "instrument_totals": instrument_totals,
        "bucket_totals": ontology["bucket_totals"],
        "score": {
            "v31_raw_from_static_scorecard": round(v31_raw, 2),
            "v31_authoritative_live": 92.42,
            "v31_near_term": round(v31_near, 2),
            "v32_projected": round(v32_raw, 2),
            "v32_near_term": round(v32_near, 2),
        },
        "gaps": gaps,
        "improvements": improvements,
    }


def write_reports(out: Path, ontology: dict, score: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "TEST_ONTOLOGY.json").write_text(json.dumps(ontology, indent=2, ensure_ascii=False))
    (out / "SCORE_FROM_ONTOLOGY.json").write_text(json.dumps(score, indent=2, ensure_ascii=False))

    md = []
    md.append("# NS∞ Test Ontology + Score Report\n")
    md.append("## Counts")
    md.append(f"- pytest total: {score['pytest_total']}")
    md.append(f"- vitest total: {score['vitest_total']}")
    md.append(f"- xctest files: {score['xctest_files']}")
    md.append(f"- unmapped: {len(ontology['unmapped'])}\n")

    md.append("## Score")
    for k, v in score["score"].items():
        md.append(f"- {k}: {v}")

    md.append("\n## Instrument Totals")
    for k, v in sorted(score["instrument_totals"].items()):
        md.append(f"- {k}: {v}")

    md.append("\n## Bucket Totals")
    for k, v in score["bucket_totals"].items():
        md.append(f"- {k}: {v}")

    md.append("\n## Gaps")
    if score["gaps"]:
        for g in score["gaps"]:
            md.append(f"- [{g['severity']}] {g['name']}: {g.get('impact', '')}")
    else:
        md.append("- None")

    md.append("\n## Priority Improvements")
    for item in score["improvements"]:
        md.append(f"- P{item['priority']} {item['name']}: {item['reason']}")

    md.append("\n## Unmapped sample")
    for obj in ontology["unmapped"][:50]:
        md.append(f"- {obj['file_path']}::{obj['test_name']}")

    (out / "TEST_ONTOLOGY_REPORT.md").write_text("\n".join(md) + "\n")
