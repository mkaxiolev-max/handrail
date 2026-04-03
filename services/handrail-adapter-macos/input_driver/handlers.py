"""
input.* namespace
=================
macOS keyboard and mouse control via AppleScript / System Events.

Ops:
  input.type    — type text via keystroke simulation
  input.click   — click at screen coordinates
  input.key     — send a named key (return, tab, cmd+c, etc.)

Dignity Guard:
  All ops require Accessibility permission.
  input.type: max 500 chars.
  input.click: coordinates must be within screen bounds (0–7680 × 0–4320).
  input.key: whitelisted safe keys only; cmd+q and other destructive combos blocked.
"""
from __future__ import annotations
import asyncio, platform, re
from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"

_SAFE_KEYS = {
    "return", "tab", "escape", "space", "delete", "backspace",
    "up", "down", "left", "right",
    "cmd+c", "cmd+v", "cmd+a", "cmd+z", "cmd+x",
    "cmd+s", "cmd+n", "cmd+t", "cmd+w",
    "f1", "f2", "f3", "f4", "f5", "f6",
}
_BLOCKED_COMBOS = {"cmd+q", "ctrl+alt+delete", "cmd+option+esc"}

_KEY_CODES = {
    "return": 36, "tab": 48, "escape": 53, "space": 49,
    "delete": 51, "backspace": 51,
    "up": 126, "down": 125, "left": 123, "right": 124,
}
_MOD_MAP = {"cmd": "command", "ctrl": "control", "opt": "option", "shift": "shift"}


async def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode().strip(), err.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


def _is_accessibility_error(err: str) -> bool:
    return "-1719" in err or "assistive" in err.lower()


async def input_type(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"skipped": True, "reason": "not_macos"})
    text = (req.params or {}).get("text", "")
    if not text:
        return AdapterResponse.failure(req, "params.text required")
    if len(text) > 500:
        raise PermissionError("input.type: text exceeds 500-char Dignity Guard limit")

    safe_text = text.replace("\\", "\\\\").replace('"', '\\"')
    script = f'tell application "System Events" to keystroke "{safe_text}"'
    rc, _, err = await _run(["osascript", "-e", script])
    if rc != 0:
        if _is_accessibility_error(err):
            return AdapterResponse.success(req, {"skipped": True, "reason": "accessibility_permission_required"})
        return AdapterResponse.failure(req, f"keystroke failed: {err[:200]}")
    return AdapterResponse.success(req, {"ok": True, "typed_length": len(text)})


async def input_click(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"skipped": True, "reason": "not_macos"})
    params = req.params or {}
    x = params.get("x")
    y = params.get("y")
    if x is None or y is None:
        return AdapterResponse.failure(req, "params.x and params.y required")
    x, y = int(x), int(y)
    if not (0 <= x <= 7680 and 0 <= y <= 4320):
        raise PermissionError(f"input.click: coordinates ({x},{y}) outside safe bounds (0–7680 × 0–4320)")

    script = f'tell application "System Events"\n  click at {{{x}, {y}}}\nend tell'
    rc, _, err = await _run(["osascript", "-e", script])
    if rc != 0:
        if _is_accessibility_error(err):
            return AdapterResponse.success(req, {"skipped": True, "reason": "accessibility_permission_required"})
        return AdapterResponse.failure(req, f"click failed: {err[:200]}")
    return AdapterResponse.success(req, {"ok": True, "clicked": {"x": x, "y": y}})


async def input_key(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"skipped": True, "reason": "not_macos"})
    key = (req.params or {}).get("key", "").lower().strip()
    if not key:
        return AdapterResponse.failure(req, "params.key required")
    if key in _BLOCKED_COMBOS:
        raise PermissionError(f"input.key: '{key}' is a constitutionally blocked combo")
    if key not in _SAFE_KEYS and not re.match(r'^[a-z0-9]$', key):
        raise PermissionError(f"input.key: '{key}' not in safe key whitelist")

    if "+" in key:
        parts = key.split("+", 1)
        mod = _MOD_MAP.get(parts[0], parts[0])
        k = parts[1]
        script = f'tell application "System Events" to keystroke "{k}" using {mod} key'
    elif key in _KEY_CODES:
        kc = _KEY_CODES[key]
        script = f'tell application "System Events" to key code {kc}'
    else:
        script = f'tell application "System Events" to keystroke "{key}"'

    rc, _, err = await _run(["osascript", "-e", script])
    if rc != 0:
        if _is_accessibility_error(err):
            return AdapterResponse.success(req, {"skipped": True, "reason": "accessibility_permission_required"})
        return AdapterResponse.failure(req, f"key failed: {err[:200]}")
    return AdapterResponse.success(req, {"ok": True, "key": key})


def build_input_handlers() -> dict:
    return {
        "input.type":  input_type,
        "input.click": input_click,
        "input.key":   input_key,
    }
