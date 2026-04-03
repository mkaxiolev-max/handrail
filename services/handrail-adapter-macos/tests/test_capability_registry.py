"""Tests for capability_registry — structural completeness checks."""
from __future__ import annotations
import pytest
from adapter_core.capability_registry import (
    CAPABILITY_REGISTRY, get_capabilities, get_namespace_capabilities,
    get_op_spec, get_namespaces,
)

VALID_SIDE_EFFECTS = {"read", "write", "external", "artifact", "stateful"}


def test_all_entries_have_required_fields():
    required = {"namespace", "op", "version", "side_effects", "deterministic", "dignity_guards", "schema_out"}
    for entry in CAPABILITY_REGISTRY:
        missing = required - entry.keys()
        assert not missing, f"{entry['namespace']}.{entry['op']} missing: {missing}"


def test_all_side_effects_valid():
    for entry in CAPABILITY_REGISTRY:
        assert entry["side_effects"] in VALID_SIDE_EFFECTS, \
            f"{entry['namespace']}.{entry['op']} bad side_effects: {entry['side_effects']}"


def test_all_deterministic_is_bool():
    for entry in CAPABILITY_REGISTRY:
        assert isinstance(entry["deterministic"], bool)


def test_all_dignity_guards_are_list():
    for entry in CAPABILITY_REGISTRY:
        assert isinstance(entry["dignity_guards"], list)


def test_all_schema_out_is_dict():
    for entry in CAPABILITY_REGISTRY:
        assert isinstance(entry["schema_out"], dict), \
            f"{entry['namespace']}.{entry['op']} schema_out must be dict"


def test_get_namespace_audio():
    caps = get_namespace_capabilities("audio")
    assert len(caps) == 3
    ops = {c["op"] for c in caps}
    assert ops == {"get_volume", "set_volume", "get_playing"}


def test_get_namespace_keychain():
    caps = get_namespace_capabilities("keychain")
    assert len(caps) == 2


def test_keychain_check_entry_dignity_guard():
    spec = get_op_spec("keychain", "check_entry")
    assert spec is not None
    assert "never_return_secret" in spec["dignity_guards"]
    assert "block_shell_metachar" in spec["dignity_guards"]


def test_keychain_check_entry_is_read_only():
    spec = get_op_spec("keychain", "check_entry")
    assert spec["side_effects"] == "read"


def test_get_capabilities_returns_all():
    caps = get_capabilities()
    assert len(caps) >= 32


def test_get_namespaces():
    ns = get_namespaces()
    for expected in ["audio", "battery", "clipboard", "display", "env", "file_watch",
                     "keychain", "network", "notify", "proc_extended"]:
        assert expected in ns, f"{expected} missing from namespaces"


def test_no_duplicate_ops():
    seen: set[str] = set()
    for entry in CAPABILITY_REGISTRY:
        key = f"{entry['namespace']}.{entry['op']}"
        assert key not in seen, f"Duplicate: {key}"
        seen.add(key)


def test_env_permissions_in_registry():
    spec = get_op_spec("env", "permissions")
    assert spec is not None
    assert spec["side_effects"] == "read"
    assert "all_granted" in spec["schema_out"]
    assert "missing" in spec["schema_out"]


def test_audio_set_volume_dignity_guard():
    spec = get_op_spec("audio", "set_volume")
    assert spec is not None
    assert "range_0_100" in spec["dignity_guards"]
    assert spec["side_effects"] == "write"


def test_clipboard_read_strips_secrets():
    spec = get_op_spec("clipboard", "read")
    assert "strip_secrets" in spec["dignity_guards"]


def test_display_set_brightness_guard():
    spec = get_op_spec("display", "set_brightness")
    assert "range_0.0_1.0" in spec["dignity_guards"]


def test_registry_by_method_index():
    from adapter_core.capability_registry import REGISTRY_BY_METHOD
    assert "audio.get_volume" in REGISTRY_BY_METHOD
    assert "keychain.check_entry" in REGISTRY_BY_METHOD


def test_registry_by_namespace_index():
    from adapter_core.capability_registry import REGISTRY_BY_NAMESPACE
    assert "audio" in REGISTRY_BY_NAMESPACE
    assert len(REGISTRY_BY_NAMESPACE["audio"]) == 3
