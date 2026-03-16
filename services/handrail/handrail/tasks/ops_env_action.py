from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_ADAPTER_URL = "http://127.0.0.1:9911/rpc"
DEFAULT_TIMEOUT_SECONDS = 10


def run_ops_env_action(run_dir: Path, payload: dict) -> dict:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    adapter_method = payload.get("adapter_method")
    adapter_params = payload.get("adapter_params") or {}
    adapter_url = payload.get("adapter_url") or DEFAULT_ADAPTER_URL
    timeout_seconds = int(payload.get("timeout_seconds") or DEFAULT_TIMEOUT_SECONDS)

    if not adapter_method:
        return {
            "ok": False,
            "rc": 400,
            "failure_reason": "missing_adapter_method",
            "artifacts": [],
            "checks": {},
            "state_change": {},
            "warnings": [],
            "adapter_method": None,
            "adapter_response": None,
        }

    now_ms = int(time.time() * 1000)
    adapter_body = {
        "method": adapter_method,
        "params": adapter_params,
        "run_id": payload.get("run_id") or f"env_{now_ms}",
        "action_id": payload.get("action_id") or f"act_{now_ms}",
        "schema_version": "adapter.v1",
    }

    (run_dir / "task_request.json").write_text(
        json.dumps(
            {
                "task_type": "ops_env_action",
                "payload": payload,
                "adapter_body": adapter_body,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    try:
        req = urllib.request.Request(
            adapter_url,
            data=json.dumps(adapter_body).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
            adapter_response = json.loads(raw)

        (run_dir / "adapter_response.json").write_text(
            json.dumps(adapter_response, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return {
            "ok": bool(adapter_response.get("ok", False)),
            "rc": int(adapter_response.get("rc", 1)),
            "failure_reason": adapter_response.get("failure_reason"),
            "artifacts": list(adapter_response.get("artifacts") or []),
            "checks": dict(adapter_response.get("checks") or {}),
            "state_change": dict(adapter_response.get("state_change") or {}),
            "warnings": list(adapter_response.get("warnings") or []),
            "adapter_method": adapter_method,
            "adapter_response": adapter_response,
        }

    except urllib.error.URLError as e:
        reason = "adapter_timeout" if "timed out" in str(e).lower() else "adapter_unreachable"
        return {
            "ok": False,
            "rc": 124 if reason == "adapter_timeout" else 1,
            "failure_reason": reason,
            "artifacts": [],
            "checks": {},
            "state_change": {},
            "warnings": [str(e)],
            "adapter_method": adapter_method,
            "adapter_response": None,
        }
    except Exception as e:
        return {
            "ok": False,
            "rc": 1,
            "failure_reason": "adapter_call_failed",
            "artifacts": [],
            "checks": {},
            "state_change": {},
            "warnings": [str(e)],
            "adapter_method": adapter_method,
            "adapter_response": None,
        }
