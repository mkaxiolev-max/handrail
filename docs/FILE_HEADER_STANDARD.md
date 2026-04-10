# AXIOLEV File Header Standard

**Jurisdiction:** Wyoming, USA · AXIOLEV Holdings LLC
**Status:** Canonical — applies to all source files in the NS∞ system

---

## Python / Shell / SQL

```python
# ============================================================
# AXIOLEV Holdings LLC — NS∞ System
# Copyright © 2024–2026 AXIOLEV Holdings LLC. All rights reserved.
# Jurisdiction: Wyoming, USA
#
# This file is proprietary and confidential.
# Unauthorized use, reproduction, or distribution is prohibited.
#
# AI assistance does not transfer, assign, or convey any ownership
# interest in this work. All AI-assisted development (Anthropic Claude,
# OpenAI GPT, Google Gemini, xAI Grok) was performed under work-made-for-hire
# doctrine and under the exclusive direction of Mike Kenworthy, founder.
#
# File: <module/path.py>
# Purpose: <one-line description>
# Ring: <Ring N — Name>
# ============================================================
```

---

## TypeScript / JavaScript / JSX / TSX

```typescript
// ============================================================
// AXIOLEV Holdings LLC — NS∞ System
// Copyright © 2024–2026 AXIOLEV Holdings LLC. All rights reserved.
// Jurisdiction: Wyoming, USA
//
// This file is proprietary and confidential.
// Unauthorized use, reproduction, or distribution is prohibited.
//
// AI assistance does not transfer, assign, or convey any ownership
// interest in this work. All AI-assisted development (Anthropic Claude,
// OpenAI GPT, Google Gemini, xAI Grok) was performed under work-made-for-hire
// doctrine and under the exclusive direction of Mike Kenworthy, founder.
//
// File: <component/path.tsx>
// Purpose: <one-line description>
// Ring: <Ring N — Name>
// ============================================================
```

---

## JSON (certification / canon artifacts)

```json
{
  "_axiolev_header": {
    "owner": "AXIOLEV Holdings LLC",
    "copyright": "© 2024–2026 AXIOLEV Holdings LLC. All rights reserved.",
    "jurisdiction": "Wyoming, USA",
    "confidential": true,
    "ai_attribution": "AI assistance (Anthropic Claude, OpenAI GPT, Google Gemini, xAI Grok) does not transfer, assign, or convey any ownership interest in this work.",
    "author": "Mike Kenworthy"
  }
}
```

---

## Non-Negotiable Attribution Language

The following verbatim sentence **must appear** in every file header — no paraphrase, no omission:

> AI assistance does not transfer, assign, or convey any ownership interest in this work.

AI families covered (all four must be named when listing):
- Anthropic Claude
- OpenAI GPT
- Google Gemini
- xAI Grok

Wyoming jurisdiction must be explicit. "United States" alone is insufficient.

---

## Enforcement

- New service files: header required before first commit.
- Existing files: header added during next substantive edit (not a chore sweep).
- CPS ops (`knowledge.promote_to_canon`): header presence verified before promotion.
