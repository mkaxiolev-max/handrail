# Copyright © 2026 Axiolev. All rights reserved.
"""Capability Registry — typed, versioned, dignity-guard mapped interface manifest."""
from __future__ import annotations

CAPABILITY_REGISTRY: list[dict] = [
    # env.*
    {"namespace":"env","op":"health","version":"1.0","side_effects":"read","deterministic":True,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"ok":"bool","mode":"str"}},
    {"namespace":"env","op":"capabilities","version":"1.0","side_effects":"read","deterministic":True,"dignity_guards":[],"schema_out":{"capabilities":"list"}},
    {"namespace":"env","op":"version","version":"1.0","side_effects":"read","deterministic":True,"dignity_guards":[],"schema_out":{"version":"str"}},
    {"namespace":"env","op":"permissions","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"permissions":"dict","all_granted":"bool","missing":"list"}},
    # audio.*
    {"namespace":"audio","op":"get_volume","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"volume":"float","muted":"bool"}},
    {"namespace":"audio","op":"set_volume","version":"1.0","side_effects":"write","deterministic":True,"dignity_guards":["range_0_100"],"schema_out":{"ok":"bool","volume_set":"float"}},
    {"namespace":"audio","op":"get_playing","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_music_not_running"],"schema_out":{"app":"str","playing":"bool","track":"str"}},
    # clipboard.*
    {"namespace":"clipboard","op":"read","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["strip_secrets"],"schema_out":{"content":"str","length":"int"}},
    {"namespace":"clipboard","op":"write","version":"1.0","side_effects":"write","deterministic":True,"dignity_guards":["max_10000_chars"],"schema_out":{"ok":"bool","length":"int"}},
    # notify.*
    {"namespace":"notify","op":"send","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"ok":"bool","delivered":"bool"}},
    {"namespace":"notify","op":"badge","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"ok":"bool"}},
    # display.*
    {"namespace":"display","op":"get_info","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"screens":"int","main_resolution":"str","brightness":"float"}},
    {"namespace":"display","op":"set_brightness","version":"1.0","side_effects":"write","deterministic":True,"dignity_guards":["range_0.0_1.0"],"schema_out":{"ok":"bool","brightness_set":"float"}},
    {"namespace":"display","op":"screenshot_info","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_no_quartz"],"schema_out":{"width":"int","height":"int","scale":"float"}},
    # battery.*
    {"namespace":"battery","op":"get_status","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_no_battery"],"schema_out":{"percent":"int","charging":"bool","time_remaining":"str","health":"str"}},
    {"namespace":"battery","op":"get_power_source","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"source":"str","ac_connected":"bool"}},
    # keychain.* — read only, strict Dignity Guard
    {"namespace":"keychain","op":"check_entry","version":"1.0","side_effects":"read","deterministic":True,"dignity_guards":["never_return_secret","block_shell_metachar"],"schema_out":{"exists":"bool","service":"str"}},
    {"namespace":"keychain","op":"list_services","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["strip_secret_lines"],"schema_out":{"services":"list","count":"int"}},
    # network.*
    {"namespace":"network","op":"http_get","version":"1.0","side_effects":"external","deterministic":False,"dignity_guards":[],"schema_out":{"status_code":"int","body":"str"}},
    {"namespace":"network","op":"port_check","version":"1.0","side_effects":"external","deterministic":False,"dignity_guards":[],"schema_out":{"open":"bool","host":"str","port":"int"}},
    {"namespace":"network","op":"dns_resolve","version":"1.0","side_effects":"external","deterministic":False,"dignity_guards":[],"schema_out":{"resolved":"bool","addresses":"list"}},
    # proc_extended.*
    {"namespace":"proc_extended","op":"list_processes","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"processes":"list","count":"int"}},
    {"namespace":"proc_extended","op":"kill_pid","version":"1.0","side_effects":"write","deterministic":True,"dignity_guards":["pid_gt_100"],"schema_out":{"ok":"bool","pid":"int"}},
    {"namespace":"proc_extended","op":"get_memory_usage","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"rss_mb":"float","vms_mb":"float"}},
    # file_watch.*
    {"namespace":"file_watch","op":"watch_path","version":"1.0","side_effects":"read","deterministic":True,"dignity_guards":[],"schema_out":{"watch_id":"str","entry_count":"int"}},
    {"namespace":"file_watch","op":"read_recent_changes","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"changes":"list","change_count":"int"}},
    # window.* — standalone window_driver, graceful skip on -1719
    {"namespace":"window","op":"list","version":"2.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_accessibility"],"schema_out":{"windows":"list","count":"int"}},
    {"namespace":"window","op":"focus","version":"2.0","side_effects":"write","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"ok":"bool","focused_app":"str"}},
    {"namespace":"window","op":"get_focused","version":"2.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_accessibility"],"schema_out":{"app":"str","title":"str"}},
    # input.* — standalone input_driver, dignity guards: accessibility + bounds + whitelist
    {"namespace":"input","op":"type","version":"2.0","side_effects":"write","deterministic":False,"dignity_guards":["requires_accessibility","max_500_chars"],"schema_out":{"ok":"bool","typed_length":"int"}},
    {"namespace":"input","op":"click","version":"2.0","side_effects":"write","deterministic":False,"dignity_guards":["requires_accessibility","bounds_0_7680_x_4320"],"schema_out":{"ok":"bool","clicked":"dict"}},
    {"namespace":"input","op":"key","version":"2.0","side_effects":"write","deterministic":False,"dignity_guards":["requires_accessibility","key_whitelist","blocked_cmd_q"],"schema_out":{"ok":"bool","key":"str"}},
    # vision.*
    {"namespace":"vision","op":"screenshot","version":"1.0","side_effects":"artifact","deterministic":False,"dignity_guards":["screen_recording_permission","artifact_written"],"schema_out":{"path":"str","hash":"str"}},
    {"namespace":"vision","op":"ocr_region","version":"1.0","side_effects":"artifact","deterministic":False,"dignity_guards":["screen_recording_permission","artifact_written"],"schema_out":{"text":"str"}},
    # fs.*
    {"namespace":"fs","op":"read_text","version":"1.0","side_effects":"read","deterministic":True,"dignity_guards":["ledger_protect","max_100kb"],"schema_out":{"content":"str","size_bytes":"int"}},
    {"namespace":"fs","op":"write_text","version":"1.0","side_effects":"write","deterministic":True,"dignity_guards":["path_allow_list_tmp_axiolev_programs"],"schema_out":{"bytes_written":"int"}},
    {"namespace":"fs","op":"list","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"entries":"list"}},
    # process.*
    {"namespace":"process","op":"list","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"processes":"list","count":"int"}},
    {"namespace":"process","op":"info","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"pid":"int","found":"bool"}},
    {"namespace":"process","op":"kill","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["blocks_system_pids_lt_500","kill_logged_to_alexandria"],"schema_out":{"ok":"bool","killed":"bool"}},
    # sys.*
    {"namespace":"sys","op":"disk_usage","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"total":"str","used":"str","pct":"str"}},
    {"namespace":"sys","op":"memory","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"total_gb":"float","used_gb":"float","pct_used":"float"}},
    {"namespace":"sys","op":"uptime","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"uptime_str":"str"}},
    # ns.*
    {"namespace":"ns","op":"proactive_intel","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"suggestions":"list"}},
]


def get_capabilities() -> list[dict]:
    return CAPABILITY_REGISTRY


def get_namespace_capabilities(namespace: str) -> list[dict]:
    return [c for c in CAPABILITY_REGISTRY if c["namespace"] == namespace]


def get_op_spec(namespace: str, op: str) -> dict | None:
    for c in CAPABILITY_REGISTRY:
        if c["namespace"] == namespace and c["op"] == op:
            return c
    return None


def get_namespaces() -> list[str]:
    return sorted({c["namespace"] for c in CAPABILITY_REGISTRY})


# Legacy index for code that imports REGISTRY_BY_NAMESPACE / REGISTRY_BY_METHOD
REGISTRY_BY_NAMESPACE: dict[str, list[dict]] = {}
REGISTRY_BY_METHOD: dict[str, dict] = {}
for _entry in CAPABILITY_REGISTRY:
    _ns = _entry["namespace"]
    REGISTRY_BY_NAMESPACE.setdefault(_ns, []).append(_entry)
    REGISTRY_BY_METHOD[f"{_entry['namespace']}.{_entry['op']}"] = _entry
