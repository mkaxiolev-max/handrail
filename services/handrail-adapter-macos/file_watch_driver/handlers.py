"""
file_watch.* namespace
=======================
Snapshot-based file/directory change detection. Stateless HTTP-friendly:
state lives in a JSON artifact on disk, not in server memory.

Methods:
  file_watch.watch_path          — capture baseline snapshot → artifact
  file_watch.read_recent_changes — diff current state against baseline

Workflow:
  1. POST watch_path  { path: "/some/dir" }
     → returns { watch_id, artifact, entry_count, snapshot_at }
  2. POST read_recent_changes { watch_id: "abc12345", path: "/some/dir" }
     → returns { changes: [{name, change_type, ...}], changed_count }

Artifact location: ADAPTER_ARTIFACTS_ROOT/{watch_id}/watch_baseline.json

Contract: every handler returns AdapterResponse.
Dignity Kernel pre-check in server.py gates every call.
"""
from __future__ import annotations
import json, os, time, uuid
from pathlib import Path

from adapter_core.contract import AdapterRequest, AdapterResponse

ARTIFACTS_ROOT = Path(os.environ.get(
    "ADAPTER_ARTIFACTS_ROOT",
    str(Path.home() / "axiolev_runtime" / ".adapter_artifacts"),
))


def _snapshot_path(p: Path) -> dict[str, dict]:
    """Return {name: {mtime, size_bytes, type}} for a file or directory."""
    if p.is_file():
        stat = p.stat()
        return {p.name: {"mtime": stat.st_mtime, "size_bytes": stat.st_size, "type": "file"}}

    entries: dict[str, dict] = {}
    for item in sorted(p.iterdir()):
        stat = item.stat()
        entries[item.name] = {
            "mtime":      stat.st_mtime,
            "size_bytes": stat.st_size if item.is_file() else None,
            "type":       "file" if item.is_file() else "dir",
        }
    return entries


async def file_watch_watch_path(req: AdapterRequest) -> AdapterResponse:
    path_str: str = req.params.get("path", "")
    if not path_str:
        return AdapterResponse.failure(req, "params.path required")

    p = Path(path_str)
    if not p.exists():
        return AdapterResponse.failure(req, f"PATH_NOT_FOUND: {path_str}")

    watch_id: str = req.params.get("watch_id") or str(uuid.uuid4())[:8]

    try:
        snapshot = _snapshot_path(p)
    except PermissionError:
        return AdapterResponse.failure(req, f"PERMISSION_DENIED: {path_str}")

    artifact_dir = ARTIFACTS_ROOT / watch_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "watch_baseline.json"

    baseline = {
        "watch_id":    watch_id,
        "path":        str(p.resolve()),
        "snapshot":    snapshot,
        "snapshot_at": time.time(),
    }
    artifact_path.write_text(json.dumps(baseline, indent=2))

    return AdapterResponse.success(
        req,
        {
            "watch_id":    watch_id,
            "path":        str(p.resolve()),
            "entry_count": len(snapshot),
            "snapshot_at": baseline["snapshot_at"],
            "artifact":    str(artifact_path),
        },
        artifacts=[str(artifact_path)],
    )


async def file_watch_read_recent_changes(req: AdapterRequest) -> AdapterResponse:
    watch_id: str = req.params.get("watch_id", "")
    path_str: str = req.params.get("path", "")
    if not watch_id:
        return AdapterResponse.failure(req, "params.watch_id required")
    if not path_str:
        return AdapterResponse.failure(req, "params.path required")

    artifact_path = ARTIFACTS_ROOT / watch_id / "watch_baseline.json"
    if not artifact_path.exists():
        return AdapterResponse.failure(req, f"WATCH_NOT_FOUND: watch_id={watch_id!r}")

    baseline = json.loads(artifact_path.read_text())
    old_snapshot: dict[str, dict] = baseline["snapshot"]

    p = Path(path_str)
    if not p.exists():
        return AdapterResponse.failure(req, f"PATH_NOT_FOUND: {path_str}")

    try:
        current = _snapshot_path(p)
    except PermissionError:
        return AdapterResponse.failure(req, f"PERMISSION_DENIED: {path_str}")

    changes: list[dict] = []

    for name, meta in current.items():
        if name not in old_snapshot:
            changes.append({"name": name, "change_type": "added", "new_mtime": meta["mtime"]})
        elif meta["mtime"] != old_snapshot[name]["mtime"]:
            changes.append({
                "name":        name,
                "change_type": "modified",
                "old_mtime":   old_snapshot[name]["mtime"],
                "new_mtime":   meta["mtime"],
            })

    for name, meta in old_snapshot.items():
        if name not in current:
            changes.append({"name": name, "change_type": "removed", "old_mtime": meta["mtime"]})

    changes.sort(key=lambda c: c["name"])

    return AdapterResponse.success(req, {
        "watch_id":           watch_id,
        "path":               str(p.resolve()),
        "baseline_snapshot_at": baseline["snapshot_at"],
        "checked_at":         time.time(),
        "changes":            changes,
        "changed_count":      len(changes),
    })


def build_file_watch_handlers() -> dict:
    return {
        "file_watch.watch_path":          file_watch_watch_path,
        "file_watch.read_recent_changes": file_watch_read_recent_changes,
    }
