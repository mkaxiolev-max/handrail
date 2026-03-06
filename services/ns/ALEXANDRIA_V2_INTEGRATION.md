# Alexandria v2.0 → NORTHSTAR Integration Requirements
# Extracted from Beautiful.ai presentation
# Date: 2026-02-18

## WHAT ALEXANDRIA v2.0 SPECIFIES (must be in NS model)

### 1. RETRIEVAL-FIRST WORKFLOW (mandatory)
- Every query must attempt retrieval from Alexandria BEFORE calling LLMs
- AI claims must cite internal or licensed sources
- No hallucination without citation — constitutional requirement
- Implementation: Add retrieval step BEFORE arbiter.reason() call

### 2. IMMUTABLE AUDITABILITY — 7+ YEAR ARCHIVE
- Every AI output logged, replayable, attributable
- Receipt chain already built — extend retention policy to 7+ years
- Add: output hash + model attribution to every receipt

### 3. DEAL-LEVEL ISOLATION (Chinese Walls)
- Permission-gated autonomy at data layer
- Separate namespaces per deal/project in Alexandria
- AI agents inherit permission boundaries automatically
- Implementation: Add project_id scoping to EtherStore and CanonStore

### 4. CROSS-CHECK LAYER
- Dedicated monitoring for factual errors and conflict alerts
- This maps to: FALSIFIER stage in EXTRACTOR → FALSIFIER → VERIFIER → ARBITER
- FALSIFIER must be a real implementation, not a passthrough
- Action: Implement FALSIFIER as a second LLM call that challenges the first

### 5. ELASTIC SWARM SCALING
- 50-100 active deals per pod by default
- Hybrid cloud + on-prem sensitive layers
- Maps to: vendor-neutral operator lattice (already in NS architecture)

### 6. PROBABILISTIC PIPELINE SCHEMA
- All operations flow through Unified Relationship Graph
- Standardized schema for all deal materials
- Action: Add schema validation to CanonStore writes

### 7. HUMAN-IN-THE-LOOP (hard gates)
- Valuation: human sign-off mandatory
- Tactical advice: human sign-off mandatory  
- Final negotiation: human sign-off mandatory
- Maps to: FOUNDER_VETO constitutional gate — already enforced

### 8. WAR GAMING / SCENARIO MODELING
- Integrated directly into workflow
- Stress-test valuations and negotiation paths
- New capability to add: /scenario endpoint on API

### 9. PERFORMANCE METRICS TO TRACK
- Throughput & Cycle Time (deal velocity)
- Fee Realization & Retention
- Error Rate & Incident Log (zero-breach target)
- These become Alexandria receipt metrics

### 10. DATA SOVEREIGNTY
- MNPI in dedicated isolated zone, never leaves perimeter
- Client-controlled encryption keys
- Maps to: MANIFOLD (internal, guarded) vs ALEXANDRIA (external SSD)
- Encryption at rest: add to CanonStore write path

## PRIORITY ACTIONS FOR NS INTEGRATION

Priority 1 (this session):
- [ ] Retrieval-first: query Alexandria index before LLM call
- [ ] FALSIFIER as real cross-check LLM call (not passthrough)

Priority 2 (next session):
- [ ] Deal/project namespace isolation in storage
- [ ] Scenario modeling endpoint
- [ ] Encryption at rest on Canon writes

Priority 3 (production):
- [ ] 7-year retention policy enforcement
- [ ] Unified Relationship Graph implementation
- [ ] Swarm scaling architecture
