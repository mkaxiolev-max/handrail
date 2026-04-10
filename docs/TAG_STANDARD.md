# AXIOLEV Tag Standard

**Jurisdiction:** Wyoming, USA · AXIOLEV Holdings LLC
**Status:** Canonical — applies to all milestone tags in the NS∞ system

---

## Annotated Tag Format

Every milestone tag must be annotated (not lightweight). The tag message must contain the full ownership block:

```
axiolev-ns-infinity-<label>-YYYYMMDD

AXIOLEV Holdings LLC — NS∞ System
Milestone: <label>
Date: YYYY-MM-DD (UTC)
Branch: <branch-at-tag>
Commit: <short-sha>

Copyright © 2024–2026 AXIOLEV Holdings LLC. All rights reserved.
Jurisdiction: Wyoming, USA

This software is proprietary and confidential.
Unauthorized use, reproduction, or distribution is prohibited.

AI assistance does not transfer, assign, or convey any ownership
interest in this work. All AI-assisted development (Anthropic Claude,
OpenAI GPT, Google Gemini, xAI Grok) was performed under
work-made-for-hire doctrine and under the exclusive direction of
Mike Kenworthy, founder, AXIOLEV Holdings LLC.

Ring status at tag:
  Ring 1 — Foundations:   COMPLETE
  Ring 2 — Intelligence:  COMPLETE
  Ring 3 — Sovereign:     COMPLETE
  Ring 4 — Capability:    COMPLETE
  Ring 5 — Production:    BLOCKED (Stripe live keys, domain, legal entity)
```

---

## Canonical Milestone Tags

| Tag | Milestone | Ring |
|-----|-----------|------|
| `axiolev-ns-infinity-final-YYYYMMDD` | Full NS∞ system certified and production-ready | R1–R4 complete |
| `axiolev-ring4-complete-YYYYMMDD` | Ring 4 Capability complete | R4 |
| `axiolev-ring3-complete-YYYYMMDD` | Ring 3 Sovereign / BLACK KNIGHT complete | R3 |
| `axiolev-ring2-complete-YYYYMMDD` | Ring 2 Intelligence / M2 Jarvis complete | R2 |
| `axiolev-ring1-complete-YYYYMMDD` | Ring 1 Foundations / M1 Founder MVP complete | R1 |
| `axiolev-omega-certified-YYYYMMDD` | Omega simulation certified — all 7 paths pass | R4 |

---

## Creation

Use `axiolev_push.sh --tag LABEL` to create tags with the canonical block automatically populated.

Manual creation:

```bash
git tag -a axiolev-ns-infinity-final-$(date -u +%Y%m%d) \
  -m "$(cat <<'EOF'
axiolev-ns-infinity-final-$(date -u +%Y%m%d)

AXIOLEV Holdings LLC — NS∞ System
...
EOF
)"
git push origin axiolev-ns-infinity-final-$(date -u +%Y%m%d)
```

Always use `git tag -a` (annotated). Lightweight tags are not acceptable for milestone markers.

---

## Confidentiality

Tags pushed to origin are visible to anyone with repository access.
Do not embed secrets, OTPs, or internal IP details in tag messages beyond the ownership block above.
