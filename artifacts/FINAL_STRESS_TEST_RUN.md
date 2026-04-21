# NS∞ FINAL STRESS TEST RUN — PHASE 4
**Generated**: 2026-04-21T21:03Z | Branch: integration/max-omega-20260421-191635

---

## Run 1: Governance + Invariants + Robustness
**Scope**: Constitutional policy, constraint satisfaction, behavioral stability

```
tests/test_governor.py        — zone block/review/pass/HA, delta alert/block/halt,
                                replication agree/disagree, Krippendorff perfect,
                                circuit breaker open/closed, EWMA drift, PSI stable/shifted
tests/test_hamiltonian_gate.py — ok context passes, missing receipt violates,
                                  bypass detected, coverage meaningful
tests/test_invariants_coverage.py — all 10 invariants named in repo
tests/test_robustness.py       — stable answer high score, unstable lower score

Result: 22/22 PASS  (1.49s)
```

**Key observations**:
- Circuit breaker correctly opens on repeated failures, stays closed on stable stream
- PSI (Population Stability Index) correctly detects distribution shift
- EWMA drift detection fires at calibrated threshold
- Hamiltonian gate correctly blocks bypass attempts and missing-receipt contexts
- All 10 policy invariants present in repo (no invariant gaps)

---

## Run 2: Super-Omega + NVIR Live Loop + Witness Cosigning
**Scope**: I6 instrument feed, INS-02 evolutionary scoring, INS-07 receipt integrity

```
tests/super_omega/test_cat1-7.py — 14 tests across perception/inquiry/execution/
                                    uls/memory/governance/autonomy
tests/test_nvir_live.py          — 16 tests: validity oracle, proposer uniqueness,
                                    graft mechanism, freshness TTL, credit formula
                                    (monotone, threshold, composite ≥2.3 at rate=0.80)
services/witness/tests/          — 14 tests: STH hash determinism, HMAC triad 2-of-3 quorum,
                                    tampered root rejection, consistency monotonicity

Result: 44/44 PASS  (0.08s)
```

**Key observations**:
- `test_6_2_live_key_in_args_triggers_dignity_violation`: Live API key in CPS args correctly triggers dignity violation — governance enforced at field level
- `test_4_2_unsafe_path_blocked`: ULS (Universal Local Sandbox) path traversal correctly blocked
- `test_7_1_tier_clamped_to_ceiling`: Autonomy tier correctly clamped — no unauthorized tier escalation
- `test_16_live_loop_achieves_nvir_rate`: E2E NVIR loop achieves ≥0.70 rate with structured JSON corpus
- `test_9_tampered_root_fails_verification`: Witness cosign correctly rejects tampered STH root

---

## Run 3: Replay Soundness + Three Realities + SLSA + Merkle Log
**Scope**: Append-only integrity, knowledge reconstruction, supply chain attestation

```
tests/test_replay_soundness.py  — same events same fingerprint, reorder breaks it,
                                   supersession monotone, round-trip sound
tests/test_three_realities.py   — reconstruction sound, disjointness high, tamper breaks
tests/test_slsa.py              — build+verify, tampered bytes fail
tests/test_merkle_log.py        — append grows size, inclusion proof roundtrip,
                                   tampered entry fails proof

Result: 12/12 PASS  (0.03s)
```

**Key observations**:
- Three-Reality reconstruction is sound with high disjointness (Lexicon/Alexandria/SAN layers are distinct)
- Merkle inclusion proofs correctly reject tampered entries
- SLSA attestations correctly reject tampered build artifacts
- Replay fingerprints are order-sensitive (insertion-order determines identity)

---

## Stress Summary

| Stress Area | Tests | Result | Critical Finding |
|-------------|-------|--------|-----------------|
| Governance / Policy | 22 | ✅ PASS | Circuit breaker + EWMA + PSI all correct |
| I6 / Super-Omega | 14 | ✅ PASS | Dignity violation at field level enforced |
| NVIR evolutionary loop | 16 | ✅ PASS | Live rate ≥0.70, credits monotone |
| Witness cosigning | 14 | ✅ PASS | Tamper rejection + 2-of-3 quorum |
| Replay / append-only | 4 | ✅ PASS | Fingerprint order-sensitive |
| Three Realities | 3 | ✅ PASS | Layers disjoint, reconstruction sound |
| SLSA supply chain | 2 | ✅ PASS | Tamper detection correct |
| Merkle log | 3 | ✅ PASS | Inclusion proofs correct |
| **TOTAL** | **78** | ✅ **78/78** | — |

**Zero failures in highest-value safety-critical test groups.**
