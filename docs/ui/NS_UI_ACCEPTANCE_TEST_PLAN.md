# NS∞ UI — Acceptance Test Plan

**Version:** 1.0 · 2026-04-27  
**Test frameworks:** Vitest (ns_ui), pytest (services), XCTest (Mac app)  
**E2E:** Playwright — NOT YET CONFIGURED (absent)  

---

## 1. Test Categories

| Category | Framework | Status |
|----------|-----------|--------|
| Service unit tests | pytest | 1,760 collected, 0 failed |
| UI contract tests | Vitest | 21 passing |
| XCTest bridge | XCTest + pytest | 9 passing |
| Route existence | Playwright | ABSENT |
| Component rendering | Vitest + jsdom | ABSENT (3 tests exist, contract-only) |
| Endpoint contract | Vitest | PARTIAL (ns_ui/__tests__) |
| Receipt linking | pytest | PARTIAL |
| Accessibility | — | ABSENT |
| E2E / Playwright | — | ABSENT |

---

## 2. Required Tests — Route Existence

These tests must verify that each UI route renders without crashing.

```typescript
// ns_ui/__tests__/routes.test.ts
describe('Route existence', () => {
  const routes = [
    '/home', '/living', '/governance', '/engine',
    '/voice', '/alexandria', '/build', '/timeline',
    '/scoring', '/omega_logos', '/ring5', '/autonomy'
  ];
  
  routes.forEach(route => {
    it(`${route} renders without crashing`, async () => {
      // Fetch route; expect 200; expect no error boundary content
    });
  });

  const absentRoutes = [
    '/aletheia', '/dwm', '/pap', '/prism',
    '/arms', '/noetic', '/ris', '/models', '/drift', '/portfolio'
  ];

  absentRoutes.forEach(route => {
    it(`${route} is ABSENT — returns 404 (expected, tracked in gap matrix)`, async () => {
      // Document absence; this test is informational not a failure condition
    });
  });
});
```

---

## 3. Required Tests — Component Rendering

```typescript
// ns_ui/__tests__/components.test.ts
describe('Core component rendering', () => {
  it('Card renders with children', () => { /* ... */ });
  it('Metric renders label and value', () => { /* ... */ });
  it('Sparkline renders with empty array', () => { /* ... */ });
  it('Sparkline renders with values array', () => { /* ... */ });
  it('FounderSidebar renders all 11 nav items', () => {
    // Assert NAV_ITEMS.length === 11
    // Assert target count === 22 (flag gap)
  });
  it('EpistemicBadge renders 7 classes (ABSENT — must be created)', () => { /* PENDING */ });
});
```

---

## 4. Required Tests — Endpoint Contracts (Vitest)

These tests verify the shape of API responses, not live data. Mock fetch.

```typescript
// ns_ui/__tests__/contracts.test.ts (extend existing)

describe('Summary contract', () => {
  it('organism_health fields are strictly boolean', () => { /* existing */ });
  it('never fabricates healthy when services down', () => { /* existing */ });
  it('priorities non-empty when ns_core offline', () => { /* existing */ });
  
  // NEW:
  it('summary response includes shalom field', () => { /* ... */ });
  it('recent_receipts each have sha256 string', () => { /* ... */ });
});

describe('Scoring contract', () => {
  it('instruments array contains I1 through I8', () => {
    const ids = instruments.map(i => i.id);
    expect(ids).toContain('I7');
    expect(ids).toContain('I8');
  });
  it('v3_1 master score is present and number', () => { /* ... */ });
  it('theoretical_ceiling >= master_v31', () => { /* ... */ });
});

describe('Engine contract', () => {
  it('handrail.is_moat is always true', () => { /* existing */ });
  it('handrail notice contains "Handrail"', () => { /* existing */ });
  
  // NEW:
  it('proof_carriers is array', () => { /* ... */ });
  it('reversibility has reversible_count and irreversible_count', () => { /* ... */ });
});

describe('PAP contract', () => {
  it('mode is shadow|graduated|blocked', () => { /* PENDING */ });
  it('graduation_review_date is ISO-8601', () => { /* PENDING */ });
  it('triadic_floor has wisdom, courage, acceptance', () => { /* PENDING */ });
});

describe('Logos Gate contract', () => {
  it('status is PASS|WARN|BLOCK', () => { /* PENDING */ });
  it('risk_scores has deception, coercion, domination', () => { /* PENDING */ });
  it('BLOCK status triggers constitutional warning', () => { /* PENDING */ });
});

describe('Memory contract', () => {
  it('memory_classes includes receipt, canonical, superseded, unresolved', () => { /* existing */ });
  it('canonical count never exceeds receipt count', () => { /* existing */ });
  
  // NEW:
  it('contradictions_open is integer >= 0', () => { /* PENDING */ });
  it('alexandria_mounted is boolean', () => { /* PENDING */ });
});

describe('DWM contract', () => {
  it('integration_state is valid enum value', () => { /* PENDING */ });
  it('ring_integration has 7 boolean keys', () => { /* PENDING */ });
  it('absent DWM displays "architecture-defined" pill', () => { /* PENDING */ });
});
```

---

## 5. Required Tests — Receipt Linking

```python
# tests/ui/test_receipt_linking.py

def test_logos_gate_receipt_links_to_chain():
    """Every Logos Gate status response must have a valid sha256 in receipt chain."""

def test_pap_receipt_links_to_chain():
    """PAP Ω shadow events must produce chained receipts."""

def test_engine_proof_carriers_link_to_receipts():
    """Each CPS proof carrier must have a receipt_sha256 in Alexandria chain."""

def test_dwm_receipts_link_to_chain():
    """DWM actions must produce receipts. (PENDING — DWM not implemented)"""

def test_no_mocked_production_receipts():
    """No receipt_sha256 value is a known test fixture string in production."""
```

---

## 6. Required Tests — Ring / Instrument Status

```python
# tests/ui/test_ring_status.py

def test_ring_status_grid_returns_7_rings():
    """GET /api/v1/ui/rings returns exactly 7 ring objects."""

def test_ring_status_values_valid():
    """Each ring status is one of OK|WARN|BLOCK."""

def test_instrument_grid_returns_I1_through_I8():
    """Scoring endpoint includes I1, I2, I3, I4, I5, I6, I7, I8."""

def test_I7_score_is_present_and_numeric():
    """I7 score is present and is a float."""

def test_I8_score_is_present_and_numeric():
    """I8 score is present and is a float."""
```

---

## 7. Required Tests — DWM Display

```typescript
// ns_ui/__tests__/dwm.test.ts

describe('DWM Console display', () => {
  it('renders DWMStatePanel with not_implemented state', () => {
    // When integration_state = not_implemented, show grey pill
  });
  it('DWMStatusPill in FounderHome shows absent state correctly', () => { /* PENDING */ });
  it('DWM action EXECUTED displays as OBSERVED_FACT badge', () => { /* PENDING */ });
  it('DWM action BLOCKED displays as BLOCKED_ACTION badge', () => { /* PENDING */ });
  it('DWM action ESCALATED displays as PENDING_REVIEW badge', () => { /* PENDING */ });
});
```

---

## 8. Required Tests — Governance Warning States

```typescript
// ns_ui/__tests__/governance.test.ts

describe('Constitutional warning flow', () => {
  it('LogosGate BLOCK status triggers ConstitutionalWarning overlay', () => { /* PENDING */ });
  it('ConstitutionalWarning overlay blocks interaction with content beneath', () => { /* PENDING */ });
  it('IrreversibleActionConfirm requires 3 steps', () => { /* PENDING */ });
  it('CollapseReadyModal triggers when NCOM threshold exceeded', () => { /* PENDING */ });
});
```

---

## 9. Required Tests — Accessibility

```typescript
// ns_ui/__tests__/accessibility.test.ts

describe('Accessibility', () => {
  it('All status indicators have aria-label', () => { /* PENDING */ });
  it('All interactive elements are keyboard reachable', () => { /* PENDING */ });
  it('Color is not the only differentiator for status', () => { /* PENDING */ });
  it('EpistemicBadge announces class via aria-label', () => { /* PENDING */ });
});
```

---

## 10. Required Tests — Mac App XCTest Integration

```swift
// apps/ns_mac/Tests/NSMacTests/NSMacComponentTests.swift (extend)

func testHabitatModeCoversAllRequired() {
    // Assert HabitatMode.allCases.count >= 9 (currently 6 — need PAP, DWM, Aletheia)
}

func testRingStatusLivePollUpdatesAppState() {
    // Assert AppState.ringStatus is updated from HealthPoller (not static seeds)
}

func testVoiceStateTransitionsValid() {
    // Assert all VoiceState cases have valid color assignments
}
```

```python
# tests/xctest/test_xctest_bridge.py (extend existing)

def test_xctest_bridge_reports_9_tests():
    """XCTest bridge currently reports 9 tests. Confirm count."""

def test_xctest_bridge_habitat_mode_coverage():
    """HabitatMode covers at minimum 6 modes (currently canonical)."""
```

---

## 11. Required Tests — No Mocked Production Data

```python
# tests/ui/test_no_mocked_data.py

def test_scoring_endpoint_not_pure_fallback():
    """When ns services are up, scoring endpoint returns real data not fallback defaults."""

def test_ring5_endpoint_not_pure_fallback():
    """Ring5 endpoint returns real gate statuses when available."""

def test_summary_uses_live_ns_core():
    """Summary organism_health.ns_core.ok reflects actual service state."""
```

---

## 12. Playwright E2E Plan (ABSENT — TO BE CONFIGURED)

```
playwright.config.ts — to be created
baseURL: http://localhost:3001

Tests:
  e2e/home.spec.ts       - Founder Home renders score, shalom, services
  e2e/scoring.spec.ts    - Scoring page shows I1-I8 table
  e2e/engine.spec.ts     - Engine room SSE connects and shows events
  e2e/governance.spec.ts - Governance page shows ring5 gate count
  e2e/receipt.spec.ts    - Click SHA-256 opens ReceiptDrawer
```

**Setup command (to be added):**
```bash
cd ns_ui && npx playwright install
cd ns_ui && npx playwright test
```
