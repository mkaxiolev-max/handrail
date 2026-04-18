# RIL + Oracle v2 Doctrine
**AXIOLEV Holdings LLC © 2026**
**Phase:** C — T3 RIL + ORACLE v2
**Branch:** `feature/ril-oracle-v2`
**Tag:** `ril-oracle-doctrine-v2`

---

## 1. Purpose

The Reflexive Integrity Layer (RIL) + Oracle v2 doctrine governs how NS∞ evaluates,
adjudicates, and enforces constitutional integrity across all execution envelopes.
RIL operates below the Loom (L4) and above the Gradient Field (L2) as a continuous
integrity signal that gates Handrail execution.

---

## 2. Seven Integrity Engines

Each engine addresses a distinct integrity dimension. All engines run per-envelope;
their outputs compose into a `ReflexiveIntegrityState`.

| # | Engine | Responsibility |
|---|--------|---------------|
| 1 | **Drift Engine** | Detects semantic drift between successive state snapshots |
| 2 | **Grounding Engine** | Validates that claims are anchored to Alexandrian Archive evidence |
| 3 | **Commitment Engine** | Confirms that PIIC has reached the `commitment` stage before action |
| 4 | **Encounter Engine** | Resolves conflicting interpretations across NCOM branches |
| 5 | **Founder Loop Breaker** | Detects and interrupts recursive founder-intent loops |
| 6 | **Reality Binding Engine** | Binds narrative output to verifiable Gradient Field observations |
| 7 | **Interface Recalibration** | Re-synchronises the Violet Interface after integrity corrections |

Each engine emits an `IntegrityRouteEffect` classifying the net effect:
`PASS`, `WARN`, `BLOCK`, or `ESCALATE`.

---

## 3. Two-Stage Oracle Adjudication

### Stage 1 — Constitutional Overlay Check
The Oracle applies the G₂ 3-form invariant (∇φ=0, `ring6_phi_parallel`) against the
current `State Manifold` snapshot. If the overlay fails, execution is denied before
engine evaluation.

### Stage 2 — Engine Composition + Policy Matrix
All seven engine outputs are composed. The `policy_matrix` maps
`(engine_set, severity_vector) → OracleDecision`. Decisions:

| Decision | Meaning |
|----------|---------|
| `PERMIT` | Envelope passes; Handrail executes |
| `DEFER` | Requires additional NCOM/PIIC cycle |
| `BLOCK` | Constitutional violation; execution denied |
| `ESCALATE` | Founder-grade quorum required |

---

## 4. Precedence Ladder

1. **I1** (Canon precedes Conversion) — highest precedence; blocks all else
2. **I4** (Hardware quorum) — YubiKey 26116460 mandatory for canon changes
3. **I16** (Reflexive integrity monotonicity) — RIL score may not regress across ticks
4. **I17** (Oracle adjudication primacy) — Oracle decision precedes Handrail execution
5. **I18** (Reality binding integrity) — grounded claims only
6. **I19** (Founder loop protection) — recursive intent loops vetoed
7. **I20** (Precedence ladder immutability) — this ladder is SACRED; L10 may not amend

---

## 5. Invariant Extensions I16–I20

These extend the core I1–I10 stack, introduced in Phase C. They are SACRED.

| ID | Name | Statement |
|----|------|-----------|
| I16 | Reflexive Integrity Monotonicity | The aggregate RIL integrity score across ticks is non-decreasing; no backward drift permitted |
| I17 | Oracle Adjudication Primacy | Oracle `OracleDecision` must be computed and resolved before any Handrail execution envelope is dispatched |
| I18 | Reality Binding Integrity | All narrative outputs must bind to at least one verifiable Gradient Field observation; ungrounded outputs are BLOCKED |
| I19 | Founder Loop Protection | Recursive founder-intent interpretation loops (depth > 3) are unconditionally vetoed by the Founder Loop Breaker engine |
| I20 | Precedence Ladder Immutability | The RIL precedence ladder is a SACRED constitutional artefact; L10 Narrative may not reorder or amend it |

---

## 6. Doctrinal Partition (reaffirmed)

- **Models propose** — bounded to L6 State Manifold; no truth authority
- **NS decides** — via Oracle adjudication and RIL
- **Violet speaks** — L10 Narrative only; never amends L1–L9
- **Handrail executes** — only after Oracle `PERMIT`
- **Alexandrian Archive remembers** — append-only, hash-chain verified

---

## 7. Receipt Names (Phase C)

| Event | Receipt Name |
|-------|-------------|
| RIL evaluation complete | `ril_evaluation_complete` |
| Oracle adjudication issued | `oracle_adjudication_issued` |
| G₂ overlay checked | `ring6_g2_invariant_checked` |
| Founder loop vetoed | `founder_loop_veto_emitted` |
| Reality binding failed | `reality_binding_failed` |
| Integrity score regressed | `ril_integrity_regression_blocked` |

---

*AXIOLEV Holdings LLC © 2026 — append-only doctrine; supersession only per I10.*
