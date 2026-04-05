# Ring 5 Go-Live Checklist
**NS∞ v1 — 5 manual steps to production revenue**

---

- [ ] **1. Stripe LLC verification**
  - Go to `https://dashboard.stripe.com`
  - Look for the "Action required" banner in the top nav
  - Complete business verification: legal name, EIN/SSN, address, business type
  - Upload any requested documents (ID, bank statement)
  - Estimated: 1–3 business days after submission
  - **Unblocks:** all `buy.stripe.com` payment links start processing charges

- [ ] **2. Stripe live keys → `.env`**
  - Go to `https://dashboard.stripe.com → Developers → API Keys`
  - Copy `Secret key` (sk_live_...) and `Publishable key` (pk_live_...)
  - Edit: `nano /Users/axiolevns/axiolev_runtime/.env`
  - Replace `STRIPE_SK_PENDING` → `sk_live_...`
  - Replace `STRIPE_PK_PENDING` → `pk_live_...`
  - Restart Handrail: `docker compose up -d --force-recreate handrail`

- [ ] **3. ROOT price IDs → Vercel env vars**
  - Go to `https://dashboard.stripe.com → Products → Add product`
  - Create **ROOT Pro**: $49.00 / month recurring → copy `price_live_...` ID
  - Create **ROOT Auto**: $99.00 / month recurring → copy `price_live_...` ID
  - Go to `https://vercel.com → root project → Settings → Environment Variables`
  - Add: `STRIPE_PRICE_ID_ROOT_PRO` = `price_live_...` (Production)
  - Add: `STRIPE_PRICE_ID_ROOT_AUTO` = `price_live_...` (Production)
  - Redeploy or push any commit — `/api/checkout` will go live automatically
  - Also create Handrail Pro ($29/mo) + Enterprise ($299/mo) prices and update `stripe_integration.py:17`

- [ ] **4. YubiKey slot_2 hardware**
  - Order: `https://www.yubico.com → YubiKey 5 NFC` (~$55)
  - Insert new key → touch to get serial number (`ykman info`)
  - Enroll via Founder Console: `http://localhost:9000/founder → FOUNDER ACTIONS → Enroll YubiKey`
  - Or via API:
    ```bash
    curl -s -X POST http://localhost:8011/yubikey/enroll \
      -H 'Content-Type: application/json' \
      -H 'X-Founder-Key: <token>' \
      -d '{"slot_id":"slot_2","serial":"NEW_SERIAL"}'
    ```
  - **Unblocks:** 2-of-2 quorum for R3/R4 CPS ops; production NS boot with full quorum

- [ ] **5. root.axiolev.com DNS**
  - Log in to your domain registrar (where axiolev.com DNS is managed)
  - Go to DNS Management for `axiolev.com`
  - Add record:
    - Type: `CNAME`
    - Name: `root`
    - Value: `cname.vercel-dns.com`
    - TTL: 3600
  - Vercel alias already configured — propagates in minutes to hours
  - **Unblocks:** `https://root.axiolev.com` resolves to ROOT landing page

---

## Post-Checklist: Launch Sequence
See `LAUNCH_SEQUENCE.md`
