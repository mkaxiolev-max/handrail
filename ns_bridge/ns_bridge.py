import json
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

HANDRAIL_URL = "http://127.0.0.1:8011/ops/cps"
CPS_DIR = Path("services/handrail/handrail/cps")
MEMORY_PATH = Path("/Volumes/NSExternal/.run/ns_memory.json")

ATOMIC = {
    "health": "health_check",
    "status": "repo_status",
    "probe": "runtime_probe",
    "catalog": "cps_catalog",
    "git": "git_inspect",
    "precommit": "precommit_check",
    "pwd": "pwd_check",
    "pytest": "pytest_smoke",
    "docker": "docker_status",
    "logs": "recent_logs",
}

COMPOSITES = {
    "system_check": ["health", "status", "probe"],
    "cps_introspect": ["catalog", "git"],
    "precommit_full": ["health", "status", "precommit"],
    "session_start": ["health", "status", "catalog"],
    "dev_check": ["health", "docker", "pytest", "logs"],
}

def now():
    return datetime.utcnow().isoformat() + "Z"

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def save_json(path: Path, obj):
    ensure_parent(path)
    path.write_text(json.dumps(obj, indent=2))

def load_memory():
    return load_json(MEMORY_PATH, {
        "last_intent": None,
        "last_cps_id": None,
        "last_run_id": None,
        "last_ok": None,
        "last_digest": None,
        "failed_ops": [],
        "next_recommended_action": None,
        "decision_history": [],
        "last_summary": None,
    })

def save_memory(mem):
    save_json(MEMORY_PATH, mem)

def cps_path(name: str) -> Path:
    p = CPS_DIR / name
    if p.exists():
        return p
    p_json = CPS_DIR / f"{name}.json"
    if p_json.exists():
        return p_json
    raise FileNotFoundError(f"CPS not found: {name} (looked in {CPS_DIR})")

def load_cps(name: str):
    return json.loads(cps_path(name).read_text())

def post_cps(payload: dict):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        HANDRAIL_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def classify_failure(result: dict):
    classes = []
    for r in result.get("results", []):
        if r.get("ok", False):
            continue
        err = (r.get("error") or "").lower()
        code = (r.get("decision_code") or "").lower()

        if "422" in err or "schema" in err:
            cls = "schema_invalid"
        elif "connection refused" in err:
            cls = "service_down"
        elif "timeout" in err:
            cls = "latency_issue"
        elif "policy" in err or "denied" in code:
            cls = "policy_denied"
        elif "not found" in err or "op_not_found" in code:
            cls = "not_found"
        elif code == "failed":
            cls = "op_failed"
        else:
            cls = "unknown"

        classes.append({
            "op_index": r.get("op_index"),
            "op": r.get("op"),
            "decision_code": r.get("decision_code"),
            "error": r.get("error"),
            "class": cls,
        })
    return classes

def summarize_result(intent: str, result: dict):
    failed = classify_failure(result)
    return {
        "intent": intent,
        "cps_id": result.get("cps_id"),
        "ok": result.get("ok"),
        "run_id": result.get("run_id"),
        "result_digest": result.get("result_digest"),
        "failed_ops": failed,
        "summary": (
            f"{intent}: ok"
            if result.get("ok") else
            f"{intent}: failed ({', '.join(sorted({f['class'] for f in failed})) or 'unknown'})"
        ),
        "timestamp": now(),
    }

def recommend_next(overall_ok: bool, failed_ops: list):
    if overall_ok:
        return "done"
    classes = {f["class"] for f in failed_ops}
    if "schema_invalid" in classes or "not_found" in classes:
        return "inspect"
    if "service_down" in classes or "latency_issue" in classes:
        return "retry"
    if "policy_denied" in classes:
        return "stop"
    return "inspect"

def run_atomic(intent: str):
    cps_name = ATOMIC[intent]
    payload = load_cps(cps_name)
    result = post_cps(payload)
    summary = summarize_result(intent, result)
    return {
        "intent": intent,
        "cps_name": cps_name,
        "result": result,
        "summary": summary,
    }

def run_composite(intent: str):
    steps = COMPOSITES[intent]
    outputs = []
    for step in steps:
        outputs.append(run_atomic(step))
    overall_ok = all(o["result"].get("ok") for o in outputs)
    failed = []
    for o in outputs:
        failed.extend(o["summary"]["failed_ops"])
    return {
        "intent": intent,
        "ok": overall_ok,
        "steps": outputs,
        "failed_ops": failed,
        "next_recommended_action": recommend_next(overall_ok, failed),
        "timestamp": now(),
    }

def run_debug_failure():
    mem = load_memory()
    if mem.get("last_ok") is True:
        return {
            "intent": "debug_failure",
            "ok": True,
            "message": "last run succeeded; nothing to debug",
            "used_memory": {
                "last_intent": mem.get("last_intent"),
                "last_run_id": mem.get("last_run_id"),
            },
            "next_recommended_action": "done",
            "timestamp": now(),
        }
    outputs = [run_atomic("status"), run_atomic("probe")]
    overall_ok = all(o["result"].get("ok") for o in outputs)
    failed = []
    for o in outputs:
        failed.extend(o["summary"]["failed_ops"])
    return {
        "intent": "debug_failure",
        "ok": overall_ok,
        "steps": outputs,
        "failed_ops": failed,
        "used_memory": {
            "last_intent": mem.get("last_intent"),
            "last_run_id": mem.get("last_run_id"),
            "failed_ops": mem.get("failed_ops"),
        },
        "next_recommended_action": recommend_next(overall_ok, failed),
        "timestamp": now(),
    }

def update_memory_from_output(output: dict):
    mem = load_memory()

    if "steps" in output:
        step_summaries = [s["summary"] for s in output["steps"]]
        last = step_summaries[-1] if step_summaries else {}
        mem["last_intent"] = output["intent"]
        mem["last_cps_id"] = last.get("cps_id")
        mem["last_run_id"] = last.get("run_id")
        mem["last_ok"] = output.get("ok")
        mem["last_digest"] = last.get("result_digest")
        mem["failed_ops"] = output.get("failed_ops", [])
        mem["next_recommended_action"] = output.get("next_recommended_action")
        mem["last_summary"] = {
            "intent": output["intent"],
            "ok": output.get("ok"),
            "step_summaries": step_summaries,
            "timestamp": output.get("timestamp"),
        }
        mem["decision_history"].append({
            "intent": output["intent"],
            "ok": output.get("ok"),
            "next_recommended_action": output.get("next_recommended_action"),
            "timestamp": output.get("timestamp"),
        })
    else:
        mem["last_intent"] = output["intent"]
        mem["last_cps_id"] = output["cps_name"]
        mem["last_run_id"] = output["summary"].get("run_id")
        mem["last_ok"] = output["summary"].get("ok")
        mem["last_digest"] = output["summary"].get("result_digest")
        mem["failed_ops"] = output["summary"].get("failed_ops", [])
        mem["next_recommended_action"] = recommend_next(
            output["summary"].get("ok", False),
            output["summary"].get("failed_ops", [])
        )
        mem["last_summary"] = output["summary"]
        mem["decision_history"].append({
            "intent": output["intent"],
            "ok": output["summary"].get("ok"),
            "next_recommended_action": mem["next_recommended_action"],
            "timestamp": output["summary"].get("timestamp"),
        })

    mem["decision_history"] = mem["decision_history"][-50:]
    save_memory(mem)
    return mem

def list_tasks():
    return {
        "atomic": sorted(ATOMIC.keys()),
        "composite": sorted(COMPOSITES.keys()) + ["debug_failure"],
    }

def inspect_last():
    return load_memory()

def replay_last():
    mem = load_memory()
    last = mem.get("last_intent")
    if not last:
        return {"ok": False, "error": "no_last_intent"}
    return dispatch(last)



def resolve_intent(raw: str):
    text = (raw or "").strip().lower()

    rules = [
        (["system", "health"], "system_check"),
        (["check", "system"], "system_check"),
        (["introspect"], "cps_introspect"),
        (["catalog"], "cps_introspect"),
        (["debug"], "debug_failure"),
        (["failure"], "debug_failure"),
        (["precommit"], "precommit_full"),
        (["session", "start"], "session_start"),
        (["start", "session"], "session_start"),
        (["open", "session"], "session_start"),
        (["before commit"], "precommit_full"),
        (["health"], "health"),
        (["status"], "status"),
        (["probe"], "probe"),
        (["git"], "git"),
        (["pwd"], "pwd"),
        (["pytest"], "pytest"),
        (["docker"], "docker"),
        (["logs"], "logs"),
        (["dev", "check"], "dev_check"),
        (["replay", "compare"], "replay_compare"),
        (["compare", "replay"], "replay_compare"),
        (["memory"], "memory"),
        (["inspect"], "inspect"),
        (["replay"], "replay"),
        (["list"], "list"),
        (["replay", "compare"], "replay_compare"),
        (["compare", "replay"], "replay_compare"),
    ]

    for needles, target in rules:
        if all(n in text for n in needles):
            return target

    if text in ATOMIC or text in COMPOSITES or text in {"debug_failure", "list", "inspect", "memory", "replay", "replay_compare"}:
        return text

    return None



def replay_compare():
    mem = load_memory()
    last = mem.get("last_intent")
    last_digest = mem.get("last_digest")
    if not last:
        return {"ok": False, "error": "no_last_intent"}

    if last in {"memory", "inspect", "list", "replay", "replay_compare"}:
        return {"ok": False, "error": f"non_replayable_intent:{last}"}

    out = dispatch(last)
    if isinstance(out, dict) and "steps" in out:
        step_summaries = [s["summary"] for s in out["steps"]]
        new_digest = step_summaries[-1].get("result_digest") if step_summaries else None
    elif isinstance(out, dict) and "summary" in out:
        new_digest = out["summary"].get("result_digest")
    else:
        new_digest = None

    return {
        "intent": "replay_compare",
        "replayed_intent": last,
        "previous_digest": last_digest,
        "new_digest": new_digest,
        "deterministic_match": (last_digest == new_digest and last_digest is not None),
        "output": out,
        "timestamp": now(),
    }

def dispatch(intent: str):
    if intent in ATOMIC:
        return run_atomic(intent)
    if intent in COMPOSITES:
        return run_composite(intent)
    if intent == "debug_failure":
        return run_debug_failure()
    if intent == "list":
        return list_tasks()
    if intent == "inspect":
        return inspect_last()
    if intent == "memory":
        return inspect_last()
    if intent == "replay":
        return replay_last()
    if intent == "replay_compare":
        return replay_compare()
    return {
        "ok": False,
        "error": f"unknown_intent:{intent}",
        "known_intents": list_tasks(),
    }



def safe_safe_execute_cps(cps_id: str):
    try:
        return safe_execute_cps(cps_id)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "cps_id": cps_id
        }

def main():
    raw_intent = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "list"
    intent = resolve_intent(raw_intent)
    if not intent:
        print(json.dumps({
            "ok": False,
            "error": f"unknown_intent:{raw_intent}",
            "known_intents": list_tasks()
        }, indent=2))
        sys.exit(1)
    out = dispatch(intent)

    if isinstance(out, dict) and ("steps" in out or "cps_name" in out):
        mem = update_memory_from_output(out)
        envelope = {
            "intent": out.get("intent", intent) if isinstance(out, dict) else intent,
            "output": out,
            "memory": {
                "last_intent": mem.get("last_intent"),
                "last_run_id": mem.get("last_run_id"),
                "last_ok": mem.get("last_ok"),
                "next_recommended_action": mem.get("next_recommended_action"),
            }
        }
        print(json.dumps(envelope, indent=2))
    else:
        print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
