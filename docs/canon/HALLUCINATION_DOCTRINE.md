# HALLUCINATION DOCTRINE

STATUS: DRAFT-FOR-G5 (awaiting YubiKey slot_2 hardware signature)

AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED

## Principle

LLMs never define truth. NER math is pure. force_ground derives from the ledger.

## NER Thresholds

- Default threshold: 3.0 (token emission rate / grounded action / minute)
- Configurable via canon/axioms/ax_core.json `ner_threshold` field
- Rising trend above threshold activates force_ground advisory

## force_ground Triggers

When NER ≥ threshold:
1. Subsequent CPS operations must include explicit ground-truth anchors
2. Accepted anchors: receipt_id, file SHA, endpoint response body
3. Until YK slot_2: advisory only — demand is logged, operation continues
4. With YK slot_2: operator abort available

## Provider Order (_violet_llm)

Groq → Grok → Ollama → Anthropic → OpenAI → canned

- Each provider ≤5s timeout
- Fail to next on timeout or non-200
- canned: static corpus, deterministic hash selection, never fabricates

## Receipt-as-Ground Anchor

Every operation on the grounded path emits a receipt_id (UUID v4).
The receipt is appended to Alexandria (append-only). Rewrite forbidden (AX-3).
NER computation is a pure function of the Alexandria receipt window.

## Hardware Gate

Until YubiKey slot_2 is bound:
- This document remains DRAFT-FOR-G5
- force_ground is advisory
- Hallucination Doctrine is active but not hardware-enforced
