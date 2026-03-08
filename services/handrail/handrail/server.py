from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from handrail.task_runner import run_task
from pydantic import BaseModel

try:
    import urllib.request as urlreq
except Exception:
    urlreq = None  # type: ignore

app = FastAPI(title="Handrail", version="0.1.0")


class TaskRequest(BaseModel):
    task_type: str
    objective: str | None = None
    payload: dict[str, Any] | None = None

# Paths visible INSIDE handrail container
WORKSPACE = Path(os.environ.get("HR_WORKSPACE", "/workspace"))
COMPOSE_FILE = WORKSPACE / "docker-compose.yml"
EXTERNAL = Path("/Volumes/NSExternal")

RUNS_DIR = EXTERNAL / ".run" / "boot"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


class RunRequest(BaseModel):
    cmd: List[str]
    cwd: Optional[str] = None
    timeout_s: int = 120


def _boot_ez_worker(run_dir):
    """
    Worker for Boot EZ:
    - restart ns + continuum only
    - never touch deps (prevents handrail self-recreate)
    - writes output files so we can debug deterministically
    """
    from pathlib import Path as _Path
    import json as _json
    try:
        rc_up = run_compose(
            ["up", "-d", "--no-deps", "--build", "--force-recreate", "ns", "continuum"],
            cwd=WORKSPACE,
            out_path=_Path(run_dir) / "compose_up_ns_continuum.txt",
        )

        health = wait_health(_Path(run_dir), deadline_s=60)
        mounts = mount_status(_Path(run_dir))

        run_compose(["ps"], cwd=WORKSPACE, out_path=_Path(run_dir) / "compose_ps_after.txt")

        resp = {
            "ok": rc_up == 0 and health.get("ns") and health.get("continuum"),
            "rc_up": rc_up,
            "health": health,
            "mounts": mounts,
            "run_dir": str(run_dir),
            "note": "Boot EZ v1 restarts ns + continuum only (handrail remains running).",
        }
        (_Path(run_dir) / "result.json").write_text(_json.dumps(resp, indent=2))
    except Exception as e:
        (_Path(run_dir) / "error.txt").write_text(f"{type(e).__name__}: {e}\n")

NS_HEALTHZ = os.environ.get("NS_HEALTHZ", "http://ns:9000/healthz")
CONT_STATE = os.environ.get("CONT_STATE", "http://continuum:8788/state")
SELF_HEALTHZ = os.environ.get("SELF_HEALTHZ", "http://127.0.0.1:8011/healthz")


def now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def http_ok(url: str, timeout: float = 2.0) -> bool:
    if urlreq is None:
        return False
    try:
        with urlreq.urlopen(url, timeout=timeout) as r:
            return 200 <= int(getattr(r, "status", 200)) < 300
    except Exception:
        return False


def http_json(url: str, timeout: float = 2.0) -> Optional[Dict[str, Any]]:
    if urlreq is None:
        return None
    try:
        with urlreq.urlopen(url, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except Exception:
        return None


def run_compose(args: list[str], cwd: Path, out_path: Path) -> int:
    """
    Runs docker-compose against the host via /var/run/docker.sock.
    IMPORTANT: never "up --force-recreate" handrail from inside handrail.
    """
    cmd = ["docker-compose", "-f", str(COMPOSE_FILE), *args]
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    out_path.write_text(p.stdout)
    return int(p.returncode)


def wait_health(run_dir: Path, deadline_s: int = 40) -> Dict[str, Any]:
    t0 = time.time()
    status = {"handrail": False, "ns": False, "continuum": False}

    while time.time() - t0 < deadline_s:
        status["handrail"] = http_ok(SELF_HEALTHZ)
        status["ns"] = http_ok(NS_HEALTHZ)
        status["continuum"] = http_ok(CONT_STATE)
        if all(status.values()):
            break
        time.sleep(2)

    (run_dir / "health.json").write_text(json.dumps(status, indent=2))
    return status


def mount_status(run_dir: Path) -> Dict[str, Any]:
    ms = {
        "handrail_sees_NSExternal": EXTERNAL.exists(),
        "ns_healthz": http_json(NS_HEALTHZ),
    }
    (run_dir / "mounts.json").write_text(json.dumps(ms, indent=2, default=str))
    return ms


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/v1/status")
def v1_status():
    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    rc_ps = run_compose(["ps"], cwd=WORKSPACE, out_path=run_dir / "compose_ps.txt")

    health = {
        "handrail": http_ok(SELF_HEALTHZ),
        "ns": http_ok(NS_HEALTHZ),
        "continuum": http_ok(CONT_STATE),
    }
    mounts = mount_status(run_dir)

    resp = {
        "ok": rc_ps == 0,
        "run_id": run_id,
        "compose_ps_rc": rc_ps,
        "health": health,
        "mounts": mounts,
        "run_dir": str(run_dir),
    }
    (RUNS_DIR / "latest").write_text(str(run_dir))
    return JSONResponse(resp)


@app.post("/v1/stack/stop")
def v1_stack_stop():
    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Do NOT stop handrail from inside handrail. Stop only ns + continuum.
    rc = run_compose(["stop", "ns", "continuum"], cwd=WORKSPACE, out_path=run_dir / "compose_stop.txt")

    resp = {
        "ok": rc == 0,
        "run_id": run_id,
        "rc": rc,
        "run_dir": str(run_dir),
    }
    (RUNS_DIR / "latest").write_text(str(run_dir))
    return JSONResponse(resp)


@app.post("/v1/boot/ez")
def v1_boot_ez(background_tasks: BackgroundTasks):
    """
    Boot EZ v1 (safe): restart ns + continuum only.
    Returns immediately; boot runs in background.
    """
    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "run_id": run_id,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "compose_file": str(COMPOSE_FILE),
        "workspace": str(WORKSPACE),
        "mode": "async",
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    run_compose(["ps"], cwd=WORKSPACE, out_path=run_dir / "compose_ps_before.txt")
    (run_dir / "queued.txt").write_text("queued\n")

    background_tasks.add_task(_boot_ez_worker, str(run_dir))

    (RUNS_DIR / "latest").write_text(str(run_dir))
    return JSONResponse({
        "accepted": True,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "note": "Boot queued. Check result.json/error.txt in run_dir."
    })



@app.post("/v1/run")
def v1_run(req: RunRequest):
    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    cwd = Path(req.cwd) if req.cwd else WORKSPACE
    meta = {
        "run_id": run_id,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(cwd),
        "cmd": req.cmd,
        "timeout_s": req.timeout_s,
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    try:
        p = subprocess.run(
            req.cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=req.timeout_s,
        )
        out = p.stdout
        rc = int(p.returncode)
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + "\n[TIMEOUT]\n" + (e.stderr or "")
        rc = 124
    except Exception as e:
        out = f"{type(e).__name__}: {e}\n"
        rc = 1

    (run_dir / "stdout.txt").write_text(out)

    resp = {
        "ok": rc == 0,
        "run_id": run_id,
        "rc": rc,
        "cwd": str(cwd),
        "cmd": req.cmd,
        "run_dir": str(run_dir),
    }
    (run_dir / "result.json").write_text(json.dumps(resp, indent=2))
    (RUNS_DIR / "latest").write_text(str(run_dir))
    return JSONResponse(resp)



@app.post("/v1/task")
def v1_task(req: TaskRequest):
    run_id = now_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "run_id": run_id,
        "task_type": req.task_type,
        "objective": req.objective,
        "payload": req.payload or {},
    }
    (run_dir / "task_request.json").write_text(json.dumps(meta, indent=2))

    task_resp = run_task(
        task_type=req.task_type,
        objective=req.objective,
        payload=req.payload,
        workspace=WORKSPACE,
        run_dir=run_dir,
    )

    resp = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        **task_resp,
    }

    (run_dir / "result.json").write_text(json.dumps(resp, indent=2))
    (RUNS_DIR / "latest").write_text(str(run_dir))

    if resp.get("ok"):
        return JSONResponse(resp)
    return JSONResponse(resp, status_code=400)

@app.get("/v1/runs/latest")
def v1_runs_latest():
    latest_file = RUNS_DIR / "latest"
    if latest_file.exists():
        p = latest_file.read_text().strip()
        return {"ok": True, "latest_run_dir": p}
    return {"ok": False, "latest_run_dir": None}





@app.get("/v1/run_summary")
def v1_run_summary(run_dir: str | None = None):
    latest_file = RUNS_DIR / "latest"
    target = Path(run_dir) if run_dir else Path(latest_file.read_text().strip())

    def read_json(name: str):
        p = target / name
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except Exception:
            return None

    def read_text(name: str):
        p = target / name
        if not p.exists():
            return None
        return p.read_text()

    result = read_json("result.json")
    task_request = read_json("task_request.json")
    stdout_txt = read_text("stdout.txt")

    boot_go_run_dir = None
    child_run_dir = None
    present_state_run_dir = None

    if isinstance(result, dict):
        boot_go_run_dir = result.get("boot_go_run_dir")
        child_run_dir = result.get("child_run_dir")
        present_state_run_dir = result.get("present_state_run_dir")

    child_result = None
    present_state_artifacts = None
    post_status = None

    if boot_go_run_dir:
        bg = Path(boot_go_run_dir)
        post_status_p = bg / "post_status.json"
        if post_status_p.exists():
            try:
                post_status = json.loads(post_status_p.read_text())
            except Exception:
                post_status = None

    if child_run_dir:
        cr = Path(child_run_dir)
        rp = cr / "result.json"
        if rp.exists():
            try:
                child_result = json.loads(rp.read_text())
            except Exception:
                child_result = None

    if present_state_run_dir:
        pr = Path(present_state_run_dir)
        present_state_artifacts = {
            "infra_boot_report": str(pr / "infra_boot_report.json") if (pr / "infra_boot_report.json").exists() else None,
            "present_state_kernel": str(pr / "present_state_kernel.json") if (pr / "present_state_kernel.json").exists() else None,
            "ancestry_graph": str(pr / "ancestry_graph.json") if (pr / "ancestry_graph.json").exists() else None,
            "coherence_report": str(pr / "coherence_report.json") if (pr / "coherence_report.json").exists() else None,
            "operating_frame": str(pr / "operating_frame.json") if (pr / "operating_frame.json").exists() else None,
            "execution_packet": str(pr / "execution_packet.json") if (pr / "execution_packet.json").exists() else None,
        }

    summary = {
        "ok": True,
        "queried_run_dir": str(target),
        "task_request": task_request,
        "task_result": result,
        "boot_go_run_dir": boot_go_run_dir,
        "child_run_dir": child_run_dir,
        "present_state_run_dir": present_state_run_dir,
        "post_status": post_status,
        "child_result": child_result,
        "present_state_artifacts": present_state_artifacts,
        "stdout_preview": stdout_txt[:2000] if stdout_txt else None,
    }
    return JSONResponse(summary)

@app.get("/v1/runs/get")
def v1_runs_get(run_dir: str | None = None):
    target = Path(run_dir) if run_dir else None

    if target is None:
        latest_file = RUNS_DIR / "latest"
        if not latest_file.exists():
            return JSONResponse({"ok": False, "error": "no latest run"}, status_code=404)
        target = Path(latest_file.read_text().strip())

    if not target.exists():
        return JSONResponse({"ok": False, "error": "run_dir not found", "run_dir": str(target)}, status_code=404)

    def read_text(name: str):
        fp = target / name
        if fp.exists():
            return fp.read_text(errors="replace")
        return None

    payload = {
        "ok": True,
        "run_dir": str(target),
        "meta_json": read_text("meta.json"),
        "result_json": read_text("result.json"),
        "error_txt": read_text("error.txt"),
        "stdout_txt": read_text("stdout.txt"),
        "stderr_txt": read_text("stderr.txt"),
        "compose_ps_txt": read_text("compose_ps.txt"),
        "compose_ps_before_txt": read_text("compose_ps_before.txt"),
        "compose_ps_after_txt": read_text("compose_ps_after.txt"),
        "compose_up_ns_continuum_txt": read_text("compose_up_ns_continuum.txt"),
        "health_json": read_text("health.json"),
        "mounts_json": read_text("mounts.json"),
        "queued_txt": read_text("queued.txt"),
    }
    return JSONResponse(payload)

@app.get("/ui", response_class=HTMLResponse)
def ui():
    # single-file UI, no build step
    return HTMLResponse(
        """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Handrail UI</title>
  <style>
    body { font-family: -apple-system, system-ui, sans-serif; margin: 16px; }
    button { margin-right: 8px; padding: 10px 12px; }
    pre { background: #f5f5f5; padding: 12px; overflow: auto; }
    .row { margin: 10px 0; }
    .ok { color: #0a0; }
    .bad { color: #a00; }
    code { background: #eee; padding: 2px 4px; }
  </style>
</head>
<body>
  <h2>Handrail Control Surface</h2>

  <div class="row">
    <button onclick="bootEz()">Boot EZ (ns+continuum)</button>
    <button onclick="status()">Status</button>
    <button onclick="stopStack()">Stop (ns+continuum)</button>
    <button onclick="latest()">Latest Run</button>
  </div>

  <div class="row" id="summary"></div>
  <pre id="out">(no output yet)</pre>

<script>
async function call(method, path) {
  const res = await fetch(path, { method });
  const text = await res.text();
  try { return JSON.parse(text); } catch { return { raw: text }; }
}
function setOut(obj) {
  document.getElementById('out').textContent = JSON.stringify(obj, null, 2);
  if (obj && obj.run_dir) {
    document.getElementById('summary').innerHTML =
      'run_id: <code>' + (obj.run_id || '') + '</code> ' +
      'run_dir: <code>' + obj.run_dir + '</code>';
  } else if (obj && obj.latest_run_dir) {
    document.getElementById('summary').innerHTML =
      'latest_run_dir: <code>' + obj.latest_run_dir + '</code>';
  } else {
    document.getElementById('summary').textContent = '';
  }
}
async function bootEz(){ setOut(await call('POST','/v1/boot/ez')); }
async function status(){ setOut(await call('GET','/v1/status')); }
async function stopStack(){ setOut(await call('POST','/v1/stack/stop')); }
async function latest(){ setOut(await call('GET','/v1/runs/latest')); }
</script>
</body>
</html>
        """.strip()
    )
