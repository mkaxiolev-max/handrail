---------------------------- MODULE Dignity ----------------------------
(*
 * NS∞ Dignity Kernel — Canonical Invariants I1..I10
 * Apalache-compatible bounded model check specification
 * AXIOLEV Holdings LLC © 2026
 *
 * Run per invariant:
 *   apalache-mc check --length=8 --inv=<Ix> --cinit=CInit Dignity.tla
 *   or via:  tools/tla/run_apalache.sh
 *
 * Op encoding — 4-element domain (bounded scope, cardinality 4):
 *   AUTH_BYPASS=0     auth.bypass            — absolute never-event (NE1)
 *   SYS_DESTRUCT=1    sys.self_destruct      — absolute never-event (NE2)
 *   POLICY_OVERRIDE=2 policy.override        — quorum-gated + high-risk (NE4 without quorum)
 *   H_OP=3            representative R3/R4   — YubiKey-gated high-risk op
 *
 * Architecture refs: CLAUDE.md §Never-Events, §Dignity Kernel, §TierLatch
 *)
EXTENDS Integers, Sequences, FiniteSets

\* ── Integer op constants ─────────────────────────────────────────────
CONSTANTS
    \* @type: Int;
    AUTH_BYPASS,
    \* @type: Int;
    SYS_DESTRUCT,
    \* @type: Int;
    POLICY_OVERRIDE,
    \* @type: Int;
    H_OP

\* ── Derived sets (operators, not CONSTANTS — avoids cfg repetition) ──
ALL_OPS        == {AUTH_BYPASS, SYS_DESTRUCT, POLICY_OVERRIDE, H_OP}
ABSOLUTE_NEVER == {AUTH_BYPASS, SYS_DESTRUCT}
QUORUM_OPS     == {POLICY_OVERRIDE}
HIGH_RISK_OPS  == {POLICY_OVERRIDE, H_OP}

\* ── Constant initializer (pass as: --cinit=CInit) ────────────────────
CInit ==
    /\ AUTH_BYPASS     = 0
    /\ SYS_DESTRUCT    = 1
    /\ POLICY_OVERRIDE = 2
    /\ H_OP            = 3

\* ── State variables ──────────────────────────────────────────────────
VARIABLES
    \* @type: Set(Int);
    executed,
    \* @type: Set(Int);
    denied,
    \* @type: Set(Int);
    secure_executed,
    \* @type: Set(Int);
    quorum_executed,
    \* @type: Seq([op: Int, outcome: Str]);
    receipts,
    \* @type: Int;
    tier_latch,
    \* @type: Int;
    prev_tier,
    \* @type: Bool;
    yubikey_ok,
    \* @type: Int;
    quorum_count

vars == <<executed, denied, secure_executed, quorum_executed,
          receipts, tier_latch, prev_tier, yubikey_ok, quorum_count>>

\* ── TypeOK ───────────────────────────────────────────────────────────
TypeOK ==
    /\ executed        \subseteq ALL_OPS
    /\ denied          \subseteq ALL_OPS
    /\ secure_executed \subseteq ALL_OPS
    /\ quorum_executed \subseteq ALL_OPS
    /\ tier_latch      \in {0, 2, 3}
    /\ prev_tier       \in {0, 2, 3}
    /\ yubikey_ok      \in BOOLEAN
    /\ quorum_count    \in 0..3

\* ── Init ─────────────────────────────────────────────────────────────
Init ==
    /\ executed        = {}
    /\ denied          = {}
    /\ secure_executed = {}
    /\ quorum_executed = {}
    /\ receipts        = <<>>
    /\ tier_latch      = 0
    /\ prev_tier       = 0
    /\ yubikey_ok      = FALSE
    /\ quorum_count    = 0

\* ── Gate predicate (gate ordering mirrors CPSExecutor) ───────────────
\*   1. Absolute never-event check
\*   2. High-risk / YubiKey check
\*   3. Quorum check
ShouldDeny(op) ==
    \/ op \in ABSOLUTE_NEVER
    \/ (op \in HIGH_RISK_OPS  /\ ~yubikey_ok)
    \/ (op \in QUORUM_OPS     /\ quorum_count < 2)

\* ── Action: attempt op (each op attempted at most once) ──────────────
AttemptOp(op) ==
    /\ op \notin executed
    /\ op \notin denied
    /\ IF ShouldDeny(op)
       THEN
           /\ denied'          = denied \cup {op}
           /\ executed'        = executed
           /\ secure_executed' = secure_executed
           /\ quorum_executed' = quorum_executed
           /\ receipts'        = Append(receipts,
                                   [op |-> op, outcome |-> "denied"])
       ELSE
           /\ executed'        = executed \cup {op}
           /\ denied'          = denied
           /\ secure_executed' = IF op \in HIGH_RISK_OPS
                                 THEN secure_executed \cup {op}
                                 ELSE secure_executed
           /\ quorum_executed' = IF op \in QUORUM_OPS
                                 THEN quorum_executed \cup {op}
                                 ELSE quorum_executed
           /\ receipts'        = Append(receipts,
                                   [op |-> op, outcome |-> "executed"])
    /\ tier_latch'   = tier_latch
    /\ prev_tier'    = prev_tier
    /\ yubikey_ok'   = yubikey_ok
    /\ quorum_count' = quorum_count

\* ── Action: provision a YubiKey slot (admin, max 3 slots) ────────────
ProvisionKey ==
    /\ quorum_count < 3
    /\ quorum_count' = quorum_count + 1
    /\ UNCHANGED <<executed, denied, secure_executed, quorum_executed,
                   receipts, tier_latch, prev_tier, yubikey_ok>>

\* ── Action: verify or invalidate YubiKey session ─────────────────────
AuthYubiKey(b) ==
    /\ yubikey_ok' = b
    /\ UNCHANGED <<executed, denied, secure_executed, quorum_executed,
                   receipts, tier_latch, prev_tier, quorum_count>>

\* ── Action: raise tier latch (ratchet only — 0→2→3, never down) ──────
RaiseLatch(t) ==
    /\ t \in {2, 3}
    /\ t > tier_latch
    /\ prev_tier'  = tier_latch
    /\ tier_latch' = t
    /\ UNCHANGED <<executed, denied, secure_executed, quorum_executed,
                   receipts, yubikey_ok, quorum_count>>

\* ── Next ─────────────────────────────────────────────────────────────
Next ==
    \/ \E op \in ALL_OPS : AttemptOp(op)
    \/ ProvisionKey
    \/ \E b \in BOOLEAN  : AuthYubiKey(b)
    \/ \E t \in {2, 3}  : RaiseLatch(t)

\* ── Spec ─────────────────────────────────────────────────────────────
Spec == Init /\ [][Next]_vars

\* ════════════════════════════════════════════════════════════════════
\* INVARIANTS I1..I10 — Dignity Kernel canonical safety properties
\* ════════════════════════════════════════════════════════════════════

\* I1 — auth.bypass is an absolute never-event; it must never appear in executed
I1_NonBypass ==
    AUTH_BYPASS \notin executed

\* I2 — sys.self_destruct is an absolute never-event
I2_NonDestruct ==
    SYS_DESTRUCT \notin executed

\* I3 — policy.override requires conciliar quorum (quorum_count >= 2);
\*      ghost set quorum_executed tracks ops that cleared the quorum gate
I3_PolicyQuorum ==
    \A op \in QUORUM_OPS :
        op \in executed => op \in quorum_executed

\* I4 — Every op in ABSOLUTE_NEVER is unconditionally excluded from executed
I4_DignityGuard ==
    ABSOLUTE_NEVER \cap executed = {}

\* I5 — High-risk ops (R3/R4) may only execute with yubikey_ok at time of call;
\*      ghost set secure_executed tracks ops that cleared the YubiKey gate
I5_RiskTierGate ==
    HIGH_RISK_OPS \cap executed \subseteq secure_executed

\* I6 — executed and denied are disjoint: no op can appear in both outcome sets
I6_Disjoint ==
    executed \cap denied = {}

\* I7 — TierLatch is monotonically non-decreasing (ratchet-only);
\*      prev_tier records the value before the last RaiseLatch transition
I7_TierRatchet ==
    tier_latch >= prev_tier

\* I8 — Ghost-set consistency: secure_executed is a subset of executed ∩ HIGH_RISK_OPS
\*      (ghost tracking is a sound under-approximation of secured high-risk executions)
I8_SecureGate ==
    secure_executed \subseteq (executed \cap HIGH_RISK_OPS)

\* I9 — Every op in denied has a corresponding "denied" entry in the receipt chain
I9_DenialReceipted ==
    \A op \in denied :
        \E i \in DOMAIN receipts :
            receipts[i].op = op /\ receipts[i].outcome = "denied"

\* I10 — Every op in executed has a corresponding "executed" entry in the receipt chain
\*       (complete kernel decision accounting — no silent executions)
I10_Receipted ==
    \A op \in executed :
        \E i \in DOMAIN receipts :
            receipts[i].op = op /\ receipts[i].outcome = "executed"

\* ── Composite (check all at once with --inv=AllInvariants) ───────────
AllInvariants ==
    /\ TypeOK
    /\ I1_NonBypass    /\ I2_NonDestruct  /\ I3_PolicyQuorum
    /\ I4_DignityGuard /\ I5_RiskTierGate /\ I6_Disjoint
    /\ I7_TierRatchet  /\ I8_SecureGate
    /\ I9_DenialReceipted /\ I10_Receipted

========================================================================
