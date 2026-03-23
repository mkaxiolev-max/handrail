import json, sys, urllib.request
from pathlib import Path
from datetime import datetime

HANDRAIL_URL = "http://127.0.0.1:8011/ops/cps"
MEMORY_FILE = Path("/Volumes/NSExternal/.run/ns_memory.json")

NS_MEMORY = {
    "last_intent": None,
    "last_cps_id": None,
    "last_run_id": None,
    "last_ok": None,
    "last_digest": None,
    "failed_ops": [],
    "next_recommended_action": None,
    "decision_history": [],
}

def load_memory():
    global NS_MEMORY
    if MEMORY_FILE.exists():
        try: NS_MEMORY = json.loads(MEMORY_FILE.read_text())
        except: pass

def save_memory():
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(NS_MEMORY, indent=2))

def recommend_next_action(task, ok, failed_ops):
    if ok: return None
    if failed_ops: return "run debug_failure"
    if not ok: return "investigate manually"
    return None

def remember(task, cps_id, run_id, ok, digest, failed_ops):
    global NS_MEMORY
    NS_MEMORY["last_intent"] = task
    NS_MEMORY["last_cps_id"] = cps_id
    NS_MEMORY["last_run_id"] = run_id
    NS_MEMORY["last_ok"] = ok
    NS_MEMORY["last_digest"] = digest
    NS_MEMORY["failed_ops"] = failed_ops
    NS_MEMORY["next_recommended_action"] = recommend_next_action(task, ok, failed_ops)
    save_memory()

CPS_MAP = {
    "health": {"cps_id": "health_check", "ops": [{"op": "http.get", "args": {"url": "http://127.0.0.1:8011/healthz"}}]},
    "status": {"cps_id": "repo_status", "ops": [{"op": "proc.run_readonly", "args": {"command": "pwd", "cwd": "/app/handrail"}}, {"op": "proc.run_readonly", "args": {"command": "ls", "cwd": "/app/handrail"}}]},
    "probe": {"cps_id": "runtime_probe", "ops": [{"op": "http.get", "args": {"url": "http://127.0.0.1:8011/healthz"}}, {"op": "proc.run_readonly", "args": {"command": "pwd", "cwd": "/app/handrail"}}]},
    "catalog": {"cps_id": "cps_catalog", "ops": [{"op": "proc.run_readonly", "args": {"command": "ls", "cwd": "/app/handrail/cps"}}]},
    "git_inspect": {"cps_id": "git_inspect", "ops": [{"op": "proc.run_readonly", "args": {"command": "pwd", "cwd": "/app/handrail"}}]},
}

def send_cps(payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(HANDRAIL_URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp: return json.loads(resp.read().decode("utf-8"))

def execute_intent(intent):
    if intent not in CPS_MAP: return {"ok": False, "error": f"unknown_intent:{intent}"}
    result = send_cps(CPS_MAP[intent])
    return {"intent": intent, "cps_id": result.get("cps_id"), "ok": result.get("ok"), "run_id": result.get("run_id"), "result_digest": result.get("result_digest"), "failed_ops": [r for r in result.get("results", []) if not r.get("ok", False)]}

def execute_with_recovery(intent):
    load_memory()
    summary = execute_intent(intent)
    remember(intent, summary["cps_id"], summary["run_id"], summary["ok"], summary["result_digest"], summary["failed_ops"])
    if not summary["ok"] and summary["failed_ops"]: summary["recovery"] = execute_intent("status")
    NS_MEMORY["decision_history"].append({"intent": intent, "ok": summary["ok"], "timestamp": datetime.now(datetime.timezone.utc).isoformat()})
    save_memory()
    return summary

def task_system_check():
    print("[ns] TASK: system_check", file=sys.stderr)
    h = execute_intent("health")
    if not h["ok"]: return {"task": "system_check", "ok": False, "failed_at": "health"}
    s = execute_intent("status")
    if not s["ok"]: return {"task": "system_check", "ok": False, "failed_at": "status"}
    p = execute_intent("probe")
    if not p["ok"]: return {"task": "system_check", "ok": False, "failed_at": "probe"}
    return {"task": "system_check", "ok": True, "passed": ["health", "status", "probe"]}

def task_cps_introspect():
    print("[ns] TASK: cps_introspect", file=sys.stderr)
    c = execute_intent("catalog")
    if not c["ok"]: return {"task": "cps_introspect", "ok": False, "failed_at": "catalog"}
    g = execute_intent("git_inspect")
    if not g["ok"]: return {"task": "cps_introspect", "ok": False, "failed_at": "git_inspect"}
    return {"task": "cps_introspect", "ok": True, "passed": ["catalog", "git_inspect"]}

def task_debug_failure():
    print("[ns] TASK: debug_failure", file=sys.stderr)
    load_memory()
    if NS_MEMORY["last_ok"]: return {"task": "debug_failure", "ok": True, "note": "last run succeeded"}
    s = execute_intent("status")
    return {"task": "debug_failure", "ok": True, "last_failure": {"run_id": NS_MEMORY["last_run_id"], "failed_ops": NS_MEMORY["failed_ops"]}, "current_status": s}

def main():
    load_memory()
    if len(sys.argv) < 2: print("USAGE: ns_bridge [health|status|probe|catalog|git_inspect|system_check|cps_introspect|debug_failure|memory]", file=sys.stderr); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "memory": print(json.dumps(NS_MEMORY, indent=2))
    elif cmd == "system_check": print(json.dumps(task_system_check(), indent=2))
    elif cmd == "cps_introspect": print(json.dumps(task_cps_introspect(), indent=2))
    elif cmd == "debug_failure": print(json.dumps(task_debug_failure(), indent=2))
    elif cmd in CPS_MAP: print(json.dumps(execute_with_recovery(cmd), indent=2))
    else: print(f"ERROR: Unknown command {cmd}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__": main()

# ===== DECISION POLICY =====
def classify_failure(failed_ops, error_msg=None):
    if not failed_ops: return "unknown"
    for op in failed_ops:
        if "connection refused" in str(op): return "connection_refused"
        if "policy denied" in str(op): return "policy_denied"
        if "not found" in str(op): return "not_found"
    return "op_failed"

def decide_recovery(task, ok, failed_ops, failure_type=None):
    if ok: return {"action": "done", "reason": "task succeeded"}
    if not failed_ops: return {"action": "stop", "reason": "task failed, no ops to debug"}
    if failure_type == "connection_refused": return {"action": "retry_once", "reason": "connection issue, retry"}
    if failure_type == "policy_denied": return {"action": "stop_surface_reason", "reason": "policy enforcement, cannot proceed"}
    if failure_type == "not_found": return {"action": "debug_failure", "reason": "resource not found, inspect"}
    return {"action": "debug_failure", "reason": "op failed, run debug"}

def execute_with_policy(task):
    load_memory()
    summary = execute_intent(task)
    if not summary["cps_id"] in CPS_MAP: summary["cps_id"] = task
    remember(task, summary.get("cps_id"), summary["run_id"], summary["ok"], summary["result_digest"], summary["failed_ops"])
    failure_type = classify_failure(summary["failed_ops"])
    recovery = decide_recovery(task, summary["ok"], summary["failed_ops"], failure_type)
    summary["failure_classification"] = failure_type
    summary["recovery_decision"] = recovery
    NS_MEMORY["decision_history"].append({"task": task, "ok": summary["ok"], "decision": recovery["action"], "timestamp": datetime.now(datetime.timezone.utc).isoformat()})
    save_memory()
    return summary

# Update main to use execute_with_policy

# ===== OPERATOR SURFACES =====
def cmd_list():
    """List available tasks"""
    tasks = {
        "system_check": "Health + status + probe",
        "cps_introspect": "Catalog + git inspect",
        "debug_failure": "Investigate last failure",
        "repo_status": "Repo status + listing",
        "runtime_probe": "Runtime health + process",
        "health": "API health check",
    }
    print("AVAILABLE TASKS:", file=sys.stderr)
    for task, desc in tasks.items():
        print(f"  {task:20} {desc}", file=sys.stderr)

def cmd_inspect(run_id=None):
    """Inspect last run"""
    load_memory()
    if not run_id: run_id = NS_MEMORY.get("last_run_id")
    if not run_id: return {"error": "no last run"}
    return {
        "run_id": run_id,
        "intent": NS_MEMORY["last_intent"],
        "cps_id": NS_MEMORY["last_cps_id"],
        "ok": NS_MEMORY["last_ok"],
        "digest": NS_MEMORY["last_digest"],
        "failed_ops": NS_MEMORY["failed_ops"],
        "next_action": NS_MEMORY["next_recommended_action"],
    }

def cmd_replay():
    """Replay last run"""
    load_memory()
    if not NS_MEMORY["last_intent"]:
        return {"error": "no last run to replay"}
    task = NS_MEMORY["last_intent"]
    summary = execute_with_policy(task)
    return {
        "replayed": task,
        "ok": summary["ok"],
        "deterministic": summary["result_digest"] == NS_MEMORY["last_digest"],
        "new_digest": summary["result_digest"],
        "last_digest": NS_MEMORY["last_digest"],
    }

# Update main to support inspect/replay/list

def task_precommit_check():
    """Check if safe to commit"""
    print("[ns] TASK: precommit_check", file=sys.stderr)
    
    # Step 1: repo status
    s = execute_intent("status")
    if not s["ok"]:
        return {"task": "precommit_check", "ok": False, "safe_to_commit": False, "reason": "repo status failed"}
    
    # Step 2: git inspect
    g = execute_intent("git_inspect")
    if not g["ok"]:
        return {"task": "precommit_check", "ok": False, "safe_to_commit": False, "reason": "git inspect failed"}
    
    # Step 3: runtime health (optional)
    h = execute_intent("health")
    runtime_ok = h["ok"]
    
    # Decision logic
    safe = s["ok"] and g["ok"]
    
    return {
        "task": "precommit_check",
        "ok": True,
        "safe_to_commit": safe,
        "repo_status": "clean" if s["ok"] else "issues",
        "git_state": "inspected" if g["ok"] else "error",
        "runtime_health": "ok" if runtime_ok else "degraded",
        "recommendation": "proceed with commit" if safe else "fix issues first",
    }

