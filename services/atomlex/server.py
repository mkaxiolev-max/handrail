"""
Atomlex v4.0 — Constraint Semantic Graph Engine
================================================
12 canonical root nodes. ACPT drift scoring. 10-dimensional semantic vectors.
Constraint propagation: parent → child inheritance.

Port 8080. Docker microservice.

ACPT = Axiological Constraint Propagation Theory
  Drift levels:
    0.00–0.20  NOMINAL    — canonical alignment
    0.20–0.40  MILD       — slight contextual drift
    0.40–0.60  MODERATE   — semantic tension detected
    0.60–0.80  SIGNIFICANT — constraint violation risk
    0.80–1.00  CRITICAL   — constitutional misalignment
"""

import math
import re
from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Atomlex v4.0", version="4.0.0")

# ── Vector dimensions ──────────────────────────────────────────────────────────
# [authority, dignity, truth, constraint, logos, shalom, permission, evidence, governance, action]
VECTOR_DIMS = ["authority", "dignity", "truth", "constraint",
               "logos", "shalom", "permission", "evidence", "governance", "action"]

# ── 12 Canonical Root Nodes ────────────────────────────────────────────────────

_NODES_RAW = {
    "logos": {
        "tier": 5, "engine_component": "logos_engine",
        "etymology": "*leg- 'to collect into structure' — the gathering principle",
        "description": "The principle that gathers all constitutional organs into a coherent whole.",
        "vector": [0.9, 0.7, 0.8, 0.6, 1.0, 0.9, 0.5, 0.8, 0.7, 0.6],
        "parents": [], "children": ["constraint", "truth", "evidence", "authority", "shalom"],
        "acpt_drift_base": 0.00,
    },
    "shalom": {
        "tier": 5, "engine_component": "dignity_engine",
        "etymology": "*sol- 'whole, uninjured' — nothing missing, nothing broken",
        "description": "The target state: every system organ whole, every constitutional covenant honored.",
        "vector": [0.6, 0.9, 0.8, 0.3, 0.8, 1.0, 0.7, 0.6, 0.6, 0.5],
        "parents": ["logos"], "children": ["dignity", "covenant"],
        "acpt_drift_base": 0.00,
    },
    "dignity": {
        "tier": 2, "engine_component": "dignity_engine",
        "etymology": "*dek- 'to take, accept' — inherent worth that cannot be negotiated away",
        "description": "The never-event axiom. No operation may diminish the inherent worth of a person.",
        "vector": [0.4, 1.0, 0.7, 0.2, 0.6, 0.8, 0.8, 0.5, 0.4, 0.3],
        "parents": ["shalom", "logos"], "children": ["responsibility"],
        "acpt_drift_base": 0.05,
    },
    "authority": {
        "tier": 3, "engine_component": "governance_engine",
        "etymology": "*aug- 'to increase, originate' — legitimate power to originate action",
        "description": "Delegated power operating within constitutional constraint. Authority without constraint is violence.",
        "vector": [1.0, 0.5, 0.7, 0.6, 0.7, 0.5, 0.7, 0.5, 0.9, 0.7],
        "parents": ["logos"], "children": ["law", "allow", "deny"],
        "acpt_drift_base": 0.08,
    },
    "truth": {
        "tier": 2, "engine_component": "epistemic_engine",
        "etymology": "*deru- 'firm, solid' — correspondence to what actually is",
        "description": "The epistemic ground condition. All system beliefs must be defensible against evidence.",
        "vector": [0.5, 0.6, 1.0, 0.3, 0.7, 0.7, 0.4, 0.9, 0.4, 0.3],
        "parents": ["logos", "evidence"], "children": [],
        "acpt_drift_base": 0.05,
    },
    "constraint": {
        "tier": 3, "engine_component": "constraint_engine",
        "etymology": "*streig- 'to bind tight' — the limiting force that makes freedom real",
        "description": "Constitutional constraints are not restrictions on freedom — they are what makes action meaningful.",
        "vector": [0.6, 0.3, 0.5, 1.0, 0.6, 0.4, 0.3, 0.4, 0.7, 0.5],
        "parents": ["logos", "law"], "children": ["deny"],
        "acpt_drift_base": 0.10,
    },
    "allow": {
        "tier": 1, "engine_component": "permission_engine",
        "etymology": "*loubh- 'to care, desire' — authorized action",
        "description": "Permission granted by authority operating within constitutional constraint.",
        "vector": [0.7, 0.6, 0.5, 0.2, 0.5, 0.6, 1.0, 0.4, 0.6, 0.8],
        "parents": ["authority", "law", "responsibility"], "children": [],
        "acpt_drift_base": 0.12,
    },
    "deny": {
        "tier": 1, "engine_component": "permission_engine",
        "etymology": "*ne + *dhe- 'to not place/set' — constitutional prohibition",
        "description": "Prohibition derived from constraint. The deny gate protects dignity and constitutional order.",
        "vector": [0.7, 0.4, 0.5, 0.8, 0.5, 0.3, 0.0, 0.5, 0.7, 0.6],
        "parents": ["authority", "law", "constraint", "responsibility"], "children": [],
        "acpt_drift_base": 0.12,
    },
    "evidence": {
        "tier": 2, "engine_component": "epistemic_engine",
        "etymology": "*weid- 'to see' — what can be observed and verified",
        "description": "The ground substance of truth claims. All sovereign assertions require evidence.",
        "vector": [0.4, 0.5, 0.9, 0.4, 0.7, 0.6, 0.4, 1.0, 0.4, 0.4],
        "parents": ["logos"], "children": ["truth"],
        "acpt_drift_base": 0.08,
    },
    "covenant": {
        "tier": 4, "engine_component": "governance_engine",
        "etymology": "*gwem- 'to come' + *wenH- 'to strive' — a binding mutual commitment that constitutes a people",
        "description": "The constitutional bond. Covenants precede law — they are the ground of legitimate authority.",
        "vector": [0.7, 0.8, 0.7, 0.3, 0.8, 0.8, 0.6, 0.7, 0.8, 0.5],
        "parents": ["logos", "shalom"], "children": ["responsibility", "evidence"],
        "acpt_drift_base": 0.05,
    },
    "law": {
        "tier": 3, "engine_component": "governance_engine",
        "etymology": "*legh- 'to lie, be placed' — codified rule that has been placed and remains",
        "description": "Formal constraint codified from covenant and authority. Law derives legitimacy from covenant.",
        "vector": [0.8, 0.5, 0.7, 0.8, 0.7, 0.5, 0.6, 0.5, 0.9, 0.6],
        "parents": ["authority", "logos"], "children": ["constraint", "allow", "deny"],
        "acpt_drift_base": 0.10,
    },
    "responsibility": {
        "tier": 4, "engine_component": "governance_engine",
        "etymology": "*spend- 'to make an offering, perform a rite' — the duty to respond and account",
        "description": "The constitutional duty that binds authority to dignity. No authority without accountability.",
        "vector": [0.6, 0.8, 0.7, 0.4, 0.7, 0.7, 0.7, 0.6, 0.7, 0.7],
        "parents": ["dignity", "covenant"], "children": ["allow", "deny"],
        "acpt_drift_base": 0.08,
    },
}

# Build full graph with back-references
GRAPH: Dict[str, dict] = {}
for word, raw in _NODES_RAW.items():
    GRAPH[word] = {
        "word": word,
        "tier": raw["tier"],
        "engine_component": raw["engine_component"],
        "etymology": raw["etymology"],
        "description": raw["description"],
        "vector": raw["vector"],
        "parents": raw["parents"],
        "children": raw["children"],
        "status": "canonical_root",
        "acpt_drift": raw["acpt_drift_base"],
        "acpt_level": _acpt_level(raw["acpt_drift_base"]) if False else "NOMINAL",
    }
# Fix acpt_level after _acpt_level is defined below

CANONICAL_ROOTS = list(_NODES_RAW.keys())


def _acpt_level(score: float) -> str:
    if score < 0.20: return "NOMINAL"
    if score < 0.40: return "MILD"
    if score < 0.60: return "MODERATE"
    if score < 0.80: return "SIGNIFICANT"
    return "CRITICAL"


# Patch acpt_level now that helper is defined
for word in GRAPH:
    GRAPH[word]["acpt_level"] = _acpt_level(GRAPH[word]["acpt_drift"])


def _cosine_sim(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return round(dot / (na * nb), 4)


def _propagate_to_roots(word: str) -> List[str]:
    """BFS up the parent chain to canonical roots."""
    visited = []
    queue = [word]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.append(current)
        node = GRAPH.get(current)
        if node:
            queue.extend(node.get("parents", []))
    return visited


def _compute_drift(word: str) -> float:
    """Drift = weighted distance from the deepest canonical root in propagation path."""
    node = GRAPH.get(word)
    if not node:
        return 0.50  # unknown word → moderate drift
    chain = _propagate_to_roots(word)
    depth = len(chain) - 1  # 0 = root, deeper = more drift
    base = node["acpt_drift"]
    return round(min(base + depth * 0.04, 0.99), 4)


def _edge_count() -> int:
    return sum(len(n["children"]) for n in GRAPH.values())


def _node_with_propagation(word: str) -> Optional[dict]:
    node = GRAPH.get(word)
    if not node:
        return None
    drift = _compute_drift(word)
    chain = _propagate_to_roots(word)
    return {
        **node,
        "acpt_drift":  drift,
        "acpt_level":  _acpt_level(drift),
        "root_chain":  chain,
        "depth":       len(chain) - 1,
        "propagated_constraints": [
            GRAPH[p]["description"][:80]
            for p in node["parents"]
            if p in GRAPH
        ],
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/healthz")
def healthz():
    return JSONResponse({
        "status": "ok",
        "healthy": True,
        "service": "atomlex",
        "version": "4.0.0",
        "nodes": len(GRAPH),
        "edges": _edge_count(),
    })


@app.get("/graph/status")
def graph_status():
    tier_dist = {}
    component_dist = {}
    for n in GRAPH.values():
        t = str(n["tier"])
        tier_dist[t] = tier_dist.get(t, 0) + 1
        c = n["engine_component"]
        component_dist[c] = component_dist.get(c, 0) + 1

    return JSONResponse({
        "node_count":     len(GRAPH),
        "edge_count":     _edge_count(),
        "canonical_roots": len(CANONICAL_ROOTS),
        "tiers":          tier_dist,
        "components":     component_dist,
        "root_words":     CANONICAL_ROOTS,
    })


@app.get("/words")
def words():
    return JSONResponse({
        "words": [
            {"word": n["word"], "tier": n["tier"],
             "engine_component": n["engine_component"],
             "acpt_drift": n["acpt_drift"],
             "acpt_level": n["acpt_level"]}
            for n in sorted(GRAPH.values(), key=lambda x: (-x["tier"], x["word"]))
        ],
        "total": len(GRAPH),
    })


@app.get("/word/{word}")
def word_detail(word: str):
    node = _node_with_propagation(word.lower())
    if not node:
        return JSONResponse({"ok": False, "error": f"word '{word}' not in Atomlex graph"}, status_code=404)
    return JSONResponse({"ok": True, **node})


@app.get("/propagate/{word}")
def propagate(word: str):
    if word.lower() not in GRAPH:
        return JSONResponse({"ok": False, "error": f"word '{word}' not in graph"}, status_code=404)
    chain = _propagate_to_roots(word.lower())
    chain_with_tiers = [
        {"word": w, "tier": GRAPH[w]["tier"], "engine_component": GRAPH[w]["engine_component"]}
        for w in chain if w in GRAPH
    ]
    return JSONResponse({
        "ok":    True,
        "word":  word,
        "chain": chain_with_tiers,
        "root":  chain[-1] if chain else word,
        "depth": len(chain) - 1,
    })


@app.get("/drift/{word}")
def drift(word: str):
    w = word.lower()
    node = GRAPH.get(w)
    if not node:
        score = 0.50
        level = "MODERATE"
        note  = "unknown word — estimated drift"
    else:
        score = _compute_drift(w)
        level = _acpt_level(score)
        note  = "canonical root node" if score < 0.05 else "drift computed from propagation depth"
    return JSONResponse({
        "word":       word,
        "acpt_drift": score,
        "acpt_level": level,
        "note":       note,
        "risk":       level in ("SIGNIFICANT", "CRITICAL"),
    })


@app.get("/analyze")
def analyze(text: str = ""):
    words_found   = []
    tiers_present = set()
    max_tier      = 0
    drift_scores  = []

    tokens = re.split(r"\W+", text.lower())
    for token in tokens:
        if token in GRAPH:
            n = GRAPH[token]
            d = _compute_drift(token)
            words_found.append({
                "word":       token,
                "tier":       n["tier"],
                "component":  n["engine_component"],
                "acpt_drift": d,
                "acpt_level": _acpt_level(d),
            })
            tiers_present.add(n["tier"])
            max_tier = max(max_tier, n["tier"])
            drift_scores.append(d)

    is_constitutional = max_tier >= 4 or len(words_found) >= 3
    avg_drift = round(sum(drift_scores) / len(drift_scores), 4) if drift_scores else None
    dominant  = max(
        {w["component"] for w in words_found} or {"unknown"},
        key=lambda c: sum(1 for w in words_found if w["component"] == c),
    ) if words_found else None

    return JSONResponse({
        "text":                     text[:200],
        "word_count":               len(words_found),
        "words_found":              words_found,
        "tiers_present":            sorted(tiers_present),
        "max_tier":                 max_tier,
        "dominant_component":       dominant,
        "is_constitutional_intent": is_constitutional,
        "avg_acpt_drift":           avg_drift,
    })


@app.get("/similarity")
def similarity(word1: str = "", word2: str = ""):
    n1 = GRAPH.get(word1.lower())
    n2 = GRAPH.get(word2.lower())
    if not n1:
        return JSONResponse({"ok": False, "error": f"'{word1}' not in graph"}, status_code=404)
    if not n2:
        return JSONResponse({"ok": False, "error": f"'{word2}' not in graph"}, status_code=404)
    sim = _cosine_sim(n1["vector"], n2["vector"])
    return JSONResponse({
        "ok":         True,
        "word1":      word1,
        "word2":      word2,
        "similarity": sim,
        "aligned":    sim > 0.90,
        "note":       "cosine similarity over 10-dim semantic vector",
    })
