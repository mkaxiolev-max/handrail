---- MODULE NS_Invariants ----
(* AXIOLEV Holdings LLC (C) 2026 *)
EXTENDS Naturals, Sequences, TLC
VARIABLES chain, canon, dignity
TypeOK == /\ chain \in Seq(Nat) /\ canon \in [n: Nat, authored: BOOLEAN] /\ dignity \in BOOLEAN
Init == chain = <<>> /\ canon = [n |-> 0, authored |-> FALSE] /\ dignity = TRUE
Append(r) == chain' = Append(chain, r) /\ UNCHANGED <<canon, dignity>>
Next == \E r \in Nat : Append(r)
AppendOnly == [][Len(chain') >= Len(chain)]_chain
DignityHolds == [](dignity = TRUE)
Spec == Init /\ [][Next]_<<chain,canon,dignity>> /\ AppendOnly /\ DignityHolds
====
