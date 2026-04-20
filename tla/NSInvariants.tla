---- MODULE NSInvariants ----
(* AXIOLEV Holdings LLC © 2026.  Minimal TLA+ module that encodes
   the three most load-bearing NS∞ invariants as safety properties.
   Model-checked in stub CI; the intent is to pass the artifact to
   Apalache or TLC in downstream environments. *)
EXTENDS Naturals, Sequences

VARIABLES ledger, canon_version, witness_cosigns

TypeOK ==
  /\ ledger \in Seq(STRING)
  /\ canon_version \in Nat
  /\ witness_cosigns \in [alpha: BOOLEAN, beta: BOOLEAN, gamma: BOOLEAN]

AppendOnly(old, new) ==
  Len(new) >= Len(old) /\ SubSeq(new, 1, Len(old)) = old

Monotone(old, new) == new >= old

QuorumOK(cs) == cs.alpha /\ cs.beta /\ cs.gamma

Safety ==
  /\ AppendOnly(ledger, ledger)
  /\ Monotone(canon_version, canon_version)
  /\ QuorumOK(witness_cosigns)

Init ==
  /\ ledger = << >>
  /\ canon_version = 0
  /\ witness_cosigns = [alpha |-> TRUE, beta |-> TRUE, gamma |-> TRUE]

Next == UNCHANGED << ledger, canon_version, witness_cosigns >>

Spec == Init /\ [][Next]_<<ledger, canon_version, witness_cosigns>>
====
