# CPI Instrument Score — NS∞
## Context + Performance + Intelligence
**Generated**: 2026-04-21 | AXIOLEV Holdings LLC © 2026

---

## CPI TOTAL: 78.95 / 100 — CPI-BETA (Operational)

```
CONTEXT     (A)  27.3 / 40   68.3%   ████████████░░░░░░░░
PERFORMANCE (B)  30.0 / 30  100.0%   ████████████████████
INTELLIGENCE(C)  21.65/ 30   72.2%   ██████████████░░░░░░
─────────────────────────────────────────────────────────
TOTAL            78.95/100   78.95%  CPI-BETA
─────────────────────────────────────────────────────────
Gap to CPI-ALPHA (80.0): 1.05 pts
Gap to CPI-OMEGA (90.0): 11.05 pts
```

---

## Sub-test Breakdown

| Sub-test | Score | Pts | Max | Status |
|----------|-------|-----|-----|--------|
| A1 Multi-needle retrieval | 37.5% | 5.6 | 15 | ⚠️ Weak |
| A2 Position bias | 66.7% | 6.7 | 10 | ⚠️ Recency gap |
| A3 MECW context scaling | 100.0% | 15.0 | 15 | ✅ |
| B1 Latency (avg 0.141s) | 100.0% | 30.0 | 30 | ✅ |
| C1 Calibration (Brier) | 46.5% | 4.65 | 10 | ⚠️ Overconfident |
| C2 Faithfulness | 100.0% | 10.0 | 10 | ✅ |
| C3 Abstention | 100.0% | 5.0 | 5 | ✅ |
| C4 Reasoning density | 40.0% | 2.0 | 5 | ⚠️ Thin |
| **TOTAL** | **78.95%** | **78.95** | **100** | **CPI-BETA** |

---

## Strengths

- **Performance perfect**: avg 0.141s, p95 0.170s, jitter 25ms. Execution is non-bottleneck.
- **MECW perfect**: Target word retrieved at all context sizes (500/2000/8000 tokens).
- **Faithfulness perfect**: Zero hallucinations. Grounded retrieval from all 3 cases.
- **Abstention perfect**: Correct refusals + correct answers. Dignity Kernel aligned.

---

## Weaknesses

- **A1 Multi-needle 37.5%**: Retrieves first fact reliably; fails on fact 2+ when query uses semantic rephrasing of key. Key-aliasing failure.
- **C1 Calibration 46.5%**: 1 factual error (17 is prime → model said No, 100% confident). Overconfidence pattern across correct answers inflates Brier penalty.
- **A2 Recency 66.7%**: Last-position fact not retrieved. Classic recency neglect.
- **C4 Reasoning 40.0%**: Step enumeration present but thin logical connectives (3.8% density).

---

## AXIOLEV Instrument Signals

| Instrument | Current v3.1 | CPI Signal | Direction |
|-----------|-------------|-----------|-----------|
| I1 Perception | 88.80 | A1=37.5%, C2=100% → implied 68.75 | ⚠️ Model gap in retrieval |
| I2 Reasoning | 89.74 | C1=46.5%, C4=40% → implied 43.9 | ⚠️ Calibration gap |
| I3 Memory | 89.34 | A3=100%, A1=37.5% → implied 81.3 | ✅ MECW strong |
| I4 Execution | 97.88 | B1=100% → implied 100 | ✅ Confirmed |
| I5 Sovereignty | 89.70 | C3=100%, A2=66.7% → implied 86.7 | ✅ Abstention strong |

CPI confirms I4/I5-abstention are NS∞ strengths; reveals model-layer gaps in I1 (retrieval) and I2 (calibration) that NS-layer infrastructure (NVIR, Alexandria) partially compensates.

---

## Optimization Path to CPI-OMEGA

| Fix | Effort | Pts | New CPI |
|-----|--------|-----|---------|
| O1: Query reformulation (A1) | 30 min | +5.6 | 84.55 |
| O4: Recency reorder (A2) | 30 min | +3.3 | 87.85 |
| O2: Confidence capping (C1) | 15 min | +2.85 | 90.70 |
| O3: Reasoning density (C4) | 15 min | +1.5 | 92.20 |
| **All four** | **90 min** | **+13.25** | **92.20 (CPI-OMEGA)** |

---

## Canonical Commands

```bash
# Run CPI harness
python3 tools/cpi/cpi_harness.py 2>/dev/null

# Artifacts
cat artifacts/CPI_SCORE.json
cat artifacts/CPI_GAP_ANALYSIS.md
cat artifacts/CPI_OPTIMIZATION_PLAN.md
```
