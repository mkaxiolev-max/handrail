# SUPERMAX_PRECHECK — NS∞
**Date**: 2026-04-22T02:35Z

---

## Branch + HEAD

| Field | Value |
|-------|-------|
| Branch | `integration/max-omega-20260421-191635` |
| HEAD | `53eb44a1` |
| Remote | `https://github.com/mkaxiolev-max/handrail.git` |

## Git Status

Dirty: YES — `.verify_artifacts/RECEIPT.json` and `REPORT.md` modified (pre-existing, not introduced by this pass)

## Tags (Recent)

```
secret-closure-pre-rewrite-20260422T023701Z  ← safety tag created this pass
axiolev-habitat-strong-20260421
sovereign-boot-v9  ... (123+ tags total)
```

## Runtime Services

All 6 ports OFFLINE — Docker not running.  
Boot command: `./boot.sh`

## Scores at Precheck

| Mode | Score |
|------|-------|
| no-tests (offline safe) | 87.63 |
| live+nvir-stale | 88.26 |
| Best live (NVIR active, services up) | 92.27 (from prior session) |

## Tests at Precheck

- 1002 passed, 13 failed (integration tests need live runtime), 2 skipped
- Pure unit tests: all pass

## Scoring Instruments at Precheck

| Instrument | Score |
|-----------|-------|
| I1 | 88.8 |
| I2 | 83.8 |
| I3 | 85.1 |
| I4 | 89.4 |
| I5 | 89.7 |
| I6 | 95.97 |
| I6 sub-scores | C1=95.5, C2=99.0, C3=95.0, C4=92.5, C5=97.5 |

## NS Native UI

- Build: SUCCEEDED (arm64-apple-macosx, Debug, Xcode 26.4.1)
- ui_score: 91 / Mind Blow Capability UI ✅
