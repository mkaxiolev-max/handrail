"""
Tests for file_watch.* namespace handlers.
Uses tmp_path fixture — no real ARTIFACTS_ROOT needed.
"""
from __future__ import annotations
import json, time
from pathlib import Path
from unittest.mock import patch
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from file_watch_driver.handlers import (
    file_watch_watch_path,
    file_watch_read_recent_changes,
    build_file_watch_handlers,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


@pytest.fixture(autouse=True)
def _patch_artifacts_root(tmp_path, monkeypatch):
    """Redirect artifact writes to a sibling directory so they never appear inside watched dirs."""
    import file_watch_driver.handlers as mod
    artifacts_dir = tmp_path / ".artifacts"
    artifacts_dir.mkdir()
    monkeypatch.setattr(mod, "ARTIFACTS_ROOT", artifacts_dir)


@pytest.fixture()
def watched(tmp_path) -> Path:
    """A clean subdirectory to watch — isolated from the artifacts root."""
    d = tmp_path / "watched"
    d.mkdir()
    return d


# ── file_watch.watch_path ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_watch_path_directory(watched):
    (watched / "a.txt").write_text("hello")
    (watched / "b.txt").write_text("world")
    (watched / "sub").mkdir()

    resp = await file_watch_watch_path(_req("file_watch.watch_path", path=str(watched)))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["entry_count"] == 3  # a.txt, b.txt, sub
    assert resp.data["watch_id"]
    assert resp.data["snapshot_at"] > 0
    assert Path(resp.data["artifact"]).exists()
    assert resp.artifacts


@pytest.mark.asyncio
async def test_watch_path_single_file(watched):
    f = watched / "config.json"
    f.write_text('{"key": "val"}')

    resp = await file_watch_watch_path(_req("file_watch.watch_path", path=str(f)))

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["entry_count"] == 1

    # Verify artifact content
    artifact = json.loads(Path(resp.data["artifact"]).read_text())
    assert "config.json" in artifact["snapshot"]
    assert artifact["snapshot"]["config.json"]["type"] == "file"


@pytest.mark.asyncio
async def test_watch_path_custom_watch_id(watched):
    (watched / "f.txt").write_text("x")
    resp = await file_watch_watch_path(
        _req("file_watch.watch_path", path=str(watched), watch_id="mywatch1")
    )
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["watch_id"] == "mywatch1"


@pytest.mark.asyncio
async def test_watch_path_missing_path():
    resp = await file_watch_watch_path(_req("file_watch.watch_path"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.path required" in resp.error


@pytest.mark.asyncio
async def test_watch_path_not_found():
    resp = await file_watch_watch_path(
        _req("file_watch.watch_path", path="/no/such/path/ever")
    )
    assert resp.status == OperationStatus.FAILURE
    assert "PATH_NOT_FOUND" in resp.error


# ── file_watch.read_recent_changes ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_read_recent_changes_no_changes(watched):
    (watched / "a.txt").write_text("stable")

    watch_resp = await file_watch_watch_path(
        _req("file_watch.watch_path", path=str(watched))
    )
    watch_id = watch_resp.data["watch_id"]

    resp = await file_watch_read_recent_changes(
        _req("file_watch.read_recent_changes", watch_id=watch_id, path=str(watched))
    )

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["changed_count"] == 0
    assert resp.data["changes"] == []


@pytest.mark.asyncio
async def test_read_recent_changes_added_file(watched):
    (watched / "a.txt").write_text("original")

    watch_resp = await file_watch_watch_path(
        _req("file_watch.watch_path", path=str(watched))
    )
    watch_id = watch_resp.data["watch_id"]

    (watched / "new.txt").write_text("new content")

    resp = await file_watch_read_recent_changes(
        _req("file_watch.read_recent_changes", watch_id=watch_id, path=str(watched))
    )

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["changed_count"] == 1
    change = resp.data["changes"][0]
    assert change["name"] == "new.txt"
    assert change["change_type"] == "added"


@pytest.mark.asyncio
async def test_read_recent_changes_removed_file(watched):
    f = watched / "gone.txt"
    f.write_text("going away")

    watch_resp = await file_watch_watch_path(
        _req("file_watch.watch_path", path=str(watched))
    )
    watch_id = watch_resp.data["watch_id"]

    f.unlink()

    resp = await file_watch_read_recent_changes(
        _req("file_watch.read_recent_changes", watch_id=watch_id, path=str(watched))
    )

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["changed_count"] == 1
    change = resp.data["changes"][0]
    assert change["name"] == "gone.txt"
    assert change["change_type"] == "removed"


@pytest.mark.asyncio
async def test_read_recent_changes_modified_file(watched):
    f = watched / "mutable.txt"
    f.write_text("v1")

    watch_resp = await file_watch_watch_path(
        _req("file_watch.watch_path", path=str(watched))
    )
    watch_id = watch_resp.data["watch_id"]

    # Force a mtime difference
    time.sleep(0.05)
    f.write_text("v2")

    resp = await file_watch_read_recent_changes(
        _req("file_watch.read_recent_changes", watch_id=watch_id, path=str(watched))
    )

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["changed_count"] == 1
    change = resp.data["changes"][0]
    assert change["name"] == "mutable.txt"
    assert change["change_type"] == "modified"
    assert change["new_mtime"] > change["old_mtime"]


@pytest.mark.asyncio
async def test_read_recent_changes_multiple_change_types(watched):
    (watched / "keep.txt").write_text("keep")
    remove_me = watched / "remove.txt"
    remove_me.write_text("bye")
    modify_me = watched / "modify.txt"
    modify_me.write_text("v1")

    watch_resp = await file_watch_watch_path(
        _req("file_watch.watch_path", path=str(watched))
    )
    watch_id = watch_resp.data["watch_id"]

    remove_me.unlink()
    time.sleep(0.05)
    modify_me.write_text("v2")
    (watched / "added.txt").write_text("new")

    resp = await file_watch_read_recent_changes(
        _req("file_watch.read_recent_changes", watch_id=watch_id, path=str(watched))
    )

    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["changed_count"] == 3
    types = {c["name"]: c["change_type"] for c in resp.data["changes"]}
    assert types["added.txt"] == "added"
    assert types["remove.txt"] == "removed"
    assert types["modify.txt"] == "modified"


@pytest.mark.asyncio
async def test_read_recent_changes_watch_not_found():
    resp = await file_watch_read_recent_changes(
        _req("file_watch.read_recent_changes", watch_id="noexist", path="/tmp")
    )
    assert resp.status == OperationStatus.FAILURE
    assert "WATCH_NOT_FOUND" in resp.error


@pytest.mark.asyncio
async def test_read_recent_changes_missing_watch_id():
    resp = await file_watch_read_recent_changes(
        _req("file_watch.read_recent_changes", path="/tmp")
    )
    assert resp.status == OperationStatus.FAILURE
    assert "params.watch_id required" in resp.error


@pytest.mark.asyncio
async def test_read_recent_changes_missing_path(watched):
    (watched / "x.txt").write_text("x")
    watch_resp = await file_watch_watch_path(
        _req("file_watch.watch_path", path=str(watched))
    )
    resp = await file_watch_read_recent_changes(
        _req("file_watch.read_recent_changes", watch_id=watch_resp.data["watch_id"])
    )
    assert resp.status == OperationStatus.FAILURE
    assert "params.path required" in resp.error


# ── registry ─────────────────────────────────────────────────────────────────

def test_build_file_watch_handlers_keys():
    handlers = build_file_watch_handlers()
    assert set(handlers.keys()) == {
        "file_watch.watch_path",
        "file_watch.read_recent_changes",
    }
    for fn in handlers.values():
        assert callable(fn)
