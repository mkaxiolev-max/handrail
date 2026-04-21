# NS∞ FINAL CLOSURE PRECHECK — PHASE 0
**Generated**: 2026-04-21T21:19Z | HEAD: 0469d2b6

---

## Git State
| Field | Value |
|-------|-------|
| Branch | integration/max-omega-20260421-191635 |
| HEAD | 0469d2b6 |
| Dirty | `.verify_artifacts/RECEIPT.json`, `.verify_artifacts/REPORT.md` (post-verify artifacts, expected) |
| Untracked | none (app_legacy committed in 0469d2b6) |

**Recent commits:**
```
0469d2b6 cert: NS∞ Final Stress+Failure+Risk+UI Certification — v3.1=91.63 Omega-Approaching
fc6a8c86 feat: INS-02 NVIR live loop — nvir_rate=0.974, v3.1=92.27 (Omega-Approaching cleared)
cf88d144 closeout: R2 tsconfig src-only + R3 pytest clean + INS-07 baselines — 999 passed
03cd4846 closeout: R1 compose + R2 ts alias + R3 pytest + INS-07 witness triad
4a03d6f1 integration: unified max-sprint + Ω-Logos — MASTER v3.1 · 16 UI sections · 14 super-omega tests
```

---

## Docker Compose — 14/14 HEALTHY
| Service | Port | Status |
|---------|------|--------|
| handrail | 8011 | ✅ ok |
| ns_core | 9000 | ✅ ok |
| continuum | 8788 | ✅ tier=0 |
| alexandria | 9001 | ✅ ok |
| ns_api | 9011 | ✅ ok |
| model_router | 9002 | ✅ ok (6 providers) |
| omega | 9010 | ✅ ok |
| omega_logos | (internal) | ✅ healthy |
| canon | 9004 | ✅ ok |
| integrity | 9005 | ✅ ok |
| violet | 9003 | ✅ ok |
| ns_ui | 3001 | ✅ HTTP 200 |
| postgres | 5433 | ✅ healthy |
| redis | 6380 | ✅ healthy |

---

## MASTER Score — Both Modes

| Mode | v3.1 | I6 | Notes |
|------|------|----|-------|
| `--no-tests` (conservative) | **91.63** | 89.95 | I6 uses baseline-only blends |
| live-tests (canonical) | **92.27** | 95.97 | 14/14 Super-Omega pass + bonus |

**NVIR live credits**: rate=0.974 (age: 28 min, TTL=60 min, FRESH)

---

## Test Suite
```
1015 passed, 2 skipped, 1 xfailed, 1 warning in 3.35s
```
Zero failures. :9090 test correctly marked xfail.

---

## Verify Script
**FIXED** (this pass): replaced stale `:9090/state` check with `:9011/health` (ns_api).  
**Result**: `READY_FOR_SHUTDOWN` — all 4 checks pass.

---

## NVIR Live State
```
rate=0.974  n_valid=500  n_total=500  corpus_size=115
ts=2026-04-21T20:51:05Z  age=28min  FRESH
```

---

## Remote Auth
- Remote: `https://github.com/mkaxiolev-max/handrail.git`
- SSH: BLOCKED (host key verification failed — no SSH key configured)
- Push: NOT DONE — branch is local only
