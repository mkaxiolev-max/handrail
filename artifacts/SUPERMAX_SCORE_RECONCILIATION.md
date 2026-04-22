# SUPERMAX_SCORE_RECONCILIATION — NS∞
**Date**: 2026-04-22T02:40Z

---

## Score Modes

| Mode | Score | Notes |
|------|-------|-------|
| **no-tests** | 87.63 | Reproducible offline. Does not require runtime. NVIR stale (no services). |
| **live+nvir-stale** | 88.26 | Runs test suite (1002 pass / 13 fail). NVIR credits zero. |
| **live+nvir-active** | ~92.27 | Requires services running + NVIR loop feeding realtime data. Previously achieved. |

---

## Delta Explanation

The gap between 87.63 and 92.27 = **4.64 points**.

Components of the gap:
1. **Test failures (-0.63)**: 13 integration tests fail when services offline. When services up, all pass.
2. **NVIR live credits (~+3.7)**: NVIR (NS Validity Invariant Rate) credits are active only when services produce live NVIR data. Previously achieved nvir_rate=0.974.
3. **Live API checks (~+0.3)**: Some instruments check live endpoint health, scoring higher when all 6 services respond.

---

## Reproducible Commands

```bash
# Conservative / certified (offline-safe):
python3 tools/scoring/master_v31.py --no-tests 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['canonical']['score'])"

# Live score (with tests, services needed):
python3 tools/scoring/master_v31.py 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['canonical']['score'])"

# Best live (requires services running + NVIR loop):
./boot.sh && sleep 60 && python3 tools/scoring/master_v31.py 2>/dev/null
```

---

## Public vs Internal Score

| Score | Value | Context |
|-------|-------|---------|
| **Public/certified** | 87.63 | Reproducible without runtime. Conservative. Safe to state publicly. |
| **Internal best** | 92.27 | Achieved with live services + NVIR active. Reproducible via boot.sh sequence. |
| **SUPERMAX composite** | 87.0 | SUPERMAX 100-pt rubric score (security, ui, certainty, all 9 domains) |

---

## Live Credits Active

No — NVIR stale. Services offline. Live credits require ./boot.sh + runtime.
