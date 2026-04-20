------------------------------ MODULE AXIOLEV ------------------------------
EXTENDS Naturals, Sequences, FiniteSets
CONSTANTS Agents, HICHolders, GenesisHash, MaxLen
ASSUME HICHolders \subseteq Agents /\ MaxLen \in Nat
VARIABLES ledger, hicCapability, signatures
vars == <<ledger, hicCapability, signatures>>
Hash(entry) == entry.parent + 1
Init ==
    /\ ledger = <<>>
    /\ hicCapability = HICHolders
    /\ signatures = [a \in {} |-> {}]
AppendEntry(e) ==
    /\ Len(ledger) < MaxLen
    /\ \/ Len(ledger) = 0 /\ e.parent = 0
       \/ Len(ledger) > 0 /\ e.parent = Hash(ledger[Len(ledger)])
    /\ ledger' = Append(ledger, e)
    /\ UNCHANGED <<hicCapability, signatures>>
IssueVeto(agent, actionId) ==
    /\ agent \in hicCapability
    /\ LET e == [type |-> "VETO", issuer |-> agent,
                 parent |-> IF Len(ledger)=0 THEN 0 ELSE Hash(ledger[Len(ledger)]),
                 action |-> actionId]
       IN AppendEntry(e)
SignAction(agent, actionId) ==
    /\ signatures' = [signatures EXCEPT
           ![actionId] = (IF actionId \in DOMAIN signatures THEN signatures[actionId] ELSE {})
                         \cup {[keyId |-> agent, sig |-> "valid"]}]
    /\ UNCHANGED <<ledger, hicCapability>>
Next ==
    \/ \E agent \in HICHolders, aid \in {"a1","a2","a3"} : IssueVeto(agent, aid)
    \/ \E agent \in Agents, aid \in {"a1","a2","a3"} : SignAction(agent, aid)
Spec == Init /\ [][Next]_vars
AppendOnly == [][\A i \in 1..Len(ledger) : i <= Len(ledger') /\ ledger'[i] = ledger[i]]_vars
ChainIntegrity == \A i \in 2..Len(ledger) : ledger[i].parent = Hash(ledger[i-1])
HICVetoAuthorized == \A i \in 1..Len(ledger) : (ledger[i].type = "VETO") => (ledger[i].issuer \in hicCapability)
Safety == AppendOnly /\ ChainIntegrity /\ HICVetoAuthorized
============================================================================
