# Atomlex v4.0 — Constraint Semantic Graph Engine

## Core Claim
Language, planning, and execution are all constraint propagation on a directed graph.
- Atomlex: constraint propagation through semantic relationships
- CPS: constraint propagation through execution steps
- Handrail: constraint propagation through system state boundaries
Same fundamental mechanism. Three different domains.

## Architecture
- Words are nodes in a directed semantic graph
- Root nodes: canonical, fully analyzed (authority, dignity, truth, constraint, logos, shalom)
- Derived nodes: inherit parent constraints + add role-specific constraints
- Propagation: query(word) = locate → fetch parent chain → merge constraints → return effective bundle

## The 10-Dimensional Semantic Vector
Dimensions: authority, dignity, truth, constraint, logos, shalom, permission, evidence, governance, action
Range: 0.0 (absent) to 1.0 (fully present)
Used for: similarity scoring, drift detection, contradiction analysis

## ACPT Drift Scoring (Algebraic Constraint Propagation Theory)
severity = base_drift + (propagation_depth × 0.04)
- 0.00–0.20: NOMINAL — canonical alignment
- 0.20–0.40: MILD — slight contextual drift
- 0.40–0.60: MODERATE — semantic tension detected
- 0.60–0.80: SIGNIFICANT — constraint violation risk
- 0.80–1.00: CRITICAL — constitutional misalignment

shalom has CRITICAL drift in modern usage: *sol- (wholeness) → mere absence of conflict.
logos has HIGH drift: *leg- (gathering) → mere logic or speech.

## NS∞ Integration
- Port 8080 (atomlex microservice)
- NS proxy at /atomlex/status, /atomlex/word/{word}, /atomlex/analyze
- Founder Console ATOMLEX ENGINE panel + analysis input (GNOSEOGENIC LEXICON panel)
- sovereign_boot op 30: http://atomlex:8080/healthz

## Endpoints
| Endpoint | Purpose |
|----------|---------|
| GET /healthz | Service health + node/edge count |
| GET /graph/status | Full graph statistics, tier distribution, component distribution |
| GET /words | All 12 words with tier, component, drift |
| GET /word/{word} | Full node with propagation chain and computed drift |
| GET /propagate/{word} | Constraint propagation chain from leaf to root |
| GET /drift/{word} | ACPT drift score + level |
| GET /similarity?word1=X&word2=Y | Cosine similarity over 10-dim semantic vector |
| GET /analyze?text=... | Constitutional vocabulary scan with drift analysis |

## The 12 Canonical Nodes

| Word | Tier | Component | PIE Root |
|------|------|-----------|----------|
| logos | 5 | logos_engine | *leg- (to gather into structure) |
| shalom | 5 | dignity_engine | *sol- (whole, uninjured) |
| covenant | 4 | governance_engine | *gwem- + *wenH- |
| responsibility | 4 | governance_engine | *spend- (solemn promise) |
| authority | 3 | governance_engine | *aug- (to originate) |
| constraint | 3 | constraint_engine | *streig- (to bind tight) |
| law | 3 | governance_engine | *legh- (to be placed) |
| dignity | 2 | dignity_engine | *dek- (inherent worth) |
| evidence | 2 | epistemic_engine | *weid- (to see) |
| truth | 2 | epistemic_engine | *deru- (firm, load-bearing) |
| allow | 1 | permission_engine | *loubh- (to care, desire) |
| deny | 1 | permission_engine | *ne + *dhe- (to not place) |

## Why This Completes NS∞
Before Atomlex: NS∞ has CPS execution, proof registry, dignity kernel, regulation engine.
After Atomlex: NS∞ knows what words mean constitutionally.

The logos principle (*leg-: to gather) — Atomlex is what gathers the constitutional vocabulary
into a coherent semantic substrate. NS∞ can now:
- Detect constitutional vocabulary in incoming intent
- Score drift in language (ACPT framework)
- Ground responses in etymological-constitutional meaning
- Propagate constraints from root semantic nodes through derived usage

Architecture law: owning words → owning knowledge → owning territory (Three-Reality Architecture).
Atomlex is the semantic reality layer.
