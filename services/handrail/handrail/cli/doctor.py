"""
handrail doctor — system readiness checks
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import httpx


def doctor(api_base: str = "http://127.0.0.1:8011") -> dict:
    checks: dict[str, bool | str] = {}

    # Handrail API reachable
    try:
        resp = httpx.get(f"{api_base}/healthz", timeout=3)
        checks["handrail_api"] = resp.status_code == 200
    except Exception as e:
        checks["handrail_api"] = False
        checks["handrail_api_error"] = str(e)

    # Docker reachable
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        checks["docker"] = result.returncode == 0
    except FileNotFoundError:
        checks["docker"] = False
    except Exception:
        checks["docker"] = False

    # CPS dir exists
    from handrail.cli.cps import _cps_dir, _policy_dir, _run_base_dir
    cps_dir = _cps_dir()
    checks["cps_dir"] = cps_dir.exists()
    if not checks["cps_dir"]:
        checks["cps_dir_path"] = str(cps_dir)

    # Policy dir exists
    policy_dir = _policy_dir()
    checks["policy_dir"] = policy_dir.exists()

    # Run dir writable
    run_dir = _run_base_dir()
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        test_file = run_dir / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        checks["run_dir_writable"] = True
    except Exception as e:
        checks["run_dir_writable"] = False
        checks["run_dir_error"] = str(e)

    ok = all(v is True for k, v in checks.items() if not k.endswith("_error") and not k.endswith("_path"))
    return {"ok": ok, "checks": checks}
