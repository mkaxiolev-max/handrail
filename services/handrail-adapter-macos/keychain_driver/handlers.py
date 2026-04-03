"""
keychain.* namespace — READ ONLY, strict Dignity Guard
=======================================================
Checks existence of keychain entries and lists service names only.
NEVER returns actual secret values.

Ops:
  keychain.check_entry   — {exists: bool, service: str}
  keychain.list_services — {services: list[str], count: int}

Dignity Guard:
  check_entry:   only checks exit code — never returns password/secret value
                 service/account must not contain shell metacharacters
  list_services: strips any line containing: pass, pwd, secret, token, key
"""
from __future__ import annotations
import asyncio, re
from adapter_core.contract import AdapterRequest, AdapterResponse

# Shell metacharacter guard — deny service/account names containing these
_SHELL_META = re.compile(r'[;&|`$<>()\\\'"!]')

# Patterns that indicate a secret value line — strip these from list output
_SECRET_LINE_PATTERN = re.compile(r'pass|pwd|secret|token|key', re.IGNORECASE)


async def _run(cmd: list[str], timeout: float = 6.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode(errors="replace").strip(), stderr.decode(errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


async def keychain_check_entry(req: AdapterRequest) -> AdapterResponse:
    service = req.params.get("service", "")
    account = req.params.get("account", "")

    if not service:
        return AdapterResponse.failure(req, "params.service required")

    # Dignity Guard — no shell metacharacters
    if _SHELL_META.search(service) or _SHELL_META.search(account):
        raise PermissionError("keychain.check_entry: service/account contains forbidden shell metacharacters")

    # Check exit code only — stdout/stderr deliberately ignored
    rc, _, _ = await _run([
        "security", "find-generic-password",
        "-s", service,
        *([ "-a", account] if account else []),
    ])

    # rc=0 → exists, rc=44 → not found, other → treat as not found (permission/error)
    exists = rc == 0

    return AdapterResponse.success(req, {"exists": exists, "service": service})


async def keychain_list_services(req: AdapterRequest) -> AdapterResponse:
    rc, out, _ = await _run(["security", "dump-keychain"])

    services: list[str] = []
    if rc == 0 and out:
        for line in out.splitlines():
            # Only process svce (service name) lines
            if '"svce"' not in line and "<svce>" not in line:
                continue
            # Dignity Guard — skip if line suggests a secret value
            if _SECRET_LINE_PATTERN.search(line):
                continue
            # Extract the quoted value after svce
            m = re.search(r'"svce"[^=]*=\s*(?:<blob>)?\s*"([^"]+)"', line)
            if m:
                svc = m.group(1).strip()
                if svc and svc not in services:
                    services.append(svc)

    return AdapterResponse.success(req, {"services": services, "count": len(services)})


def build_keychain_handlers() -> dict:
    return {
        "keychain.check_entry":    keychain_check_entry,
        "keychain.list_services":  keychain_list_services,
    }
