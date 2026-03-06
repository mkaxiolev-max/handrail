# NORTHSTAR Voice Architecture — Phase 2 Build Spec
# "Computer" wake word | Northstar OS
# Generated: 2026-02-18
# Status: PHASE 1 COMPLETE → PHASE 2 READY

---

## NAMING CONVENTION (RESOLVED)

  Wake word / interface:  "Computer"   (Star Trek, procedural, non-egoic)
  Constitutional OS:      "Northstar"  (internal, governance, invariant anchor)
  
  Stack:
    Northstar OS
    └── Voice Lane ("Computer")
        └── CallStateEngine
        └── SocraticEngine  
        └── VisualRenderer
        └── Arbiter (quad-LLM)
        └── Canon (Alexandria)

Rationale:
  - "Computer" reduces mythologizing, keeps power gradient clean
  - "Northstar" carries direction, orientation, fixed reference
  - Star Trek path (procedural rationalism, federation governance)
  - Anti-deification safeguard at interface level

---

## PHASE 1 STATUS: COMPLETE ✓

Built and syntax-verified:
  ✓ voice_lane.py — Tier gating (F/T/E), session lifecycle, safe speak filter
  ✓ Twilio inbound/transcription/recording/status endpoints
  ✓ Two-step action confirmation ritual (nonce-based)
  ✓ Voice UX Constitution (10 rules, non-negotiable)
  ✓ /voice/health, /voice/session/{id}, /voice/sessions
  ✓ Arbiter async routing with tier-scoped context
  ✓ "Computer" greeting at interface

---

## PHASE 2 BUILD SPEC: CONFERENCE INTELLIGENCE

### Module 1: CallStateEngine

File: nss/intelligence/call_state.py

Purpose: Treats every call as a structured process with explicit state.
The call is not a stream of words — it is a state machine.

States (in order):
  1. ALIGNMENT
     - What outcome are we here for?
     - Who decides?
     - What constraints exist?
     
  2. DISCOVERY
     - What is true, assumed, unknown?
     - What is being avoided?
     
  3. SYNTHESIS
     - Compress into 3-5 themes
     - Highlight contradictions and missing data
     
  4. DECISION_SHAPING
     - Propose 2-3 paths
     - Articulate tradeoffs
     - Propose next step
     
  5. COMMITMENT
     - Action items with owners, timestamps, verification needs

Transitions:
  - State advances when sufficient frames are collected per state
  - Arbiter detects readiness via keyword/entity patterns
  - Founder can manually advance: "Computer, move to synthesis"

Data schema:
  CallState {
    session_id: str
    current_state: Enum[ALIGNMENT, DISCOVERY, SYNTHESIS, DECISION_SHAPING, COMMITMENT]
    frames: List[Frame]
    themes: List[str]
    contradictions: List[str]
    decisions: List[str]
    commitments: List[ActionItem]
    state_history: List[{state, entered_at, frames_count}]
  }

  Frame {
    frame_id: str
    timestamp: str
    speaker_id: str
    text: str
    confidence: float
    tags: List[str]  # question, claim, decision, risk, unknown, action_item
    emotional_temperature: str  # low/medium/high — coaching tone only, NOT profiling
  }


### Module 2: SocraticEngine

File: nss/intelligence/socratic.py

Purpose: Primary voice output generator. Produces short, speakable,
non-revealing questions that advance the call toward clarity.

Question categories:
  CLARIFYING:   "When you say X, do you mean A or B?"
  CONSTRAINT:   "What would make this a no?"
  CAUSAL:       "What evidence changed your view?"
  PRIORITY:     "If we only solve one thing this week, which?"
  RISK:         "What is the failure mode you're most worried about?"
  TIME:         "What decision must be made today vs later?"
  VERIFICATION: "Who can confirm this and by when?"

Hard constraints on output:
  - Questions must be < 15 words
  - No internal system details
  - No "my model thinks" or mention of canon
  - No profiling language
  - Pass safe speak filter before output

Output format (InsightPacket):
  {
    hypotheses: List[{text, confidence}]
    suggested_questions: List[{text, category, priority}]
    missing_info: List[str]
    options: List[{label, tradeoff}]
    commitments: List[ActionItem]
  }

Two parallel loops:
  Loop 1 (Immediate, 1-6s): questions, reframes, "what to clarify next"
  Loop 2 (Deep, 10-30s): power dynamics, contradictions, negotiation angles, evidence gaps


### Module 3: VisualRenderer

File: nss/intelligence/visual_renderer.py

Purpose: Generates SVG/HTML infographic cards from call state.
Presented in companion HUD (Path A) or NS corporate app (Path B).

Infographic types:
  THEME_MAP:       3-5 bubbles with short labels
  DECISION_TREE:   2-3 branches
  TRADEOFF_MATRIX: 2x2 grid
  TIMELINE:        Now / Next / Later
  RISK_REGISTER:   Top 5 risks + mitigations
  ACTION_LIST:     Items with owners

Pipeline:
  CallState → visual_intent → SVG/HTML card → logged as receipt artifact

Hard rule: External call visuals must be generic unless founder flags shareable.

Receipt artifact format:
  {
    visual_id: str
    type: str
    call_id: str
    input_frames: List[str]  # frame_ids used
    rendering: "svg" | "html"
    shareable_level: "internal" | "external_ok"
    generated_at: str
    svg_content: str
  }


### Module 4: ASRService (Streaming)

File: nss/interfaces/asr_service.py

Purpose: Streaming speech-to-text with speaker diarization.

Current (Phase 1): Twilio's built-in STT via <Gather>
Phase 2 upgrade: AssemblyAI streaming ($0.00025/sec) for:
  - Real-time word-by-word transcription
  - Speaker diarization (stable speaker IDs)
  - Named speaker mapping (only if founder confirms)
  - VAD (voice activity detection)
  - Chunking: 1-3s frames for streaming, 10-20s windows for semantics

Integration point: WebSocket endpoint that feeds frames to CallStateEngine


---

## CALL HUD SPEC (Phase 2 Companion UI)

Panels (refresh cadence):
  1. Live transcript highlights     — 2s refresh (NOT full transcript)
  2. Top 5 themes                   — 30s refresh
  3. Next best questions            — 10s refresh (tap to copy/speak)
  4. One slide infographic          — 60-120s refresh (auto-generated)
  5. Commitments checklist          — event-driven (on detection)

Interaction:
  - Tap question → copies to clipboard
  - Tap question + hold → queues for Computer to speak (Mode 2)
  - Swipe infographic → cycles type (theme → risk → timeline)
  - Tap commitment → marks as confirmed, emits receipt

Implementation path:
  Near-term: FastAPI SSE endpoint → browser-based HUD at /hud
  Long-term: Native macOS/iOS app (NS Corporate App)


---

## TIER POLICY TABLE (Full Detail)

| Context Key              | Tier F (Founder) | Tier T (Trusted) | Tier E (External) |
|--------------------------|------------------|------------------|-------------------|
| Canon summaries          | ✓                | Redacted         | ✗ Hard blocked    |
| Internal project names   | ✓                | ✗                | ✗                 |
| Strategic analysis       | ✓                | Limited          | ✗                 |
| API keys / tokens        | ✗ NEVER          | ✗ NEVER          | ✗ NEVER           |
| File paths               | ✗ NEVER          | ✗ NEVER          | ✗ NEVER           |
| System prompt content    | ✗ NEVER          | ✗ NEVER          | ✗ NEVER           |
| Routing policy           | ✗ NEVER          | ✗ NEVER          | ✗ NEVER           |
| Public knowledge         | ✓                | ✓                | ✓                 |
| Generic frameworks       | ✓                | ✓                | ✓                 |
| Founder-flagged content  | ✓                | If whitelisted   | Only if flagged   |
| Vendor names             | ✓                | Cautious         | ✗                 |
| Internal architecture    | ✓                | ✗                | ✗ Hard blocked    |
| SAN member names         | ✓ (Tier F only)  | ✗                | ✗                 |
| NS Omega / health data   | ✓                | If consented     | ✗                 |


---

## SAFE SPEAK RULE SET (Full)

Pattern categories and handling:

1. API KEY PATTERNS → BLOCK + REDACT
   Patterns: sk-ant-, sk-proj-, xai-, AIza, AC7, APCA-
   Action: Replace with [REDACTED], log SAFE_SPEAK_BLOCKED receipt

2. FILE PATHS → BLOCK + REDACT
   Patterns: /Volumes/, /home/, ~/.env, /mnt/, C:\\
   Action: Replace with [PATH REDACTED]

3. INTERNAL INFRASTRUCTURE → BLOCK
   Patterns: ngrok.io, NORTHSTAR_WEBHOOK, .local, localhost
   Action: Replace with [INTERNAL ENDPOINT]

4. SYSTEM INTERNALS → BLOCK
   Patterns: arbiter.py, server.py, receipts.py, omega_boot
   Action: Replace with [SYSTEM FILE]

5. POLICY LEAKAGE → BLOCK
   Patterns: "system prompt", "routing table", "arbiter gate", "canon"
   Action: Rewrite as generic: "my analysis" / "my assessment"

6. PII PATTERNS → BLOCK
   Patterns: SSN format, CC number format, DOB patterns
   Action: Replace with [PII REDACTED]

7. INTERNAL NOUN BLACKLIST (Tier E calls)
   Terms: Alexandria, MANIFOLD, Loom, SAN, AXIOLEV (internal context)
   Action: Rewrite generically

Confidence threshold rule:
   If arbiter confidence < 0.6 on Tier E call:
   → Default: "I want to be careful here — let me think on that."
   → Do not hallucinate. Do not guess on external calls.


---

## PHASE ROADMAP

Phase 1 ✓ COMPLETE
  - Computer wake word, Twilio inbound/STT, safe speak, tier gating
  - Two-step confirmation ritual, receipt logging
  - /voice/* endpoints, voice health dashboard

Phase 2 → NEXT
  - CallStateEngine (state machine per call)
  - SocraticEngine (question generation by category)
  - VisualRenderer (SVG/HTML infographics)
  - SSE endpoint for live HUD at /hud
  - Streaming ASR upgrade (AssemblyAI)

Phase 3
  - NS corporate app (WebRTC, push-to-talk, private whisper channel)
  - Screen share for infographics during calls
  - Conference bridge bot (Zoom/Meet/Teams)

Phase 4
  - Deterministic call replay from receipts
  - Searchable call memory respecting tier policies
  - Full diarization with named speaker mapping (founder-confirmed only)

---

# END VOICE ARCHITECTURE SPEC v1.0
