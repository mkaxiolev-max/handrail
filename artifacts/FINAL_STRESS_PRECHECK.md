# NS∞ FINAL STRESS CERTIFICATION — PHASE 0 PRECHECK
**Generated**: 2026-04-21T21:01Z  
**Branch**: integration/max-omega-20260421-191635  
**HEAD**: fc6a8c86

---

## Git State
| Field | Value |
|-------|-------|
| Branch | integration/max-omega-20260421-191635 |
| HEAD | fc6a8c86 |
| Dirty files | `.verify_artifacts/RECEIPT.json`, `.verify_artifacts/REPORT.md` (unmodified logic), `ns_ui/app/` deleted (moved to app_legacy) |
| Tags (latest) | yubikey-v1, yubikey-quorum-v1, v1.0.0, week1-schema-fixed-*, voice-*, violet-* … (full sovereign tag set present) |

**Recent commits:**
```
fc6a8c86 feat: INS-02 NVIR live loop — nvir_rate=0.974, v3.1=92.27 (Omega-Approaching cleared)
cf88d144 closeout: R2 tsconfig src-only + R3 pytest clean + INS-07 baselines — 999 passed
03cd4846 closeout: R1 compose + R2 ts alias + R3 pytest + INS-07 witness triad
4a03d6f1 integration: unified max-sprint + Ω-Logos — MASTER v3.1 · 16 UI sections · 14 super-omega tests
a57628ab verify: ns_ui healthcheck + canon enforced field + verify artifacts
```

---

## Docker Compose — 14 Services ALL HEALTHY

| Service | Port | Status |
|---------|------|--------|
| handrail | 8011 | ✅ healthy |
| ns_core | 9000 | ✅ healthy |
| continuum | 8788 | ✅ healthy |
| alexandria | 9001 | ✅ healthy |
| ns_api | 9011 | ✅ healthy |
| model_router | 9002 | ✅ healthy |
| omega | 9010 | ✅ healthy |
| omega_logos | 9010 (internal) | ✅ healthy |
| canon | 9004 | ✅ healthy |
| integrity | 9005 | ✅ healthy |
| violet | 9003 | ✅ healthy |
| ns_ui | 3001 | ✅ HTTP 200 |
| postgres | 5433 | ✅ healthy |
| redis | 6380 | ✅ healthy |

---

## MASTER Score (no-tests, live NVIR credits applied)

| Version | Score |
|---------|-------|
| v2.1 | 91.95 |
| v3.0 | 91.68 |
| **v3.1** | **91.63** |

**Bands**: Omega-Approaching ✅ (≥90.0) | Omega-Certified ❌ (need ≥93.0, gap 1.37)

**Instruments (with NVIR live credits, rate=0.974):**
- I1: 88.80 | I2: 89.74 | I3: 89.34 | I4: 97.88 | I5: 89.70 | I6: 89.95

**I6 Sub-scores (baseline blend):**
- C1: 89.0 | C2: 96.0 | C3: 88.0 | C4: 83.0 | C5: 93.0

---

## Test Suite
```
1015 passed, 1 failed, 2 skipped — 3.39s
FAILED: tests/abi/test_endpoint_fixes.py::test_state_api_9090_reachable
  → Expected offline (no :9090 service in compose); KNOWN/ACCEPTABLE
```

---

## Continuum State
- Global tier: 0 (ACTIVE)
- All streams at 0 events (clean slate)
- SSD mounted: true
- Data dir: /Volumes/NSExternal/ALEXANDRIA/continuum

---

## Key External State
- NVIR live result: `/Volumes/NSExternal/ALEXANDRIA/nvir/live_result.json` — rate=0.974, ts fresh
- Alexandria SSD: `/Volumes/NSExternal/ALEXANDRIA` mounted
- Model Router: 6 providers live (anthropic/openai/gemini/grok/groq/ollama)
