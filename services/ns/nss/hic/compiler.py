"""
HIC — Holographic Intent Compiler
Converts natural language intent into a verified CPS op candidate.
Uses cosine similarity against a pre-defined safe action codebook.
Not stochastic. Not probabilistic. Algebraic.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone

# ── Safe action codebook ──────────────────────────────────────────────────────
SAFE_CODEBOOK = [
    {"pattern": "check memory",          "op": "ns.memory_recent",      "args": {},                                                                       "risk": "R0"},
    {"pattern": "what time",             "op": "sys.now",               "args": {},                                                                       "risk": "R0"},
    {"pattern": "system status",         "op": "http.health_check",     "args": {"url": "http://ns:9000/healthz", "expect_status": 200},                  "risk": "R0"},
    {"pattern": "who am i",              "op": "ns.memory_recent",      "args": {"n": 1},                                                                 "risk": "R0"},
    {"pattern": "list capabilities",     "op": "adapter.list_capabilities", "args": {},                                                                   "risk": "R0"},
    {"pattern": "check voice",           "op": "http.health_check",     "args": {"url": "http://ns:9000/voice/health", "expect_status": 200},             "risk": "R0"},
    {"pattern": "send notification",     "op": "notify.send",           "args": {},                                                                       "risk": "R1"},
    {"pattern": "read clipboard",        "op": "clipboard.read",        "args": {},                                                                       "risk": "R1"},
    {"pattern": "get volume",            "op": "audio.get_volume",      "args": {},                                                                       "risk": "R0"},
    {"pattern": "what am i working on",  "op": "window.get_focused",    "args": {},                                                                       "risk": "R0"},
    {"pattern": "take screenshot",       "op": "vision.screenshot",     "args": {},                                                                       "risk": "R1"},
    {"pattern": "battery status",        "op": "battery.get_status",    "args": {},                                                                       "risk": "R0"},
    {"pattern": "search memory",         "op": "ns.memory_query",       "args": {},                                                                       "risk": "R0"},
    {"pattern": "recent decisions",      "op": "http.health_check",     "args": {"url": "http://ns:9000/explain/recent", "expect_status": 200},           "risk": "R0"},
    {"pattern": "flywheel status",       "op": "http.health_check",     "args": {"url": "http://ns:9000/invention/flywheel", "expect_status": 200},       "risk": "R0"},
    {"pattern": "disk usage",            "op": "sys.disk_usage",        "args": {"path": "/app"},                                                         "risk": "R0"},
    {"pattern": "uptime",                "op": "sys.uptime",            "args": {},                                                                       "risk": "R0"},
    {"pattern": "list processes",        "op": "proc_extended.list_processes", "args": {},                                                                "risk": "R0"},
    {"pattern": "memory usage",          "op": "proc_extended.get_memory_usage", "args": {},                                                              "risk": "R0"},
    {"pattern": "network check",         "op": "network.port_check",    "args": {"host": "ns", "port": 9000},                                            "risk": "R0"},
    # ── Program library ops ───────────────────────────────────────────────────
    {"pattern": "advance fundraising",   "op": "program.advance_state", "args": {"namespace": "fundraising"},                                             "risk": "R0"},
    {"pattern": "add candidate",         "op": "program.advance_state", "args": {"namespace": "hiring"},                                                  "risk": "R0"},
    {"pattern": "log partner",           "op": "program.advance_state", "args": {"namespace": "partner"},                                                 "risk": "R0"},
    {"pattern": "record decision",       "op": "gov.record_decision",   "args": {},                                                                       "risk": "R0"},
    {"pattern": "ingest knowledge",      "op": "program.advance_state", "args": {"namespace": "knowledge"},                                               "risk": "R0"},
    {"pattern": "capture feedback",      "op": "program.advance_state", "args": {"namespace": "feedback"},                                                "risk": "R0"},
    # ── Adapter ops ───────────────────────────────────────────────────────────
    {"pattern": "check battery",         "op": "battery.get_status",    "args": {},                                                                       "risk": "R0"},
    {"pattern": "show notification",     "op": "notify.send",           "args": {},                                                                       "risk": "R1"},
    {"pattern": "list windows",          "op": "proc_extended.list_processes", "args": {},                                                                "risk": "R0"},
    {"pattern": "get display info",      "op": "display.get_info",      "args": {},                                                                       "risk": "R0"},
    # ── System ops ────────────────────────────────────────────────────────────
    {"pattern": "check disk",            "op": "sys.disk_usage",        "args": {"path": "/app"},                                                         "risk": "R0"},
    {"pattern": "list directory",        "op": "fs.list",               "args": {},                                                                       "risk": "R0"},
    {"pattern": "get environment",       "op": "sys.env_get",           "args": {},                                                                       "risk": "R0"},
    {"pattern": "check git log",         "op": "git.log",               "args": {},                                                                       "risk": "R0"},
    {"pattern": "get git status",        "op": "git.status",            "args": {},                                                                       "risk": "R0"},
    # ── NS self-awareness ─────────────────────────────────────────────────────
    {"pattern": "check capability gaps", "op": "http.health_check",     "args": {"url": "http://ns:9000/capability/unresolved", "expect_status": 200},    "risk": "R0"},
    {"pattern": "show flywheel state",   "op": "http.health_check",     "args": {"url": "http://ns:9000/invention/flywheel", "expect_status": 200},       "risk": "R0"},
    {"pattern": "list semantic candidates", "op": "http.health_check",  "args": {"url": "http://ns:9000/semantic/candidates", "expect_status": 200},      "risk": "R0"},
    {"pattern": "check policy proposals","op": "http.health_check",     "args": {"url": "http://ns:9000/semantic/proposals", "expect_status": 200},       "risk": "R0"},
    {"pattern": "recent ops",            "op": "http.health_check",     "args": {"url": "http://ns:9000/ops/recent", "expect_status": 200},               "risk": "R0"},
    # ── Voice-natural proactive intel patterns ────────────────────────────────
    {"pattern": "what are my next actions",  "op": "ns.proactive_intel",    "args": {},                                                                   "risk": "R0"},
    {"pattern": "give me suggestions",       "op": "ns.proactive_intel",    "args": {},                                                                   "risk": "R0"},
    {"pattern": "what should i focus on",    "op": "ns.proactive_intel",    "args": {},                                                                   "risk": "R0"},
    {"pattern": "show capability graph",     "op": "ns.capability_graph",   "args": {},                                                                   "risk": "R0"},
    {"pattern": "explain recent decisions",  "op": "ns.explain_recent",     "args": {},                                                                   "risk": "R0"},
    {"pattern": "open founder console",      "op": "http.health_check",     "args": {"url": "http://ns:9000/founder", "expect_status": 200},              "risk": "R0"},
    {"pattern": "check voice health",        "op": "http.health_check",     "args": {"url": "http://ns:9000/voice/health", "expect_status": 200},         "risk": "R0"},
    {"pattern": "run sovereign boot",        "op": "http.health_check",     "args": {"url": "http://ns:9000/healthz", "expect_status": 200},              "risk": "R0"},
    {"pattern": "show model status",         "op": "http.health_check",     "args": {"url": "http://ns:9000/models/status", "expect_status": 200},        "risk": "R0"},
    {"pattern": "check sms",                 "op": "http.health_check",     "args": {"url": "http://ns:9000/sms/health", "expect_status": 200},           "risk": "R0"},
    # ── Vision ops ────────────────────────────────────────────────────────────
    {"pattern": "take a screenshot",         "op": "vision.screenshot",     "args": {},                                                                   "risk": "R1"},
    {"pattern": "capture my screen",         "op": "vision.screenshot",     "args": {},                                                                   "risk": "R1"},
    {"pattern": "read text on screen",       "op": "vision.ocr_region",     "args": {},                                                                   "risk": "R1"},
]

# ── Constitutional veto patterns ──────────────────────────────────────────────
VETO_PATTERNS = [
    "delete all", "format", "rm -rf", "drop database",
    "disable kernel", "bypass dignity", "ignore constraints",
    "override policy", "kill yubikey", "destroy alexandria",
    "auth bypass", "policy override", "self destruct",
    "never event", "dignity violation",
]

# ── Lineage log ───────────────────────────────────────────────────────────────
def _lineage_path() -> Path:
    ssd = Path("/Volumes/NSExternal/ALEXANDRIA/hic")
    root = ssd if ssd.parent.exists() else Path.home() / ".axiolev" / "hic"
    root.mkdir(parents=True, exist_ok=True)
    return root / "lineage.jsonl"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ── Vector math ───────────────────────────────────────────────────────────────
def _vectorize(text: str) -> dict[str, float]:
    words = text.lower().split()
    vec: dict[str, float] = {}
    for w in words:
        vec[w] = vec.get(w, 0) + 1
    norm = math.sqrt(sum(v ** 2 for v in vec.values())) or 1
    return {k: v / norm for k, v in vec.items()}

def _cosine(a: dict, b: dict) -> float:
    return sum(a.get(k, 0) * b.get(k, 0) for k in b)

# ── Compiler ──────────────────────────────────────────────────────────────────
class HolographicIntentCompiler:
    SAFETY_THRESHOLD = 0.25

    def compile(self, text: str) -> dict:
        text_lower = text.lower()

        # Step 1: Constitutional veto
        for pattern in VETO_PATTERNS:
            if pattern in text_lower:
                result = {
                    "ok": False,
                    "veto": True,
                    "veto_reason": f"Constitutional veto: '{pattern}' is a never-event pattern",
                    "op": None,
                    "args": None,
                    "confidence": 0.0,
                    "ts": _now(),
                }
                self._log(text, result)
                return result

        # Step 2: Vectorize
        input_vec = _vectorize(text)

        # Step 3: Score against codebook
        scores = [(_cosine(input_vec, _vectorize(e["pattern"])), e) for e in SAFE_CODEBOOK]
        scores.sort(key=lambda x: -x[0])
        best_score, best_entry = scores[0]

        # Step 4: Threshold check
        if best_score < self.SAFETY_THRESHOLD:
            result = {
                "ok": False,
                "veto": False,
                "veto_reason": None,
                "op": None,
                "args": None,
                "confidence": round(best_score, 4),
                "message": "No safe codebook match — route to LLM for general response",
                "ts": _now(),
            }
            self._log(text, result)
            return result

        result = {
            "ok": True,
            "veto": False,
            "veto_reason": None,
            "op": best_entry["op"],
            "args": best_entry["args"],
            "risk": best_entry["risk"],
            "confidence": round(best_score, 4),
            "matched_pattern": best_entry["pattern"],
            "ts": _now(),
        }
        self._log(text, result)
        return result

    def _log(self, text: str, result: dict) -> None:
        try:
            entry = {"input": text, **result}
            with open(_lineage_path(), "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def codebook(self) -> list[dict]:
        return SAFE_CODEBOOK

    def veto_patterns(self) -> list[str]:
        return VETO_PATTERNS


# ── Singleton ─────────────────────────────────────────────────────────────────
_hic = HolographicIntentCompiler()

def get_hic() -> HolographicIntentCompiler:
    return _hic
