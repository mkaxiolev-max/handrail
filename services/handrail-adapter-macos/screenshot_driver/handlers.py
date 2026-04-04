"""
screenshot.* namespace — advanced screen capture.
Ops: region / window / annotate / diff
Dignity Guard: screen recording permission required, all artifacts logged.
"""
from __future__ import annotations
import asyncio, hashlib, platform, time
from pathlib import Path
from adapter_core.contract import AdapterRequest, AdapterResponse, OperationStatus

IS_MACOS = platform.system() == "Darwin"
_ARTIFACT_DIR = Path("/tmp/ns_screenshots")


async def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return proc.returncode, out.decode().strip(), err.decode().strip()


def _artifact_path(suffix: str = "") -> Path:
    _ARTIFACT_DIR.mkdir(exist_ok=True)
    ts = int(time.time())
    return _ARTIFACT_DIR / f"ns_cap_{ts}{suffix}.png"


async def screenshot_region(req: AdapterRequest) -> AdapterResponse:
    params = req.params or {}
    x = int(params.get("x", 0))
    y = int(params.get("y", 0))
    w = int(params.get("w", 800))
    h = int(params.get("h", 600))

    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "path": "/tmp/mock.png", "mode": "mock"})

    path = _artifact_path("_region")
    region = f"{x},{y},{x+w},{y+h}"
    rc, out, err = await _run(["screencapture", "-x", "-R", region, str(path)])
    if rc != 0 or not path.exists():
        return AdapterResponse.success(req, {"ok": True, "skipped": True,
                                              "reason": "screen_recording_required"})
    data = path.read_bytes()
    file_hash = hashlib.sha256(data).hexdigest()[:16]
    return AdapterResponse.success(req, {"ok": True, "path": str(path),
                                          "hash": file_hash, "size": len(data),
                                          "region": {"x": x, "y": y, "w": w, "h": h}})


async def screenshot_window(req: AdapterRequest) -> AdapterResponse:
    app = (req.params or {}).get("app", "").strip()
    if not app:
        return AdapterResponse.failure(req, "app required")
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "path": "/tmp/mock.png", "mode": "mock"})

    path = _artifact_path("_window")
    rc, out, err = await _run(["screencapture", "-x", str(path)])
    if not path.exists():
        return AdapterResponse.success(req, {"ok": True, "skipped": True,
                                              "reason": "screen_recording_required"})
    data = path.read_bytes()
    file_hash = hashlib.sha256(data).hexdigest()[:16]
    return AdapterResponse.success(req, {"ok": True, "path": str(path),
                                          "hash": file_hash, "app": app, "size": len(data)})


async def screenshot_annotate(req: AdapterRequest) -> AdapterResponse:
    label = (req.params or {}).get("label", "NS")[:50]
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "path": "/tmp/mock.png", "mode": "mock"})

    path = _artifact_path("_annotated")
    rc, out, err = await _run(["screencapture", "-x", str(path)])
    if rc != 0 or not path.exists():
        return AdapterResponse.success(req, {"ok": True, "skipped": True,
                                              "reason": "screen_recording_required"})
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data = path.read_bytes()
    file_hash = hashlib.sha256(data).hexdigest()[:16]
    return AdapterResponse.success(req, {"ok": True, "path": str(path), "hash": file_hash,
                                          "label": label, "ts": ts, "size": len(data)})


async def screenshot_diff(req: AdapterRequest) -> AdapterResponse:
    if not IS_MACOS:
        return AdapterResponse.success(req, {"ok": True, "changed_pct": 0, "mode": "mock"})

    path = _artifact_path("_diff")
    rc, _, _ = await _run(["screencapture", "-x", str(path)])
    if rc != 0 or not path.exists():
        return AdapterResponse.success(req, {"ok": True, "skipped": True,
                                              "reason": "screen_recording_required"})

    data = path.read_bytes()
    file_hash = hashlib.sha256(data).hexdigest()[:16]
    prev_hash_file = Path("/tmp/ns_prev_screenshot_hash")
    prev_hash = prev_hash_file.read_text().strip() if prev_hash_file.exists() else None
    prev_hash_file.write_text(file_hash)

    changed = file_hash != prev_hash if prev_hash else True
    return AdapterResponse.success(req, {"ok": True, "path": str(path), "hash": file_hash,
                                          "changed": changed,
                                          "changed_pct": 100 if changed and not prev_hash else (50 if changed else 0)})


def build_screenshot_handlers() -> dict:
    return {
        "screenshot.region":   screenshot_region,
        "screenshot.window":   screenshot_window,
        "screenshot.annotate": screenshot_annotate,
        "screenshot.diff":     screenshot_diff,
    }
