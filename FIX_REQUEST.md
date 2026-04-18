# FIX_REQUEST — NS∞ Master — Phase ring-6 (G2 3-form Invariant)

- **Attempt:** 3 of 3
- **Workdir:** /Users/axiolevns/axiolev_runtime
- **Failing test:** ns/tests/test_ring6_g2_invariant.py
- **Branch:** boot-operational-closure
- **HEAD:** 57c26ba
- AXIOLEV Holdings LLC © 2026 — axiolevns <axiolevns@axiolev.com>

## Workdir status (first 40 lines)
```
 M .terminal_manager/logs/lineage_MASTER_20260418T231155Z.jsonl
 M .terminal_manager/logs/master_20260418T231155Z.log
?? .terminal_manager/logs/pytest_ring-6_a1_20260418T231155Z.log
?? .terminal_manager/logs/pytest_ring-6_a2_20260418T231155Z.log
?? .terminal_manager/logs/pytest_ring-6_a3_20260418T231155Z.log
?? FIX_REQUEST.md
```

## pytest tail (last 80 lines)
```
ERROR: file or directory not found: ns/tests/test_ring6_g2_invariant.py


no tests ran in 0.00s
```

## Instructions
1. Re-read PROMPT.md before editing.
2. Fix ONLY the scope needed to pass `ns/tests/test_ring6_g2_invariant.py`.
3. Preserve prior phase tags and commits.
4. Do NOT relax Canon gate thresholds or the 6 gate conditions.
5. Keep the T2/T3/T4 integration surface intact:
   - ConstraintClass enum (SACRED/RELAXABLE) exported from Ring 1
   - Alexandrian Archive layout keeps ledger/ at /Volumes/NSExternal/ALEXANDRIA/ledger/
   - ring6_phi_parallel importable from ns.domain.models.g2_invariant
   - scaffold receipt names (ns/domain/receipts/names.py) preserved
6. Do NOT reintroduce deprecated names:
   Ether, Lexicon alone, Manifold alone, Alexandria alone, CTF,
   Storytime as a layer name.
7. Bash 3.2 only in shell scripts.
8. Stop when `python3 -m pytest -x -q ns/tests/test_ring6_g2_invariant.py` is green.
