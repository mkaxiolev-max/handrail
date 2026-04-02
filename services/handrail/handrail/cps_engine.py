# Copyright © 2026 Axiolev. All rights reserved.
"""
Handrail CPS Engine — Phase 1
Normalized result shape, external policy profiles, expect validation,
metrics, artifact manifest, docker.compose_up support.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

POLICY_DIR = Path(__file__).parent / "policy"

BUILTIN_POLICIES: dict[str, dict] = {
    "readonly.local": {
        "name": "readonly.local",
        "allowed_paths": ["/Volumes/NSExternal", "/workspace", "/tmp", "/var/tmp"],
        "allowed_programs": ["pwd", "ls", "cat", "tail", "head", "wc", "find", "git", "curl"],
        "allow_mutation": False,
    },
    "repo.inspect": {
        "name": "repo.inspect",
        "allowed_paths": ["/workspace", "/Volumes/NSExternal", "/tmp"],
        "allowed_programs": ["git", "pwd", "ls", "cat", "curl"],
        "allow_mutation": False,
    },
    "boot.runtime": {
        "name": "boot.runtime",
        "allowed_paths": ["/workspace", "/Volumes/NSExternal", "/tmp", "/var/tmp"],
        "allowed_programs": ["docker", "curl", "python3", "bash", "sh", "git", "pwd", "ls", "cat"],
        "allow_mutation": True,
    },
    "default": {
        "name": "default",
        "allowed_paths": ["/workspace", "/tmp"],
        "allowed_programs": ["pwd", "ls", "cat", "git", "curl"],
        "allow_mutation": False,
    },
    "founder": {
        "name": "founder",
        "allowed_paths": ["/workspace", "/Volumes/NSExternal", "/tmp", "/var/tmp"],
        "allowed_programs": ["docker", "curl", "python3", "bash", "sh", "git", "pwd", "ls", "cat"],
        "allow_mutation": True,
        "founder_only": True,
    },
}


def load_policy(profile_name: str | None) -> dict:
    name = profile_name or "default"
    # Try external file first
    external = POLICY_DIR / f"{name}.json"
    if external.exists():
        return json.loads(external.read_text())
    # Fall back to builtin
    if name in BUILTIN_POLICIES:
        return BUILTIN_POLICIES[name]
    raise ValueError(f"Unknown policy profile: {name!r}")


class PolicyEngine:
    def __init__(self, profile: dict):
        self.profile = profile

    def check_path(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.profile.get("allowed_paths", []))

    def check_program(self, program: str) -> bool:
        return program in self.profile.get("allowed_programs", [])

    def allow_mutation(self) -> bool:
        return bool(self.profile.get("allow_mutation", False))


# ---------------------------------------------------------------------------
# Digest helpers
# ---------------------------------------------------------------------------

def _sha256(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return "sha256:" + h.hexdigest()


# ---------------------------------------------------------------------------
# Op handlers
# ---------------------------------------------------------------------------

def _op_fs_pwd(_args: dict, _policy: PolicyEngine) -> dict:
    import os
    return {"cwd": os.getcwd()}


def _op_fs_list(args: dict, policy: PolicyEngine) -> dict:
    path = args.get("path", ".")
    if not policy.check_path(str(Path(path).resolve())):
        raise PermissionError(f"Path not allowed: {path}")
    entries = sorted(Path(path).iterdir(), key=lambda p: p.name)
    return {"entries": [{"name": e.name, "type": "dir" if e.is_dir() else "file"} for e in entries]}


def _op_fs_read(args: dict, policy: PolicyEngine) -> dict:
    path = args.get("path", "")
    if not policy.check_path(str(Path(path).resolve())):
        raise PermissionError(f"Path not allowed: {path}")
    content = Path(path).read_text()
    return {"content": content, "size": len(content)}


def _op_git_status(args: dict, _policy: PolicyEngine) -> dict:
    repo = args.get("repo", "/workspace")
    result = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, timeout=10)
    return {"output": result.stdout, "clean": result.stdout.strip() == "", "returncode": result.returncode}


def _op_git_log(args: dict, _policy: PolicyEngine) -> dict:
    repo = args.get("repo", "/workspace")
    limit = args.get("limit", 5)
    oneline = args.get("oneline", True)
    fmt = "--oneline" if oneline else "--format=%H %s"
    result = subprocess.run(["git", "-C", repo, "log", fmt, f"-{limit}"], capture_output=True, text=True, timeout=10)
    return {"output": result.stdout.strip(), "returncode": result.returncode}


def _op_docker_compose_ps(args: dict, policy: PolicyEngine) -> dict:
    if not policy.check_program("docker"):
        raise PermissionError("docker not in allowed programs")
    project_dir = args.get("project_dir", "/workspace")
    result = subprocess.run(
        ["docker", "compose", "-f", f"{project_dir}/docker-compose.yml", "ps", "--format", "json"],
        capture_output=True, text=True, timeout=15,
    )
    try:
        services = json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        services = result.stdout.strip()
    return {"services": services, "returncode": result.returncode}


def _op_docker_compose_up(args: dict, policy: PolicyEngine) -> dict:
    if not policy.check_program("docker"):
        raise PermissionError("docker not in allowed programs")
    if not policy.allow_mutation():
        raise PermissionError("Policy does not allow mutation (compose up)")
    project_dir = args.get("project_dir", "/workspace")
    detached = args.get("detached", True)
    build = args.get("build", False)
    cmd = ["docker", "compose", "-f", f"{project_dir}/docker-compose.yml", "up"]
    if detached:
        cmd.append("-d")
    if build:
        cmd.append("--build")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return {"returncode": result.returncode, "stdout": result.stdout[-500:], "stderr": result.stderr[-500:]}


def _op_http_get(args: dict, _policy: PolicyEngine) -> dict:
    url = args.get("url", "")
    timeout_ms = args.get("timeout_ms", 5000)
    try:
        resp = httpx.get(url, timeout=timeout_ms / 1000)
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:500]
        return {"status_code": resp.status_code, "body": body}
    except httpx.TimeoutException:
        raise TimeoutError(f"GET {url} timed out after {timeout_ms}ms")
    except Exception as e:
        raise RuntimeError(f"GET {url} failed: {e}")


def _op_proc_run_readonly(args: dict, policy: PolicyEngine) -> dict:
    # Accepts either cmd (list) or command (str)
    cmd = args.get("cmd") or args.get("command")
    if not cmd:
        raise ValueError("proc.run_readonly requires cmd list or command string")
    if isinstance(cmd, str):
        cmd = cmd.split()
    program = cmd[0].split("/")[-1]
    if not policy.check_program(program):
        raise PermissionError(f"Program not allowed: {program}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def _op_proc_run(args: dict, policy: PolicyEngine) -> dict:
    cmd = args.get("cmd", [])
    if not cmd:
        raise ValueError("proc.run_allowed requires cmd list")
    program = cmd[0].split("/")[-1]
    if not policy.check_program(program):
        raise PermissionError(f"Program not allowed: {program}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def _op_git_diff(args: dict, _policy: PolicyEngine) -> dict:
    repo = args.get("repo", "/workspace")
    ref = args.get("ref", "HEAD")
    result = subprocess.run(["git", "-C", repo, "diff", ref, "--stat"], capture_output=True, text=True, timeout=10)
    return {"output": result.stdout.strip(), "returncode": result.returncode}


def _op_git_commit(args: dict, policy: PolicyEngine) -> dict:
    if not policy.allow_mutation():
        raise PermissionError("Policy does not allow mutation (git.commit)")
    repo = args.get("repo", "/workspace")
    message = args.get("message", "")
    if not message:
        raise ValueError("git.commit requires message")
    result = subprocess.run(["git", "-C", repo, "commit", "-m", message], capture_output=True, text=True, timeout=15)
    return {"output": result.stdout.strip(), "returncode": result.returncode, "stderr": result.stderr.strip()}


def _op_http_post(args: dict, _policy: PolicyEngine) -> dict:
    url = args.get("url", "")
    body = args.get("body", {})
    timeout_ms = args.get("timeout_ms", 5000)
    try:
        resp = httpx.post(url, json=body, timeout=timeout_ms / 1000)
        try:
            resp_body = resp.json()
        except Exception:
            resp_body = resp.text[:500]
        return {"status_code": resp.status_code, "body": resp_body}
    except httpx.TimeoutException:
        raise TimeoutError(f"POST {url} timed out after {timeout_ms}ms")
    except Exception as e:
        raise RuntimeError(f"POST {url} failed: {e}")


def _op_http_health_check(args: dict, _policy: PolicyEngine) -> dict:
    url = args.get("url", "")
    timeout_ms = args.get("timeout_ms", 3000)
    expect_status = args.get("expect_status", 200)
    try:
        resp = httpx.get(url, timeout=timeout_ms / 1000)
        return {"status_code": resp.status_code, "healthy": resp.status_code == expect_status, "url": url}
    except Exception as e:
        return {"status_code": None, "healthy": False, "url": url, "error": str(e)}


_SYS_ENV_ALLOWLIST = {
    "ANTHROPIC_API_KEY", "YUBIKEY_CLIENT_ID", "FOUNDER_PHONE", "NS_URL",
    "HANDRAIL_URL", "CONTINUUM_URL", "TWILIO_ACCOUNT_SID", "NODE_ENV",
    "HR_WORKSPACE", "STRIPE_WEBHOOK_SECRET", "SLACK_WEBHOOK_URL",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "FOUNDER_EMAIL",
    "STRIPE_SECRET_KEY",
}

def _op_sys_env_get(args: dict, _policy: PolicyEngine) -> dict:
    import os
    key = args.get("key", "")
    if key not in _SYS_ENV_ALLOWLIST:
        raise PermissionError(f"env var not in allowlist: {key}")
    val = os.environ.get(key)
    return {"key": key, "set": val is not None, "value": "***" if val else None}


def _op_sys_disk_usage(args: dict, _policy: PolicyEngine) -> dict:
    import shutil
    path = args.get("path", "/")
    total, used, free = shutil.disk_usage(path)
    return {
        "path": path,
        "total_gb": round(total / 1e9, 2),
        "used_gb": round(used / 1e9, 2),
        "free_gb": round(free / 1e9, 2),
        "used_pct": round(used / total * 100, 1),
    }


def _op_sys_uptime(args: dict, _policy: PolicyEngine) -> dict:
    try:
        raw = Path("/proc/uptime").read_text().split()
        uptime_s = float(raw[0])
        idle_s = float(raw[1]) if len(raw) > 1 else None
        return {"uptime_s": uptime_s, "idle_s": idle_s, "source": "/proc/uptime"}
    except Exception:
        result = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
        return {"uptime": result.stdout.strip(), "returncode": result.returncode, "source": "uptime"}


# ---------------------------------------------------------------------------
# Slack adapter
# ---------------------------------------------------------------------------

def _op_slack_post_message(args: dict, _policy: PolicyEngine) -> dict:
    import os
    url = args.get("webhook_url") or os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        raise ValueError("slack.post_message requires webhook_url arg or SLACK_WEBHOOK_URL env var")
    text = args.get("text", "")
    blocks = args.get("blocks")
    payload: dict = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    try:
        resp = httpx.post(url, json=payload, timeout=5)
        return {"status_code": resp.status_code, "ok": resp.status_code == 200, "response": resp.text[:200]}
    except Exception as e:
        raise RuntimeError(f"slack.post_message failed: {e}")


def _op_slack_notify(args: dict, policy: PolicyEngine) -> dict:
    import os
    url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        return {"ok": False, "skipped": True, "reason": "SLACK_WEBHOOK_URL not configured"}
    return _op_slack_post_message({"webhook_url": url, "text": args.get("text", "NS∞ notification")}, policy)


# ---------------------------------------------------------------------------
# Email adapter
# ---------------------------------------------------------------------------

def _op_email_send(args: dict, _policy: PolicyEngine) -> dict:
    import os, smtplib
    from email.message import EmailMessage
    host = args.get("smtp_host") or os.environ.get("SMTP_HOST", "")
    port = int(args.get("smtp_port") or os.environ.get("SMTP_PORT", 587))
    user = args.get("smtp_user") or os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    to_addr = args.get("to", "")
    subject = args.get("subject", "NS∞ Notification")
    body = args.get("body", "")
    if not host or not to_addr:
        return {"ok": False, "skipped": True, "reason": "smtp_host and to required"}
    try:
        msg = EmailMessage()
        msg["From"] = user
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            if user and password:
                s.login(user, password)
            s.send_message(msg)
        return {"ok": True, "to": to_addr, "subject": subject}
    except Exception as e:
        raise RuntimeError(f"email.send failed: {e}")


def _op_email_notify(args: dict, policy: PolicyEngine) -> dict:
    import os
    to_addr = os.environ.get("FOUNDER_EMAIL", "")
    if not to_addr:
        return {"ok": False, "skipped": True, "reason": "FOUNDER_EMAIL not configured"}
    return _op_email_send({**args, "to": to_addr}, policy)


# ---------------------------------------------------------------------------
# Stripe adapter
# ---------------------------------------------------------------------------

def _stripe_get(path: str) -> dict:
    import os, base64
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        return {"ok": False, "error": "STRIPE_SECRET_KEY not configured"}
    token = base64.b64encode(f"{key}:".encode()).decode()
    try:
        resp = httpx.get(f"https://api.stripe.com/v1{path}",
                         headers={"Authorization": f"Basic {token}"}, timeout=10)
        return {"ok": resp.status_code == 200, "status_code": resp.status_code, "data": resp.json()}
    except Exception as e:
        raise RuntimeError(f"Stripe GET {path} failed: {e}")


def _op_stripe_get_balance(args: dict, _policy: PolicyEngine) -> dict:
    result = _stripe_get("/balance")
    if result.get("ok") and "data" in result:
        d = result["data"]
        result["available"] = d.get("available", [])
        result["pending"] = d.get("pending", [])
    return result


def _op_stripe_list_customers(args: dict, _policy: PolicyEngine) -> dict:
    limit = args.get("limit", 10)
    result = _stripe_get(f"/customers?limit={limit}")
    if result.get("ok") and "data" in result:
        result["count"] = len(result["data"].get("data", []))
    return result


def _op_stripe_list_payments(args: dict, _policy: PolicyEngine) -> dict:
    limit = args.get("limit", 10)
    result = _stripe_get(f"/payment_intents?limit={limit}")
    if result.get("ok") and "data" in result:
        result["count"] = len(result["data"].get("data", []))
    return result


# ---------------------------------------------------------------------------
# Schedule adapter
# ---------------------------------------------------------------------------

_SCHEDULE_DIR = Path("/Volumes/NSExternal/ALEXANDRIA/scheduled")
_SCHEDULE_DIR_FALLBACK = Path.home() / "ALEXANDRIA" / "scheduled"

def _sched_dir() -> Path:
    d = _SCHEDULE_DIR if Path("/Volumes/NSExternal/ALEXANDRIA").exists() else _SCHEDULE_DIR_FALLBACK
    d.mkdir(parents=True, exist_ok=True)
    return d


def _op_schedule_run_at(args: dict, _policy: PolicyEngine) -> dict:
    plan_id = args.get("plan_id", "")
    run_at = args.get("run_at", "")  # ISO8601
    plan = args.get("plan", {})
    if not plan_id or not run_at:
        raise ValueError("schedule.run_at requires plan_id and run_at (ISO8601)")
    entry = {"plan_id": plan_id, "run_at": run_at, "plan": plan,
             "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    dest = _sched_dir() / f"{plan_id}.json"
    dest.write_text(json.dumps(entry, indent=2))
    return {"ok": True, "plan_id": plan_id, "run_at": run_at, "path": str(dest)}


def _op_schedule_list(args: dict, _policy: PolicyEngine) -> dict:
    d = _sched_dir()
    plans = []
    for f in sorted(d.glob("*.json")):
        try:
            entry = json.loads(f.read_text())
            plans.append({"plan_id": entry.get("plan_id"), "run_at": entry.get("run_at"),
                          "created_at": entry.get("created_at")})
        except Exception:
            pass
    return {"ok": True, "count": len(plans), "plans": plans}


def _op_schedule_cancel(args: dict, _policy: PolicyEngine) -> dict:
    plan_id = args.get("plan_id", "")
    if not plan_id:
        raise ValueError("schedule.cancel requires plan_id")
    dest = _sched_dir() / f"{plan_id}.json"
    if dest.exists():
        dest.unlink()
        return {"ok": True, "cancelled": plan_id}
    return {"ok": False, "error": f"plan not found: {plan_id}"}


# ---------------------------------------------------------------------------
# NS comms adapter (Phase 6 — M1 Founder MVP)
# ---------------------------------------------------------------------------

_NS_URL = None

def _get_ns_url() -> str:
    import os
    global _NS_URL
    if _NS_URL is None:
        _NS_URL = os.environ.get("NS_URL", "http://ns:9000")
    return _NS_URL


def _op_ns_sms_send(args: dict, _policy: PolicyEngine) -> dict:
    import os
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN", "")
    from_number = args.get("from_number") or os.environ.get("TWILIO_PHONE_NUMBER", "")
    to_number   = args.get("to", "")
    body        = args.get("body", "")
    if not account_sid or not auth_token:
        return {"ok": False, "skipped": True, "reason": "Twilio credentials not configured"}
    if not to_number or not body:
        raise ValueError("ns.sms_send requires to and body")
    try:
        resp = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            data={"To": to_number, "From": from_number, "Body": body},
            auth=(account_sid, auth_token), timeout=10,
        )
        return {"ok": resp.status_code == 201, "status_code": resp.status_code,
                "sid": resp.json().get("sid")}
    except Exception as e:
        raise RuntimeError(f"ns.sms_send failed: {e}")


def _op_ns_voice_call(args: dict, _policy: PolicyEngine) -> dict:
    import os
    account_sid  = os.environ.get("TWILIO_ACCOUNT_SID", "")
    auth_token   = os.environ.get("TWILIO_AUTH_TOKEN", "")
    from_number  = args.get("from_number") or os.environ.get("TWILIO_PHONE_NUMBER", "")
    to_number    = args.get("to", "")
    webhook_base = args.get("webhook_base") or os.environ.get("NORTHSTAR_WEBHOOK_BASE", "")
    twiml_body   = args.get("twiml", "<Response><Say>NS calling.</Say></Response>")
    url          = args.get("url") or (f"{webhook_base}/voice/inbound" if webhook_base else "")
    if not account_sid or not auth_token:
        return {"ok": False, "skipped": True, "reason": "Twilio credentials not configured"}
    if not to_number:
        raise ValueError("ns.voice_call requires to")
    try:
        data: dict = {"To": to_number, "From": from_number}
        if url:
            data["Url"] = url
        else:
            data["Twiml"] = twiml_body
        resp = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json",
            data=data, auth=(account_sid, auth_token), timeout=10,
        )
        return {"ok": resp.status_code == 201, "status_code": resp.status_code,
                "sid": resp.json().get("sid")}
    except Exception as e:
        raise RuntimeError(f"ns.voice_call failed: {e}")


def _op_ns_memory_query(args: dict, _policy: PolicyEngine) -> dict:
    q = args.get("q", "")
    n = args.get("n", 20)
    if not q:
        raise ValueError("ns.memory_query requires q")
    try:
        resp = httpx.get(f"{_get_ns_url()}/memory/search", params={"q": q, "n": n}, timeout=10)
        result = resp.json()
        return {"ok": resp.status_code == 200, "status_code": resp.status_code, **result}
    except Exception as e:
        raise RuntimeError(f"ns.memory_query failed: {e}")


def _op_ns_memory_recent(args: dict, _policy: PolicyEngine) -> dict:
    n = args.get("n", 10)
    try:
        resp = httpx.get(f"{_get_ns_url()}/memory/recent", params={"n": n}, timeout=10)
        result = resp.json()
        return {"ok": resp.status_code == 200, "status_code": resp.status_code, **result}
    except Exception as e:
        raise RuntimeError(f"ns.memory_recent failed: {e}")


def _op_ns_broadcast(args: dict, policy: PolicyEngine) -> dict:
    import os
    text = args.get("text", "")
    if not text:
        raise ValueError("ns.broadcast requires text")
    results: dict = {}
    to_number = args.get("to") or os.environ.get("FOUNDER_PHONE", "")
    if to_number:
        try:
            results["sms"] = _op_ns_sms_send({"to": to_number, "body": text}, policy)
        except Exception as e:
            results["sms"] = {"ok": False, "error": str(e)}
    try:
        resp = httpx.post(f"{_get_ns_url()}/chat/quick",
                          json={"text": f"[broadcast] {text}"}, timeout=5)
        results["console"] = {"ok": resp.status_code == 200}
    except Exception as e:
        results["console"] = {"ok": False, "error": str(e)}
    return {"ok": True, "channels": results, "text": text}


# ---------------------------------------------------------------------------
# Program Library v1 — 10 namespaces, 68 ops + 5 meta-contract ops
# ---------------------------------------------------------------------------

_PROG_SSD = Path("/Volumes/NSExternal/ALEXANDRIA/programs")
_PROG_FALLBACK = Path.home() / ".axiolev" / "programs"

def _prog_base() -> Path:
    return _PROG_SSD if Path("/Volumes/NSExternal/ALEXANDRIA").exists() else _PROG_FALLBACK

def _prog_path(namespace: str, instance_id: str) -> Path:
    d = _prog_base() / namespace
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{instance_id}.jsonl"

def _prog_write(namespace: str, instance_id: str, action: str, state: str, meta: dict | None = None) -> dict:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = {"program_id": instance_id, "namespace": namespace, "action": action,
             "state": state, "ts": ts, **(meta or {})}
    p = _prog_path(namespace, instance_id)
    with p.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"ok": True, "program_id": instance_id, "namespace": namespace,
            "state": state, "action": action, "ts": ts}

def _require_founder_policy(policy: PolicyEngine, op_name: str) -> None:
    if policy.profile.get("name") != "founder":
        raise PermissionError(f"{op_name} requires policy_profile: founder")

def _prog_op(namespace: str, action: str, args: dict, policy: PolicyEngine,
             require_founder: bool = False, require_arg: str | None = None,
             require_confirmed: bool = False) -> dict:
    if require_founder:
        _require_founder_policy(policy, f"{namespace}.{action}")
    if require_arg and not args.get(require_arg):
        raise ValueError(f"{namespace}.{action} requires args.{require_arg}")
    if require_confirmed and not args.get("confirmed"):
        raise ValueError(f"{namespace}.{action} requires args.confirmed: true")
    program_id = args.get("program_id") or args.get("instance_id") or f"{namespace}_default"
    state = args.get("next_state") or args.get("state") or action
    meta = {k: v for k, v in args.items() if k not in ("program_id", "instance_id", "state", "next_state")}
    return _prog_write(namespace, program_id, action, state, meta)

def _make_prog_op(namespace: str, action: str, **kwargs):
    def _handler(args: dict, policy: PolicyEngine) -> dict:
        return _prog_op(namespace, action, args, policy, **kwargs)
    _handler.__name__ = f"_op_{namespace}_{action}"
    return _handler

_FUNDRAISING_OPS: dict[str, Any] = {
    "fundraising.advance_state":      _make_prog_op("fundraising", "advance_state"),
    "fundraising.add_target":         _make_prog_op("fundraising", "add_target"),
    "fundraising.score_fit":          _make_prog_op("fundraising", "score_fit"),
    "fundraising.attach_material":    _make_prog_op("fundraising", "attach_material"),
    "fundraising.log_diligence":      _make_prog_op("fundraising", "log_diligence"),
    "fundraising.record_term_signal": _make_prog_op("fundraising", "record_term_signal"),
    "fundraising.request_approval":   _make_prog_op("fundraising", "request_approval"),
}
_HIRING_OPS: dict[str, Any] = {
    "hiring.create_role":        _make_prog_op("hiring", "create_role"),
    "hiring.add_candidate":      _make_prog_op("hiring", "add_candidate"),
    "hiring.score_candidate":    _make_prog_op("hiring", "score_candidate"),
    "hiring.advance_state":      _make_prog_op("hiring", "advance_state"),
    "hiring.capture_feedback":   _make_prog_op("hiring", "capture_feedback"),
    "hiring.prepare_offer":      _make_prog_op("hiring", "prepare_offer"),
    "hiring.start_onboarding":   _make_prog_op("hiring", "start_onboarding"),
}
_PARTNER_OPS: dict[str, Any] = {
    "partner.add_target":        _make_prog_op("partner", "add_target"),
    "partner.score_fit":         _make_prog_op("partner", "score_fit"),
    "partner.map_incentives":    _make_prog_op("partner", "map_incentives"),
    "partner.advance_state":     _make_prog_op("partner", "advance_state"),
    "partner.prepare_brief":     _make_prog_op("partner", "prepare_brief"),
    "partner.launch_pilot":      _make_prog_op("partner", "launch_pilot"),
    "partner.track_activation":  _make_prog_op("partner", "track_activation"),
}
_MA_OPS: dict[str, Any] = {
    "ma.add_target":        _make_prog_op("ma", "add_target"),
    "ma.score_target":      _make_prog_op("ma", "score_target"),
    "ma.advance_state":     _make_prog_op("ma", "advance_state"),
    "ma.request_diligence": _make_prog_op("ma", "request_diligence"),
    "ma.attach_loi":        _make_prog_op("ma", "attach_loi"),
    "ma.track_red_flags":   _make_prog_op("ma", "track_red_flags"),
    "ma.close_transaction": _make_prog_op("ma", "close_transaction", require_arg="approval_ref"),
}
_ADVISOR_OPS: dict[str, Any] = {
    "advisor.add_candidate":        _make_prog_op("advisor", "add_candidate"),
    "advisor.score_signal":         _make_prog_op("advisor", "score_signal"),
    "advisor.activate":             _make_prog_op("advisor", "activate"),
    "advisor.assign_mission":       _make_prog_op("advisor", "assign_mission"),
    "advisor.log_touchpoint":       _make_prog_op("advisor", "log_touchpoint"),
    "advisor.review_effectiveness": _make_prog_op("advisor", "review_effectiveness"),
}
_CS_OPS: dict[str, Any] = {
    "cs.start_kickoff":     _make_prog_op("cs", "start_kickoff"),
    "cs.assign_owner":      _make_prog_op("cs", "assign_owner"),
    "cs.track_activation":  _make_prog_op("cs", "track_activation"),
    "cs.log_health_score":  _make_prog_op("cs", "log_health_score"),
    "cs.flag_risk":         _make_prog_op("cs", "flag_risk"),
    "cs.prepare_renewal":   _make_prog_op("cs", "prepare_renewal"),
    "cs.request_reference": _make_prog_op("cs", "request_reference"),
}
_FEEDBACK_OPS: dict[str, Any] = {
    "feedback.capture":         _make_prog_op("feedback", "capture"),
    "feedback.normalize":       _make_prog_op("feedback", "normalize"),
    "feedback.cluster":         _make_prog_op("feedback", "cluster"),
    "feedback.score_impact":    _make_prog_op("feedback", "score_impact"),
    "feedback.route_to_team":   _make_prog_op("feedback", "route_to_team"),
    "feedback.link_to_roadmap": _make_prog_op("feedback", "link_to_roadmap"),
    "feedback.close_loop":      _make_prog_op("feedback", "close_loop"),
}
_GOV_OPS: dict[str, Any] = {
    "gov.submit_proposal":    _make_prog_op("gov", "submit_proposal"),
    "gov.classify_risk":      _make_prog_op("gov", "classify_risk"),
    "gov.request_review":     _make_prog_op("gov", "request_review"),
    "gov.record_decision":    _make_prog_op("gov", "record_decision",   require_founder=True),
    "gov.issue_constraint":   _make_prog_op("gov", "issue_constraint",  require_founder=True),
    "gov.audit_change":       _make_prog_op("gov", "audit_change"),
    "gov.rollback_if_needed": _make_prog_op("gov", "rollback_if_needed"),
}
_KNOWLEDGE_OPS: dict[str, Any] = {
    "knowledge.ingest":            _make_prog_op("knowledge", "ingest"),
    "knowledge.parse":             _make_prog_op("knowledge", "parse"),
    "knowledge.extract_entities":  _make_prog_op("knowledge", "extract_entities"),
    "knowledge.validate":          _make_prog_op("knowledge", "validate"),
    "knowledge.classify":          _make_prog_op("knowledge", "classify"),
    "knowledge.store":             _make_prog_op("knowledge", "store"),
    "knowledge.link":              _make_prog_op("knowledge", "link"),
    "knowledge.promote_to_canon":  _make_prog_op("knowledge", "promote_to_canon", require_confirmed=True),
}

def _op_program_advance_state(args: dict, policy: PolicyEngine) -> dict:
    ns = args.get("namespace", "")
    if not ns:
        raise ValueError("program.advance_state requires namespace")
    return _prog_op(ns, "advance_state", args, policy)

def _op_program_flag_risk(args: dict, policy: PolicyEngine) -> dict:
    ns = args.get("namespace", "")
    if not ns:
        raise ValueError("program.flag_risk requires namespace")
    return _prog_op(ns, "flag_risk", args, policy)

def _op_program_request_approval(args: dict, policy: PolicyEngine) -> dict:
    ns = args.get("namespace", "")
    if not ns:
        raise ValueError("program.request_approval requires namespace")
    return _prog_op(ns, "request_approval", args, policy)

def _op_program_log_receipt(args: dict, policy: PolicyEngine) -> dict:
    ns = args.get("namespace", "")
    if not ns:
        raise ValueError("program.log_receipt requires namespace")
    return _prog_op(ns, "log_receipt", args, policy)

def _op_program_archive(args: dict, policy: PolicyEngine) -> dict:
    ns = args.get("namespace", "")
    if not ns:
        raise ValueError("program.archive requires namespace")
    return _prog_op(ns, "archive", {**args, "next_state": "archived"}, policy)

_META_OPS: dict[str, Any] = {
    "program.advance_state":    _op_program_advance_state,
    "program.flag_risk":        _op_program_flag_risk,
    "program.request_approval": _op_program_request_approval,
    "program.log_receipt":      _op_program_log_receipt,
    "program.archive":          _op_program_archive,
}

# ---------------------------------------------------------------------------
# Failure event writer (Block 3B — failure classification)
# ---------------------------------------------------------------------------

_FAILURE_LOG_SSD  = Path("/Volumes/NSExternal/ALEXANDRIA/ledger/failure_events.jsonl")
_FAILURE_LOG_FALLBACK = Path.home() / "ALEXANDRIA" / "ledger" / "failure_events.jsonl"

def _failure_log_path() -> Path:
    if Path("/Volumes/NSExternal/ALEXANDRIA/ledger").exists():
        return _FAILURE_LOG_SSD
    p = _FAILURE_LOG_FALLBACK
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _write_failure_event(op_name: str, failure_class: str, severity: str,
                          strategy: str, details: str) -> None:
    entry = {"op": op_name, "failure_class": failure_class, "severity": severity,
             "strategy": strategy, "details": details[:500],
             "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        with _failure_log_path().open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Don't let failure logging break execution

# ---------------------------------------------------------------------------
# OP_DISPATCH
# ---------------------------------------------------------------------------

OP_DISPATCH: dict[str, Any] = {
    "fs.pwd": _op_fs_pwd,
    "fs.list": _op_fs_list,
    "fs.read": _op_fs_read,
    "git.status": _op_git_status,
    "git.log": _op_git_log,
    "git.diff": _op_git_diff,
    "git.commit": _op_git_commit,
    "proc.run_readonly": _op_proc_run_readonly,
    "docker.compose_ps": _op_docker_compose_ps,
    "docker.compose_up": _op_docker_compose_up,
    "http.get": _op_http_get,
    "http.post": _op_http_post,
    "http.health_check": _op_http_health_check,
    "proc.run_allowed": _op_proc_run,
    "sys.env_get": _op_sys_env_get,
    "sys.disk_usage": _op_sys_disk_usage,
    "sys.uptime": _op_sys_uptime,
    "slack.post_message": _op_slack_post_message,
    "slack.notify": _op_slack_notify,
    "email.send": _op_email_send,
    "email.notify": _op_email_notify,
    "stripe.get_balance": _op_stripe_get_balance,
    "stripe.list_customers": _op_stripe_list_customers,
    "stripe.list_payments": _op_stripe_list_payments,
    "schedule.run_at": _op_schedule_run_at,
    "schedule.list": _op_schedule_list,
    "schedule.cancel": _op_schedule_cancel,
    # NS comms
    "ns.sms_send": _op_ns_sms_send,
    "ns.voice_call": _op_ns_voice_call,
    "ns.memory_query": _op_ns_memory_query,
    "ns.memory_recent": _op_ns_memory_recent,
    "ns.broadcast": _op_ns_broadcast,
    # Program Library v1 — 10 namespaces (68 ops + 5 meta)
    **_FUNDRAISING_OPS,
    **_HIRING_OPS,
    **_PARTNER_OPS,
    **_MA_OPS,
    **_ADVISOR_OPS,
    **_CS_OPS,
    **_FEEDBACK_OPS,
    **_GOV_OPS,
    **_KNOWLEDGE_OPS,
    **_META_OPS,
}


# ---------------------------------------------------------------------------
# Expect validation
# ---------------------------------------------------------------------------

def _resolve_path(obj: Any, path: str) -> Any:
    """Resolve dot-bracket path like results[1].data.status_code"""
    import re
    parts = re.split(r"\.|\[(\d+)\]", path)
    cur = obj
    for part in parts:
        if part is None or part == "":
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            cur = cur[part]
        else:
            raise KeyError(f"Cannot traverse into {type(cur)} at {part!r}")
    return cur


def _validate_expect(results: list, expect: dict) -> dict:
    failures = []
    for path, expected in expect.items():
        try:
            actual = _resolve_path({"results": results}, path)
            if actual != expected:
                failures.append({"path": path, "expected": expected, "actual": actual})
        except Exception as e:
            failures.append({"path": path, "expected": expected, "actual": f"ERROR: {e}"})
    return {"passed": len(failures) == 0, "failures": failures}


# ---------------------------------------------------------------------------
# Main executor
# ---------------------------------------------------------------------------


READONLY_ALLOWLIST = {
    "pwd": ["pwd"],
    "ls": ["ls"],
    "git_status": ["git", "status", "--short", "--branch"],
    "git_log": ["git", "log", "--oneline", "-5"],
    "pytest_smoke": ["pytest", "-q", "tests"],
    "docker_ps": ["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"],
    "recent_handrail_logs": ["sh", "-lc", "ls -1dt /app/handrail/.run/* 2>/dev/null | head -n 1 | xargs -I{} sh -lc 'find \"{}\" -maxdepth 2 -type f | sort | tail -n 20'"],
}

def _op_proc_run_readonly(args):
    import subprocess, time, os

    command = args.get("command")
    cwd = args.get("cwd", "/app")

    allowed = {
        "pwd": ["pwd"],
        "ls": ["ls"],
    }

    if command not in allowed:
        return {
            "ok": False,
            "data": {},
            "signal": None,
            "error": f"not allowed: {command}",
            "latency_ms": 0.0,
        }

    try:
        start = time.time()
        cp = subprocess.run(
            allowed[command],
            cwd=cwd,
            capture_output=True,
            text=True
        )

        elapsed = int((time.time() - start) * 1000)

        return {
            "ok": cp.returncode == 0,
            "data": {
                "stdout": cp.stdout,
                "stderr": cp.stderr,
                "returncode": cp.returncode,
                "command": command,
                "cwd": cwd,
            },
            "signal": cp.returncode,
            "error": None if cp.returncode == 0 else (cp.stderr or "nonzero exit"),
            "latency_ms": elapsed,
        }

    except Exception as e:
        return {
            "ok": False,
            "data": {
                "command": command,
                "cwd": cwd,
            },
            "signal": None,
            "error": str(e),
            "latency_ms": 0,
        }

    if not os.path.isdir(cwd):
        return {
            "ok": False,
            "data": {},
            "signal": None,
            "error": f"Invalid cwd: {cwd}",
            "latency_ms": 0.0,
        }

    try:
        start = time.time()
        cp = subprocess.run(
            READONLY_ALLOWLIST[command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        elapsed = round((time.time() - start) * 1000, 1)
        return {
            "ok": cp.returncode == 0,
            "data": {
                "command": command,
                "cwd": cwd,
                "stdout": cp.stdout,
                "stderr": cp.stderr,
                "returncode": cp.returncode,
            },
            "signal": cp.returncode,
            "error": None if cp.returncode == 0 else (cp.stderr or f"returncode={cp.returncode}"),
            "latency_ms": elapsed,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "data": {
                "command": command,
                "cwd": cwd,
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": None,
            },
            "signal": None,
            "error": f"timeout: {command}",
            "latency_ms": 30000.0,
        }
    except Exception as e:
        return {
            "ok": False,
            "data": {
                "command": command,
                "cwd": cwd,
            },
            "signal": None,
            "error": f"{type(e).__name__}: {e}",
            "latency_ms": 0.0,
        }


class CPSExecutor:
    @staticmethod
    def execute(cps: dict, workspace: Path | None = None) -> dict:
        policy_profile_name = cps.get("policy_profile")
        policy_data = load_policy(policy_profile_name)
        policy = PolicyEngine(policy_data)

        # ── R3/R4 YubiKey gate — BEFORE Dignity Kernel never-event evaluation ──
        risk_tier = cps.get("risk_tier", "R0")
        if risk_tier in ("R3", "R4"):
            if not cps.get("yubikey_verified", False):
                _write_failure_event(
                    "yubikey_gate", "POLICY_DENIAL", "high", "quarantine_log",
                    f"risk_tier={risk_tier} requires yubikey_verified:true"
                )
                return {
                    "cps_id": cps.get("cps_id"),
                    "ok": False,
                    "results": [],
                    "expect_result": {"passed": False, "failures": [
                        {"reason": "yubikey_required", "risk_tier": risk_tier}
                    ]},
                    "metrics": {"op_count": 0, "typed_ops_ratio": 0, "duration_ms": 0},
                    "result_digest": _sha256({"error": "yubikey_required"}),
                    "policy_profile": policy_profile_name or "default",
                    "failure_class": "POLICY_DENIAL",
                    "severity": "high",
                    "strategy": "quarantine_log",
                    "error": f"risk_tier {risk_tier} requires yubikey_verified: true in CPS payload",
                    "validity_checked": True,
                }

        ops = cps.get("ops", [])
        expect = cps.get("expect", {})

        results: list[dict] = []
        all_ok = True
        start_total = time.monotonic()

        for idx, op_spec in enumerate(ops):
            op_name = op_spec.get("op", "")
            op_args = op_spec.get("args", {})
            start_op = time.monotonic()
            result: dict = {
                "op_index": idx,
                "op": op_name,
                "args": op_args,
                "ok": False,
                "data": {},
                "signal": None,
                "error": None,
                "latency_ms": 0,
                "decision_code": "PENDING",
                "op_digest": "",
            }

            handler = OP_DISPATCH.get(op_name)
            if handler is None:
                result["error"] = f"Unknown op: {op_name}"
                result["decision_code"] = "UNKNOWN_OP"
                all_ok = False
            else:
                try:
                    data = handler(op_args, policy)
                    result["ok"] = True
                    result["data"] = data
                    result["decision_code"] = "OK"
                    # Derive signal
                    if "status_code" in data:
                        result["signal"] = data["status_code"]
                    elif "returncode" in data:
                        result["signal"] = data["returncode"]
                    else:
                        result["signal"] = "ok"
                except PermissionError as e:
                    result["error"] = str(e)
                    result["decision_code"] = "POLICY_DENIED"
                    result["failure_class"] = "POLICY_DENIAL"
                    result["severity"] = "high"
                    result["strategy"] = "quarantine_log"
                    _write_failure_event(op_name, "POLICY_DENIAL", "high", "quarantine_log", str(e))
                    all_ok = False
                except TimeoutError as e:
                    result["error"] = str(e)
                    result["decision_code"] = "TIMEOUT"
                    result["failure_class"] = "EXECUTION_FAILURE"
                    result["severity"] = "medium"
                    result["strategy"] = "retry_backoff"
                    _write_failure_event(op_name, "EXECUTION_FAILURE", "medium", "retry_backoff", str(e))
                    all_ok = False
                except ValueError as e:
                    result["error"] = str(e)
                    result["decision_code"] = "OP_ERROR"
                    result["failure_class"] = "SEMANTIC_FAILURE"
                    result["severity"] = "low"
                    result["strategy"] = "replan"
                    _write_failure_event(op_name, "SEMANTIC_FAILURE", "low", "replan", str(e))
                    all_ok = False
                except Exception as e:
                    result["error"] = str(e)
                    result["decision_code"] = "OP_ERROR"
                    result["failure_class"] = "UNKNOWN"
                    result["severity"] = "high"
                    result["strategy"] = "escalate"
                    _write_failure_event(op_name, "UNKNOWN", "high", "escalate", str(e))
                    all_ok = False

            result["latency_ms"] = round((time.monotonic() - start_op) * 1000, 1)
            result["op_digest"] = _sha256({"op": op_name, "args": op_args, "data": result["data"]})
            results.append(result)

        duration_ms = round((time.monotonic() - start_total) * 1000, 1)
        expect_result = _validate_expect(results, expect) if expect else {"passed": True, "failures": []}
        result_digest = _sha256(results)

        return {
            "cps_id": cps.get("cps_id"),
            "ok": all_ok and expect_result["passed"],
            "results": results,
            "expect_result": expect_result,
            "metrics": {
                "op_count": len(ops),
                "typed_ops_ratio": 1.0,
                "duration_ms": duration_ms,
            },
            "result_digest": result_digest,
            "policy_profile": policy_profile_name or "default",
            "validity_checked": True,
        }

    @staticmethod
    def handle_app_focus(args):
        import subprocess
        app_name = args.get("app_name")
        try:
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to activate'], timeout=5, check=True, capture_output=True)
            return {"ok": True, "focused": True}
        except:
            return {"ok": False, "error": "focus_failed"}

    @staticmethod
    def handle_ui_click(args):
        x, y = args.get("x", 0), args.get("y", 0)
        import subprocess
        try:
            subprocess.run(["osascript", "-e", f'tell application "System Events" to click at {{{x}, {y}}}'], timeout=5, check=True, capture_output=True)
            return {"ok": True, "clicked": True}
        except:
            return {"ok": False, "error": "click_failed"}

    @staticmethod
    def handle_ui_type(args):
        text = args.get("text", "").replace('"', '\\"')
        import subprocess
        try:
            subprocess.run(["osascript", "-e", f'tell application "System Events" to keystroke "{text}"'], timeout=5, check=True, capture_output=True)
            return {"ok": True, "typed": True}
        except:
            return {"ok": False, "error": "type_failed"}

    @staticmethod
    def handle_vision_capture(args):
        import subprocess, time
        artifact_path = f"/Volumes/NSExternal/.run/boot/screen_{int(time.time()*1000)}.png"
        try:
            subprocess.run(["screencapture", "-x", artifact_path], timeout=5, check=True)
            return {"ok": True, "captured": True, "artifact": artifact_path}
        except:
            return {"ok": False, "error": "capture_failed"}

    @staticmethod
    def handle_fs_read(args):
        path = args.get("path")
        try:
            with open(path, 'r') as f:
                content = f.read()
            return {"ok": True, "read": True, "content": content, "length": len(content)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

def _op_app_focus(args: dict, _policy: PolicyEngine) -> dict:
    import subprocess
    app_name = args.get("app_name")
    try:
        subprocess.run(["osascript", "-e", f'tell application "{app_name}" to activate'], timeout=5, check=True, capture_output=True)
        return {"ok": True, "focused": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _op_ui_click(args: dict, _policy: PolicyEngine) -> dict:
    import subprocess
    x, y = args.get("x", 0), args.get("y", 0)
    try:
        subprocess.run(["osascript", "-e", f'tell application "System Events" to click at {{{x}, {y}}}'], timeout=5, check=True, capture_output=True)
        return {"ok": True, "clicked": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _op_ui_type(args: dict, _policy: PolicyEngine) -> dict:
    import subprocess
    text = args.get("text", "").replace('"', '\\"')
    try:
        subprocess.run(["osascript", "-e", f'tell application "System Events" to keystroke "{text}"'], timeout=5, check=True, capture_output=True)
        return {"ok": True, "typed": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _op_vision_capture(args: dict, _policy: PolicyEngine) -> dict:
    import subprocess, time
    artifact_path = f"/Volumes/NSExternal/.run/boot/screen_{int(time.time()*1000)}.png"
    try:
        subprocess.run(["screencapture", "-x", artifact_path], timeout=5, check=True)
        return {"ok": True, "captured": True, "artifact": artifact_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _op_fs_read_full(args: dict, _policy: PolicyEngine) -> dict:
    path = args.get("path")
    try:
        with open(path, 'r') as f:
            content = f.read()
        return {"ok": True, "read": True, "content": content, "length": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
