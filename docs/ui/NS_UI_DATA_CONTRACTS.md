# NS∞ UI — Data Contracts

**Version:** 1.0 · 2026-04-27  
**Backend base:** `http://localhost:9011` (ns_api)  
**NS Core base:** `http://localhost:9000`  
**Handrail base:** `http://localhost:8011`  

All endpoints should return `Content-Type: application/json`.  
Receipt links are SHA-256 hex strings referencing the Alexandria receipt chain.  
All timestamps are ISO-8601 UTC.

---

## 1. Founder Home — Summary

```json
{
  "surface": "FounderHome",
  "widget": "Summary",
  "endpoint": "/api/v1/ui/summary",
  "method": "GET",
  "polling_interval_ms": 15000,
  "response": {
    "organism_health": {
      "ns_core": { "ok": "boolean", "shalom": "boolean" },
      "handrail": { "ok": "boolean" },
      "continuum": { "ok": "boolean", "tier": "integer|null" },
      "omega": { "ok": "boolean" },
      "alexandria_mounted": "boolean"
    },
    "invariants": { "total": "integer", "enforced": "integer" },
    "services": { "total": "integer", "healthy": "integer" },
    "priorities": [
      { "rank": "integer", "label": "string", "urgency": "critical|high|medium|low" }
    ],
    "open_loops": [
      { "id": "string", "description": "string", "since": "ISO-8601" }
    ],
    "recent_receipts": [
      { "receipt_id": "string", "sha256": "string", "type": "string", "timestamp": "ISO-8601" }
    ],
    "shalom": "boolean",
    "captured_at": "ISO-8601"
  },
  "error_state": { "all_fields_false_or_null": true, "priorities": ["{ urgency: critical, label: API unreachable }"] },
  "tests": ["unit:summary-contract", "contract:no-fabrication", "integration:shalom-indicator"]
}
```

---

## 2. Scoring

```json
{
  "surface": "Scoring",
  "widget": "MasterScorePanel",
  "endpoint": "/api/v1/ui/scoring",
  "method": "GET",
  "polling_interval_ms": 60000,
  "response": {
    "v2_1": { "master": "number", "instruments": "array" },
    "v3_0": { "master": "number", "instruments": "array", "history": "number[]" },
    "v3_1": { "master": "number", "authoritative": true },
    "instruments": [
      {
        "id": "string (I1-I8)",
        "name": "string",
        "score": "number",
        "weight_v21": "number",
        "weight_v30": "number",
        "weight_v31": "number",
        "receipt_sha256": "string|null",
        "last_evaluated": "ISO-8601|null"
      }
    ],
    "theoretical_ceiling": "number",
    "deltas_to_99": { "I1": "number", "I2": "number", "I3": "number", "I4": "number", "I5": "number", "I6": "number", "I7": "number", "I8": "number" }
  },
  "tests": ["contract:scoring-instruments-I1-I8", "unit:I7-present", "unit:I8-present", "integration:v31-score"]
}
```

---

## 3. Logos Gate Status

```json
{
  "surface": "Governance",
  "widget": "LogosGateStatus",
  "endpoint": "/api/v1/aletheion/logos/status",
  "method": "GET",
  "polling_interval_ms": 10000,
  "response": {
    "status": "PASS|WARN|BLOCK",
    "last_receipt_sha256": "string",
    "risk_scores": {
      "deception": "number (0-1)",
      "coercion": "number (0-1)",
      "domination": "number (0-1)"
    },
    "updated_at": "ISO-8601"
  },
  "error_state": { "status": "WARN", "risk_scores": "null" },
  "tests": ["unit:logos-gate-display", "contract:logos-api", "integration:logos-gate-block-triggers-constitutional-warning", "receipt-link:logos"]
}
```

---

## 4. PAP Ω Status

```json
{
  "surface": "PAP",
  "widget": "PAPPanel",
  "endpoint": "/api/v1/pap/status",
  "method": "GET",
  "polling_interval_ms": 30000,
  "response": {
    "mode": "shadow|graduated|blocked",
    "shadow_metrics": {
      "triadic_floor": { "wisdom": "number", "courage": "number", "acceptance": "number" },
      "floor_passed": "boolean",
      "shadow_score": "number"
    },
    "graduation_review_date": "ISO-8601",
    "graduation_ready": "boolean",
    "last_receipt_sha256": "string",
    "updated_at": "ISO-8601"
  },
  "tests": ["contract:pap-status-api", "integration:pap-shadow-display", "unit:graduation-countdown", "receipt-link:pap"]
}
```

---

## 5. Aletheia-Control Ω / C25

```json
{
  "surface": "Aletheia",
  "widget": "AletheiaControlPanel",
  "endpoint": "/api/v1/aletheia_control/status",
  "method": "GET",
  "polling_interval_ms": 30000,
  "response": {
    "omega_score": "number",
    "c25": {
      "composite": "number",
      "questions": [
        { "id": "string", "text": "string", "status": "resolved|open|blocked", "score": "number|null" }
      ],
      "golden_corpus_size": "integer"
    },
    "classifiers": {
      "control_influence_concern_mixed": { "control": "number", "influence": "number", "concern": "number", "mixed": "number" },
      "concern_waste_route": "string"
    },
    "triadic": { "wisdom": "number", "courage": "number", "acceptance": "number" },
    "last_receipt_sha256": "string",
    "updated_at": "ISO-8601"
  },
  "tests": ["contract:c25-api", "integration:c25-display", "receipt-link:aletheia"]
}
```

---

## 6. DWM Status

```json
{
  "surface": "DWM",
  "widget": "DWMConsole",
  "endpoint": "/api/v1/dwm/status",
  "method": "GET",
  "polling_interval_ms": 10000,
  "response": {
    "integration_state": "not_implemented|initializing|active|degraded",
    "ring_integration": {
      "ring1": "boolean", "ring2": "boolean", "ring3": "boolean",
      "ring4": "boolean", "ring5": "boolean", "ring6": "boolean", "ring7": "boolean"
    },
    "inputs_received": "integer",
    "outputs_generated": "integer",
    "recent_log": [
      { "ts": "ISO-8601", "type": "string", "summary": "string" }
    ],
    "score_impact": "number",
    "gaps": ["string"],
    "last_receipt_sha256": "string|null",
    "updated_at": "ISO-8601"
  },
  "notes": "This endpoint does not exist yet. Architecture-defined. Returns integration_state: not_implemented until DWM service is built.",
  "tests": ["unit:dwm-display-absent-state", "contract:dwm-api", "integration:dwm-ring-map", "receipt-link:dwm"]
}
```

---

## 7. PRISM-Ω

```json
{
  "surface": "PRISM",
  "widget": "PRISMOmegaPanel",
  "endpoint": "/api/v1/prism/status",
  "method": "GET",
  "polling_interval_ms": 30000,
  "response": {
    "composite_score": "number",
    "axes": [
      { "id": "string", "name": "string", "score": "number", "weight": "number" }
    ],
    "last_synthesis": "ISO-8601",
    "synthesis_log": [
      { "ts": "ISO-8601", "input_count": "integer", "output_score": "number" }
    ],
    "last_receipt_sha256": "string",
    "updated_at": "ISO-8601"
  },
  "tests": ["contract:prism-api", "integration:prism-display"]
}
```

---

## 8. Engine Live (existing + extended)

```json
{
  "surface": "EngineRoom",
  "widget": "EngineRoomPage",
  "endpoint": "/api/v1/engine/live",
  "sse_endpoint": "/api/v1/engine/live/stream",
  "method": "GET",
  "polling_interval_ms": 8000,
  "response": {
    "layers": [
      { "id": "string", "name": "string", "status": "active|idle|blocked", "shalom": "boolean" }
    ],
    "cognition": { "active_model": "string", "decisions": "integer" },
    "adjudication": { "queue_depth": "integer", "last_op": "string" },
    "handrail": {
      "ok": "boolean",
      "is_moat": true,
      "notice": "All real-world actions dispatch through Handrail. No UI surface bypasses this boundary.",
      "queue_depth": "integer"
    },
    "proof_carriers": [
      { "id": "string", "action": "string", "status": "pending|proven|failed", "receipt_sha256": "string|null" }
    ],
    "reversibility": { "reversible_count": "integer", "irreversible_count": "integer" },
    "ts": "ISO-8601"
  },
  "contract_invariants": ["handrail.is_moat must always be true"],
  "tests": ["contract:handrail-is-moat", "integration:engine-sse", "unit:proof-carrier-display"]
}
```

---

## 9. RIS Sources

```json
{
  "surface": "RIS",
  "widget": "RISSourceGrid",
  "endpoint": "/api/v1/ris/sources",
  "method": "GET",
  "polling_interval_ms": 60000,
  "response": {
    "sources": [
      {
        "id": "string",
        "name": "string",
        "type": "USPTO|SEC|news|technical|regulatory|standards",
        "status": "active|paused|error",
        "credibility_score": "number (0-1)",
        "last_ingest": "ISO-8601",
        "ingest_count": "integer"
      }
    ],
    "queue_depth": "integer",
    "updated_at": "ISO-8601"
  },
  "tests": ["contract:ris-sources-api", "integration:ris-display"]
}
```

---

## 10. Model Router Registry

```json
{
  "surface": "Models",
  "widget": "LocalModelRegistry",
  "endpoint": "/api/v1/models/registry",
  "method": "GET",
  "polling_interval_ms": 120000,
  "response": {
    "local_models": [
      {
        "id": "string",
        "name": "string",
        "status": "loaded|unloaded|error",
        "context_window": "integer",
        "eval_score": "number|null",
        "last_used": "ISO-8601|null"
      }
    ],
    "cloud_models": [
      {
        "provider": "string",
        "model_id": "string",
        "routing_enabled": "boolean",
        "privacy_level": "local_only|hybrid|cloud_ok"
      }
    ],
    "current_routing_policy": "string",
    "privacy_budget": { "remaining_tokens_cloud": "integer", "period": "string" },
    "updated_at": "ISO-8601"
  },
  "tests": ["contract:model-registry-api"]
}
```

---

## 11. Alexandria Memory

```json
{
  "surface": "Alexandria",
  "widget": "AlexandriaLedger",
  "endpoint": "/api/v1/ui/memory",
  "method": "GET",
  "polling_interval_ms": 30000,
  "response": {
    "alexandria_mounted": "boolean",
    "chain_valid": "boolean",
    "latest_receipt_sha256": "string|null",
    "memory_classes": [
      { "class": "receipt|canonical|superseded|unresolved", "count": "integer", "description": "string" }
    ],
    "atoms_total": "integer",
    "contradictions_open": "integer",
    "corpus_ingestion": { "active_jobs": "integer", "last_completed": "ISO-8601|null" },
    "updated_at": "ISO-8601"
  },
  "contract_invariants": [
    "memory_classes must include receipt, canonical, superseded, unresolved",
    "canonical count must never exceed receipt count"
  ],
  "tests": ["contract:memory-classes", "unit:canonical-le-receipt", "integration:alexandria-chain"]
}
```

---

## 12. Ring Status

```json
{
  "surface": "Organism",
  "widget": "RingStatusGrid",
  "endpoint": "/api/v1/ui/rings",
  "method": "GET",
  "polling_interval_ms": 15000,
  "response": {
    "rings": [
      {
        "ring": "integer (1-7)",
        "name": "string",
        "status": "OK|WARN|BLOCK",
        "description": "string",
        "instruments": ["I1", "I2"],
        "last_receipt_sha256": "string|null",
        "updated_at": "ISO-8601"
      }
    ]
  },
  "notes": "This endpoint does not yet exist. Currently ns_ui home page derives ring status implicitly from summary.",
  "tests": ["contract:rings-api", "integration:ring-status-grid", "unit:ring-7-count"]
}
```

---

## Polling / Subscription Model Summary

| Endpoint | Strategy | Interval |
|----------|----------|----------|
| `/api/v1/ui/summary` | Polling | 15s |
| `/api/v1/engine/live` | Polling + SSE | 8s / SSE |
| `/api/v1/engine/live/stream` | SSE | push |
| `/api/v1/ui/scoring` | Polling | 60s |
| `/api/v1/ui/governance` | Polling | 20s |
| `/api/v1/aletheion/logos/status` | Polling | 10s |
| `/api/v1/pap/status` | Polling | 30s |
| `/api/v1/aletheia_control/status` | Polling | 30s |
| `/api/v1/dwm/status` | Polling | 10s |
| `/api/v1/prism/status` | Polling | 30s |
| `/api/v1/ris/sources` | Polling | 60s |
| `/api/v1/models/registry` | Polling | 120s |
| `/api/v1/ui/memory` | Polling | 30s |
| `/api/v1/ui/rings` | Polling | 15s |
