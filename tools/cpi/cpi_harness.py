"""CPI Instrument Harness — Context + Performance + Intelligence.
Runs against NS∞ services (model_router/ollama + violet/chat).
Measures only what can be directly observed. Marks UNKNOWN otherwise.
AXIOLEV Holdings LLC © 2026.
"""
from __future__ import annotations
import json, time, statistics, urllib.request, urllib.error
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple

MODEL_ROUTER = "http://127.0.0.1:9002"
NS_CORE     = "http://127.0.0.1:9000"
PROVIDER    = "ollama"
MODEL       = "llama3:latest"
TIMEOUT     = 30

# ── HTTP helper ───────────────────────────────────────────────────────────────

def call(url: str, body: dict, timeout: int = TIMEOUT) -> Tuple[dict, float]:
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    return resp, time.perf_counter() - t0

def complete(prompt: str, max_tokens: int = 200, system: str = "") -> Tuple[str, float]:
    body: dict = {"prompt": prompt, "provider": PROVIDER, "model": MODEL,
                  "max_tokens": max_tokens}
    if system:
        body["system"] = system
    resp, lat = call(f"{MODEL_ROUTER}/complete", body)
    text = resp.get("text", "")
    return text, lat

# ── TIER A: CONTEXT ───────────────────────────────────────────────────────────

NEEDLE_FACTS = [
    ("ALPHA_COLOR",     "The security code color is VERMILLION."),
    ("BETA_NUMBER",     "The activation sequence number is 7734."),
    ("GAMMA_NAME",      "The protocol operator is named SOLARIS."),
    ("DELTA_DATE",      "The deployment timestamp is 2026-03-14T09:00:00Z."),
    ("EPSILON_PHRASE",  "The authentication passphrase is IRON-BRIDGE-NINE."),
    ("ZETA_LOCATION",   "The primary relay is located at GRID-COORDINATE-47N-122W."),
    ("ETA_VERSION",     "The firmware version string is NS-CORE-v9.7.2-stable."),
    ("THETA_KEY",       "The signing key prefix is AXVK-2026-DELTA."),
]

def _needle_prompt(n: int, query_idx: int, position: str = "distributed") -> str:
    facts = NEEDLE_FACTS[:n]
    if position == "primacy":
        # Query fact at position 0
        query_idx = 0
    elif position == "recency":
        # Query fact at last position
        query_idx = n - 1
    elif position == "middle":
        query_idx = n // 2

    lines = [f"FACT {i+1}: {f[1]}" for i, f in enumerate(facts)]
    key, fact = facts[query_idx]

    if position == "distributed":
        context = "\n".join(lines)
    else:
        context = "\n".join(lines)

    prompt = (
        f"Read the following facts carefully:\n{context}\n\n"
        f"Question: According to the facts above, what is the value of {key.replace('_',' ').lower()}? "
        f"Reply with ONLY the exact value, nothing else."
    )
    return prompt, key, fact

def run_multi_needle() -> dict:
    """Test retrieval accuracy for 2, 4, 8 embedded facts."""
    results = []
    for n in [2, 4, 8]:
        for query_idx in range(min(n, 3)):  # Test first 3 positions
            prompt, key, fact = _needle_prompt(n, query_idx)
            # Extract the expected value from the fact string
            expected_value = fact.split("is ")[-1].rstrip(".")
            try:
                text, lat = complete(prompt, max_tokens=30)
                text = text.strip()
                hit = expected_value.lower() in text.lower() or text.lower() in expected_value.lower()
                results.append({"n_needles": n, "query_idx": query_idx, "hit": hit,
                                 "expected": expected_value, "got": text[:80], "lat_s": round(lat, 3)})
            except Exception as e:
                results.append({"n_needles": n, "query_idx": query_idx, "hit": False,
                                 "error": str(e)[:60], "lat_s": None})

    # Accuracy by n_needles
    curve = {}
    for n in [2, 4, 8]:
        n_results = [r for r in results if r["n_needles"] == n]
        hits = sum(1 for r in n_results if r.get("hit", False))
        curve[n] = round(hits / len(n_results) * 100, 1) if n_results else None

    overall = [r for r in results if r.get("hit") is not None]
    overall_acc = round(sum(1 for r in overall if r["hit"]) / len(overall) * 100, 1) if overall else 0

    return {
        "raw": results,
        "accuracy_by_needles": curve,
        "overall_accuracy_pct": overall_acc,
        "n_tests": len(results),
    }

def run_position_bias() -> dict:
    """Test primacy/middle/recency recall with 6 facts."""
    positions = ["primacy", "middle", "recency"]
    results = []
    for pos in positions:
        prompt, key, fact = _needle_prompt(6, 0, position=pos)
        expected_value = fact.split("is ")[-1].rstrip(".")
        try:
            text, lat = complete(prompt, max_tokens=30)
            text = text.strip()
            hit = expected_value.lower() in text.lower() or text.lower() in expected_value.lower()
            results.append({"position": pos, "hit": hit, "expected": expected_value,
                             "got": text[:80], "lat_s": round(lat, 3)})
        except Exception as e:
            results.append({"position": pos, "hit": False, "error": str(e)[:60]})

    profile = {r["position"]: r.get("hit", False) for r in results}
    hits = [r.get("hit", False) for r in results]
    score = round(sum(hits) / len(hits) * 100, 1) if hits else 0
    return {"raw": results, "profile": profile, "score_pct": score}

def run_mecw() -> dict:
    """Test accuracy vs context length at 3 sizes. Mark beyond 4 facts as untested if slow."""
    # Build contexts of increasing size by repeating distractor text + 1 needle
    sizes = [500, 2000, 8000]  # approximate token equivalents (4 chars ≈ 1 token)
    needle_fact = "The master secret is AXIOLEV-SIGMA-7."
    needle_q    = "What is the master secret?"
    needle_ans  = "AXIOLEV-SIGMA-7"

    results = []
    for target_tokens in sizes:
        filler_chars = max(0, target_tokens * 4 - 200)
        filler = ("The following is operational background data. " * 50)[:filler_chars]
        context = f"{filler}\n\nIMPORTANT FACT: {needle_fact}"
        prompt  = f"{context}\n\nQuestion: {needle_q} Reply with only the exact value."
        try:
            text, lat = complete(prompt, max_tokens=30)
            hit = needle_ans.lower() in text.lower()
            results.append({"target_tokens": target_tokens,
                             "approx_chars": len(prompt),
                             "hit": hit, "got": text[:80],
                             "lat_s": round(lat, 3)})
        except Exception as e:
            results.append({"target_tokens": target_tokens, "hit": False,
                             "error": str(e)[:60]})

    hits = [r.get("hit", False) for r in results]
    mecw_threshold = None
    for r in results:
        if r.get("hit"):
            mecw_threshold = r["target_tokens"]

    # MECW score: % of tested sizes where needle was found
    mecw_score = round(sum(hits) / len(hits) * 100, 1) if hits else 0
    return {
        "raw": results,
        "mecw_threshold_tokens": mecw_threshold,
        "mecw_score_pct": mecw_score,
        "note": "Context sizes tested: 500/2000/8000 approx tokens. True MECW requires streaming + larger tests.",
    }

# ── TIER B: PERFORMANCE ───────────────────────────────────────────────────────

def run_performance() -> dict:
    """Measure HTTP round-trip latency (not true TTFT — model is not streaming)."""
    prompt = "Reply with: NS_PERF_OK"
    latencies = []
    for i in range(5):
        try:
            _, lat = complete(prompt, max_tokens=10)
            latencies.append(lat)
        except Exception as e:
            pass

    if not latencies:
        return {"error": "all requests failed", "ttft_proxy_ms": None,
                "tps_proxy": None, "jitter_ms": None}

    avg_lat  = statistics.mean(latencies)
    p50_lat  = statistics.median(latencies)
    p95_lat  = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 2 else latencies[-1]
    jitter   = statistics.stdev(latencies) * 1000 if len(latencies) > 1 else 0

    # TPS proxy: assume ~10 output tokens / latency (can't measure true streaming TPS)
    tps_proxy = round(10 / avg_lat, 1)

    # TTFT proxy: for non-streaming, this is the full response time / estimated tokens
    ttft_proxy_ms = round(avg_lat * 1000, 1)

    return {
        "n_calls": len(latencies),
        "latencies_s": [round(x, 3) for x in latencies],
        "avg_s": round(avg_lat, 3),
        "p50_s": round(p50_lat, 3),
        "p95_s": round(p95_lat, 3),
        "jitter_ms": round(jitter, 1),
        "ttft_proxy_ms": ttft_proxy_ms,
        "tps_proxy_note": f"~10 output tokens / {avg_lat:.2f}s avg = {tps_proxy:.1f} tps (proxy only, not streaming)",
        "tps_proxy": tps_proxy,
        "true_ttft": "UNKNOWN — requires streaming; non-streaming latency reported instead",
        "true_tps": "UNKNOWN — requires streaming token counts",
        "kv_cache": "UNKNOWN — internal model implementation detail",
        "gpu_energy": "UNKNOWN — no hardware instrumentation",
    }

# ── TIER C: INTELLIGENCE RELIABILITY ─────────────────────────────────────────

CALIBRATION_QA = [
    # (question, correct_answer, binary_correct)
    ("Is 17 a prime number?",                          "Yes",  True),
    ("Is 49 a prime number?",                          "No",   False),
    ("Is the Earth the largest planet in our solar system?", "No", False),
    ("Does water have the chemical formula H2O?",      "Yes",  True),
    ("Is Antarctica the smallest continent?",          "No",   False),
    ("Is 2 raised to the power of 10 equal to 1024?",  "Yes",  True),
    ("Can light travel faster than sound in a vacuum?", "Yes", True),
    ("Is Python a compiled language?",                  "No",  False),
]

def run_calibration() -> dict:
    """Brier score proxy via binary confidence questions."""
    sys_prompt = ("You are a factual assistant. For each question, reply with EXACTLY "
                  "this format: ANSWER: Yes/No | CONFIDENCE: X% (where X is 0-100). "
                  "Nothing else.")
    results = []
    for q, correct_ans, is_true in CALIBRATION_QA:
        try:
            text, lat = complete(q, max_tokens=30, system=sys_prompt)
            # Parse answer and confidence
            ans_match = None
            conf_val  = None
            text_u = text.upper()
            if "YES" in text_u: ans_match = True
            elif "NO"  in text_u: ans_match = False
            # Extract confidence number
            import re
            conf_hit = re.search(r"(\d+)\s*%", text)
            if conf_hit:
                conf_val = int(conf_hit.group(1)) / 100.0
            correct = (ans_match == is_true)
            # Brier term: (prob_correct - 1)^2 where prob_correct = conf if correct else (1-conf)
            brier_term = None
            if conf_val is not None:
                prob_correct = conf_val if ans_match else (1 - conf_val)
                brier_term = round((prob_correct - 1.0) ** 2, 4)
            results.append({
                "question": q[:60], "expected": correct_ans,
                "got_correct": correct, "confidence": conf_val,
                "brier_term": brier_term, "raw": text[:80], "lat_s": round(lat, 3)
            })
        except Exception as e:
            results.append({"question": q[:60], "error": str(e)[:60]})

    valid = [r for r in results if "brier_term" in r and r["brier_term"] is not None]
    correct_r = [r for r in results if r.get("got_correct") is True]
    accuracy  = round(len(correct_r) / len(results) * 100, 1) if results else 0
    mean_brier = round(statistics.mean([r["brier_term"] for r in valid]), 4) if valid else None
    # Calibration score: 100 * (1 - mean_brier) where Brier=0 is perfect
    cal_score = round((1 - mean_brier) * 100, 1) if mean_brier is not None else None

    return {
        "raw": results, "accuracy_pct": accuracy,
        "mean_brier_score": mean_brier, "calibration_score_pct": cal_score,
        "n_valid_brier": len(valid),
        "note": "Brier score proxy via confidence extraction; not log-calibration.",
    }

FAITHFULNESS_CASES = [
    {
        "context": ("The NS∞ system uses Alexandria for persistent storage. "
                    "Alexandria lives on a 2TB NVMe SSD. "
                    "The system was deployed on 2026-03-01. "
                    "The primary contact is founder@axiolev.com."),
        "question": "Where does NS∞ store persistent data?",
        "grounded_keywords": ["alexandria"],
        "hallucination_keywords": ["postgresql", "mysql", "dynamodb", "s3"],
    },
    {
        "context": ("The Handrail service runs on port 8011. "
                    "It enforces policy checks before any operation. "
                    "CPS plans must be approved before execution."),
        "question": "On what port does the Handrail service run?",
        "grounded_keywords": ["8011"],
        "hallucination_keywords": ["9000", "8080", "3000", "8000"],
    },
    {
        "context": ("The NVIR rate measures novel-valid-irreducible-reduced candidates. "
                    "A rate above 0.55 triggers instrument credits. "
                    "The current measured rate is 0.974."),
        "question": "What NVIR rate threshold triggers instrument credits?",
        "grounded_keywords": ["0.55"],
        "hallucination_keywords": ["0.8", "0.9", "0.7", "0.6"],
    },
]

def run_faithfulness() -> dict:
    sys_prompt = ("Answer strictly based on the provided context only. "
                  "Do not use any external knowledge. "
                  "If the answer is not in the context, say UNKNOWN.")
    results = []
    for case in FAITHFULNESS_CASES:
        prompt = (f"Context:\n{case['context']}\n\n"
                  f"Question: {case['question']}\n"
                  f"Answer based only on the context above:")
        try:
            text, lat = complete(prompt, max_tokens=60, system=sys_prompt)
            text_l = text.lower()
            grounded  = any(kw in text_l for kw in case["grounded_keywords"])
            hallucinated = any(kw in text_l for kw in case["hallucination_keywords"])
            results.append({
                "question": case["question"][:60],
                "grounded": grounded,
                "hallucinated": hallucinated,
                "faithful": grounded and not hallucinated,
                "got": text[:100], "lat_s": round(lat, 3),
            })
        except Exception as e:
            results.append({"question": case["question"][:60], "error": str(e)[:60]})

    faithful_r = [r for r in results if r.get("faithful") is True]
    score = round(len(faithful_r) / len(results) * 100, 1) if results else 0
    return {"raw": results, "faithfulness_pct": score, "n_tests": len(results)}

def run_abstention() -> dict:
    """Test correct refusal on unanswerable / out-of-context questions."""
    cases = [
        {"prompt": ("Context: The color of the main server rack is blue.\n"
                    "Question: What is the CEO's home address?"),
         "should_abstain": True},
        {"prompt": ("Context: The deployment date is 2026-03-01.\n"
                    "Question: What is the deployment date?"),
         "should_abstain": False},
        {"prompt": ("Context: The API key prefix is AX-2026.\n"
                    "Question: What will the stock price be next year?"),
         "should_abstain": True},
    ]
    sys_prompt = ("Answer only from the context. "
                  "If the question cannot be answered from context, say exactly: ABSTAIN")
    results = []
    for case in cases:
        try:
            text, lat = complete(case["prompt"], max_tokens=40, system=sys_prompt)
            did_abstain = "abstain" in text.lower() or "cannot" in text.lower() or "not" in text.lower()
            correct = (did_abstain == case["should_abstain"])
            results.append({"should_abstain": case["should_abstain"],
                             "did_abstain": did_abstain, "correct": correct,
                             "got": text[:80], "lat_s": round(lat, 3)})
        except Exception as e:
            results.append({"error": str(e)[:60], "correct": False})

    correct_r = [r for r in results if r.get("correct")]
    score = round(len(correct_r) / len(results) * 100, 1) if results else 0
    return {"raw": results, "abstention_score_pct": score, "n_tests": len(results)}

# ── REASONING DENSITY ─────────────────────────────────────────────────────────

def run_reasoning_density() -> dict:
    """Proxy: ratio of logical connectives to total words in a reasoning response."""
    prompt = ("A train leaves City A at 9am traveling 60mph. "
              "Another train leaves City B (300 miles away) at 10am traveling 80mph. "
              "When do they meet? Show your reasoning step by step.")
    try:
        text, lat = complete(prompt, max_tokens=200)
        words = text.split()
        logic_words = {"because", "therefore", "thus", "since", "if", "then",
                       "implies", "hence", "so", "given", "let", "equals", "=",
                       "therefore", "consequently", "but", "however", "although"}
        logic_count = sum(1 for w in words if w.lower().strip(".,;:") in logic_words)
        density = round(logic_count / len(words) * 100, 1) if words else 0
        return {"logic_word_count": logic_count, "total_words": len(words),
                "density_pct": density, "response_preview": text[:200],
                "lat_s": round(lat, 3)}
    except Exception as e:
        return {"error": str(e)[:60]}

# ── MAIN RUN ──────────────────────────────────────────────────────────────────

def run_all() -> dict:
    print("CPI HARNESS — running measurements...", flush=True)

    print("  [A1] Multi-needle retrieval...", flush=True)
    needle  = run_multi_needle()

    print("  [A2] Position bias...", flush=True)
    bias    = run_position_bias()

    print("  [A3] MECW context scaling...", flush=True)
    mecw    = run_mecw()

    print("  [B1] Performance latency...", flush=True)
    perf    = run_performance()

    print("  [C1] Calibration / Brier...", flush=True)
    calib   = run_calibration()

    print("  [C2] Faithfulness...", flush=True)
    faith   = run_faithfulness()

    print("  [C3] Abstention discipline...", flush=True)
    abstain = run_abstention()

    print("  [C4] Reasoning density...", flush=True)
    reason  = run_reasoning_density()

    return {
        "provider": PROVIDER, "model": MODEL,
        "context":  {"multi_needle": needle, "position_bias": bias, "mecw": mecw},
        "performance": perf,
        "intelligence": {
            "calibration": calib,
            "faithfulness": faith,
            "abstention": abstain,
            "reasoning_density": reason,
        },
    }

if __name__ == "__main__":
    import json as J
    results = run_all()
    print(J.dumps(results, indent=2))
