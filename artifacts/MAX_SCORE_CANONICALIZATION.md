# NS∞ MAX SCORE CANONICALIZATION — PHASE 2
**Generated**: 2026-04-21T21:42Z

---

## Problem Statement

Three overlapping v3.1 score values existed:
- 92.27 (commit `fc6a8c86`, live+NVIR)
- 91.63 (stress-cert pass, used `--no-tests`)
- 91.63 (conservative auxiliary, `--no-tests`)

The certification packets recorded 91.63 as the primary certified score while simultaneously acknowledging 92.27 as "best live." This created ambiguity about which number is canonical.

---

## Canonicalization Applied This Pass

### Change 1: `canonical` field added to scorer output

`tools/scoring/master_v31.py` — `report()` function now returns a `canonical` key:

```python
"canonical": {
    "score": v31,          # always the current-mode v3.1 score
    "mode": scoring_mode,  # "live" | "no-tests" | "live+nvir-stale" | "no-tests+nvir-stale"
    "nvir_active": nvir_fresh,
    "nvir_rate": nvir_rate,
    "note": "Run without --no-tests with fresh NVIR for canonical live score."
}
```

**Live mode** (`python3 tools/scoring/master_v31.py`):
```json
"canonical": {"score": 92.27, "mode": "live", "nvir_active": true, "nvir_rate": 0.974}
```

**Conservative mode** (`python3 tools/scoring/master_v31.py --no-tests`):
```json
"canonical": {"score": 91.63, "mode": "no-tests", "nvir_active": true}
```

### Why live is the canonical path

The live score (92.27) is:
1. **Reproducible**: `python3 tools/scoring/master_v31.py` always reproduces it when NVIR is fresh (refresh: `python3 -m services.nvir.live_loop`)
2. **Honest**: I6=95.97 reflects actual empirical 14/14 Super-Omega pass results (not conservative baselines)
3. **Complete**: NVIR credits reflect actually-measured live evolutionary performance
4. **Already committed**: commit `fc6a8c86` is tagged as the INS-02 NVIR baseline

The no-tests score (91.63) is:
1. **Conservative**: Uses I6 baseline blends only (no empirical evidence) 
2. **Auxiliary**: Useful for fast checks, not for canonical reporting
3. **Time-invariant**: Reproducible without any live components

---

## The Conservative Score Stays as Auxiliary

**91.63 is not wrong** — it represents the minimum guaranteed score with zero live data, zero test execution, using only the April 20 ceiling run baselines + NVIR credits. It is a valid lower bound.

**The public number should be 91.63** (conservative, time-invariant, cannot be disputed).  
**The internal/live number is 92.27** (requires fresh NVIR + test run, fully honest).

Both numbers coexist honestly. The `canonical.mode` field now makes this explicit in every scorer output.

---

## Canonical Scoring Reference

| Use Case | Command | Score | When |
|----------|---------|-------|------|
| Canonical live (internal) | `python3 tools/scoring/master_v31.py` | 92.27 | With fresh NVIR (within 60 min of rerun) |
| Conservative (public) | `python3 tools/scoring/master_v31.py --no-tests` | 91.63 | Any time |
| Refresh NVIR then score | `python3 -m services.nvir.live_loop && python3 tools/scoring/master_v31.py` | 92.27 | When NVIR expired |
