# ADR-0001: Adopt 5-Team Swarm Pattern (runtime + governance dual-nature)
## Status
Accepted
## Context
NS∞ Lens Cabinet must scale from 1 founder to 5+ collaborators without architectural
refactor. Solo-founder discipline and future team delegation must share the same codebase.
## Decision
We will implement 5 Teams as runtime Python classes (BaseTeam subclasses) AND governance
documentation. Teams own Lenses CODEOWNERS-style, register CPS lanes, enforce CI/CD gates,
and emit Prometheus metrics. Quorum starts 1-of-1 (Mike); expands by YAML + CODEOWNERS edit.
## Consequences
Positive: delegation is a data change, not an architecture change. Governance is machine-readable.
Negative: Team objects add ~200 lines of boilerplate. Acceptable for the durability gained.
## Metadata
- date: 2026-04-28
- decision_makers: [mike]
- teams_consulted: [architecture]
- supersedes: none
