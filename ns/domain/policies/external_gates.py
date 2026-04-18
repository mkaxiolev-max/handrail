"""Ring 5 — External Gates (noted, out-of-band). No network calls."""

EXTERNAL_GATES = [
    {"id": "stripe_llc_verification", "status": "pending", "note": "out-of-band"},
    {"id": "stripe_live_keys_vercel", "status": "pending", "note": "out-of-band"},
    {"id": "root_handrail_price_ids", "status": "pending", "note": "out-of-band"},
    {"id": "yubikey_slot2", "status": "pending", "note": "~$55 procurement"},
    {"id": "dns_cname_root", "status": "pending",
     "note": "root.axiolev.com -> root-jade-kappa.vercel.app"},
]
