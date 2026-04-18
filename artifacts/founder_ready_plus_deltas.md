# NS∞ Delta Classification
**Audited:** 2026-04-17  

## Bucket A — Runtime drift only
None found.

## Bucket B — Missing file/route/feature
None found.

## Bucket C — Broken verifier/reporting tool
None found.
Note: Initial probes used wrong paths (/autopoiesis/initiatives, /cps/force_ground/status).
Correct paths (/autopoiesis/state, /cps/force_ground/state) respond HTTP 200.
This was an audit probe error, not a system defect.

## Bucket D — External Ring 5 only (5 gates)
1. G1: AXIOLEV Holdings LLC formation → Stripe business verification
2. G2: Stripe live secret key (sk_live_...)
3. G3: Stripe price IDs → STRIPE_PRICE_ID_ROOT_PRO/AUTO env vars
4. G4: YubiKey slot_2 provisioning (~$55 at yubico.com) → POST /kernel/yubikey/provision
5. G5: DNS — root.axiolev.com CNAME → Cloudflare

## Classification result
Only Bucket D exists. No code work needed.
