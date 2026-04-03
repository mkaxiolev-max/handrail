"""Tests for artifact_writer."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from adapter_core.artifact_writer import write_artifact


def test_write_artifact_creates_file(tmp_path, monkeypatch):
    import adapter_core.artifact_writer as aw
    monkeypatch.setattr(aw, "ARTIFACTS_ROOT", tmp_path)
    result = write_artifact("run_001", "env.capture_screen", b"fake_png_data", ".png")
    assert result["size"] == len(b"fake_png_data")
    assert len(result["hash"]) == 16
    assert result["hash"].isalnum()
    assert Path(result["path"]).exists()
    assert Path(result["path"]).read_bytes() == b"fake_png_data"


def test_write_artifact_string_data(tmp_path, monkeypatch):
    import adapter_core.artifact_writer as aw
    monkeypatch.setattr(aw, "ARTIFACTS_ROOT", tmp_path)
    data = json.dumps({"key": "value"})
    result = write_artifact("run_002", "file_watch.watch_path", data, ".json")
    assert result["size"] == len(data.encode())
    assert Path(result["path"]).exists()


def test_write_artifact_hash_consistency(tmp_path, monkeypatch):
    import adapter_core.artifact_writer as aw
    monkeypatch.setattr(aw, "ARTIFACTS_ROOT", tmp_path)
    data = b"deterministic_content"
    r1 = write_artifact("run_003", "env.capture_screen", data, ".bin")
    r2 = write_artifact("run_004", "env.capture_screen", data, ".bin")
    assert r1["hash"] == r2["hash"]


def test_write_artifact_different_data_different_hash(tmp_path, monkeypatch):
    import adapter_core.artifact_writer as aw
    monkeypatch.setattr(aw, "ARTIFACTS_ROOT", tmp_path)
    r1 = write_artifact("run_005", "op", b"data_a", ".bin")
    r2 = write_artifact("run_006", "op", b"data_b", ".bin")
    assert r1["hash"] != r2["hash"]


def test_write_artifact_ts_present(tmp_path, monkeypatch):
    import adapter_core.artifact_writer as aw
    monkeypatch.setattr(aw, "ARTIFACTS_ROOT", tmp_path)
    result = write_artifact("run_007", "op", b"x")
    assert "ts" in result
    assert "T" in result["ts"]


def test_write_artifact_dot_in_op_name(tmp_path, monkeypatch):
    """Dots in op name must be replaced so the filename is valid."""
    import adapter_core.artifact_writer as aw
    monkeypatch.setattr(aw, "ARTIFACTS_ROOT", tmp_path)
    result = write_artifact("run_008", "env.capture_screen", b"data", ".png")
    assert "env_capture_screen" in result["path"]
    assert Path(result["path"]).exists()


def test_write_artifact_subdirs_created(tmp_path, monkeypatch):
    import adapter_core.artifact_writer as aw
    monkeypatch.setattr(aw, "ARTIFACTS_ROOT", tmp_path)
    result = write_artifact("deep/run_009", "op", b"data")
    assert Path(result["path"]).exists()
