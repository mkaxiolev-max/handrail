# SFE Semantic Versioning Rules v1.0
# Including: Split Protocol, Conflict Protocol, Drift Prevention
# NS∞ / AXIOLEV Holdings

## Core Rule

> No MAJOR change without outcome pressure or structural contradiction evidence.
> No silent changes ever. Everything is receipted.

Violation of either rule is a constitutional violation under the Conciliar Amendment.

---

## Version Schema

`MAJOR.MINOR.PATCH`

All concepts start at `0.1.0` (candidate, not yet grounded).
Version 1.0.0 requires completeness_score = 1.0 (all 6 questions answered with evidence).

---

## PATCH

**Semantics:** No meaning change. Surface improvements only.

**Permitted triggers:**
- Clarify wording of a phrasing_variant
- Add a usage example or citation
- Add a new evidence pack citation to an existing answer
- Fix typos, formatting in constraint_expression
- Add synonyms to surface_forms

**Not permitted via PATCH:**
- Change answer_payload content
- Change invariant_core
- Change boundary scope
- Add or remove question from minimal_basis

**Process:**
1. Propose change
2. Emit receipt `SFE_CONCEPT_UPDATED_PATCH`
3. Bump PATCH version
4. No council required

**API:**
```python
sfe.update_concept(
    concept_id, 
    changes={"phrasing_clarification": "..."},
    version_impact=VersionImpact.PATCH,
    updated_by="user_id"
)
```

---

## MINOR

**Semantics:** Additive change. No existing meaning destroyed.

**Permitted triggers:**
- Add a domain variant (new ConceptVariant)
- Add a boundary condition
- Add a new measurement method to QC-2
- Update or add a TranslationMap
- Add optional_basis questions (not minimal)
- Answer a previously unanswered question class

**Not permitted via MINOR:**
- Change invariant_core
- Remove a boundary (deprecate only)
- Change existing answer_payload (create new answer record instead)
- Merge or split concepts

**Process:**
1. Propose change
2. Domain quorum: minimum 2 affected domains must be notified
3. Emit receipt `SFE_CONCEPT_UPDATED_MINOR`
4. Abbreviated review (2 domain stewards)
5. Bump MINOR version

---

## MAJOR

**Semantics:** Breaking change to meaning. Existing dependents must be re-evaluated.

**Permitted triggers:**
- Split concept (fission protocol)
- Change invariant_core
- Retire an unsafe or falsified definition
- Rebase primitive_mapping
- Merge two concepts into one
- Change minimal_basis questions

**MANDATORY requirements — no exceptions:**
1. `justification` with either:
   - `outcome_pressure_evidence` (OutcomeRef showing systematic failure), OR
   - `structural_contradiction_evidence` (ConflictRef showing incompatibility)
2. Full CPC vote (Canon Promotion Council)
3. 72h cooling period
4. All dependents notified (all concepts using this concept via TranslationMap or linked)
5. `SFE_CONCEPT_UPDATED_MAJOR` receipt with all fields

**What "outcome pressure" means:**
- 3+ Outcomes with prediction error > 0.4 linked to this concept
- OR contested_boundary_ratio >= 0.5 (detect_split_pressure returns true)
- OR explicit falsification event (QC-5 answer shows systematic failure)

**What "structural contradiction" means:**
- Conflict record of type CLASH or MEASUREMENT in OPEN state for > 14 days
- OR constraint_incompatibility: to keep concept, must hold mutually exclusive assumptions

---

## SPLIT PROTOCOL (Concept Fission)

**Trigger conditions (any one sufficient):**

1. **Prediction divergence**
   - Same concept basis yields systematically different outcome predictions across domains
   - Detection: `sfe.detect_split_pressure()` returns "PREDICTION_DIVERGENCE"

2. **Outcome divergence**
   - Outcomes cluster into distinct regimes under the same label
   - Detection: 2+ outcome clusters with between-cluster error > 0.5, within-cluster < 0.2

3. **Constraint incompatibility**
   - Keeping the concept requires holding mutually exclusive assumptions
   - Detection: contested_boundary_ratio >= 0.5

4. **Measurement incompatibility**
   - Measurement schema cannot be unified without losing explanatory power
   - Detection: QC-2 answers incompatible across domain_variants

**Split execution:**

```python
children = sfe.split_concept(
    parent_id="CONCEPT-xxxx",
    child_labels=["risk-market", "risk-operational"],
    split_reason="Prediction divergence: market risk and operational risk have incompatible measurement schemas",
    evidence_pack_id="EP-xxxx",   # Required
    created_by="founder",
)
```

**What happens:**
1. Parent concept status → DEPRECATED (not deleted)
2. Two child concepts created at version 0.1.0
3. `parent_concept_id` set on each child
4. TranslationMaps created from parent → each child (for continuity)
5. Old canon remains valid within its historical scope (parent not erased)
6. All dependent concepts notified via receipt

**Historical guarantee:**
Parent concept is NEVER deleted. Its history, its answers, its boundaries persist permanently.
Canon that referenced the parent remains valid as a historical record.
Dependents must explicitly re-link to the appropriate child.

---

## CONFLICT PROTOCOL

### Types and Detection

**POLYSEMY** — one term, multiple concepts
- Detection: `sfe.detect_polysemy(term)` finds term linked to > 1 concept
- Example: "risk" in trading vs "risk" in medicine have different QC-2 schemas

**SYNONYMY** — many terms, one concept
- Detection: two terms map to semantically identical concepts (high question-basis overlap)
- Action: create TranslationMap with loss=0, propose merge as MINOR or MAJOR

**CLASH** — two concept variants incompatible in same context
- Detection: same context_id used with two concepts that have contradictory boundary conditions
- Action: scope separation or fission

**SCOPE_GAP** — concept used outside its validated scope
- Detection: domain_tags in Outcome don't match concept's valid_scope in QC-3
- Action: expand scope (MINOR) or create domain_variant (MINOR)

**MEASUREMENT** — measurement schemas cannot be unified
- Detection: two QC-2 answers for same concept have incompatible schemas
- Action: requires MAJOR split

### Resolution States

**OPEN** — conflict detected, not yet addressed
- All new conflicts start here
- SFE dashboard shows open conflicts as urgent
- Conflicts open > 14 days trigger MAJOR review requirement

**SCOPED_COEXISTENCE** — both variants valid, in different scopes
- Applies to: POLYSEMY, SYNONYMY with domain variants
- Action: create domain_variants on concept, separate TranslationMaps
- Canon promotes the scoped coexistence explicitly

**SPLIT** — incompatibility resolved by fission
- Applies to: CLASH, MEASUREMENT
- Action: split_concept() executed, TranslationMaps created

**SUPERSEDED** — one side was wrong, deprecated
- Applies to: cases where evidence clearly favors one variant
- Action: losing variant deprecated, winning variant MINOR-updated

**INVALID** — conflict was based on erroneous detection
- Action: mark invalid with explanation, receipt required

### Conflict Resolution API

```python
sfe.resolve_conflict(
    conflict_id="CONF-xxxx",
    resolution=ConflictResolution.SCOPED_COEXISTENCE,
    resolution_notes="risk in trading = expected loss (QC-2: loss distribution). "
                     "risk in medicine = harm probability (QC-2: clinical indicator). "
                     "Separate domain_variants created. TranslationMap: loss=0.4.",
    resolved_by="founder",
)
```

---

## Drift Prevention

### The anti-drift properties are structural, not procedural:

1. **Append-only receipts** — no concept mutation without receipt
2. **MAJOR gate** — requires outcome pressure or contradiction (not opinion)
3. **Falsification requirement** — every canonical concept must have QC-5 answered
4. **Auto-revert of provisional canon** — per Conciliar Amendment Section XIII
5. **Dissent preservation** — minority votes on MAJOR changes stored permanently

### Drift detection signals:

- MAJOR changes without outcome_pressure: immediate URGENCY_INFLATION_ALERT
- Concept version increments without evidence: blocked by API validation
- Completeness_score decreasing: impossible by design (answers append-only)
- Silent meaning changes: impossible — all writes are append-only JSONL

### The semantic equivalent of "oral tradition rotting":

Without SFE, meaning drifts when:
- Teams change and redefine terms informally
- Documents accumulate and contradict each other
- "Common sense" overrides careful definition
- Cross-domain analogies are imported without loss accounting

SFE prevents all four by making:
- Every definition change require evidence and a receipt
- Every cross-domain use require a TranslationMap with explicit loss
- Every meaning dispute a structured Conflict (not culture war)
- Every concept version traceable to its origin and evolution

This is moving from oral tradition to scientific method.
