"""
vision.* namespace
==================
macOS screen capture and OCR via screencapture + tesseract.

Ops:
  vision.screenshot  — {path, hash, size_bytes}  full-screen or region PNG
  vision.ocr_region  — {text, confidence, region} screencapture region → tesseract

Dignity Guard:
  Both ops require screen_recording permission (macOS 10.15+).
  All captures are written as artifacts via _artifact_path().
  Ledger path (~/.axiolev/ledger) is never written here.
"""
from __future__ import annotations
import asyncio, hashlib, os, platform, shutil
from pathlib import Path
from adapter_core.contract import AdapterRequest, AdapterResponse

IS_MACOS = platform.system() == "Darwin"

ARTIFACTS_ROOT = Path(os.environ.get(
    "ADAPTER_ARTIFACTS_ROOT",
    str(Path.home() / "axiolev_runtime" / ".adapter_artifacts")
))


async def _run(cmd: list[str], timeout: float = 10.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "TIMEOUT"


def _artifact_path(run_id: str, name: str) -> Path:
    p = ARTIFACTS_ROOT / run_id
    p.mkdir(parents=True, exist_ok=True)
    return p / name


async def vision_screenshot(req: AdapterRequest) -> AdapterResponse:
    run_id = req.run_id
    out_path = _artifact_path(run_id, "screenshot.png")

    if not IS_MACOS:
        out_path.write_bytes(b"\x89PNG\r\n\x1a\n")
        return AdapterResponse.success(req, {
            "path": str(out_path), "mock": True, "hash": "sha256:mock0000",
            "width": 1920, "height": 1080, "ts": 0,
        }, artifacts=[str(out_path)])

    x = req.params.get("x")
    y = req.params.get("y")
    w = req.params.get("w")
    h = req.params.get("h")
    cmd = ["screencapture", "-x"]
    if all(v is not None for v in [x, y, w, h]):
        cmd += ["-R", f"{x},{y},{w},{h}"]
    cmd.append(str(out_path))

    rc, _, err = await _run(cmd)
    if rc != 0:
        return AdapterResponse.failure(req, "screencapture failed: " + err)

    img_bytes = out_path.read_bytes()
    img_hash = "sha256:" + hashlib.sha256(img_bytes).hexdigest()[:16]
    return AdapterResponse.success(req, {
        "path": str(out_path),
        "size_bytes": len(img_bytes),
        "hash": img_hash,
        "ts": int(out_path.stat().st_mtime),
    }, artifacts=[str(out_path)])


async def vision_ocr_region(req: AdapterRequest) -> AdapterResponse:
    run_id = req.run_id
    img_path = _artifact_path(run_id, "ocr_region.png")
    x = req.params.get("x", 0)
    y = req.params.get("y", 0)
    w = req.params.get("w", 400)
    h = req.params.get("h", 100)

    if not IS_MACOS:
        return AdapterResponse.success(req, {
            "text": "[MOCK OCR TEXT]", "confidence": 0.99,
            "region": {"x": x, "y": y, "w": w, "h": h}, "mock": True,
        }, artifacts=[str(img_path)])

    # Capture region
    rc, _, err = await _run(["screencapture", "-x", "-R", f"{x},{y},{w},{h}", str(img_path)])
    if rc != 0:
        return AdapterResponse.failure(req, "screencapture failed: " + err)

    # OCR via tesseract — graceful skip if not installed
    if not shutil.which("tesseract"):
        return AdapterResponse.success(req, {
            "text": None, "confidence": None,
            "note": "tesseract not installed — OCR skipped",
            "region": {"x": x, "y": y, "w": w, "h": h},
        }, artifacts=[str(img_path)])

    rc, ocr_text, err = await _run(["tesseract", str(img_path), "stdout", "--psm", "6"])
    if rc != 0:
        return AdapterResponse.failure(req, "tesseract failed: " + err)

    return AdapterResponse.success(req, {
        "text": ocr_text,
        "confidence": None,  # tesseract stdout doesn't expose per-word confidence
        "region": {"x": x, "y": y, "w": w, "h": h},
    }, artifacts=[str(img_path)])


def build_vision_handlers() -> dict:
    return {
        "vision.screenshot": vision_screenshot,
        "vision.ocr_region": vision_ocr_region,
    }
