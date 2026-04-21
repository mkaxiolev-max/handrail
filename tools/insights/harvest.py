"""Insight harvester — AXIOLEV © 2026"""
from __future__ import annotations
import json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]

def exists(p): return (ROOT / p).exists()
def grep_count(pattern, path):
    try:
        out = subprocess.check_output(["grep","-rnE","--include=*.py","--include=*.ts","--include=*.tsx",pattern,str(ROOT/path)], text=True)
        return len(out.splitlines())
    except Exception:
        return 0

insights = [
    {"id":"INS-01","name":"Expand CPS to full action-surface","targets":["I6.C3 +10","I4.RCI +3"],"weeks":3,"composite_delta":2.2,"action":"Audit all external API calls; route through Handrail CPS with R0-R4 tiering + receipt."},
    {"id":"INS-02","name":"Production NVIR loop with oracle validator","targets":["I6.C1 +10","I4.NVIR +8"],"weeks":5,"composite_delta":2.4,"action":"Implement live generator → oracle verifier → receipt pipeline."},
    {"id":"INS-03","name":"Reversibility registry 80% → 100%","targets":["I6.C5 +8","I5.reversibility +8"],"weeks":2,"composite_delta":1.6,"action":"Classify every state transition; write kenosis proof."},
    {"id":"INS-04","name":"TLC/Apalache on Dignity Kernel invariants","targets":["I6.C2 +5","I1.D4 +5"],"weeks":3,"composite_delta":1.4,"action":"Write TLA+ specs for 10 canonical invariants; run Apalache."},
    {"id":"INS-05","name":"Validator adapters — 3 domains","targets":["I6.C4 +8","I3.admin +4"],"weeks":6,"composite_delta":1.2,"action":"Build adapter contracts for Lean, DFT, FDA-class."},
    {"id":"INS-06","name":"Calibration SFT (tokenized Brier)","targets":["I2.calibration +7"],"weeks":2,"composite_delta":1.4,"action":"Build Brier/ECE/AURC pipeline; log to Alexandria."},
    {"id":"INS-07","name":"Witness cosigning (Rekor v2 pattern)","targets":["I4.RCI +7","I5.attestation +8"],"weeks":4,"composite_delta":1.9,"action":"Three-witness cosign on Alexandria root; publish STH."},
    {"id":"INS-08","name":"Hormetic harness B0→B5 full sweep","targets":["I4.HDRC +5","I2.robust +3"],"weeks":2,"composite_delta":1.1,"action":"Run full B0→B5 pressure sweep on UOIE pack."},
]

for x in insights:
    x["impact_per_week"] = round(x["composite_delta"] / max(1, x["weeks"]), 3)
insights.sort(key=lambda x: x["impact_per_week"], reverse=True)

report = {
    "generated_ut": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    "count": len(insights),
    "total_composite_delta_if_all_applied": round(sum(x["composite_delta"] for x in insights), 2),
    "insights": insights,
}
print(json.dumps(report, indent=2))
