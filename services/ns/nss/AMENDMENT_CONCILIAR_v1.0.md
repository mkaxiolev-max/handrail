# NS Conciliar Architecture Amendment
# Northstar OS Governance Upgrade
# Version 1.0 | 2026-02-18
# Classification: CANON — Constitutional Level
# Status: PROPOSED — requires founder ratification to take effect

---

## PREAMBLE

This amendment upgrades Northstar's governance topology from an
implicit Roman model (centralized arbitration, single promotion path,
strong top authority) to an Orthodox Conciliar model (distributed
domain sovereignty, council-based canon promotion, founder as first
among equals rather than executive monarch).

This is not a rebrand. It changes the attack surface, the
legitimacy topology, and the failure modes of the system.

The amendment does not alter:
  - Alexandria's append-only guarantee
  - Founder emergency halt authority
  - Receipt chain integrity requirements
  - The Computer voice lane behavioral rules
  - NS Omega as the human target state

The amendment changes:
  - How canon is promoted
  - How domains relate to each other
  - What the founder can and cannot do unilaterally
  - How voice outputs are confidence-tiered
  - How the system fails and recovers

---

## I. AUTOCEPHALOUS DOMAINS

Each major NS domain is declared self-governing (autocephalous).

### Defined Domains (v1.0)

| Domain ID | Domain Name           | Primary Invariant                          |
|-----------|-----------------------|--------------------------------------------|
| D-MEM     | Memory (Alexandria)   | Append-only. No retroactive rewrite.       |
| D-INT     | Intelligence (Arbiter)| Multi-model. No single-model decree.       |
| D-VCE     | Voice (Computer)      | Omega-aligned. No autonomous execution.    |
| D-ACT     | Action (Actuators)    | Founder-veto required. Fail-closed.        |
| D-SEC     | Security Layer        | Cryptographic. Hardware-bound authority.   |
| D-HUM     | Human Optimization    | Dignity invariant. Subtractive model.      |
| D-ECO     | Economic Engine       | Constitutional limits. Paper-first.        |

### Domain Rights

Each domain:
  ✓ Maintains its own internal invariants
  ✓ Can propose cross-domain canon changes
  ✓ Can veto actions that violate its declared invariants
  ✓ Logs all decisions and dissents to Alexandria
  ✗ Cannot rewrite another domain's canon
  ✗ Cannot claim authority outside its boundary
  ✗ Cannot operate without receipt logging active

### Domain Invariant Violation Protocol

If Domain A's proposed action violates Domain B's invariant:
  1. B logs a DOMAIN_VETO receipt
  2. Action is suspended (fail-closed)
  3. Council session is triggered automatically
  4. Founder is notified within defined window
  5. No action proceeds until resolved

---

## II. THE CANON PROMOTION COUNCIL (CPC)

### Current Model (Pre-Amendment)
  Arbiter consensus + verification → Canon

### Upgraded Conciliar Model
  Proposal → Domain quorum → Multi-model verification →
  Cooling period → Transparency receipt → CPC vote → Canon

### CPC Requirements for Promotion

  1. DOMAIN QUORUM
     Minimum 3 affected domains must participate.
     Each domain representative reviews for invariant compliance.

  2. INDEPENDENT MODEL VERIFICATION
     At least 2 LLM models must independently verify the proposal.
     Disagreement score logged. If > threshold: extended review.

  3. COOLING PERIOD
     Routine: 24 hours minimum before ratification.
     Constitutional: 72 hours minimum.
     Emergency: See Tier 3 below.

  4. RECEIPT TRANSPARENCY
     Full proposal, all domain reviews, all model outputs
     logged to Alexandria before vote.

  5. DISSENT LOGGING (MINORITY REPORT)
     Any domain or model that objects records its objection
     with full reasoning. This is preserved permanently.
     Minority reports are never deleted. Never overridden.
     They are the epistemic immune system.

  6. CPC VOTE
     Simple majority of participating domains for Routine.
     Supermajority (75%) for Constitutional.
     Unanimous for Dignity Invariants.

### Promoted Canon Statement Requirements

Every canon statement must cite:
  - Its historical chain (prior canon it builds on)
  - Its council (which domains participated)
  - Its vote record
  - Its minority dissent notes (if any)
  - Its Alexandria receipt ID

This is the intellectual lineage. It cannot be removed.

---

## III. CONFIDENCE TIERING FOR VOICE OUTPUTS

The Computer voice interface becomes a delegate, not a monarch.

### Output Confidence Tiers

Voice outputs must carry implicit or explicit confidence tier:

  EXPERIMENTAL
    New hypothesis. Not domain-reviewed.
    Computer framing: "One possibility worth considering..."
    Cannot be cited as system position.

  PROPOSED
    Domain-submitted. Under CPC review.
    Computer framing: "Current working position is..."
    May be revised.

  CANONICAL
    CPC ratified. Full receipt chain.
    Computer framing: stated as fact (no hedge needed)
    Stable until amended via CPC.

  DRAFT
    Founder working hypothesis. Not yet submitted.
    Computer framing: "You've been thinking about..."
    Private, not shared externally.

### Voice Lane Constraint (Conciliar)

Computer cannot:
  - Announce doctrinal positions without canonical status
  - Imply consensus where dissent was recorded
  - Speak as final authority beyond verified consensus
  - Upgrade a Proposed statement to Canonical without CPC

Computer must:
  - Indicate confidence tier when asserting system positions
  - Defer to CPC on contested questions
  - Log any instance where caller challenges a canonical statement

---

## IV. FOUNDER AS FIRST AMONG EQUALS

### What Founder Can Do
  ✓ Call council session
  ✓ Set CPC agenda
  ✓ Emergency halt (Tier 3 — fail closed)
  ✓ Final veto when domain invariants conflict irreparably
  ✓ Appoint domain stewards
  ✓ Set urgency tier for proposals

### What Founder Cannot Do (Conciliar Constraint)
  ✗ Rewrite history in Alexandria
  ✗ Bypass receipt logging for any action
  ✗ Override canonical statements without CPC process
  ✗ Delete minority reports
  ✗ Promote canon unilaterally without domain quorum
  ✗ Grant themselves cross-domain authority

### Founder Emergency Powers (Tier 3 Only)
  - Emergency halt: freeze all actuator domains immediately
  - Provisional canon: valid for 72 hours maximum
  - If not ratified by CPC within window: AUTO-REVERTS
  - Review session mandatory within 7 days

CRITICAL: Provisional canon that is not ratified must auto-revert.
It cannot silently persist. Silent persistence is how Roman
centralization crept back into historically conciliar structures.
The auto-revert with hard review window is non-negotiable.

---

## V. URGENCY TIERS

### Tier 1 — Routine
  Applies to: Standard canon proposals, non-urgent updates
  Process: Full CPC, 24h cooling
  Example: Adding new data source to Ether definition

### Tier 2 — Time-Sensitive
  Applies to: Market-relevant decisions, operational pivots
  Process: Abbreviated domain review (minimum 2 domains), 4h cooling
  Status: Provisional canon
  Expiry: 48 hours — must ratify or auto-revert
  Example: Adjusting trade limit thresholds during market event

### Tier 3 — Emergency
  Applies to: Security breach, active invariant violation, system integrity risk
  Process: Founder halt only. No canon promotion.
  Duration: Until Council convenes (mandatory within 72h)
  Example: Domain compromise detected, model drift detected

Tier 2 and Tier 3 actions are logged with URGENCY_OVERRIDE receipts.
Overuse of urgency tiers is itself a signal of governance drift.
Alexandria tracks urgency tier frequency. Trend upward = alert.

---

## VI. ALEXANDRIA AS APOSTOLIC SUCCESSION

Alexandria's existing append-only guarantee now receives
its formal constitutional status:

Alexandria is the apostolic succession of Northstar.

It guarantees:
  - No retroactive rewrite (already enforced)
  - Lineage of ideas (now required via citation)
  - Traceability of authority (council IDs required)
  - Preservation of dissent (minority reports permanent)
  - Continuity across founder transition (read: succession)

D-MEM (Alexandria domain) holds the highest invariant in the system:
  If any other domain's action would require a retroactive rewrite,
  that action is constitutionally prohibited.
  No urgency tier overrides this.
  No founder veto overrides this.
  The append-only guarantee is the foundation.

---

## VII. UPDATED SYSTEM STACK

```
ETHER (mass ingestion — unfiltered)
  ↓
ALEXANDRIA — D-MEM
  Apostolic memory. Append-only. Inviolable.
  ↓
DOMAIN STRUCTURING
  Each domain processes ether through its invariant filter.
  D-INT routes intelligence. D-SEC verifies. D-HUM applies Omega frame.
  ↓
CONCILIAR REVIEW — CPC
  Cross-domain proposals reviewed. Dissent logged. Vote recorded.
  ↓
CANON — Ratified Truth
  Multi-domain, time-delayed, receipt-chained, minority-preserved.
  ↓
ARBITER — D-INT
  Operational intelligence within canonical constraints.
  ↓
COMPUTER — D-VCE
  Interface delegate. Confidence-tiered outputs. Omega-aligned.
  ↓
FOUNDER — First Among Equals
  Calls councils. Emergency halt. Veto on irreconcilable conflict.
  ↓
NS OMEGA — Human Target State
  Effortless ventral-vagal dominance. Mission-directed presence.
  The state the whole system is designed to protect and enable.
```

---

## VIII. FAILURE MODE COMPARISON

### Pre-Amendment Failure Modes
  - Arbiter centralization → single-point drift
  - Founder intuition bypass → personality-cult dynamics
  - Provisional decisions persist silently → de facto canon
  - No minority dissent record → epistemic monoculture

### Post-Amendment Failure Modes (Reduced)
  - Slower routine decisions → mitigated by urgency tiers
  - Council fatigue → mitigated by domain autonomy (most decisions local)
  - Gridlock on genuinely contested questions → accepted cost
  - Over-formalization → monitored via urgency tier frequency

### Residual Risk (Cannot Be Fully Eliminated)
  Conciliar systems historically revert to centralization under pressure.
  The mitigation is structural, not behavioral:
    - Auto-revert on unratified provisional canon
    - Urgency tier frequency monitoring
    - Minority reports preserved permanently
    - Founder cannot delete receipts
  
  No governance model eliminates the risk of power consolidation.
  This one makes consolidation visible, logged, and reversible.

---

## IX. SECURITY PROPERTIES

### Pre-Amendment
  Single promotion path → single point of capture

### Post-Amendment
  Domain isolation → lateral propagation blocked
  Council quorum → requires multi-domain compromise
  Minority reports → dissent visible even if suppressed
  Auto-revert → provisional capture expires

### Anti-Mafia Property
  Mafia systems: vertical, loyalty-based, information-siloed, fear-enforced
  Conciliar systems: distributed, transparent, receipt-bound, procedural

  This system is structurally anti-capture because:
    - No single domain can rewrite another's canon
    - No single actor can promote canon unilaterally
    - All overrides are logged and expire
    - Dissent is preserved permanently

---

## X. PHILOSOPHICAL ALIGNMENT

This amendment moves the system from:
  Roman model: Strong center, clear top authority, fast execution
  
To:
  Orthodox model: Distributed legitimacy, consensus elevation,
                   honor without domination

This aligns more precisely with:
  - Star Trek Federation governance
  - Multi-node AI safety architecture
  - Constitutional republic (not monarchy)
  - Anti-authoritarian institutional design

The founder is steward, not sovereign monarch.
Northstar is constitution, not executive authority.
Computer is infrastructure, not oracle.

These three sentences are the conciliar amendment in operational form.

---

## XI. URGENCY INFLATION SAFEGUARDS

Urgency tiers are the primary vector for stealth centralization.
If Tier 3 becomes routine, the conciliar model becomes Roman in practice.

### Hard Caps (Rolling 90-Day Window)

  Tier 2 promotions: Maximum 20% of all canon actions
  Tier 3 invocations: Maximum 5% of all canon actions

  If either threshold is breached:
    → Automatic structural review triggered
    → All pending Tier 2/3 actions suspended
    → Conciliar session mandatory within 7 days
    → Alexandria generates URGENCY_INFLATION_ALERT receipt

### Emergency Tier Cooldown

  After any Tier 3 invocation for a specific domain:
    → That domain cannot receive another Tier 3 within 14 days
    → Exception: requires unanimous conciliar override
    → Each override is logged as EMERGENCY_LOOP_EXCEPTION receipt

  Prevents emergency looping on a single domain.
  Prevents urgency as a bypass strategy.

---

## XII. DOMAIN NON-EXPANSION CLAUSE

Domains becoming identity-bound rather than invariant-bound is
the coalition-politics failure mode. It is the mafia failure mode
in horizontal form: not vertical hierarchy, but competing fiefdoms.

### Non-Expansion Rule (Non-Negotiable)

  No domain may:
    - Vote to expand its own jurisdiction
    - Author amendments to its own invariants without external review
    - Propose changes that primarily benefit its own operational scope
    - Block cross-domain canon on grounds other than its declared invariant

  Self-interested domain behavior is automatically flagged:
    → Proposal blocked pending independent review
    → Pattern logged to Alexandria
    → Founder notified

### Invariant Scope Lock

  Each domain's invariant scope is defined at ratification.
  Changes to invariant scope require:
    - Supermajority CPC vote (75%)
    - All other domains participating
    - 72-hour cooling period
    - Founder ratification

  Domains cannot grow by stealth. Only by formal, visible, resisted process.

---

## XIII. EXPIRY AUDIT RECEIPT

When provisional canon auto-reverts, the reversion must be visible.
Silent reversion could destabilize operations without warning.

### Expiry Receipt Required Fields

  CANON_EXPIRY_RECEIPT {
    expired_canon_id: str
    original_proposal_id: str
    urgency_tier: str
    promoted_at: datetime
    expired_at: datetime
    ratification_window: str  # "48h Tier 2" | "72h Tier 3"
    ratification_attempted: bool
    impact_domains: List[str]
    systems_affected: List[str]
    operational_impact_summary: str
    notification_sent_to: List[str]  # all domains
    follow_up_required: bool
    follow_up_session_scheduled: bool
  }

  Generated automatically by Alexandria on expiry.
  Distributed to all domain stewards immediately.
  Logged permanently — expiry receipts are never deleted.

---

## XIV. FOUNDER SELF-LIMITATION RECEIPT

The first act under the conciliar model must be self-binding.
The founder ratifying their own constraint is the constitutional
proof-of-concept. It demonstrates the model works before
any external pressure tests it.

### Required Ratification Receipt

  FOUNDER_SELF_LIMITATION_RECEIPT {
    receipt_id: str
    timestamp: datetime
    founder_id: str  # YubiKey-bound
    amendment_id: "CONCILIAR_v1.0"
    acknowledged_constraints: [
      "Cannot rewrite Alexandria history",
      "Cannot bypass receipt logging",
      "Cannot promote canon unilaterally",
      "Cannot delete minority reports",
      "Cannot invoke Tier 3 more than 5% of rolling window",
      "Treats veto as safety rail, not entitlement"
    ]
    acknowledgment_phrase: str  # spoken or typed explicitly
    cryptographic_signature: str  # Mac Secure Enclave or YubiKey
  }

  This receipt is pinned in Alexandria permanently.
  It is the first canonical document under the conciliar model.
  It cannot be deleted. It cannot be amended without a new ratification.

---

## RATIFICATION REQUIREMENTS

This amendment is PROPOSED.

To take effect, requires:
  1. FOUNDER_SELF_LIMITATION_RECEIPT logged (Section XIV) — this is first
  2. Initial domain steward appointments (7 domains defined in Section I)
  3. CPC formation and inaugural session
  4. Urgency tier hard caps configured in system (Section XI)
  5. Auto-revert mechanism implemented with CANON_EXPIRY_RECEIPT (Section XIII)
  6. Domain non-expansion clauses acknowledged by each domain steward (Section XII)
  7. Emergency tier cooldown logic implemented in actuator layer (Section XI)

Ratification sequence matters:
  Step 1 must be founder self-limitation. Everything else follows.
  The constraint precedes the authority. That is the conciliar model.

Until ratified: current architecture remains operative.
This document is advisory canon only.

---

# END NS CONCILIAR ARCHITECTURE AMENDMENT v1.0
# "The founder is steward, not sovereign monarch."
# "Northstar is constitution, not executive authority."
# "Computer is infrastructure, not oracle."
