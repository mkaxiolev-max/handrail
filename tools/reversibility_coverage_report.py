"""Reversibility coverage report generator.

Emits artifacts/reversibility_coverage.json with the shape:
    {
        "total_ops":                <int>,
        "reversible":               <int>,
        "irreversible_with_proof":  <int>,
        "irreversible_without_proof": 0      # must always be 0
    }

Exit code: 0 on success, 1 if the coverage gate fails (any op missing a proof).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from services.ns_core.reversibility.registry import coverage_gate, REGISTRY, NON_REVERSIBLE
from services.ns_core.reversibility.kenosis import all_proofs


def build_report() -> dict:
    """Run the coverage gate and build the full coverage report."""
    gate = coverage_gate()   # raises RuntimeError if any proof is missing

    proofs = all_proofs()
    proof_index = {p.op_id: p for p in proofs}

    # Per-op detail (useful for CI artefact inspection).
    ops = []
    for op_id, spec in sorted(REGISTRY.items()):
        entry: dict = {
            "op_id":   op_id,
            "domain":  spec.domain,
            "kind":    spec.kind.value,
            "from":    spec.from_state,
            "to":      spec.to_state,
        }
        if proof := proof_index.get(op_id):
            entry["kenosis_proof"] = {
                "pre_state_hash":   proof.pre_state_hash,
                "post_state_hash":  proof.post_state_hash,
                "receipt_ref":      proof.receipt_ref,
                "bounded_budget":   proof.bounded_budget,
                "compensating_action": proof.compensating_action,
            }
        ops.append(entry)

    return {
        **gate,
        "ops": ops,
    }


def main() -> int:
    artifacts_dir = _ROOT / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    out_path = artifacts_dir / "reversibility_coverage.json"

    try:
        report = build_report()
    except RuntimeError as exc:
        print(f"[COVERAGE GATE FAIL] {exc}", file=sys.stderr)
        # Write a partial report so CI has evidence.
        partial = {
            "total_ops": len(REGISTRY),
            "reversible": 0,
            "irreversible_with_proof": 0,
            "irreversible_without_proof": len(NON_REVERSIBLE),
            "error": str(exc),
        }
        out_path.write_text(json.dumps(partial, indent=2))
        return 1

    out_path.write_text(json.dumps(report, indent=2))

    summary = (
        f"total={report['total_ops']}  "
        f"reversible={report['reversible']}  "
        f"irreversible_with_proof={report['irreversible_with_proof']}  "
        f"irreversible_without_proof={report['irreversible_without_proof']}"
    )
    print(f"[OK] Reversibility coverage: {summary}")
    print(f"[OK] Artifact written to: {out_path.relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
