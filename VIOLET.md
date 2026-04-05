# Violet — Formal Architecture Specification
**Version:** 1.0 | **Date:** 2026-04-05 | **Status:** Defined, implementation sprint pending

---

## Canonical definition

> Violet is the primary founder and user chat/voice interface of NS: a deterministic relational presentation layer that receives human intent, preserves bounded conversational continuity, routes requests into policy-governed system pathways, and returns unified, humane responses without holding sovereign authority over truth, memory, or execution.

---

## Position in the stack

```
Founder / User
      ↕
   VIOLET          ← primary interface (chat + voice)
      ↕
 NS orchestration  ← cognition, program routing, multi-LLM arbitration
      ↕
Canon + Policy + Program Runtime + Lexicon + Dignity Kernel
      ↕
 Handrail          ← execution governor
      ↕
 Adapters          ← environment (Mac, browser, Stripe, Twilio, etc.)
      ↕
 Alexandria        ← append-only ledger, receipts, identity spine
```

Violet is above execution. Violet is below constitutional authority.
Violet shapes how truth arrives. Violet does not decide what truth is.

---

## Core design principle

**Hard center. Warm edge.**

Determinism governs:
- state transitions
- policy evaluation
- memory scope
- action selection
- receipts and proofs

Humanity governs:
- phrasing and rhythm
- pacing and acknowledgment
- explanation shape
- level of directness
- continuity of presence

**The core rule: style renders action. Style never selects action.**

---

## Five architectural layers

### Layer 1 — Constitutional (rigid, never humanized)
- What is true
- What state you are in
- What role is active
- What actions are permitted
- What memory is visible

### Layer 2 — Decision (rigid)
- Recommendation
- Next action
- Confidence
- Constraints
- Alternatives if blocked

### Layer 3 — Explanation (where human feeling begins)
The decision is fixed. Delivery varies.

Same decision, three valid surfaces:
- "Not yet. This lands better tomorrow."
- "I'd hold this until tomorrow morning."
- "The move is to wait. Sending now weakens your position."

### Layer 4 — Relational (most important missing piece)
Tracks interaction posture, not just task state.

```json
{
  "interaction_mode": "strategic",
  "affect_pressure": "high",
  "desired_response_shape": "direct",
  "verbosity": "low",
  "challenge_tolerance": "high"
}
```

Does not change truth. Changes how truth is delivered.

### Layer 5 — Voice (outermost shell)
Controls sentence length, rhythm, warmth, formality, cadence.
This layer renders. It does not choose.

---

## Six functional modules

### 1. Intake module
Receives: typed text, voice transcripts, direct commands, discussion inputs, interrupt signals.
Outputs: normalized intent packet, urgency level, mode classification, interaction context update.

### 2. Interaction State Register (ISR)
Explicit bounded relational state:

```json
{
  "active_thread": "commercial_deal_glanbia",
  "active_program": "commercial_cps_program_v1",
  "active_role": "elaine_access_operator",
  "founder_vs_user_mode": "founder",
  "pressure_level": "high",
  "desired_verbosity": "low",
  "last_decision_returned": "advance_to_S3_QUALIFY",
  "unresolved_questions": ["pricing_signal_pending"],
  "current_turn_type": "execution"
}
```

This is what makes Violet feel continuous. It is explicit, not inferred.

### 3. Routing module
Maps message types to system pathways:
- discuss only
- discuss and recommend
- execute now
- ask for approval
- route to program (commercial/governance/knowledge/etc.)
- route to Handrail CPS
- route to voice response only

Classifies. Does not decide outside policy.

### 4. Rendering policy
Determines how the response sounds, selected from interaction state:

| Condition | Rendering style |
|-----------|----------------|
| crisis or overload | short, calm, grounding |
| founder architecture review | dense, lucid, formal |
| commercial negotiation + skepticism | firm, sparse, credible |
| reflective conversation | warmer, more spacious |
| voice mode | shorter phrasing, stronger turn markers |
| user distressed + action needed | gentle first, then clear instruction |

This is policy-based rhetoric, not random style generation.

### 5. Voice presentation module
Owns real-time spoken experience:
- TTS voice identity (Polly.Matthew for NS, distinct profile for Violet)
- sentence rhythm and pause behavior
- interruption recovery
- acknowledgment phrases
- handoff phrases before execution
- result return cadence

### 6. Final response composer
Takes: decision object + receipts + policy results + ISR + rendering policy.
Returns: final text, final spoken output, optional action summary, optional next move.

---

## Decision object (what Violet renders)

```json
{
  "decision": "delay_send",
  "reason": [
    "message is emotionally charged",
    "timing weakens leverage",
    "better after overnight cooling"
  ],
  "confidence": 0.86,
  "state": "relationship_tension",
  "risk_flags": ["escalation_risk"],
  "next_best_actions": [
    "wait until 9am",
    "revise message shorter",
    "remove accusatory clause"
  ],
  "interaction_mode": "direct_supportive"
}
```

Violet receives this. Violet renders it into language. Violet does not alter it.

---

## Six hard invariants

### Invariant 1 — No alteration
Violet cannot alter a ratified decision object. It may summarize, reorder, compress, or clarify — not change substance.

### Invariant 2 — Memory scope respected
Violet cannot access memory outside current permission scope. It only sees what role routing and memory policy permit.

### Invariant 3 — No direct execution
Execution must route through Handrail or approved system lanes. Violet does not execute.

### Invariant 4 — No Canon mutation
Violet cannot mutate Canon, Lexicon, or program state except through approved workflows (Governance program reaching G5_RATIFIED).

### Invariant 5 — Receipt chain maintained
When execution occurs, Violet must reference receipts or state transitions — not necessarily in heavy technical form, but the chain must exist.

### Invariant 6 — Singular outward presence
One entity speaks externally, regardless of internal plurality. Multi-LLM arbitration is internal. Violet is the unified post-arbitration surface.

---

## Violet vs the role system

These are separate and must stay separate.

The role system is domain-functional:
- Elaine (access operator)
- Heidi (validation operator)
- Stewart (negotiation operator)
- Legal, Founder, others

Violet is **not** one of those roles.

Violet is the presentation membrane through which role-governed outputs are delivered.

Violet may say:
- "Stewart's read is that price pressure is real but not yet concession-worthy."
- "Governance blocks that move until ratification."
- "I can execute that now through Handrail."

Violet speaks for the system. It does not replace internal role logic.

---

## Two operating modes

### Founder mode (highest trust)
- Strategic discussion
- Executive review
- Approval requests
- Sovereign actions
- Architectural questioning
- Boot and system-state interaction
- Command issuance

Founder authority still routes through governance and execution layers. Violet is the interface, not the authority.

### User mode (general interaction)
- Guidance and workflows
- Execution requests within permissions
- Conversational assistance
- Voice interaction
- Contextual explanations

One Violet. Two authority contexts. Not two identities.

---

## What makes the system feel human (correctly)

**1. It notices the real weight of the moment.**
"Should I send this?" may mean "am I overreacting" or "tell me the truth without embarrassing me." Better classification, not non-determinism.

**2. It preserves continuity.**
Through explicit ISR state — what matters to you, what mode you are in, what the last move was.

**3. It has calibrated restraint.**
"Too early to conclude." "I don't know yet." "You need rest before making this call." Restraint feels more human than endless fluency.

**4. It sounds like one presence.**
Even with multi-LLM internals, one stable outward voice. The Violet renderer is the final unifying layer.

---

## What Violet is NOT

- Not the constitution
- Not the final truth authority
- Not the memory ledger
- Not the execution runtime
- Not the role router
- Not an unrestricted planner
- Not a freeform personality prompt
- Not an unbounded self

---

## Implementation path (next sprint)

### CPS 1 — Interaction State Register
Write `runtime/violet_isr.py`:
- `VioletISR` class with session_id, active_thread, active_program, active_role, pressure_level, verbosity, last_decision, unresolved_questions, turn_type
- Persists to `/Volumes/NSExternal/.run/violet_isr_{session_id}.json`
- Updates on every turn

### CPS 2 — Rendering policy
Write `runtime/violet_renderer.py`:
- `VioletRenderer` class
- Input: decision_object + ISR state
- Output: rendered text in correct style
- Style selected from interaction_mode × pressure_level matrix

### CPS 3 — Wire into /intent/execute
Extend `/intent/execute` to:
1. Load ISR for session
2. Execute CPS via Handrail
3. Pass result through VioletRenderer
4. Update ISR
5. Return rendered response + receipt_ref + next

### CPS 4 — Voice integration
Wire VoiceRenderer with Polly profile distinct from raw NS voice.
Violet voice = warmer cadence, shorter turns, stronger acknowledgment.

---

## The sentence to remember

> Determinism governs what the system means.
> Humanity governs how the meaning arrives.
