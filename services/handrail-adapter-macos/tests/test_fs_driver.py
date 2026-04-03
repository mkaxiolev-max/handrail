"""
Tests for fs.* namespace handlers.
All file I/O uses tmp_path fixture — no real filesystem side effects.
"""
from __future__ import annotations
from pathlib import Path
import pytest

from adapter_core.contract import AdapterRequest, OperationStatus
from fs_driver.handlers import (
    fs_read_text,
    fs_write_text,
    fs_list,
    build_fs_handlers,
    _LEDGER_GUARD,
    _MAX_READ_BYTES,
)


def _req(method: str, **params) -> AdapterRequest:
    return AdapterRequest(method=method, params=params)


# ── fs.read_text ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_read_text_success(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    resp = await fs_read_text(_req("fs.read_text", path=str(f)))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["content"] == "hello world"
    assert resp.data["size_bytes"] == len("hello world")
    assert resp.data["truncated"] is False


@pytest.mark.asyncio
async def test_read_text_missing_path_param():
    resp = await fs_read_text(_req("fs.read_text"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.path required" in resp.error


@pytest.mark.asyncio
async def test_read_text_file_not_found(tmp_path):
    resp = await fs_read_text(_req("fs.read_text", path=str(tmp_path / "nope.txt")))
    assert resp.status == OperationStatus.FAILURE
    assert "FILE_NOT_FOUND" in resp.error


@pytest.mark.asyncio
async def test_read_text_file_too_large(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * (_MAX_READ_BYTES + 1))
    resp = await fs_read_text(_req("fs.read_text", path=str(f)))
    assert resp.status == OperationStatus.FAILURE
    assert "FILE_TOO_LARGE" in resp.error


@pytest.mark.asyncio
async def test_read_text_ledger_blocked():
    """Dignity Guard: ALEXANDRIA/ledger path must be denied."""
    resp = await fs_read_text(_req("fs.read_text", path="/Volumes/NSExternal/ALEXANDRIA/ledger/main.db"))
    assert resp.status == OperationStatus.DENIED
    assert "ledger path is protected" in resp.error


@pytest.mark.asyncio
async def test_read_text_content_truncated_at_8192(tmp_path):
    f = tmp_path / "big.txt"
    content = "a" * 9000
    f.write_text(content)
    resp = await fs_read_text(_req("fs.read_text", path=str(f)))
    assert resp.status == OperationStatus.SUCCESS
    assert len(resp.data["content"]) == 8192
    assert resp.data["truncated"] is True


# ── fs.write_text ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_write_text_allowed_tmp(tmp_path):
    """Write to /tmp is allowed."""
    f = tmp_path / "out.txt"
    with pytest.MonkeyPatch.context() as mp:
        # Patch _write_allowed to allow tmp_path (simulates /tmp)
        import fs_driver.handlers as fh
        mp.setattr(fh, "_write_allowed", lambda p: True)
        resp = await fs_write_text(_req("fs.write_text", path=str(f), content="test content"))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["bytes_written"] == len("test content")
    assert f.read_text() == "test content"


@pytest.mark.asyncio
async def test_write_text_missing_path_param():
    resp = await fs_write_text(_req("fs.write_text", content="data"))
    assert resp.status == OperationStatus.FAILURE
    assert "params.path required" in resp.error


@pytest.mark.asyncio
async def test_write_text_dignity_guard_blocks_disallowed(tmp_path):
    """Write to arbitrary path is denied by dignity guard."""
    f = tmp_path / "secret.txt"
    import fs_driver.handlers as fh
    from unittest.mock import patch
    with patch.object(fh, "_write_allowed", return_value=False):
        resp = await fs_write_text(_req("fs.write_text", path=str(f), content="data"))
    assert resp.status == OperationStatus.DENIED
    assert "not in allowed roots" in resp.error


@pytest.mark.asyncio
async def test_write_text_creates_parent_dirs(tmp_path):
    import fs_driver.handlers as fh
    from unittest.mock import patch
    nested = tmp_path / "a" / "b" / "c" / "file.txt"
    with patch.object(fh, "_write_allowed", return_value=True):
        resp = await fs_write_text(_req("fs.write_text", path=str(nested), content="nested"))
    assert resp.status == OperationStatus.SUCCESS
    assert nested.exists()


@pytest.mark.asyncio
async def test_write_text_empty_content(tmp_path):
    import fs_driver.handlers as fh
    from unittest.mock import patch
    f = tmp_path / "empty.txt"
    with patch.object(fh, "_write_allowed", return_value=True):
        resp = await fs_write_text(_req("fs.write_text", path=str(f), content=""))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["bytes_written"] == 0


# ── fs.list ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_directory(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("bb")
    (tmp_path / "subdir").mkdir()
    resp = await fs_list(_req("fs.list", path=str(tmp_path)))
    assert resp.status == OperationStatus.SUCCESS
    names = {e["name"] for e in resp.data["entries"]}
    assert names == {"a.txt", "b.txt", "subdir"}
    assert resp.data["count"] == 3


@pytest.mark.asyncio
async def test_list_entry_types(tmp_path):
    (tmp_path / "file.txt").write_text("x")
    (tmp_path / "mydir").mkdir()
    resp = await fs_list(_req("fs.list", path=str(tmp_path)))
    types = {e["name"]: e["type"] for e in resp.data["entries"]}
    assert types["file.txt"] == "file"
    assert types["mydir"] == "dir"


@pytest.mark.asyncio
async def test_list_not_found(tmp_path):
    resp = await fs_list(_req("fs.list", path=str(tmp_path / "nope")))
    assert resp.status == OperationStatus.FAILURE
    assert "PATH_NOT_FOUND" in resp.error


@pytest.mark.asyncio
async def test_list_empty_directory(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    resp = await fs_list(_req("fs.list", path=str(empty)))
    assert resp.status == OperationStatus.SUCCESS
    assert resp.data["entries"] == []
    assert resp.data["count"] == 0


@pytest.mark.asyncio
async def test_list_capped_at_100(tmp_path):
    for i in range(120):
        (tmp_path / f"f{i:03d}.txt").write_text("")
    resp = await fs_list(_req("fs.list", path=str(tmp_path)))
    assert resp.status == OperationStatus.SUCCESS
    assert len(resp.data["entries"]) == 100
    assert resp.data["count"] == 120


# ── registry ──────────────────────────────────────────────────────────────────

def test_build_fs_handlers_keys():
    handlers = build_fs_handlers()
    assert set(handlers.keys()) == {"fs.read_text", "fs.write_text", "fs.list"}
    for fn in handlers.values():
        assert callable(fn)
