"""
clipboard.* namespace
=====================
macOS clipboard read/write via pbpaste / pbcopy.

Ops:
  clipboard.read  — {content: str, length: int}
  clipboard.write — {ok: bool, length: int}

Dignity Guard:
  clipboard.read:  strips content containing secret patterns (sk_, whsec_)
  clipboard.write: content must be < 10000 chars (PermissionError otherwise)
"""
from __future__ import annotations
import asyncio, re
from adapter_core.contract import AdapterRequest, AdapterResponse

_SECRET_PATTERN = re.compile(r'(sk_[A-Za-z0-9_]+|whsec_[A-Za-z0-9+/=]+)')
_MAX_WRITE_CHARS = 10_000


async def _run_simple(cmd: list[str], stdin_data: bytes | None = None, timeout: float = 5.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if stdin_data is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(input=stdin_data), timeout=timeout)
        return proc.returncode, stdout.decode(errors="replace").strip(), stderr.decode(errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


async def clipboard_read(req: AdapterRequest) -> AdapterResponse:
    rc, content, err = await _run_simple(["pbpaste"])
    if rc != 0:
        return AdapterResponse.failure(req, f"pbpaste failed: {err}")

    # Dignity Guard — strip secret patterns
    if _SECRET_PATTERN.search(content):
        content = _SECRET_PATTERN.sub("[REDACTED]", content)

    return AdapterResponse.success(req, {"content": content, "length": len(content)})


async def clipboard_write(req: AdapterRequest) -> AdapterResponse:
    content = req.params.get("content", "")

    # Dignity Guard
    if len(content) >= _MAX_WRITE_CHARS:
        raise PermissionError(f"clipboard.write: content length {len(content)} exceeds maximum {_MAX_WRITE_CHARS}")

    rc, _, err = await _run_simple(["pbcopy"], stdin_data=content.encode())
    if rc != 0:
        return AdapterResponse.failure(req, f"pbcopy failed: {err}")

    return AdapterResponse.success(req, {"ok": True, "length": len(content)})


def build_clipboard_handlers() -> dict:
    return {
        "clipboard.read":  clipboard_read,
        "clipboard.write": clipboard_write,
    }
