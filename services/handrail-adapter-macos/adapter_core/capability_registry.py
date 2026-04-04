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
    # app.*
    {"namespace":"app","op":"launch","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["blocked_shell_apps","launch_logged"],"schema_out":{"ok":"bool","launched":"bool"}},
    {"namespace":"app","op":"quit","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"ok":"bool","quit":"bool"}},
    {"namespace":"app","op":"is_running","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"running":"bool"}},
    {"namespace":"app","op":"list_open","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"apps":"list","count":"int"}},
    # ns_query.*
    {"namespace":"ns_query","op":"health_full","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"ok":"bool","subsystems":"dict"}},
    {"namespace":"ns_query","op":"context","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"ok":"bool","context":"dict"}},
    {"namespace":"ns_query","op":"last_error","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"ok":"bool","last_error":"any"}},
    # alert.*
    {"namespace":"alert","op":"dialog","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["max_500_chars","no_screen_recording_block"],"schema_out":{"ok":"bool","button":"str","cancelled":"bool"}},
    {"namespace":"alert","op":"confirm","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"ok":"bool","confirmed":"bool"}},
    {"namespace":"alert","op":"input","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["input_never_logged","max_200_chars"],"schema_out":{"ok":"bool","value":"str","cancelled":"bool"}},
    # calendar.*
    {"namespace":"calendar","op":"list","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_no_permission"],"schema_out":{"calendars":"list","count":"int"}},
    {"namespace":"calendar","op":"today","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_no_permission"],"schema_out":{"events":"list","count":"int"}},
    {"namespace":"calendar","op":"upcoming","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_no_permission","max_20_events"],"schema_out":{"events":"list","count":"int"}},
    # contacts.*
    {"namespace":"contacts","op":"search","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["max_10_results","read_only"],"schema_out":{"contacts":"list","count":"int"}},
    {"namespace":"contacts","op":"count","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"count":"int"}},
    {"namespace":"contacts","op":"vcard","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["read_only","name_field_only"],"schema_out":{"vcard":"str","found":"bool"}},
    # reminders.*
    {"namespace":"reminders","op":"list","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["graceful_skip_no_permission"],"schema_out":{"reminders":"list","count":"int"}},
    {"namespace":"reminders","op":"add","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["max_200_chars"],"schema_out":{"ok":"bool","added":"bool"}},
    {"namespace":"reminders","op":"complete","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["exact_name_only","no_bulk_delete"],"schema_out":{"ok":"bool","completed":"bool"}},
    # url.*
    {"namespace":"url","op":"open","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["https_only","no_file_scheme","no_javascript_scheme"],"schema_out":{"ok":"bool","opened":"bool"}},
    {"namespace":"url","op":"fetch","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["https_only","timeout_10s","max_5000_chars"],"schema_out":{"ok":"bool","content":"str","status":"int"}},
    {"namespace":"url","op":"qr","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":["https_only"],"schema_out":{"ok":"bool","qr_base64":"str"}},
    # speech.*
    {"namespace":"speech","op":"say","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["max_1000_chars","say_logged"],"schema_out":{"ok":"bool","said":"str"}},
    {"namespace":"speech","op":"say_async","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["max_1000_chars"],"schema_out":{"ok":"bool","queued":"bool"}},
    {"namespace":"speech","op":"voices","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"voices":"list","count":"int"}},
    {"namespace":"speech","op":"stop","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":[],"schema_out":{"ok":"bool","stopped":"bool"}},
    # power.*
    {"namespace":"power","op":"battery","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"charge_pct":"int","status":"str"}},
    {"namespace":"power","op":"sleep","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["min_5_minute_delay"],"schema_out":{"ok":"bool","scheduled_minutes":"int"}},
    {"namespace":"power","op":"wake_lock","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["max_4_hours"],"schema_out":{"ok":"bool","seconds":"int"}},
    {"namespace":"power","op":"cancel_wake_lock","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":[],"schema_out":{"ok":"bool","cancelled":"bool"}},
    # media.*
    {"namespace":"media","op":"now_playing","version":"1.0","side_effects":"read","deterministic":False,"dignity_guards":[],"schema_out":{"playing":"bool","track":"str"}},
    {"namespace":"media","op":"play_pause","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"ok":"bool","toggled":"bool"}},
    {"namespace":"media","op":"next","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["graceful_skip_non_macos"],"schema_out":{"ok":"bool","skipped":"bool"}},
    {"namespace":"media","op":"volume","version":"1.0","side_effects":"write","deterministic":False,"dignity_guards":["range_0_100"],"schema_out":{"ok":"bool","volume":"int"}},
    # screenshot.*
    {"namespace":"screenshot","op":"region","version":"1.0","side_effects":"artifact","deterministic":False,"dignity_guards":["screen_recording_permission","artifact_written","logged"],"schema_out":{"ok":"bool","path":"str","hash":"str"}},
    {"namespace":"screenshot","op":"window","version":"1.0","side_effects":"artifact","deterministic":False,"dignity_guards":["screen_recording_permission","artifact_written"],"schema_out":{"ok":"bool","path":"str","hash":"str"}},
    {"namespace":"screenshot","op":"annotate","version":"1.0","side_effects":"artifact","deterministic":False,"dignity_guards":["screen_recording_permission","artifact_written","logged"],"schema_out":{"ok":"bool","path":"str","ts":"str"}},
    {"namespace":"screenshot","op":"diff","version":"1.0","side_effects":"artifact","deterministic":False,"dignity_guards":["screen_recording_permission"],"schema_out":{"ok":"bool","changed":"bool","changed_pct":"int"}},
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
