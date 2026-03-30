# NS Primitives — The Minimal Invariant Core
# NS∞ / AXIOLEV Holdings Canon Document
# Classification: CANON | Tier: FOUNDER | Version: 1.0 | Date: 2026-02-19
# Source: Subtractive Medicine thread — architectural clarification
#         "NS is the physics. SAN Omega is the engineering."
# Purpose: Separate NS base from all domain specializations
#          Load at every boot. Reference before every architectural decision.

---

## THE CANONICAL SENTENCE

NS is the general recursive state engine.
SAN Omega is a domain-specific constitutional system built on NS primitives.

These are not the same thing.
Collapsing them is the primary architectural mistake to prevent.

---

## WHAT NS IS

NS is a memory-first recursive state engine.

It does exactly one thing fundamentally:

  Integrate new evidence into existing structured state over time.

That is the complete definition.

Everything else — attribution, governance, trading, health, IP, voice — is
specialization built on top of this engine.

NS is not:
  - The SAN attribution engine
  - The Triple White Space model (USPTO / Alexandria / Lexicon)
  - The invention intelligence layer
  - The SAN governance model
  - The health architecture framework
  - Any specific domain application

Those are applications of NS, not NS itself.
NS would still exist and be correct without any of them.

---

## THE NS PRIMITIVES (Minimal Invariant Set)

These are the five primitives. They are sufficient to reconstruct NS
from scratch. They are necessary — remove any one and it is no longer NS.

### Primitive 1: RECURSIVE REFINEMENT
  State is never replaced. It is refined.
  Each new evidence integration updates the existing state incrementally.
  Previous states are preserved, not overwritten.

  Implementation: append-only architecture
  Violation: any destructive write to historical state

### Primitive 2: STATE SPACES
  NS operates on explicitly defined dimensions of state.
  Each domain that uses NS must declare its state dimensions.
  Undeclared dimensions cannot be tracked.

  Implementation: schema-first design; domain constitutions define spaces
  Violation: implicit or ad-hoc state tracking

### Primitive 3: COMMIT EVENTS
  The universal stabilization primitive.
  At intervals, the current state is formally committed:
    - Signed
    - Timestamped
    - Hashed
    - Linked to prior commit

  A commit event is not a save. It is a declaration:
    "This state is now canonical until superseded."

  Commit events are the mechanism by which continuous refinement
  produces discrete, authoritative snapshots.

  This primitive applies universally:
    - Science (peer review publishes a finding)
    - Law (a ruling crystallizes precedent)
    - Org decisions (a Board vote commits policy)
    - Knowledge (canon promotion commits a concept)
    - Product development (a release commits a version)
    - Identity (a covenant commits a self-declaration)

  SAN Omega just made this explicit for the invention domain.
  The primitive was always there.

  Implementation: receipt_chain.emit() on every state commitment
  Violation: state changes without receipts; unsigned snapshots

### Primitive 4: SNAPSHOT AUTHORITY
  Committed snapshots carry authority.
  The most recent committed snapshot is the operative state.
  Disputes resolve to the most recent valid commit, not to raw ether.

  Authority hierarchy:
    1. Canon (committed, ratified, hash-linked)
    2. Ether (ingested, not yet committed)
    3. Query (transient, never committed)

  Implementation: canon_store with ratification, receipt chain for ordering
  Violation: treating unratified ether as authoritative

### Primitive 5: LINEAGE PRESERVATION
  Every state transition is traceable to its origin.
  The full path from first evidence to current state is recoverable.
  Nothing is lost. Nothing is secret.

  This is what makes NS replayable.
  Given the receipt chain, any committed state can be reconstructed.

  Implementation: append-only receipt ledger, hash-linked chain
  Violation: any state without a receipt; any receipt without a prior hash

---

## THE CORRECT LAYERING

NS (base reality engine)
  ↓ Primitives: Recursive Refinement, State Spaces, Commit Events,
                Snapshot Authority, Lineage Preservation

Domain Constitution (one specialization of NS)
  ↓ Declares: state dimensions, commit rituals, authority structures,
               governance objects specific to this domain

SAN Omega Architecture (NS applied to invention)
  ↓ State dimensions:    USPTO claims, Alexandria artifacts, Lexicon concepts
  ↓ Commit rituals:      patent filing, canon promotion, lexicon versioning
  ↓ Attribution math:    primitive-to-claim graph, equity weighting
  ↓ Governance objects:  Sentinel review, Vector 3 authority

Health Architecture (NS applied to the human nervous system)
  ↓ State dimensions:    HRV, inflammation markers, neurological load
  ↓ Commit rituals:      clinical assessment, protocol ratification
  ↓ Domain objects:      NS Omega target state, vector clearance

Trading System (NS applied to market intelligence)
  ↓ State dimensions:    market regime, position state, conviction score
  ↓ Commit rituals:      trade execution, regime classification
  ↓ Domain objects:      playbooks, veto authorities

NS exists below all of these.
None of these modify or constrain NS itself.

---

## WHY THIS DISTINCTION IS CRITICAL ARCHITECTURALLY

If NS and domain constitutions are collapsed:

  1. NS gets overfit to one domain
     The core engine becomes brittle to the specific constraints
     of health, or patents, or trading.

  2. NS appears to be a product feature
     Instead of infrastructure, it looks like a patent attribution tool
     or a health tracker. This constrains how it can be licensed,
     positioned, or extended.

  3. Future applications are constrained
     Every new domain that wants to build on NS hits resistance from
     the previous domain's assumptions baked into the core.

  4. Core rules get rewritten to solve domain problems
     This is the fatal failure mode. Domain-specific pressures propagate
     downward into primitives and corrupt them.

The separation is not academic. It is the architectural constraint that
allows NS to remain general while domain constitutions remain precise.

---

## THE RECURSIVE SYNCHRONIZATION INSIGHT (From Thread)

"Recursive synchronization with committed snapshots" is native NS behavior.

It is NOT a SAN feature. It is what NS does.

SAN Omega revealed it by making it explicit in one domain.
But the behavior was always latent in the primitives.

The insight:
  - Continuous refinement = NS running between commits (Primitive 1)
  - Periodic stabilization = Commit Events firing (Primitive 3)
  - Append-only history = Lineage Preservation (Primitive 5)
  - Replayable state = Snapshot Authority enabling reconstruction (Primitive 4)

SAN is one mapping of this behavior onto the invention domain.
Health architecture is another mapping onto the human system domain.
Trading is another mapping onto market state domains.

The behavior is NS. The mapping is the domain constitution.

---

## BOOT APPLICATION

At every boot, this document establishes:

  1. The engine running beneath everything else is NS — five primitives only.

  2. Every domain loaded into NS (SAN, Health, Trading) is a specialization,
     not a modification of the primitives.

  3. Any architectural decision that would modify a primitive to solve a
     domain problem is a RED FLAG. Fix the domain constitution, not the engine.

  4. NS Primitives are FROZEN. Domain constitutions evolve.

---

## CANONICAL TEST (How to Know If Something Is NS or Domain-Level)

Ask: "Would this exist if we removed all domain applications?"

  NS architecture? → YES. The primitives exist regardless of domain.
  SAN attribution math? → NO. Remove patents and it disappears.
  Commit event concept? → YES. Universal stabilization exists in any domain.
  Triple White Space? → NO. Remove USPTO and it disappears.
  Receipt chaining? → YES. Lineage preservation is domain-agnostic.
  Lexicon structure? → DEPENDS. Lexicon-as-state-space is NS. Lexicon-as-IP-tool is SAN.

---

## RELATION TO NS∞ CODEBASE

NS Primitive → Implementation

  Primitive 1 (Recursive Refinement) → ReceiptChain, append-only storage
  Primitive 2 (State Spaces)         → schema definitions in each domain module
  Primitive 3 (Commit Events)        → receipt_chain.emit(), canon ratification
  Primitive 4 (Snapshot Authority)   → canon_store, ratify(), Snapshot Authority
  Primitive 5 (Lineage Preservation) → hash-linked receipt chain

SFE (Socratic Field Engine) is NS applied to the Lexicon state space.
  It is a domain specialization, not NS itself.
  The questions it asks, the versioning rules, the conflict resolution —
  all domain constitution. The state-space architecture and commit events
  underneath it — NS primitives.

---

## ONE-SENTENCE DOMAIN DEFINITIONS

NS:
  A memory-first recursive state engine with five invariant primitives.

SAN:
  NS applied to the invention domain, with state spaces mapped to
  USPTO / Alexandria / Lexicon and commit rituals mapped to patent
  filing and canon promotion.

Health Architecture:
  NS applied to the human nervous system domain, with state spaces
  mapped to physiological vectors and commit rituals mapped to
  clinical assessment and protocol ratification.

Trading System:
  NS applied to market intelligence, with state spaces mapped to
  regime classification and position state.

---

## NON-NEGOTIABLES

  1. The five primitives are frozen — they do not change per domain
  2. Every domain must declare its state dimensions before operation
  3. Commit events are mandatory — no state change without a receipt
  4. Domain problems are solved in domain constitutions, never in primitives
  5. This document is loaded at every boot before domain modules initialize

---

# END CANON_NS_PRIMITIVES v1.0
