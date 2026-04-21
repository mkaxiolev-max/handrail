# NS∞ MAX SCORE GAP FORENSICS — PHASE 1
**Generated**: 2026-04-21T21:41Z

---

## Scores (All Modes)

| Mode | v3.1 | I6 | NVIR credits | Command |
|------|------|----|-------------|---------|
| live + NVIR (canonical) | **92.27** | 95.97 | Active (rate=0.974) | `python3 tools/scoring/master_v31.py` |
| no-tests + NVIR | **91.63** | 89.95 | Active (rate=0.974) | `python3 tools/scoring/master_v31.py --no-tests` |
| live + no NVIR | ~88.88 | 95.97 | None | (after TTL expiry, without refresh) |
| no-tests + no NVIR | ~87.39 | 89.95 | None | (cold state, no live data) |

**Gap to Omega-Certified (93.0) from canonical live: 0.73 pts**

---

## Exact Gap Decomposition

| Instrument | Current Score | Weight | Contribution | Target (×weight=93) | Shortfall |
|------------|--------------|--------|-------------|---------------------|---------|
| I1 | 88.80 | 0.135 | 11.988 | 12.555 | **-0.567** |
| I2 | 89.74 | 0.185 | 16.601 | 17.205 | **-0.604** |
| I3 | 89.34 | 0.175 | 15.635 | 16.275 | **-0.641** |
| I4 | 97.88 | 0.255 | 24.959 | 23.715 | **+1.244** (over) |
| I5 | 89.70 | 0.145 | 13.007 | 13.485 | **-0.479** |
| I6 | 95.97 | 0.105 | 10.077 | 9.765 | **+0.312** (over) |
| **Total** | | | **92.267** | **93.000** | **-0.733** |

**Key insight**: I4 and I6 are OVER-contributing relative to a uniform 93.0 distribution. The gap is entirely in I1, I2, I3, I5 — which are all in the 88-90 range and have no available NVIR credits (I1, I5) or have NVIR credits already maxed to current ceiling (I2, I3).

---

## Gap Source Analysis

### I1 shortfall: -0.567 pts
- I1 baseline: 88.80 (from April 20 ceiling run, already includes Q4 Three-Realities + Q18/Q19 improvements)
- No NVIR credits for I1 (covers perception/lexicon — not in NVIR credit formula)
- To close via I1 alone: need +5.43 pts → headroom: 11.20 → **FEASIBLE but requires new Ring capability**
- Available honest uplift: 0 pts (no grounded basis for baseline increase)

### I2 shortfall: -0.604 pts
- I2 baseline: 83.80 (post-INS-07 bump). With NVIR credit: 83.80 + 5.936 = 89.74
- NVIR rate at 1.0 (max): I2 = 83.80 + 6.30 = 90.10 → contribution = 16.669 → uplift = +0.067 pts
- To close via I2 alone: need +3.97 pts from baseline → **requires new novelty/inquiry capability**

### I3 shortfall: -0.641 pts
- I3 baseline: 85.10 (post-INS-07). With NVIR credit: 85.10 + 4.24 = 89.34
- NVIR rate at 1.0: I3 = 85.10 + 4.50 = 89.60 → uplift = +0.046 pts
- To close via I3 alone: needs +4.19 pts from baseline → **requires new execution/grounding capability**

### I5 shortfall: -0.479 pts
- I5 baseline: 89.70 (post-INS-07 bump). No NVIR credits for I5.
- To close via I5 alone: need +5.06 pts → **requires new sovereignty/memory capability**

### NVIR rate ceiling (I4/I2/I3 combined)
- Current rate: 0.974 (97.4% novel+valid), repeated on refresh — this IS the ceiling for 115-entry corpus
- If rate hits 1.0: composite uplift = +0.245 pts → 92.27 + 0.245 = **92.52** (still 0.48 short)
- Rate 0.974 = stable ceiling for this corpus size + tau_nov=0.30

---

## Uplift Lever Table

| Lever | Domain | Est. Uplift | Confidence | Cost | safe_now |
|-------|--------|-------------|------------|------|---------|
| NVIR rate 0.974→1.0 (run more steps/larger corpus) | I4/I2/I3 | +0.245 | MEDIUM | 2 min | YES |
| I6 C4 sub-baseline +5 (need evidence) | I6/C4 | +0.053 | LOW | code change | NO — not honest |
| I6 C1 sub-baseline +5 (need evidence) | I6/C1 | +0.053 | LOW | code change | NO — not honest |
| I1 baseline +1 (need new Ring capability) | I1 | +0.135 | LOW | weeks | NO |
| I5 baseline +1 (need new Ring capability) | I5 | +0.145 | LOW | weeks | NO |
| Pre-commit hook (already installed) | security | +security score | HIGH | 0 | YES |
| .gitleaksignore for false positive | security | +security score | HIGH | done | YES |
| Scorer canonical mode field | certainty | +certainty | HIGH | done | YES |
| NVIR TTL refresh automation | certainty | +certainty | HIGH | small | YES |
| I2/I3 baseline bump (DOUBLE COUNTS with NVIR credits) | I2/I3 | NOT_HONEST | — | — | NO |

**Maximum safe honest uplift from NVIR rate improvement**: +0.245 pts
**Maximum reachable score this pass**: 92.27 + 0.245 = **~92.52** (if NVIR rate reaches 1.0)
**Gap to 93.0 after max safe uplift**: **~0.48 pts** — structural gap, requires new Ring 5 work

---

## Why the Gap Cannot Be Closed This Pass

The gap is structural. I4 and I6 are already over-contributing (I4=97.88, I6=95.97 both well above 93.0). The shortfall lives entirely in I1, I2, I3, I5 which require genuine new capability for honest baseline increases. The NVIR credit formula was specifically designed to capture I2/I3/I4 uplift from NVIR work — raising those baselines additionally would be double-counting.

**Honest ceiling today**: 92.27 (live) or up to ~92.52 if NVIR rate improves. Omega-Certified (93.0) requires new Ring work, likely targeting I1 and I5 specifically.
