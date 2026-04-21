# NS∞ MAX UPLIFT APPLIED — PHASE 3
**Generated**: 2026-04-21T21:42Z

---

## Applied Uplifts

### U1: NVIR Refresh (rate stability confirmed)
**Domain**: I4/I2/I3  
**File**: `/Volumes/NSExternal/ALEXANDRIA/nvir/live_result.json`  
**Action**: Re-ran `LiveNVIRLoop(n_steps=500, n_islands=5)` against 115-entry Alexandria corpus.  
**Result**: rate=0.974 (stable — same as prior run). 500/500 valid, 487/500 novel+valid.  
**Score impact**: 0 (rate unchanged). TTL reset to fresh (60 min window extended).  
**Safety**: zero risk — read-only against corpus, result written to Alexandria NVIR dir.  
**Verdict**: NVIR rate 0.974 is the **stable ceiling** for the current 115-entry corpus with tau_nov=0.30. Not a regression.

### U2: Scorer Canonical Mode Field
**Domain**: certainty / scoring  
**File**: `tools/scoring/master_v31.py`  
**Action**: Added `canonical` dict to `report()` return with `score`, `mode`, `nvir_active`, `nvir_rate`, `note` fields.  
**Before**: No programmatic distinction between live and conservative mode in output.  
**After**: Every scorer run explicitly declares its mode. `canonical.mode = "live"` when tests ran + NVIR fresh.  
**Score impact**: +certainty (documented canonical path). No raw score change.  
**Safety**: Additive field, backward-compatible.

### U3: `.gitleaksignore` Created
**Domain**: security  
**File**: `.gitleaksignore`  
**Action**: Added annotation to suppress `stripe-access-token` false positive in `services/handrail-adapter-macos/tests/test_clipboard.py`.  
**Before**: 19 findings in gitleaks scan (1 false positive inflating count).  
**After**: 18 real findings, false positive suppressed.  
**Score impact**: +security_score (false positive removed from finding count).  
**Safety**: Only suppresses confirmed false positive. Real findings still reported.

### U4: Pre-Commit Hook — Confirmed Present (prior session)
**Domain**: security  
**File**: `.git/hooks/pre-commit`  
**Status**: ALREADY INSTALLED — blocks `ghp_*`, `github_pat_*`, `sk_live_*`, `sk_test_*`, `whsec_*`, `AKIA*`, `AIza*`, `xox*`.  
**Also**: calls `gitleaks protect --staged` if gitleaks is available.  
**Score impact**: security_score corrected upward (was underestimated in prior pass).

---

## Candidates Investigated and Not Applied

### Not Applied: NVIR more steps (500→1000)
**Reason**: rate 0.974 is stable ceiling — more steps don't increase novelty rate given current corpus. Confirmed by two independent runs both returning 0.974.

### Not Applied: I6 sub-baseline adjustments
**Reason**: C4=81.0 is the weakest sub-baseline. Raising it without evidence of new memory replay capability would fabricate green state. The empirical blended score (92.5) already exceeds the baseline, which is the correct behavior.

### Not Applied: I1/I5 baseline increases
**Reason**: Current baselines reflect April 20 ceiling + INS-07 bumps. No new I1/I5 capability has been added. Raising these would be dishonest.

### Not Applied: NVIR tau_nov reduction (0.30→0.20)
**Reason**: Would lower the novelty threshold, weakening the meaning of "novel." NOT honest.

---

## Score After Applied Uplifts

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| v3.1 live | 92.27 | **92.27** | 0 (rate unchanged) |
| v3.1 no-tests | 91.63 | **91.63** | 0 |
| certainty_score | 87 | **90** | +3 (canonical field + mode clarity) |
| security_score | 68 | **78** | +10 (hook confirmed + FP removed) |
| gitleaks findings | 19 | **18** | -1 (FP suppressed) |

**Raw score cannot be honestly improved beyond 92.27 in this pass.** The gap to 93.0 is structural. All safe uplifts have been applied.
