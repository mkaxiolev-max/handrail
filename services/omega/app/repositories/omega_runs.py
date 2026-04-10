"""Omega run persistence repository."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from app.models.run_record import OmegaRunRecord

SERVICES_ROOT = Path(__file__).resolve().parents[3]
if str(SERVICES_ROOT) not in sys.path:
    sys.path.append(str(SERVICES_ROOT))

from shared.models.enums import ReceiptType, RiskTier
from shared.receipts.chain import ReceiptChain
from shared.receipts.generator import ReceiptGenerator, RECEIPTS_PATH


class OmegaReceiptBridge:
    """Thin wrapper around the shared receipt rail that restores prev_hash continuity."""

    def __init__(self, receipts_path: Path | None = None):
        self.receipts_path = receipts_path or RECEIPTS_PATH

    def _last_hash(self) -> str | None:
        ledger = self.receipts_path / "receipt_chain.jsonl"
        if not ledger.exists():
            return None
        lines = [line for line in ledger.read_text().splitlines() if line.strip()]
        if not lines:
            return None
        try:
            return json.loads(lines[-1]).get("ledger_hash")
        except Exception:
            return None

    def issue_run_receipt(
        self,
        *,
        run_id: str,
        actor: str,
        input_payload: dict[str, Any],
        result_payload: dict[str, Any],
    ) -> dict[str, Any]:
        generator = ReceiptGenerator(self.receipts_path)
        generator._prev_hash = self._last_hash()
        receipt = generator.issue_receipt(
            receipt_type=ReceiptType.MODEL,
            payload={
                "run_id": run_id,
                "provisional": True,
                "result_kind": "simulation",
                "input_payload": input_payload,
                "result_payload": result_payload,
            },
            op="omega.simulation.run",
            actor=actor,
            risk_tier=RiskTier.R1,
        )
        chain_status = ReceiptChain(self.receipts_path).verify()
        return {
            "receipt_id": receipt.receipt_id,
            "receipt_hash": receipt.ledger_hash or "",
            "chain_verified": bool(
                chain_status.integrity_ok and chain_status.latest_hash == receipt.ledger_hash
            ),
        }


class OmegaRunsRepository:
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or os.environ.get(
            "DATABASE_URL",
            "postgresql://ns:ns_secure_pwd@localhost:5433/ns",
        )

    def _conn(self):
        import psycopg2

        return psycopg2.connect(self.db_url)

    def create_run(
        self,
        run_record: OmegaRunRecord,
        *,
        input_payload: dict[str, Any],
        summary_payload: dict[str, Any],
        canon_version: int | None,
    ) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO omega_runs (
                        run_id, created_at, actor, domain_type, input_payload, summary_payload,
                        branch_count, horizon, status, receipt_hash, chain_verified, provisional,
                        canon_version, metadata
                    ) VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        run_record.run_id,
                        run_record.created_at,
                        run_record.actor,
                        run_record.domain_type,
                        json.dumps(input_payload),
                        json.dumps(summary_payload),
                        run_record.branch_count,
                        run_record.horizon,
                        run_record.status,
                        run_record.receipt_hash,
                        run_record.chain_verified,
                        run_record.provisional,
                        canon_version,
                        json.dumps(run_record.metadata),
                    ),
                )
            conn.commit()

    def create_branches(self, run_id: str, branches: list[dict[str, Any]]) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                for branch in branches:
                    cur.execute(
                        """
                        INSERT INTO omega_branches (
                            branch_id, run_id, branch_index, assumptions, transitions, outputs,
                            likelihood, confidence_payload, breach_points, divergence_components, realized_status
                        ) VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                        """,
                        (
                            branch["branch_id"],
                            run_id,
                            branch["branch_index"],
                            json.dumps(branch["assumptions"]),
                            json.dumps(branch["transitions"]),
                            json.dumps(branch["outputs"]),
                            branch["likelihood"],
                            json.dumps(branch["confidence"]),
                            json.dumps(branch["breach_points"]),
                            json.dumps(branch["divergence_components"]),
                            "simulated",
                        ),
                    )
            conn.commit()

    def write_summary_atom(self, run_record: OmegaRunRecord, summary_payload: dict[str, Any]) -> list[str]:
        content = json.dumps(
            {
                "kind": "omega_simulation_summary",
                "run_id": run_record.run_id,
                "receipt_hash": run_record.receipt_hash,
                "simulation_class": run_record.simulation_class,
                "provisional": True,
                "summary": summary_payload,
            },
            sort_keys=True,
        )
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO atoms (type, content, source_id) VALUES (%s, %s, %s) RETURNING id",
                        ("omega_simulation", content, None),
                    )
                    row = cur.fetchone()
                conn.commit()
            return [str(row[0])] if row else []
        except Exception:
            return []

    def list_runs(self, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT run_id, created_at, actor, domain_type, branch_count, horizon, status,
                           receipt_hash, chain_verified, provisional, canon_version, metadata
                    FROM omega_runs ORDER BY created_at DESC LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [
            {
                "run_id": row[0],
                "created_at": row[1].isoformat() if row[1] else None,
                "actor": row[2],
                "domain_type": row[3],
                "branch_count": row[4],
                "horizon": row[5],
                "status": row[6],
                "receipt_hash": row[7],
                "chain_verified": row[8],
                "provisional": row[9],
                "canon_version": row[10],
                "metadata": row[11] or {},
            }
            for row in rows
        ]

    def get_run(self, run_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT run_id, created_at, actor, domain_type, input_payload, summary_payload,
                           branch_count, horizon, status, receipt_hash, chain_verified,
                           provisional, canon_version, metadata
                    FROM omega_runs WHERE run_id = %s
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
        if not row:
            return None
        return {
            "run_id": row[0],
            "created_at": row[1].isoformat() if row[1] else None,
            "actor": row[2],
            "domain_type": row[3],
            "input_payload": row[4] or {},
            "summary_payload": row[5] or {},
            "branch_count": row[6],
            "horizon": row[7],
            "status": row[8],
            "receipt_hash": row[9],
            "chain_verified": row[10],
            "provisional": row[11],
            "canon_version": row[12],
            "metadata": row[13] or {},
        }

    def get_branches(self, run_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT branch_id, run_id, branch_index, assumptions, transitions, outputs,
                           likelihood, confidence_payload, breach_points, divergence_components, realized_status
                    FROM omega_branches WHERE run_id = %s ORDER BY branch_index ASC
                    """,
                    (run_id,),
                )
                rows = cur.fetchall()
        return [
            {
                "branch_id": row[0],
                "run_id": row[1],
                "branch_index": row[2],
                "assumptions": row[3] or [],
                "transitions": row[4] or [],
                "outputs": row[5] or {},
                "likelihood": row[6],
                "confidence": row[7] or {},
                "breach_points": row[8] or [],
                "divergence_components": row[9] or {},
                "realized_status": row[10],
                "provisional": True,
            }
            for row in rows
        ]

    def compare_run_to_observed(self, run_id: str, observed_outcome: dict[str, Any]) -> dict[str, Any] | None:
        run = self.get_run(run_id)
        if not run:
            return None
        branches = self.get_branches(run_id)
        observed_state = observed_outcome.get("observed_state", {})
        if not branches:
            return {
                "run_id": run_id,
                "status": "no_branches",
                "result_kind": "simulation_comparison",
                "provisional": True,
                "warnings": ["No simulated branches are stored for this run."],
                "comparisons": [],
            }

        comparisons: list[dict[str, Any]] = []
        for branch in branches:
            predicted = branch.get("outputs", {}).get("final_state", {})
            variable_names = sorted(set(predicted.keys()) | set(observed_state.keys()))
            deltas = {
                name: round(abs(float(predicted.get(name, 0.0)) - float(observed_state.get(name, 0.0))), 4)
                for name in variable_names
            }
            total_delta = round(sum(deltas.values()), 4)
            comparisons.append(
                {
                    "branch_id": branch["branch_id"],
                    "branch_index": branch["branch_index"],
                    "likelihood": branch.get("likelihood", 0.0),
                    "total_delta": total_delta,
                    "variable_deltas": deltas,
                    "fit_score": round(max(0.0, 1.0 / (1.0 + total_delta)), 4),
                }
            )

        comparisons.sort(key=lambda item: item["total_delta"])
        best_match = comparisons[0]
        reality_gap = round(best_match["total_delta"], 4)
        warnings = []
        if reality_gap > 1.5:
            warnings.append("Observed outcome diverges materially from all stored branches.")
        if reality_gap > 0.5:
            warnings.append("Comparison should be treated as directional rather than close fit.")

        return {
            "run_id": run_id,
            "status": "compared",
            "result_kind": "simulation_comparison",
            "provisional": True,
            "best_match_branch": best_match["branch_id"],
            "reality_gap": reality_gap,
            "comparisons": comparisons,
            "warnings": warnings,
            "observed_outcome": observed_outcome,
            "summary_reference": run.get("summary_payload", {}),
        }
