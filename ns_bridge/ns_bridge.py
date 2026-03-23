import json
import sys
import urllib.request

HANDRAIL_URL = "http://127.0.0.1:8011/ops/cps"

CPS_MAP = {
    "health": {
        "cps_id": "health_check",
        "objective": "ns bridge health check",
        "ops": [
            {
                "op": "http.get",
                "args": {
                    "url": "http://127.0.0.1:8011/healthz"
                }
            }
        ],
        "expect": {}
    },
    "status": {
        "cps_id": "repo_status",
        "objective": "ns bridge repo status",
        "ops": [
            {
                "op": "proc.run_readonly",
                "args": {
                    "command": "pwd",
                    "cwd": "/app/handrail"
                }
            },
            {
                "op": "proc.run_readonly",
                "args": {
                    "command": "ls",
                    "cwd": "/app/handrail"
                }
            }
        ],
        "expect": {}
    },
    "probe": {
        "cps_id": "runtime_probe",
        "objective": "ns bridge runtime probe",
        "ops": [
            {
                "op": "http.get",
                "args": {
                    "url": "http://127.0.0.1:8011/healthz"
                }
            },
            {
                "op": "proc.run_readonly",
                "args": {
                    "command": "pwd",
                    "cwd": "/app/handrail"
                }
            }
        ],
        "expect": {}
    }
}

def send_cps(payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        HANDRAIL_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    intent = sys.argv[1] if len(sys.argv) > 1 else "health"
    if intent not in CPS_MAP:
        print(json.dumps({
            "ok": False,
            "error": f"unknown_intent:{intent}",
            "known_intents": sorted(CPS_MAP.keys())
        }, indent=2))
        sys.exit(1)

    result = send_cps(CPS_MAP[intent])

    summary = {
        "intent": intent,
        "cps_id": result.get("cps_id"),
        "ok": result.get("ok"),
        "run_id": result.get("run_id"),
        "result_digest": result.get("result_digest"),
        "failed_ops": [
            {
                "op_index": r.get("op_index"),
                "op": r.get("op"),
                "decision_code": r.get("decision_code"),
                "error": r.get("error"),
            }
            for r in result.get("results", [])
            if not r.get("ok", False)
        ],
        "raw": result,
    }

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
