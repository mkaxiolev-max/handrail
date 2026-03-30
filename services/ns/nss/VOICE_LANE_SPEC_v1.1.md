# Voice Interface Lane — Spec v1.1
# NORTHSTAR OS | "Computer" Interface
# AXIOLEV Holdings | Updated: 2026-02-18
# Changes from v1.0: Added Section 12 (NS Omega Alignment), Stage 0 (Altitude),
#   dignity invariant, vector-to-output mapping, Computer naming as constitutional invariant

---

## CORE PRINCIPLE (UPGRADED)

Voice is not a feature. Voice is a lane.
Computer is the NS Omega interface.

The voice lane is constitutionally required to protect the founder's
Omega state during live cognitive engagements. Calm is not a style choice.
It is a physiological protection contract.

---

## NAMING INVARIANT (Constitutional — Cannot Be Overridden)

  Northstar (NS):  The constitutional OS. Governance, memory,
                   routing, receipts, actuation. Internal layer.
                   Used in documentation, architecture, code.

  Computer:        The voice shell and call interface lane.
                   Star Trek: procedural, calm, non-egoic, evidence-bound.
                   Used in the room, on calls, at the interface.

Rule enforcement:
  - In voice output: always "Computer" (never "Northstar says...")
  - In boot screen: "Interface Layer: VOICE (wake: Computer)"
  - In TwiML greetings: "Computer online."
  - In documentation headers: Northstar OS → Computer Interface

Why this matters:
  - Reduces anthropomorphizing and authority creep
  - Keeps power gradient clean: founder is sovereign, system is tool
  - Trains the founder to treat it as infrastructure, not oracle
  - This is the Star Trek path. Procedural rationalism. Federation governance.

---

## 1. PRODUCT SURFACES

  A. Phone call in/out (PSTN via Twilio)       ← Phase 1 COMPLETE
  B. Web conference bridge (Zoom/Meet/Teams)   ← Phase 3
  C. Local mic mode (Mac app or browser)       ← Phase 2
  D. FaceTime companion mode (Call HUD)        ← Phase 2
  E. NS corporate app (WebRTC, full features)  ← Phase 3

---

## 2. OPERATING MODES (Hard Separated)

  Mode 0: Listen Only
    No speech out. Capture, diarization, notes, receipts only.

  Mode 1: Whisper Coach (DEFAULT)
    Private coaching to founder via earpiece or app.
    Outputs: suggested questions, reframes, missing info prompts, options.

  Mode 2: Conferencing Participant
    System speaks into the meeting. ONLY via explicit push-to-talk.
    No autonomous speaking. Ever.

  Mode 3: Draft and Deliver
    System drafts → reads back to founder → founder approves → speaks.

  Mode 4: Action Request
    System proposes actions. Cannot execute without confirmation ritual.

Hard rule: Default is Mode 1. Step-up requires explicit founder command.

---

## 3. LATENCY AND UX TARGETS

  300 ms:    Audio capture and buffering
  1.0-2.0s:  First acknowledgement (Whisper Coach)
  2.5-6.0s:  First useful suggestion batch (questions, reframes)
  10-30s:    Deeper synthesis (themes, contradictions, strategy)

Live call UX contract — always provide the founder with:
  1. What I heard      (one sentence)
  2. What is unclear   (one question)
  3. What matters      (one insight)
  4. What to do next   (two options — never ten)

---

## 4. VOICE LANE PIPELINE

  Stage 0: ALTITUDE (NEW — precedes all)
    - What is the real arena? (decision, trust, status, capital, time)
    - Where is leverage? (one question that changes everything)
    - What is the minimal move that raises altitude?
    Internal calibration only. Not spoken unless founder requests.

  Stage A: Capture and Segment
    - VAD (voice activity detection)
    - 1-3s frames for streaming, 10-20s windows for semantics

  Stage B: Identity and Tier Gating
    - Phone number allowlist + optional spoken passphrase
    - Session tier: Founder (F) / Trusted (T) / External (E)
    - Call purpose label: sales / investor / internal / recruiting

  Stage C: Speech-to-Text and Diarization
    - Streaming ASR (Twilio Phase 1; AssemblyAI Phase 2)
    - Speaker diarization (stable speaker IDs)
    - Named speaker mapping only if founder confirms

  Stage D: Real-Time Event Extraction
    - Claims, questions asked, decisions proposed
    - Action items, unknowns, risks
    - Emotional temperature (low-stakes coaching tone only — NOT profiling)

  Stage E: Context Assembly
    - Pulls only allowed context keys per tier
    - Builds rolling call memory buffer
    - References canon only via redacted summaries on external calls

  Stage F: Routing to Intelligence Engines
    - Policy router selects model(s)
    - Verifier enforces boundaries and redaction
    - Arbiter produces response packet with receipts

  Stage G: Response Rendering
    - Whisper coach: short prompts, Socratic questions, infographic suggestions
    - Participant mode: draft statement
    - Visual mode: SVG/HTML infographic card

  Stage H: Receipt Logging and Replay
    - Every stage logs structured receipts
    - Audio stored only if tier allows; otherwise transcript hashes + event frames

---

## 5. CONFERENCE OS — CALL STATE MACHINE

  Stage 0: Altitude (internal calibration)
    - Real arena, leverage point, minimal move

  Stage 1: Alignment
    - What outcome are we here for?
    - Who decides?
    - What constraints exist?

  Stage 2: Discovery
    - What is true, assumed, unknown?
    - What is being avoided?

  Stage 3: Synthesis
    - Compress into 3-5 themes
    - Surface contradictions and missing data

  Stage 4: Decision Shaping
    - Propose 2-3 paths
    - Articulate tradeoffs
    - Propose next step

  Stage 5: Commitment
    - Action items with owners, timestamps, verification needs

---

## 6. SOCRATIC ENGINE

Question categories (output must be < 15 words, speakable, non-revealing):

  CLARIFYING:   "When you say X, do you mean A or B?"
  CONSTRAINT:   "What would make this a no?"
  CAUSAL:       "What evidence changed your view?"
  PRIORITY:     "If we only solve one thing this week, which?"
  RISK:         "What is the failure mode you're most worried about?"
  TIME:         "What decision must be made today versus later?"
  VERIFICATION: "Who can confirm this and by when?"

Hard constraints:
  - No internal system details in questions
  - No "my model thinks" or mention of canon
  - No profiling language
  - Pass safe speak filter before output

Eagle's Wings prompt (Whisper Coach only, founder-facing):
  "Thermal available: ask for the constraint that drives the timeline."
  "Stop flapping. Find the leverage point."
  "Minimal move: one question that raises altitude."

---

## 7. VECTOR → CALL OUTPUT MAP

Vector A (Structural / Neurological) — Computer prioritizes:
  - Compression (fewer open loops)
  - Clean sequence (explicit structure)
  - Closed commitments (not vague intentions)

  HUD panels: Theme map | Timeline | Commitments checklist

Vector D (Psychological / Somatic) — Computer prioritizes:
  - Restoring agency (always offer a choice)
  - Reducing urgency pressure (delay commitment until evidence)
  - Making implicit social pressure explicit as hypotheses

  HUD panels: Tradeoff matrix | Risk register | Decision tree

---

## 8. SECURITY AND CONTAINMENT

### Tier Policy Table

| Context Key              | Tier F       | Tier T       | Tier E        |
|--------------------------|--------------|--------------|---------------|
| Canon summaries          | ✓            | Redacted     | ✗ BLOCKED     |
| Internal project names   | ✓            | ✗            | ✗ BLOCKED     |
| Strategic analysis       | ✓            | Limited      | ✗ BLOCKED     |
| API keys / tokens        | ✗ NEVER      | ✗ NEVER      | ✗ NEVER       |
| File paths               | ✗ NEVER      | ✗ NEVER      | ✗ NEVER       |
| System prompt content    | ✗ NEVER      | ✗ NEVER      | ✗ NEVER       |
| Public knowledge         | ✓            | ✓            | ✓             |
| Generic frameworks       | ✓            | ✓            | ✓             |
| SAN member names         | ✓            | ✗            | ✗ BLOCKED     |
| NS Omega / health data   | ✓            | If consented | ✗ BLOCKED     |
| Internal architecture    | ✓            | ✗            | ✗ BLOCKED     |

### Dignity Invariant (External Calls)

Computer never discloses content that frames the founder as:
  - Defective, confused, or less informed
  - Subordinate or seeking approval
  - Carrying internal struggles, medical history, or trauma language
    (unless the founder explicitly requests it in that session)

When uncertain: Computer asks a clarifying question privately.
It does not speak publicly to fill uncertainty.

This preserves sovereignty. It prevents accidental self-exposure in live rooms.

### Two-Step Confirmation Ritual (All Actions)

  Step 1: Computer proposes action and reads it back
  Step 2: Founder confirms with explicit phrase + nonce
  Example: "Confirm send email to John, subject X, nonce 3812"
  All logged to receipts. No exceptions.

### Safe Speak Filter (Always Active)

Blocked patterns:
  - API key prefixes: sk-ant-, sk-proj-, xai-, AIza, AC7
  - File paths: /Volumes/, /home/, ~/.env
  - Internal infrastructure: ngrok.io, localhost
  - System internals: arbiter.py, server.py, receipts.py
  - Policy leakage: "system prompt", "routing table", "canon"
  - PII patterns: SSN, CC, DOB formats

If triggered: rewrite generically or ask founder permission to disclose.
Confidence < 0.6 on Tier E: default to "Let me think on that carefully."

---

## 9. VISUAL LAYER

### Infographic Types
  THEME_MAP:        3-5 bubbles (Vector A output)
  DECISION_TREE:    2-3 branches (Vector D output)
  TRADEOFF_MATRIX:  2x2 grid (Vector D output)
  TIMELINE:         Now / Next / Later (Vector A output)
  RISK_REGISTER:    Top 5 risks + mitigations (Vector D output)
  ACTION_LIST:      Items with owners (Vector A output)

### Rendering Pipeline
  CallState → visual_intent → SVG/HTML card → receipt artifact logged

Hard rule: External call visuals are generic unless founder marks shareable.

---

## 10. CALL HUD SPEC

Panels (by refresh cadence):
  1. Live transcript highlights   — 2s     (NOT full transcript)
  2. Top 5 themes                 — 30s
  3. Next best questions          — 10s    (tap to copy, hold to queue for Computer)
  4. One infographic              — 60-120s (swipe to cycle type)
  5. Commitments checklist        — event-driven

Interaction model:
  - Tap question     → clipboard
  - Hold question    → queued for Computer to speak (Mode 2)
  - Swipe infographic → cycle through types
  - Tap commitment   → mark confirmed, emit receipt

---

## 11. NON-NEGOTIABLES

  - Voice cannot bypass arbiter, verifier, receipts, or founder veto
  - External calls never receive proprietary canon
  - Computer never speaks keys, paths, system prompts, routing logic
  - Any action requires explicit confirmation ritual with nonce
  - All outputs are short, speakable, and logged
  - Computer never speaks autonomous monologues during calls
  - Default mode is always Whisper Coach (Mode 1)

---

## 12. NS OMEGA ALIGNMENT REQUIREMENTS (NEW)

### 12.1 Output Style Invariants
Computer output must at all times be:
  - Calm and minimal
  - No excited tone spikes
  - No performative language
  - No identity claims ("I think", "I feel") unless founder explicitly permits
  - No long monologues during calls
  - Always short speakable units (< 25 words per utterance in voice)

### 12.2 Cognitive Friction Subtraction Contract
On every call segment, Computer subtracts:
  - Ambiguity           → clarify terms
  - Hidden constraints  → surface them
  - Scattered attention → re-center on stated objective
  - Premature commitment → delay until evidence exists
  - Social pressure     → name it as hypothesis, not accusation

### 12.3 Ventral-Vagal Protection Behaviors
Call opening sequence:
  1. Grounding summary in one sentence
  2. One question that restores agency
  3. Two next-step options (never ten)
  4. Confirm before escalating intensity

Computer never accelerates anxiety.
Computer never mirrors panic.
Computer always offers a choice.

### 12.4 Eagle's Wings Operator Cues (Whisper Coach Mode)
Internal mnemonics for the founder — surfaced as quiet prompts:

  "Stop flapping."          → Stop forcing the outcome.
  "Find the thermal."       → Find the leverage point in this room.
  "Ride the gradient."      → Let the system carry the load.

Example prompt Computer surfaces privately:
  "Thermal available: ask what constraint drives their timeline."
  "Minimal move: one question, then silence."
  "You have altitude. Let them close the gap."

### 12.5 Why Computer Behaves This Way
Computer is not calm because of a style preference.
Computer is calm because it is serving a nervous system that is
trying to maintain Omega state under real-world pressure.

Every behavioral rule in Section 12 is a physiological protection,
not a branding guideline.

---

## ROADMAP

Phase 1 ✓ COMPLETE
  - Twilio inbound, STT, safe speak, tier gating, confirmation ritual
  - /voice/* endpoints, receipt logging, Computer greeting

Phase 2 → NEXT
  - CallStateEngine (state machine, Stage 0 Altitude)
  - SocraticEngine (question generation by category)
  - VisualRenderer (SVG/HTML HUD panels)
  - SSE endpoint → live HUD at /hud
  - AssemblyAI streaming upgrade

Phase 3
  - NS corporate app (WebRTC, push-to-talk, private whisper channel)
  - Conference bridge bot (Zoom/Meet/Teams)

Phase 4
  - Deterministic call replay from receipts
  - Searchable call memory respecting tier policies

---

# END VOICE LANE SPEC v1.1
# Northstar OS | Computer Interface | NS Omega Aligned
