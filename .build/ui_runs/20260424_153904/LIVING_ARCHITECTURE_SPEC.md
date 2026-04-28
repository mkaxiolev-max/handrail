# NS∞ Living Architecture — Canonical UI Spec (ground truth)

The running NSInfinityApp must render every element below with exact design tokens.
Anything missing or drifting = GAP. No placeholder labels allowed.

## Design tokens (EXACT hex — no approximations)

| role      | hex      |
|-----------|----------|
| founder   | #FF6B00  |
| violet    | #00D4FF  |
| chambers  | #6B00FF  |
| adj       | #00FF88  |
| handrail  | #00FFFF  |
| alex      | #FFFF00  |
| kernel    | #FF3333  |
| build     | #4A6FA5  |
| bg        | #0A0E27  |

## Required scene: 3-pane + HUD + overlay + timeline

### 1. Top HUD (fixed strip, top)
- "NS∞" wordmark (left)
- "Docker 11/11" status pill
- "Invariants 8/10" pill
- "Ring 5 0/5" warn-state pill
- "YubiKey 26116460" label
- "Shalom ✓" green badge

### 2. Voice Overlay Pill (top-right, floats above every view)
- Text: "Violet · ready"
- Pulsing dot (voice-membrane animation)
- Color: violet token

### 3. Left Rail (fixed ≈ 200 pt)
- Six modes, in order, tappable, active highlighted:
    1. Living Architecture   (default active)
    2. Engine Room
    3. Programs Runtime
    4. Memory
    5. Governance
    6. Build Space
- Seven live-services status list (green dot when live)
- Founder identity card at bottom (founder token)

### 4. Center Canvas — Organism Map (fills center)
- Violet node at center, glowing (violet token, radial glow)
- Five chambers arrayed around Violet (chambers token):
    Forge, Institute, Board, Omega, Registry
- Adjudication node (adj token) between chambers and handrail
- Handrail band/ring (handrail token)
- Programs node + Alexandria node (alex token for Alexandria)
- Animated autopoietic flow lines between nodes
- Privacy membrane: translucent ring around Violet
- Constitutional boundary: dashed ellipse enclosing chambers + Adj + Handrail
- Dignity Kernel band (kernel token) INSIDE the boundary
- YubiKey band INSIDE the boundary
- Build Space label/area OUTSIDE the boundary (build token)
- Founder node (founder token) feeding into Violet

### 5. Right Panel (fixed ≈ 320 pt)
- Violet identity card (top)
- Live chamber scores:
    Institute 7.6
    Board 5.15
    Forge 4.9
- "10/10 proofs + Shalom" block
- Ring 5 gates: 5 rows, all red
- Alexandria counts block (edges, atoms, receipts)

### 6. Bottom Timeline (fixed ≈ 120 pt)
- Rolling receipts stream (right-to-left scroll)
- Rows color-coded by layer (token colors)
- Row types visible: receipt, adjudication, atom_write, invariant_check

## Hard invariants (non-negotiable)
- Background = bg token (#0A0E27) across all views.
- All six left-rail modes must be reachable; tapping routes the center canvas.
- VoiceOverlayPill renders above every view.
- No "TODO", "Sample", "Lorem ipsum", "Placeholder" strings anywhere visible.
- Dignity Kernel visual INSIDE the constitutional boundary.
- Build Space visual OUTSIDE the boundary.
- Design tokens referenced by name, not hardcoded hex, wherever feasible.
