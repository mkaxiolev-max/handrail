"""Explainability Engine — reconstruct WHY a decision happened."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Ledger paths ──────────────────────────────────────────────────────────────
def _alexandria_root() -> Path:
    ssd = Path("/Volumes/NSExternal/ALEXANDRIA")
    if ssd.exists():
        return ssd
    return Path.home() / "ALEXANDRIA"

def _ledger(name: str) -> Path:
    return _alexandria_root() / "ledger" / name

def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ── Engine ────────────────────────────────────────────────────────────────────
class ExplainabilityEngine:
    """Reconstruct decision traces from Alexandria ledger sources."""

    def _receipts(self) -> list[dict]:
        return _read_jsonl(_ledger("ns_receipt_chain.jsonl"))

    def _model_decisions(self) -> list[dict]:
        return _read_jsonl(_ledger("model_decisions.jsonl"))

    def _failure_events(self) -> list[dict]:
        return _read_jsonl(_ledger("failure_events.jsonl"))

    def _kernel_decisions(self) -> list[dict]:
        return _read_jsonl(_ledger("kernel_decisions.jsonl"))

    def explain_run(self, run_id: str) -> dict:
        receipts = [r for r in self._receipts()
                    if r.get("run_id") == run_id or r.get("id") == run_id]
        model_hits = [m for m in self._model_decisions()
                      if m.get("run_id") == run_id]
        failures = [f for f in self._failure_events()
                    if f.get("run_id") == run_id]
        kernel_hits = [k for k in self._kernel_decisions()
                       if k.get("run_id") == run_id]

        # Build trace steps
        trace = []

        # Step 1: Intent
        intent_data = {}
        if receipts:
            r = receipts[0]
            intent_data = {
                "op": r.get("op") or r.get("operation"),
                "args": r.get("args", {}),
                "risk_tier": r.get("risk_tier"),
                "ts": r.get("ts") or r.get("created_at"),
            }
        trace.append({"step": "intent", "data": intent_data})

        # Step 2: Model council
        models_used = []
        intent_class = None
        if model_hits:
            m = model_hits[0]
            models_used = m.get("models_used", [m.get("model", "unknown")])
            intent_class = m.get("intent_class") or m.get("intent")
        trace.append({"step": "model_council", "models_used": models_used,
                      "intent_class": intent_class})

        # Step 3: Kernel
        kernel_allowed = None
        kernel_reason = None
        if kernel_hits:
            k = kernel_hits[0]
            kernel_allowed = k.get("allowed") or k.get("verified")
            kernel_reason = k.get("reason") or k.get("decision")
        trace.append({"step": "kernel", "allowed": kernel_allowed,
                      "reason": kernel_reason})

        # Step 4: Execution
        ops_executed = []
        exec_ok = True
        if receipts:
            ops_executed = [r.get("op") or r.get("operation") for r in receipts]
        if failures:
            exec_ok = False
        trace.append({"step": "execution", "ops": ops_executed, "ok": exec_ok})

        # Step 5: Outcome
        failure_class = failures[0].get("failure_class") if failures else None
        semantic_impact = None
        if receipts:
            semantic_impact = receipts[-1].get("semantic_impact")
        trace.append({"step": "outcome", "failure_class": failure_class,
                      "semantic_impact": semantic_impact})

        # Plain English summary
        if failures:
            summary = (f"Run {run_id[:8]} failed during execution "
                       f"({failure_class or 'unknown error'}).")
        elif kernel_allowed is False:
            summary = (f"Run {run_id[:8]} was blocked by the Dignity Kernel "
                       f"({kernel_reason or 'policy denial'}).")
        else:
            op_str = ops_executed[0] if ops_executed else "unknown op"
            summary = (f"Run {run_id[:8]} executed {op_str} successfully "
                       f"via {intent_class or 'default'} routing.")

        return {
            "run_id": run_id,
            "found": bool(receipts or model_hits or failures or kernel_hits),
            "trace": trace,
            "summary": summary,
            "sources": {
                "receipts": len(receipts),
                "model_decisions": len(model_hits),
                "failure_events": len(failures),
                "kernel_decisions": len(kernel_hits),
            },
            "ts": _now(),
        }

    def explain_decision(self, decision_id: str) -> dict:
        kernel_decisions = self._kernel_decisions()
        match = next(
            (k for k in kernel_decisions
             if k.get("receipt_id") == decision_id or k.get("id") == decision_id),
            None
        )
        if match is None:
            return {"decision_id": decision_id, "found": False, "ts": _now()}
        return {
            "decision_id": decision_id,
            "found": True,
            "policy_referenced": match.get("policy") or match.get("never_event"),
            "decision": match.get("allowed") or match.get("verified"),
            "reason": match.get("reason") or match.get("decision"),
            "actor": match.get("actor") or match.get("proposer"),
            "risk_tier": match.get("risk_tier"),
            "ts": match.get("ts") or _now(),
            "raw": match,
        }

    def recent_decisions(self, n: int = 10) -> list[dict]:
        kernel = self._kernel_decisions()
        model = self._model_decisions()
        receipts = self._receipts()

        decisions = []
        # Combine all ledger entries into unified timeline
        for k in kernel[-n:]:
            decisions.append({
                "source": "kernel",
                "id": k.get("receipt_id") or k.get("id"),
                "action": k.get("decision") or ("allowed" if k.get("allowed") else "blocked"),
                "ts": k.get("ts", ""),
            })
        for m in model[-n:]:
            decisions.append({
                "source": "model_council",
                "id": m.get("id"),
                "action": m.get("intent_class") or m.get("intent"),
                "ts": m.get("ts", ""),
            })
        for r in receipts[-n:]:
            decisions.append({
                "source": "receipt",
                "id": r.get("id"),
                "action": r.get("op") or r.get("operation"),
                "ts": r.get("ts") or r.get("created_at", ""),
            })

        decisions.sort(key=lambda d: d.get("ts", ""), reverse=True)
        return decisions[:n]


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine: Optional[ExplainabilityEngine] = None

def get_engine() -> ExplainabilityEngine:
    global _engine
    if _engine is None:
        _engine = ExplainabilityEngine()
    return _engine
