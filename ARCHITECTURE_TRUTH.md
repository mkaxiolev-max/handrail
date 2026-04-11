# NS∞ ARCHITECTURE TRUTH
Generated: Fri Apr 10 19:01:35 PDT 2026

## Canonical Subsystems (from docker-compose.yml + source inspection)

| Subsystem | Port | Role | Source |
|---|---|---|---|
| ns_core | 9000 | Primary API: Violet, voice, intent, governance proxy, HIC/PDP, programs, model routing | services/ns_core/ |
| alexandria | 9001 | Memory substrate: atoms, edges, receipts, feed. Append-only, SSD-backed | services/alexandria/ |
| model_router | 9002 | LLM adjudication: Anthropic/Grok/Gemini/OpenAI/Groq/Ollama | services/model_router/ |
| violet | 9003 | Relational presentation layer, identity, ISR | services/violet/ |
| canon | 9004 | Governance authority, single write gate, canon_commits | services/canon/ |
| integrity | 9005 | Receipt chain verification, boot invariants | services/integrity/ |
| omega | 9010 | Bounded simulation engine, advisory_only, HIC/PDP guarded | services/omega/ |
| ns_api | 9011 | Additional API surface | services/ns_api/ (if exists) |
| postgres | 5432/5433 | Primary DB: atoms, edges, receipts, omega_runs, voice_sessions | Docker |
| redis | 6379/6380 | Cache / pub-sub | Docker |
| frontend | 3000 | Vite+React founder UI: /violet, /briefing, /engine, /omega etc | frontend/ |
| ns_ui | 3002 | Next.js Living Architecture orbital view | ns_ui/ |

## Declared but not in current compose stack
| Subsystem | Declared Role | Status |
|---|---|---|
| Handrail | CPS execution control plane | PARALLEL_PRODUCT — see HANDRAIL_ROLE_DECISION.md |
| Continuum | Additional runtime surface | NOT_IN_COMPOSE |
| Mac Adapter | 27 adapter modules | DECLARED_IN_DOCS |
| Atomlex v4 | Semantic constraint graph :8080 | NOT_IN_COMPOSE |

## Constitutional Architecture
- HIC Engine: 60 patterns, 8 USDL gates (G1-G8), R0/R1/VETO verdicts
- PDP/ABAC: 5 rules, founder-required gate
- Omega: advisory_only, promotion_allowed=False always
- Receipt chain: TRUTH = REPLAY invariant
- Canon: sole promotion path
- Dignity Kernel: H = 0.85phi - 0.92V
