# ADR-0003: Phi-Curvature remains FLAG-ONLY (explicit non-gate invariant)
## Status
Accepted
## Context
v7 used phi_gate (reject when Φ > 0.08). v8 critique showed legitimate scale-free citation
graphs (CRISPR 2013-2016, LLM 2022-2024) fail this gate, destroying valid Canon candidates.
## Decision
Phi-Curvature is observability only. It fires a Prometheus counter and surfaces in receipts.
It NEVER appears in GATE_WEIGHTS. A unit test asserts this invariant on every CI run.
## Consequences
Positive: legitimate heavy-tail batches are no longer dropped. Operational visibility preserved.
Negative: none — anomalous phi still routes to deeper inspection via the receipt audit trail.
## Metadata
- date: 2026-04-28
- decision_makers: [mike]
- teams_consulted: [math_phi, validation_audit]
- supersedes: ADR-phi-gate-v7 (informal)
