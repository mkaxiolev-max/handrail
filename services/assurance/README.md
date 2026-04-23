# NS-AL AssuranceLayer

**Constitutional Invariant 11** — proof-carrying execution for NS∞.

> "No state transition without a receipt.  
>  No receipt without a justification artifact.  
>  No artifact without verification or obligation."

---

## Architecture

```
State Transition
      │
      ▼
@assured(contract)          ← enforcement.py
      │
      ├─ precondition check (before fn executes)
      ├─ fn executes
      ├─ postcondition check (after fn returns)
      │
      ▼
VerificationDispatcher      ← dispatcher.py
      │
      ├─ No justification artifacts?
      │     └─ resolved obligation present? → VERIFIED receipt
      │     └─ otherwise              → ObligationArtifact (PENDING) → RAISE
      │
      ├─ VerificationReceipt submitted without justification? → REJECTED → RAISE
      │
      ├─ ProofArtifact: hash == sha256(canonical JSON)?
      ├─ CertificateArtifact: expiry > now(UTC)?
      ├─ BoundedClaim: confidence ∈ [0.0, 1.0]?
      │
      ├─ R4 contract + yubikey_verified=False? → REJECTED → RAISE
      │
      └─ All checks pass → VERIFIED receipt → transition allowed
```

## Domain types (`types.py`)

| Type | Role |
|------|------|
| `ComputationContract` | Formal specification of a transition: inputs/outputs schema, pre/post conditions, side effects, risk tier |
| `ProofArtifact` | Hash-verified proof object (formal/empirical/attestation/audit) |
| `CertificateArtifact` | Signed certificate with expiry (issuer/subject/claims) |
| `BoundedClaim` | Probabilistic claim with confidence bound and derivation lineage |
| `ObligationArtifact` | Commitment to provide justification by a deadline, with a compensating action |
| `VerificationReceipt` | Immutable dispatch outcome (VERIFIED/REJECTED/OBLIGATION_PENDING) |

## Risk tiers

| Tier | YubiKey required | Typical use |
|------|-----------------|-------------|
| R0–R2 | No | Read-only, low-impact transitions |
| R3 | No (YubiKey recommended) | Stateful mutation ops |
| R4 | **Yes** — YubiKey 26116460 | Canon-touching, irreversible, ledger-modifying |

## Obligation path

When no justification artifact is present the dispatcher emits an `ObligationArtifact`
(status=PENDING) and `@assured` raises `AssuranceViolation(obligation=<ob>)`.

The caller inspects `exc.obligation`, executes `ob.compensating_action`, then retries
with a new `ObligationArtifact(status=RESOLVED)` in the artifact bundle.  The dispatcher
converts a resolved obligation into a VERIFIED receipt.

## Receipt chaining

Pass `prev_hash=receipt.subject_hash` to `dispatcher.dispatch()` (or to `@assured`) to
link consecutive receipts.  `verify_receipt_chain(receipts)` checks that each receipt's
`evidence_refs` contains a `prev:<hash>` entry pointing at its predecessor.

## Ledger

All dispatch outcomes are appended (gracefully, non-blocking) to:

```
/Volumes/NSExternal/ALEXANDRIA/ledger/assurance_receipts.jsonl   (SSD)
~/ALEXANDRIA/ledger/assurance_receipts.jsonl                     (fallback)
```

Lineage Fabric receipts only — never CTF.
