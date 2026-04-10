# AXIOLEV Commit Standard

**Jurisdiction:** Wyoming, USA · AXIOLEV Holdings LLC
**Status:** Canonical — mandatory for all commits to the NS∞ system

---

## Format

```
TYPE(SCOPE): imperative summary under 72 chars

Optional body — what and why, not how. Wrap at 72 chars.

IP: AXIOLEV Holdings LLC © 2024–2026 · Wyoming, USA · All rights reserved
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

The `IP:` trailer is **non-negotiable** on every commit.

---

## Types

| Type | Use |
|------|-----|
| `feat` | New capability added to the canonical system |
| `fix` | Bug fix — defect in existing behavior |
| `cert` | Certification artifact, proof, or OMEGA_CERTIFICATION update |
| `harden` | Security, policy rail, dignity guard, never-event enforcement |
| `test` | Test additions or fixes (no production code change) |
| `infra` | Docker, boot scripts, CI, environment, Dockerfile |
| `docs` | Documentation only (standards, changelogs, READMEs) |
| `refactor` | Internal restructure — no behavior change |
| `chore` | Tooling, formatting, dependency bumps, cleanup |
| `revert` | Explicit revert of a prior commit |

---

## Scopes — AXIOLEV Stack Map

| Scope | Covers |
|-------|--------|
| `ns_core` | services/ns_core — main FastAPI app, proxy routes |
| `handrail` | services/handrail — CPS engine, policy gateway |
| `omega` | services/omega — simulation engine, branches, compare |
| `alexandria` | Receipt chain, ledger, snapshot, Merkle proof |
| `hic` | HIC engine, USDL gates, pattern library |
| `pdp` | PolicyDecisionPoint, ABAC rules, FOUNDER_REQUIRED |
| `mac_adapter` | Mac adapter bridge ops (audio, clipboard, display…) |
| `program_runtime` | Program Library v1 (10 namespaces, 68 ops) |
| `violet` | Violet identity, voice lane, VioletLogo brand |
| `voice` | Voice sessions, STT, intent classification |
| `canon` | Canon promotion, semantic binder, proposals |
| `integrity` | Boot invariants, receipt chain verification |
| `ui` | frontend/ React + Vite app |
| `ns_ui` | ns_ui/ Next.js app |
| `ring5` | Ring 5 production milestones (Stripe, domain, legal) |
| `brand` | AXIOLEV brand assets, VioletMark, wordmark |
| `cert` | Certification artifacts in certification/ |
| `migration` | SQL migrations in migrations/ |
| `boot` | boot.sh, sovereign_boot.json, boot proof |
| `corpus` | Alexandria corpus, ether ingest, raw_ingest |

---

## Examples

```
feat(omega): wire HIC/PDP policy rails into simulate + compare routes

harden(pdp): fails-closed guard on omega compare-to-reality endpoint

cert(cert): OMEGA_CERTIFICATION.json — all 7 paths PASS, advisory-only

fix(ns_core): add HTTPException import to fix 500 on proxy 4xx

docs(docs): AXIOLEV IP dignity — file headers, commit taxonomy, tag standard

infra(boot): add httpx to ns_core Dockerfile for async omega proxy

test(omega): 11/11 tests pass including metadata.execute block guard
```

---

## Annotated Tags

See `docs/TAG_STANDARD.md` for the full annotated tag format.
Use `axiolev_push.sh --tag LABEL` to create tags with the canonical ownership block.
