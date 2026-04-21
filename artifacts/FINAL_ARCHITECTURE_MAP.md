# NS∞ FINAL ARCHITECTURE MAP
**Generated**: 2026-04-21T21:01Z | Branch: integration/max-omega-20260421-191635

---

## Core Stack (3-tier)

```
                    ┌─────────────────────────────────────────┐
                    │   HANDRAIL :8011  (CPS Execution Engine) │
                    │   services/handrail/handrail/server.py   │
                    │   • POST /ops/cps  (125 ops, 25 domains) │
                    │   • Policy gates (R0–R4 risk tiers)      │
                    │   • YubiKey R3/R4 gate                   │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │   NS CORE :9000   (Constitutional AI OS) │
                    │   services/ns_core/main.py               │
                    │   • Arbiter, receipts, voice lane        │
                    │   • Ether ingest, SAN terrain            │
                    │   • YubiKey verify, meet/transcript      │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │   CONTINUUM :8788 (Append-only Event)    │
                    │   services/continuum/src/server.py       │
                    │   • TierLatch 0=active/2=isolated/3=susp │
                    │   • POST /append, /receipts              │
                    │   • SSD-backed: ALEXANDRIA/continuum     │
                    └─────────────────────────────────────────┘
```

---

## Supporting Services (11 additional)

| Service | Port | Role |
|---------|------|------|
| ns_api | 9011 | REST gateway, external-facing API |
| alexandria | 9001 | Knowledge store, ledger, receipts |
| model_router | 9002 | 6-provider LLM routing (anthropic/openai/gemini/grok/groq/ollama) |
| omega | 9010 | Omega scoring engine |
| omega_logos | 9010 (internal) | Ω-Logos spec evaluation |
| canon | 9004 | Canonical knowledge enforcement |
| integrity | 9005 | Integrity verification service |
| violet | 9003 | UI/presentation layer backend |
| ns_ui | 3001 | Next.js 16 Founder Console (src/app/, Turbopack) |
| postgres | 5433 | pgvector/pg16 persistent store |
| redis | 6380 | Cache/pub-sub |

---

## Persistence Layer — Alexandria

```
/Volumes/NSExternal/ALEXANDRIA/        (SSD primary)
~/.axiolev/ALEXANDRIA/                 (fallback)
├── ledger/
│   ├── ns_receipt_chain.jsonl         (audit log)
│   ├── kernel_decisions.jsonl         (YubiKey + R3/R4 gate decisions)
│   └── model_decisions.jsonl          (model router outcomes)
├── snapshots/                         (boot proof snapshots)
├── ether/                             (document ingest)
├── continuum/                         (TierLatch event streams)
├── nvir/
│   └── live_result.json               (NVIR live rate, TTL=1hr)
├── san/                               (SAN territory nodes)
└── programs/{namespace}/{id}.jsonl    (Program Library v1 state)
```

---

## Rings (1–5)

| Ring | Status | Key Capability |
|------|--------|----------------|
| 1 Foundations | ✅ COMPLETE | Boot, voice, receipts, Alexandria, Handrail CPS |
| 2 Intelligence | ✅ COMPLETE | Program Library v1, Model Router, Proactive Intel, Console v2 |
| 3 Sovereign | ✅ COMPLETE | YubiKey quorum, Dignity Kernel, Continuum v1, Boot Proof |
| 4 Capability | ✅ COMPLETE | SAN, Semantic Binder, Mac Adapter (73 ops), perf/crash proofs |
| 5 Production | ⛔ BLOCKED | Stripe live keys, production domain, legal entity formation |

---

## Scoring Architecture

```
tools/scoring/master_v31.py
├── BASELINES  {I1:88.80, I2:83.80, I3:85.10, I4:89.40, I5:89.70}
├── WEIGHTS_V31 {I1:0.135, I2:0.185, I3:0.175, I4:0.255, I5:0.145, I6:0.105}
├── Super-Omega (14 tests) → I6 composite (C1–C5 sub-scores)
├── INS-02 NVIR live loop → I4/I2/I3 credits (rate=0.974 → +8.48/+5.94/+4.24)
└── MASTER v3.1 = 91.63 (Omega-Approaching ✅, gap to Omega-Certified: 1.37)
```

---

## Key Security Invariants

| Invariant | Enforcement Point |
|-----------|-----------------|
| Never-events (NE1–NE4) | services/ns/nss/kernel/dignity.py |
| R3/R4 YubiKey gate | services/handrail/handrail/cps_engine.py |
| Receipt chain immutability | services/ns/nss/core/receipts.py |
| Witness cosigning (INS-07) | services/witness/__init__.py (2-of-3 HMAC quorum) |
| Canon enforcement | services/canon/main.py |
| Secrets veil | model_router veil gate |

---

## Test Coverage (1015 passing)

| Test Area | Count | Location |
|-----------|-------|----------|
| Super-Omega (I6) | 14 | tests/super_omega/ |
| NVIR live loop | 16 | tests/test_nvir_live.py |
| Witness cosigning | 14 | services/witness/tests/ |
| Adversarial | ~50 | services/ns_core/ |
| ABI/endpoint | ~30 | tests/abi/ |
| Instruments (calibration, MCI, etc.) | ~200 | tests/test_*.py |
| Handrail smoke | ~20 | services/handrail/tests/ |
| Omega/governor/hamiltonian | ~100 | tests/ |
| **TOTAL** | **1015** | — |

**1 known-acceptable failure**: `test_state_api_9090_reachable` — no :9090 service in compose.
