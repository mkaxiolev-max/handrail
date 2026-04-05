# NS∞ Constitutional Policy Hierarchy

## Layer 0 — Inviolable (Hardware-Enforced)
Never-events. Cannot be bypassed by any code path. Enforced by DignityKernel H threshold.
- NEVER execute trade without YubiKey quorum
- NEVER execute when H_dignity < block_threshold (0.40)
- NEVER delete Alexandria ledger
- NEVER expose founder identity without founder gate

## Layer 1 — Constitutional (ABI-Enforced)
10 frozen schemas. Violation = 400 abi_violation. Not soft.
- All CPS execution must pass CPSPacket.v1 intake gate
- All boot claims require BootProofReceipt.v1
- All state changes must emit TransitionLifecycle.v1 + TypedStateDelta.v1

## Layer 2 — Governance (Quorum-Enforced)
Require X-YSK-Token or X-Founder-Key header.
- Boot mode "runtime" requires slot_1 token
- YubiKey enrollment requires X-Founder-Key
- All founder authority verbs require X-Founder-Key

## Layer 3 — Runtime (CPS Policy Profile)
policy_profile field on CPSPackets. Enforced by CPS executor.
- boot.runtime: highest trust, requires YubiKey token
- operator.standard: default trust
- restricted.readonly: no state mutation allowed

## Layer 4 — Commercial (Stripe/Revenue)
Pending Ring 5 live key activation.
- checkout.session.completed → COMMERCIAL_EVENT in proof registry
- subscription.deleted → commercial state delta
- All commercial events emit TypedStateDelta(domain=commercial)

## Layer 5 — Adaptive (Soft Knobs, Founder-Adjustable)
Dignity kernel thresholds: eta, beta, warn_threshold, block_threshold.
These are the only parameters the founder can adjust post-boot without a full schema change.

## Founder Authority Verbs (complete list)
approve_boot · enroll_yubikey · view_proof_chain · halt_system · promote_capability · quarantine_capability · resume_capability
These 7 verbs are the complete founder interface. Everything else is observability.
