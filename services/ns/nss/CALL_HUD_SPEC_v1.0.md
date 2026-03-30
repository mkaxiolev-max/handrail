# Call HUD Layout Spec
# NORTHSTAR OS | Computer Interface | NS Omega Aligned
# Version 1.0 | 2026-02-18
# Surface: Browser companion (/hud) → Phase 3: Native macOS/iOS app

---

## DESIGN PHILOSOPHY

The HUD is not a dashboard. It is not an information display.

It is a cognitive load reduction instrument.

Every pixel serves one purpose: keep the founder in NS Omega state
while engaged in a live call. That means:

  - Show less than you think
  - Surface leverage, not everything
  - Never interrupt with non-actionable information
  - Always offer a choice, never a command
  - Calm is not aesthetic — it is functional

Star Trek LCARS is the visual ancestor.
The HUD should feel like infrastructure that thinks, not software that talks.

---

## LAYOUT (1080p reference, 5-panel grid)

```
╔═══════════════════════════════════════════════════════════════╗
║  COMPUTER  ·  [CALL DURATION]  ·  TIER: F  ·  MODE: WHISPER  ║
╠══════════════════════╦════════════════════════════════════════╣
║                      ║                                        ║
║   PANEL 1            ║   PANEL 3                              ║
║   HEARD              ║   NEXT QUESTION                        ║
║   (live, 2s refresh) ║   (top 1, tap to copy)                 ║
║                      ║                                        ║
╠══════════════════════╬════════════════════════════════════════╣
║                      ║                                        ║
║   PANEL 2            ║   PANEL 4                              ║
║   THEMES             ║   INFOGRAPHIC                          ║
║   (3-5, 30s refresh) ║   (60-120s, swipe to cycle)            ║
║                      ║                                        ║
╠══════════════════════╩════════════════════════════════════════╣
║  PANEL 5 — COMMITMENTS                                        ║
║  [owner · item · timestamp]  tap to confirm · emits receipt   ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## PANEL SPECIFICATIONS

### HEADER BAR
Always visible. Always calm. Dark background. Minimal.

  Left:    COMPUTER  (wake word, identity anchor)
  Center:  [00:00:00]  (call duration, live)
  Right:   TIER: F | MODE: WHISPER | [STAGE: DISCOVERY]

Colors:
  Background: #050d1a
  Text: #607080
  Active element: #00ff88
  Warning: #ffaa44
  Blocked/external: #ff4444

Typography: SF Mono or similar monospace. No serifs. No decorative fonts.

---

### PANEL 1 — HEARD
Purpose: Closes the loop between what was said and what Computer registered.
Shows the founder what Computer is working from. Builds trust.

Position: Upper left (primary attention zone)
Size: 35% width, 30% height
Refresh: 2 seconds (real-time feel)

Content:
  - Last 1-3 sentences of transcript (not full — highlights only)
  - Speaker label if diarization is active ("You:" / "Them:")
  - Confidence indicator: green dot (>0.8) / yellow dot (0.6-0.8) / red dot (<0.6)

Design rules:
  - Never scroll. If it doesn't fit, truncate.
  - Never show the full transcript here. That's a separate receipt view.
  - Font: 14px, line height 1.5

Label: HEARD
Label color: #607080

---

### PANEL 2 — THEMES
Purpose: Vector A output. Compression. Fewer open loops.
Shows what the call is actually about, stripped of noise.

Position: Lower left
Size: 35% width, 30% height
Refresh: 30 seconds (stability over reactivity)

Content:
  - 3-5 theme labels, one per line
  - Each label: 4-8 words maximum
  - Priority order: highest signal first
  - Optional: small confidence bar (right-aligned, muted)

Example:
  ─────────────────────
  Timeline is the real constraint
  Budget not yet committed
  Decision authority unclear
  Risk framing missing
  ─────────────────────

Design rules:
  - No bullets. Single weight text.
  - Themes appear/disappear as call evolves. No animation.
  - If fewer than 3 themes: show what exists, don't pad.
  - If more than 5: show top 5 only.

Label: THEMES
Label color: #607080

---

### PANEL 3 — NEXT QUESTION
Purpose: Primary Socratic output. The most leverage Computer can offer in real time.
Shows ONE question, not a list. Abundance kills action.

Position: Upper right (action zone)
Size: 65% width, 30% height
Refresh: 10 seconds (or on new event frame)

Content:
  - ONE question (the highest-priority Socratic output)
  - Category label: CLARIFYING / CONSTRAINT / RISK / TIME / etc.
  - Eagle's Wings cue if applicable (whisper-mode only, muted):
    e.g. "Thermal: constraint drives timeline"

Display format:
  ╔═══════════════════════════════════════════════════════════╗
  ║  CONSTRAINT                                               ║
  ║                                                           ║
  ║  "What would make this a no?"                             ║
  ║                                                           ║
  ║  [COPY]  [QUEUE FOR COMPUTER]          Thermal available  ║
  ╚═══════════════════════════════════════════════════════════╝

Interactions:
  - [COPY]: copies question text to clipboard
  - [QUEUE FOR COMPUTER]: queues for Computer to speak (Mode 2, requires Mode 2 active)
  - Tap anywhere: reveals next 2 questions in queue (secondary panel expands)

Eagle's Wings prompt (muted text, lower right):
  Appears only in Whisper mode, only when a leverage point is detected.
  Maximum 8 words. Never speaks. Only shown to founder.

Design rules:
  - Question text: 20px, prominent
  - Category label: 10px, all caps, muted
  - Never show multiple questions in primary view

Label: NEXT QUESTION
Label color: #607080

---

### PANEL 4 — INFOGRAPHIC
Purpose: Visual synthesis. One slide. Auto-selected by call state.
Vector A types: Theme map, Timeline, Commitments
Vector D types: Tradeoff matrix, Risk register, Decision tree

Position: Lower right
Size: 65% width, 30% height
Refresh: 60-120 seconds (stability — don't flicker during synthesis)

Content: SVG or HTML card, auto-selected based on call state:

  ALTITUDE / ALIGNMENT state → Theme map
  DISCOVERY state           → Risk register
  SYNTHESIS state           → Timeline (Now/Next/Later)
  DECISION SHAPING state    → Tradeoff matrix (2x2) or Decision tree
  COMMITMENT state          → Action list with owners

Swipe behavior:
  Swipe left/right → cycle through available infographic types
  Founder controls what they want to see

Shareable flag:
  Small lock icon: 🔒 = internal only  |  🌐 = marked shareable by founder
  External call infographics are generic unless founder unlocks

Each infographic logged as receipt artifact:
  {visual_id, type, call_id, input_frames[], rendered_at, shareable_level}

Design rules:
  - SVG preferred (scalable, clean, no raster artifacts)
  - Maximum 5 data elements per infographic (cognitive load cap)
  - No gradients, shadows, or decorative elements
  - Label font: SF Mono 11px

Label: INFOGRAPHIC  |  [← →] swipe indicator
Label color: #607080

---

### PANEL 5 — COMMITMENTS
Purpose: Closes every call with explicit, timestamped, receipted action items.
Prevents the most common call failure: good discussion, no decisions.

Position: Full-width footer
Size: 100% width, ~15% height
Refresh: Event-driven (appears when commitment detected)

Content:
  [owner] · [action item] · [timestamp] · [CONFIRM] · [DISPUTE]

Example:
  ─────────────────────────────────────────────────────────────
  Mike  ·  Send revised term sheet by Friday  ·  14:23  [CONFIRM]
  Sarah ·  Confirm budget authority by EOD    ·  14:31  [CONFIRM]
  —     ·  Revisit pricing in next session    ·  14:38  [DISPUTE]
  ─────────────────────────────────────────────────────────────

Interactions:
  - [CONFIRM]: marks commitment as accepted, emits COMMITMENT_CONFIRMED receipt
  - [DISPUTE]: flags for review, emits COMMITMENT_DISPUTED receipt
  - Tap item: expand to show full transcript context that generated it

Design rules:
  - Panel collapses if no commitments detected
  - Maximum 5 visible; scroll if more
  - Color: confirmed = green accent | disputed = orange | pending = muted

Label: COMMITMENTS  |  [n detected]
Label color: #607080

---

## COLOR SYSTEM

```
Background (base):      #050d1a
Background (panel):     #0a1428
Background (active):    #0f1e38
Border (panel):         #1a2e4a
Border (active):        #1e4060

Text (primary):         #d0e0f0
Text (secondary):       #8099b0
Text (muted / labels):  #607080

Accent (healthy):       #00ff88   (Tier F, high confidence, confirmed)
Accent (caution):       #ffaa44   (Tier T, medium confidence, pending)
Accent (blocked):       #ff4444   (Tier E hard block, low confidence)
Accent (insight):       #66aaff   (Eagle's Wings cue, thermal available)
```

---

## OMEGA ALIGNMENT CHECKLIST FOR HUD

Before every HUD render, verify:

  ✓ Panel 3 shows ONE question — not a list
  ✓ Panel 2 shows THEMES — not a transcript dump
  ✓ Eagle's Wings cues are muted — not prominent
  ✓ No panel is blinking, animating, or demanding attention
  ✓ Commitment panel is collapsed if nothing detected
  ✓ Header shows current stage — not a progress bar or urgency indicator
  ✓ Infographic has ≤ 5 data elements
  ✓ External tier: no proprietary content visible anywhere

If any check fails: the HUD is adding noise, not subtracting it.
A HUD that creates cognitive load has failed its purpose.

---

## IMPLEMENTATION PATH

Phase 2 (Browser SSE):
  - FastAPI /hud endpoint → HTML page with SSE stream
  - Server pushes panel updates via Server-Sent Events
  - CSS grid layout per above spec
  - Keyboard shortcuts: Cmd+C (copy question), Cmd+Q (queue), Cmd+→ (next infographic)

Phase 3 (Native app):
  - SwiftUI on macOS/iOS
  - WebRTC audio channel for push-to-talk
  - Private whisper audio (AirPod left ear only, if supported)
  - Share sheet for infographics
  - Offline receipt review (call timeline after)

---

## ONE-PAGE SUMMARY (shareable)

COMPUTER CALL HUD

5 panels. 1 purpose: keep you in Omega state during live calls.

  HEARD         What Computer registered (2s refresh)
  THEMES        What the call is actually about (30s refresh)
  NEXT QUESTION One Socratic question — highest leverage (10s refresh)
  INFOGRAPHIC   One visual synthesis — auto-selected by call state (60-120s)
  COMMITMENTS   Action items with owners, timestamped, receipted (event-driven)

Rules:
  - ONE question at a time. Not a list.
  - FIVE themes maximum. Not a transcript.
  - Eagle's Wings cues are whispered. Not displayed.
  - Nothing blinks. Nothing demands attention.
  - Everything is receipted. Deterministic replay at any time.

Computer subtracts noise.
You ride the thermal.

---

# END CALL HUD LAYOUT SPEC v1.0
