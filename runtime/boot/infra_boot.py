from __future__ import annotations

import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from runtime.state.schemas import InfraBootReport


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def http_json(url: str, timeout: float = 3.0) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url}


def run_cmd(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return int(p.returncode), p.stdout


def collect_infra_boot(run_id: str, run_dir: Path, workspace: Path) -> InfraBootReport:
    ps_rc, ps_out = run_cmd(["docker", "compose", "ps"], cwd=str(workspace))

    handrail = http_json("http://127.0.0.1:8011/healthz")
    ns = http_json("http://127.0.0.1:9000/healthz")
    continuum = http_json("http://127.0.0.1:8788/state")

    report = InfraBootReport(
        boot_ok=(ps_rc == 0),
        run_id=run_id,
        boot_timestamp=now_utc_iso(),
        container_status={
            "compose_ps_rc": ps_rc,
            "compose_ps_txt": ps_out,
        },
        endpoint_status={
            "handrail": handrail,
            "ns": ns,
            "continuum": continuum,
        },
        storage_status={
            "external_ssd": bool(ns.get("storage", {}).get("external_ssd")),
            "ns_ssd_mounted": bool(ns.get("ether", {}).get("ssd_mounted")),
            "run_dir_parent_exists": run_dir.parent.exists(),
        },
        auth_status={
            "status": "stub",
        },
        dependency_status={
            "handrail_ok": handrail.get("ok") is True,
            "ns_ok": ns.get("status") == "ok",
            "continuum_ok": "global_tier" in continuum,
        },
    )

    return report
