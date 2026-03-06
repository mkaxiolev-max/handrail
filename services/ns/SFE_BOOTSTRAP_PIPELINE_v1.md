# SFE Lexicon Bootstrap Pipeline v1.0
# Deterministic steps from ether ingest to Lexicon v0.1
# NS∞ / AXIOLEV Holdings

## Purpose

Produce Lexicon v0.1 from cold start on first boot.
No canonization. No authority claims.
Every concept created as CANDIDATE with completeness_score = 0.0.
Authority is earned through outcomes only.

---

## Invariants

1. Every term extracted is receipted.
2. Every concept created is receipted.
3. No concept is promoted to ACTIVE without answering at least QC-1 (identity).
4. Conflicts are flagged, never suppressed.
5. Bootstrap is idempotent — running it twice produces the same state (upsert, not duplicate).

---

## Pipeline Steps

### Step 0 — Prerequisites

- Alexandria SSD mounted or internal fallback confirmed
- Receipt chain active
- SFE initialized (get_sfe() returns live instance)
- Ether store has at least one batch of ingested signal

### Step 1 — Term Extraction

**Input:** ether/events/*.json — all raw signal from ingest loop

**Process:**

For each ether batch:
1. Extract noun phrases, technical terms, domain-specific vocabulary
2. For each term:
   - Call `sfe.upsert_term(surface_form, domain_tags, usage_coord)`
   - Record chunk ref as usage_coord
   - Tag with source domain (trading, medicine, governance, etc.)

**Output:** term store populated, all receipted

**Quality gate:** at least 10 unique terms before proceeding

---

### Step 2 — Concept Candidate Clustering

**Input:** term store from Step 1

**Process:**

For each unique term stem:
1. Check if concept with this label already exists (`sfe.find_concept_by_label(label)`)
2. If exists: link term to existing concept
3. If not: create concept candidate

```
sfe.create_concept(
    label=term.surface_forms[0],
    invariant_core="[Provisional bootstrap definition — requires grounding]",
    domain_tags=term.domain_tags,
    created_by="bootstrap_v0",
)
```

This creates:
- Concept record at version 0.1.0 (CANDIDATE)
- QuestionBasis with all 6 canonical questions (unanswered)
- completeness_score = 0.0

**Output:** concept candidates created for all unique term stems

---

### Step 3 — QuestionBasis Proposal (Provisional)

**Input:** concept candidates from Step 2

**Process:**

For each concept candidate:
1. Auto-generate provisional identity answer from available corpus evidence:

```python
answer, refusal = sfe.record_answer(
    concept_id=concept["concept_id"],
    question_type=QuestionType.IDENTITY,
    answer_payload={
        "operational_definition": "[Extracted from corpus: ...]",
        "distinguishing_features": [...],
        "what_it_is_not": [],
        "domain": domain,
    },
    evidence_pack_id=ep_id,  # EvidencePack from chunk_store
    confidence=0.3,           # Low confidence — bootstrap
    created_by="bootstrap_v0",
)
```

2. If corpus has measurement language for this term, also attempt QC-2
3. Mark all bootstrap answers with confidence <= 0.4
4. completeness_score will be 0.17 (1/6) to 0.33 (2/6) after bootstrap

**Output:** partial groundings, confidence clearly marked as bootstrap-quality

---

### Step 4 — Usage Card Generation

**Input:** concepts + answers from Step 3

**Process:**

For each concept:
1. Generate a Usage Card — a structured summary:

```yaml
concept_id: CONCEPT-xxxx
label: "risk"
version: 0.1.0
status: CANDIDATE
confidence_tier: EXPERIMENTAL
completeness: 0.17

identity_answer:
  text: "[Provisional: ...]"
  confidence: 0.3
  evidence: EP-xxxx

open_questions:
  - measurement: "How do we observe or measure risk in this domain?"
  - constraint: "Where does risk apply and where does it fail?"
  - decision: "What actions change if risk is true vs false?"
  - falsification: "What outcome pattern proves we are using risk wrong?"
  - translation: "What is preserved and lost mapping risk to another domain?"

usage_citations:
  - chunk_ref: [chunk_store IDs]

next_step: "Answer open questions with evidence to increase completeness."
```

2. Store usage card as a structured note in Alexandria (proto_canon/)

---

### Step 5 — Conflict Detection

**Input:** term store, concept store

**Process:**

For each term with multiple domain_tags:
1. Check if the term maps to different concept definitions across domains
2. If so: call `sfe.detect_polysemy(term)` — creates Conflict record
3. For near-synonym clusters: call `sfe._create_conflict(ConflictType.SYNONYMY, ...)`

**Output:** Conflict records, all OPEN, none suppressed

---

### Step 6 — Translation Map Suggestions

**Input:** concept pairs that share domain vocabulary

**Process:**

For each pair of concepts where:
- Same term appears in both domain_tags
- OR concept labels are known cross-domain pairs

Create provisional TranslationMap:

```python
sfe.create_translation_map(
    source_concept_id=c1_id,
    source_domain="trading",
    target_concept_id=c2_id,
    target_domain="medicine",
    shared_questions=["Q-CANONICAL-identity", "Q-CANONICAL-falsification"],
)
```

Maps are created as PROPOSED status. Validated by outcomes only.

**Output:** Translation map suggestions with loss estimates

---

### Step 7 — Bootstrap Receipt and Summary

**Emits:**

```
LEXICON_BOOTSTRAP_COMPLETE
  terms_extracted: N
  concepts_created: N
  average_completeness: 0.17
  conflicts_flagged: N
  translations_suggested: N
  status: v0.1
  note: "No concept is canonical. All require grounding through use."
```

---

## API Usage (after boot)

```bash
# Trigger bootstrap manually
curl -X POST http://localhost:9000/lexicon/bootstrap \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "trading",
    "terms": [
      {"term": "risk", "definition": "Probability-weighted expected loss", "domain_tags": ["trading"]},
      {"term": "volatility", "definition": "Measure of price variability", "domain_tags": ["trading"]},
      {"term": "liquidity", "definition": "Ease of converting asset to cash", "domain_tags": ["trading"]}
    ]
  }'

# Check lexicon state
curl http://localhost:9000/lexicon/summary \
  -H "Authorization: Bearer $TOKEN"

# Get concept with grounding status
curl http://localhost:9000/lexicon/concepts/CONCEPT-xxxx \
  -H "Authorization: Bearer $TOKEN"

# Record an answer to ground a concept
curl -X POST http://localhost:9000/lexicon/concepts/CONCEPT-xxxx/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_type": "measurement",
    "answer_payload": {
      "measurement_procedure": "Max drawdown over rolling 30-day window",
      "observable_signals": ["portfolio_pnl", "position_size"],
      "measurement_schema": {"field": "drawdown_pct", "type": "float", "range": [-1, 0]},
      "scale": "ratio"
    },
    "evidence_pack_id": "EP-xxxx",
    "confidence": 0.8
  }'
```

---

## Graduation: Lexicon v0.1 → v1.0

Lexicon reaches v1.0 when:
- At least 10 concepts have completeness_score >= 0.8
- At least 3 concepts have completeness_score = 1.0 (canonical)
- All open conflicts have resolution_state (not all must be resolved, but classified)
- At least one TranslationMap validated by outcomes
- LEXICON_V1_RATIFIED receipt emitted by Founder

This is not a time-based graduation. It is outcome-based.
