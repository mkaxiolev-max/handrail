import json
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

HANDRAIL_URL = "http://127.0.0.1:8011/ops/cps"
MEMORY_FILE = Path("/Volumes/NSExternal/.run/ns_memory.json")

NS_MEMORY = {
    "last_intent": None,
    "last_run_id": None,
    "last_ok": None,
    "last_digest": None,
    "failed_ops": [],
    "decision_history": [],
}

def load_memory():
    global NS_MEMORY
    if MEMORY_FILE.exists():
        try:
            NS_MEMORY = json.loads(MEMORY_FILE.read_text())
        except:
            pass

def save_memory():
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(NS_MEMORY, indent=2))

def remember(summary):
    global NS_MEMORY
    NS_MEMORY["last_intent"] = summary["intent"]
    NS_MEMORY["last_run_id"] = summary["run_id"]
    NS_MEMORY["last_ok"] = summary["ok"]
    NS_MEMORY["last_digest"] = summary["result_digest"]
    NS_MEMORY["failed_ops"] = summary["failed_ops"]
    save_memory()

CPS_MAP = {
    "health": {"cps_id": "health_check", "objective": "health check", "ops": [{"op": "http.get", "args": {"url": "http://127.0.0.1:8011/healthz"}}], "expect": {}},
    "status": {"cps_id": "repo_status", "objective": "repo status", "ops": [{"op": "proc.run_readonly", "args": {"command": "pwd", "cwd": "/app/handrail"}}, {"op": "proc.run_readonly", "args": {"command": "ls", "cwd": "/app/handrail"}}], "expect": {}},
    "probe": {"cps_id": "runtime_probe", "objective": "runtime probe", "ops": [{"op": "http.get", "args": {"url": "http://127.0.0.1:8011/healthz"}}, {"op": "proc.run_readonly", "args": {"command": "pwd", "cwd": "/app/handrail"}}], "expect": {}},
    "catalog": {"cps_id": "cps_catalog", "objective": "list CPS", "ops": [{"op": "proc.run_readonly", "args": {"command": "ls", "cwd": "/app/handrail/cps"}}], "expect": {}},
    "git_inspect": {"cps_id": "git_inspect", "objective": "git inspect", "ops": [{"op": "proc.run_readonly", "args": {"command": "pwd", "cwd": "/app/handrail"}}], "expect": {}},
}

def send_cps(payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(HANDRAIL_URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def execute_intent(intent):
    if intent not in CPS_MAP:
        return {"ok": False, "error": f"unknown_intent:{intent}"}
    result = send_cps(CPS_MAP[intent])
    summary = {"intent": intent, "cps_id": result.get("cps_id"), "ok": result.get("ok"), "run_id": result.get("run_id"), "result_digest": result.get("result_digest"), "failed_ops": [r for r in result.get("results", []) if not r.get("ok", False)]}
    return summary

def decide(summary):
    return "success" if summary["ok"] else ("retry_with_status" if summary["failed_ops"] else "stop")

def execute_with_recovery(intent):
    load_memory()
    summary = execute_intent(intent)
    remember(summary)
    decision = decide(summary)
    if decision == "retry_with_status":
        status = execute_intent("status")
        remember(status)
        summary["recovery"] = status
    NS_MEMORY["decision_history"].append({"intent": intent, "decision": decision, "timestamp": datetime.utcnow().isoformat()})
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
    if NS_MEMORY["last_ok"]:
        return {"task": "debug_failure", "ok": True, "note": "last run succeeded"}
    s = execute_intent("status")
    return {"task": "debug_failure", "ok": True, "last_failure": {"run_id": NS_MEMORY["last_run_id"], "failed_ops": NS_MEMORY["failed_ops"]}, "current_status": s}

def main():
    load_memory()
    if len(sys.argv) < 2:
        print("USAGE: ns_bridge [health|status|probe|catalog|git_inspect|system_check|cps_introspect|debug_failure|memory]", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "memory":
        print(json.dumps(NS_MEMORY, indent=2))
    elif cmd == "system_check":
        print(json.dumps(task_system_check(), indent=2))
    elif cmd == "cps_introspect":
        print(json.dumps(task_cps_introspect(), indent=2))
    elif cmd == "debug_failure":
        print(json.dumps(task_debug_failure(), indent=2))
    elif cmd in CPS_MAP:
        print(json.dumps(execute_with_recovery(cmd), indent=2))
    else:
        print(f"ERROR: Unknown command {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
