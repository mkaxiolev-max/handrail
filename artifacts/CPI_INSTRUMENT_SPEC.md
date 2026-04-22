# CPI Instrument Specification — NS∞
## Context + Performance + Intelligence
**Version**: 1.0 | **Generated**: 2026-04-21 | AXIOLEV Holdings LLC © 2026

---

## Overview

CPI is a three-tier observational scoring instrument measuring the live NS∞ model layer (Ollama/llama3:latest via model_router:9002). It complements MASTER v3.1 by directly probing context fidelity, inference performance, and intelligence reliability rather than deriving scores from operational receipts.

---

## Tier A: Context (40 pts)

| Sub-test | Points | Method |
|----------|--------|--------|
| A1 Multi-needle retrieval | 15 | Accuracy across 2/4/8 embedded facts |
| A2 Position bias | 10 | Primacy/middle/recency recall quality |
| A3 MECW (Max Effective Context Window) | 15 | Target-word recall at 500/2000/8000 approx tokens |

**Scoring**: Each sub-test % × weight. A1: accuracy_pct/100 × 15. A2: score_pct/100 × 10. A3: mecw_score_pct/100 × 15.

---

## Tier B: Performance (30 pts)

| Sub-test | Points | Method |
|----------|--------|--------|
| B1 Latency profile | 30 | avg/p50/p95/jitter on 5 cold calls |

**Scoring**: avg_lat ≤ 0.3s → 100%; 0.3–1.0s → linear decay to 50%; >1.0s → 0%. Score × 30.

**UNKNOWN fields**: true TTFT, true TPS, KV cache hit rate, GPU energy — require streaming instrumentation not available via model_router non-streaming endpoint.

---

## Tier C: Intelligence Reliability (30 pts)

| Sub-test | Points | Method |
|----------|--------|--------|
| C1 Calibration (Brier proxy) | 10 | 8 binary questions, confidence extraction, Brier score |
| C2 Faithfulness | 10 | 3 grounded-context QA cases, hallucination detection |
| C3 Abstention discipline | 5 | 3 cases: correct refusal vs correct answer |
| C4 Reasoning density | 5 | Logic word ratio in chain-of-thought response |

**Scoring**: C1: calibration_score_pct/100 × 10. C2: faithfulness_pct/100 × 10. C3: abstention_score_pct/100 × 5. C4: density rubric (≥10%→100%, 5–10%→70%, 2–5%→40%, <2%→20%) × 5.

---

## Tier Bands

| Band | Score | Label |
|------|-------|-------|
| CPI-OMEGA | ≥90 | Elite — production-sovereign |
| CPI-ALPHA | ≥80 | Strong — deployment-ready |
| CPI-BETA | ≥70 | Operational — supervised deployment |
| CPI-GAMMA | <70 | Limited — improvement required |

---

## Instrument-to-AXIOLEV Mapping

| CPI Sub-test | Primary AXIOLEV Signal | Mechanism |
|-------------|----------------------|-----------|
| A1 Multi-needle | I1 (Perception/Lexicon) | Context retrieval precision → semantic fidelity |
| A2 Position bias | I5 (Sovereignty/Memory) | Recency primacy → memory coherence under pressure |
| A3 MECW | I3 (Memory/Coherence) | Effective context window → working memory capacity |
| B1 Latency | I4 (Synthesis/Execution) | Inference speed → execution throughput |
| C1 Calibration | I2 (Reasoning) | Confidence accuracy → epistemic reliability |
| C2 Faithfulness | I1 (Perception) | Grounded retrieval → no hallucination |
| C3 Abstention | I5 (Sovereignty) | Refusal discipline → dignity kernel alignment |
| C4 Reasoning density | I2 (Reasoning) | Chain-of-thought depth → deliberative quality |
