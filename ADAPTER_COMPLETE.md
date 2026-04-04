# handrail-adapter-macos — COMPLETE
**Timestamp:** 2026-04-04T02:47:14Z
**Commit:** b64f6e3 docs: COMPLETION_RECEIPT.md — NS∞ software phase complete, all systems verified
**Tags:** 224

## Summary

| Metric | Value |
|--------|-------|
| Adapter methods | 81 |
| Driver modules | 27 |
| Registry ops | 82 |
| Write-guard truth | 100% (35/35) |
| CPS OP_DISPATCH | 114 entries |
| HIC patterns | 89 |
| Total git tags | 224 |

## Driver Modules (27)

| Module | Namespace | Key Dignity Guards |
|--------|-----------|-------------------|
| alert_driver | alert.* | max_500_chars, input_not_logged |
| app_driver | app.* | blocked_shell_apps, launch_logged |
| audio_driver | audio.* | range_0-100 |
| battery_driver | battery.* | read_only |
| calendar_driver | calendar.* | read_only, graceful_skip_no_permission |
| clipboard_driver | clipboard.* | max_5000_chars |
| contacts_driver | contacts.* | read_only, max_10_results |
| display_driver | display.* | range_0-100 |
| env_driver | env.* | graceful_skip |
| file_watch_driver | file_watch.* | read_only |
| fs_driver | fs.* | path_allow_list, max_100kb |
| input_driver | input.* | accessibility, bounds, key_whitelist |
| keychain_driver | keychain.* | never_returns_secret |
| media_driver | media.* | range_0-100 |
| network_driver | network.* | read_only |
| notify_driver | notify.* | max_256_chars |
| ns_query_driver | ns_query.* | read_only |
| power_driver | power.* | min_5min_sleep, max_4hr_lock |
| proc_extended_driver | proc_extended.* | graceful_skip |
| process_driver | process.* | pid_lt_500_blocked, kill_logged |
| reminders_driver | reminders.* | max_200_chars, exact_name_only |
| screenshot_driver | screenshot.* | screen_recording_permission, artifact_logged |
| speech_driver | speech.* | max_1000_chars, say_logged |
| sys_driver | sys.* | read_only |
| url_driver | url.* | https_only, no_file_scheme |
| vision_driver | vision.* | screen_recording_permission |
| window_driver | window.* | graceful_skip |

## Architecture Invariants

1. **Every handler uses** `AdapterResponse.success(req, {...})` / `.failure(req, ...)` — never raw constructor
2. **Every namespace has** a standalone `*_driver/` module + `__init__.py` + `build_*_handlers()` function
3. **Every write/artifact op** has at least one dignity_guard annotation in capability_registry
4. **All tests are** isolated via monkeypatching — no real macOS calls in CI
5. **IS_MACOS gate** on every handler — clean mock path for non-macOS environments
6. **build_registry()** in `macos_driver/handlers.py` is the single registration point

## SOFTWARE: COMPLETE ✅ FROZEN ✅
**Tag:** adapter-complete-v1
