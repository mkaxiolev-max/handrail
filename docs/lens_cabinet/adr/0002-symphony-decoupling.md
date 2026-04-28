# ADR-0002: Decouple Symphony OS via JSON-Schema contract surface
## Status
Accepted
## Context
Symphony OS is a StrategicInitiative under NS∞. Its Document-to-Program Compiler consumes
Lens Canon output. Tight import coupling would create circular dependency and lock release
cadences together.
## Decision
We will publish a versioned JSON Schema contract surface in contracts_external/symphony_contracts.py.
No imports flow in either direction. CI/CD lint rule enforces the boundary.
## Consequences
Positive: Symphony and Lens Cabinet evolve independently. Breaking changes require semver bump + 90-day cycle.
Neutral: Requires JSON Schema publishing infrastructure (axiolev.io/schemas/).
## Metadata
- date: 2026-04-28
- decision_makers: [mike]
- supersedes: none
