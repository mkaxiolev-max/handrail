# NS∞ FINAL SCORE RECONCILIATION — PHASE 1
**Generated**: 2026-04-21T21:19Z

---

## The Score Fragmentation Explained

Three v3.1 scores have appeared across this session:

| Score | Context | Cause |
|-------|---------|-------|
| **92.27** | Commit `fc6a8c86` (INS-02 NVIR) | Full test run — Super-Omega empirical I6 + NVIR credits |
| **91.63** | Stress-cert packet (Phase 5) | `--no-tests` flag used — I6 falls back to baseline-only blend |
| **91.63** | Verify script artifact | Same `--no-tests` call |

**Root cause of delta (0.64 pts)**:  
`compute_i6_subs()` with no test data uses `I6_SUB_BASELINES` (C1=87, C2=94, C3=86, C4=81, C5=91) blended at 0.4×emp + 0.6×baseline when no empirical rate is available, producing I6=89.95.  
With 14/14 Super-Omega passes, the empirical rate is 1.00 for all categories → blended = min(100, 0.5×100 + 0.5×baseline + 2.0), producing I6=95.97.

The **live-test score of 92.27 is the correct canonical score** because:
1. It was the score at the moment INS-02 was committed and tagged
2. It is fully reproducible by running `python3 tools/scoring/master_v31.py` (no flags)
3. The Super-Omega test results (14/14) are the honest empirical feed for I6
4. The `--no-tests` mode is a fast approximate mode, not the authoritative mode

---

## Current Reproducibility Confirmation

**Command**: `python3 tools/scoring/master_v31.py`  
**Result** (just run):

| Instrument | Score |
|------------|-------|
| I1 | 88.80 |
| I2 | 89.74 (NVIR credit: +5.94) |
| I3 | 89.34 (NVIR credit: +4.24) |
| I4 | 97.88 (NVIR credit: +8.48) |
| I5 | 89.70 |
| I6 | 95.97 (Super-Omega 14/14, empirical blend) |

| Version | Score |
|---------|-------|
| v2.1 | 91.95 |
| v3.0 | 92.26 |
| **v3.1** | **92.27** |

**NVIR live credits**: Active — rate=0.974, TTL fresh (28 min of 60 min elapsed).

---

## Score Modes Summary

| Mode | Score | When to use |
|------|-------|-------------|
| `python3 tools/scoring/master_v31.py` | **92.27** | Canonical / authoritative (live I6 + NVIR) |
| `python3 tools/scoring/master_v31.py --no-tests` | **91.63** | Conservative fast mode (no subprocess test runs) |
| After NVIR TTL expiry (>60 min, no refresh) | ~88.88 | NVIR credits drop to 0 |

---

## Canonical Final Score

**certified_score** (conservative, public-safe): **91.63**  
→ No dependencies on time-bound live state. Reproducible forever from current baselines + `--no-tests`.

**best_live_score** (authoritative with fresh state): **92.27**  
→ Requires fresh NVIR result (refresh: `python3 -m services.nvir.live_loop`) + test run.

**Delta**: 0.64 pts (I6 empirical uplift from 89.95 → 95.97 via 14/14 Super-Omega)

**Gap to Omega-Certified (93.0)**:  
- From live score: **0.73 pts**  
- From certified score: **1.37 pts**
