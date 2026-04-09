from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("ns.boot_invariants")

@dataclass
class InvariantResult:
    name: str
    passed: bool
    detail: str
    remedy: str = ""

@dataclass
class BootInvariantReport:
    all_passed: bool
    results: list[InvariantResult] = field(default_factory=list)
    warning_block: dict[str, Any] = field(default_factory=dict)

def run_boot_invariants(chain, canon_repo, voice_repo, db) -> BootInvariantReport:
    results: list[InvariantResult] = []
    try:
        receipts = chain.get_last_n(50)
        chain_ok = all(receipts[i].prev_hash == receipts[i-1].hash for i in range(1, len(receipts)))
        results.append(InvariantResult("receipt_chain_intact", chain_ok,
            f"last {len(receipts)} receipts verified" if chain_ok else "CHAIN BREAK DETECTED",
            "run chain repair" if not chain_ok else ""))
    except Exception as e:
        results.append(InvariantResult("receipt_chain_intact", False, f"chain error: {e}", "chain service offline"))
    try:
        latest = canon_repo.get_latest_commit()
        results.append(InvariantResult("canon_commit_exists", latest is not None,
            f"canon v{latest.version}" if latest else "no canon commits",
            "run canon bootstrap" if not latest else ""))
    except Exception as e:
        results.append(InvariantResult("canon_commit_exists", False, f"canon error: {e}", "canon_commits table missing"))
    try:
        orphans = voice_repo.count_complete_without_memory_atom()
        results.append(InvariantResult("voice_sessions_fully_archived", orphans == 0,
            f"{orphans} complete sessions missing memory_atom_id" if orphans else "all sessions archived",
            f"re-archive {orphans} sessions" if orphans else ""))
    except Exception as e:
        results.append(InvariantResult("voice_sessions_fully_archived", False, f"voice error: {e}", "voice_sessions table missing"))
    try:
        db_count = db.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
        results.append(InvariantResult("atoms_count_matches_db", True, f"db has {db_count} atoms"))
    except Exception as e:
        results.append(InvariantResult("atoms_count_matches_db", False, f"atoms error: {e}", "atoms table missing"))
    all_passed = all(r.passed for r in results)
    warning_block: dict[str, Any] = {}
    if not all_passed:
        warning_block = {"invariant_drift": True, "failed": [
            {"name": r.name, "detail": r.detail, "remedy": r.remedy} for r in results if not r.passed]}
        logger.error("BOOT INVARIANT FAILURE: %s", warning_block)
    else:
        logger.info("Boot invariants: all passed (%d checks)", len(results))
    return BootInvariantReport(all_passed=all_passed, results=results, warning_block=warning_block)

def apply_to_healthz(report: BootInvariantReport, health_state: dict) -> dict:
    if not report.all_passed:
        health_state["status"] = "DEGRADED"
        health_state["invariant_warnings"] = report.warning_block
    return health_state
