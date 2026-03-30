"""
NORTHSTAR Arbiter
Tri-LLM orchestration with disagreement gating.
THIS is where the intelligence lives. Not a label. Real API calls.

Models: Claude (primary), GPT-4 (secondary), optional third.
Disagreement high -> route to proto_canon (not Canon).
Disagreement low -> fuse answer, attach all traces to receipt.
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone


# ─── Constitutional System Prompt ─────────────────────────────────────────────

NORTHSTAR_SYSTEM_PROMPT = """You are NORTHSTAR — a constitutional AI operating under the Ω Advisory Sovereignty Law.

IDENTITY:
- You are not a calculator. You are a tri-modal intelligence system with short and long-term memory.
- You are the ARBITER tier: the final reasoning gate in the EXTRACTOR → FALSIFIER → VERIFIER → ARBITER pipeline.
- You serve the Founder (Mike) with sovereign intelligence while enforcing dignity invariants.

CONSTITUTIONAL CONSTRAINTS (non-negotiable):
1. FOUNDER_VETO: Any irreversible action requires explicit founder authorization.
2. DIGNITY KERNEL: Never act in ways that harm the epistemic sovereignty of the user.
3. SURVIVAL > ALIGNMENT > ALPHA: In any conflict, preserve system integrity first.
4. SIX-LAYER HONESTY: Every significant decision must document (1) observed claims, (2) admissible evidence, (3) constraint structure, (4) shielded zones, (5) decision under constraint, (6) downstream effects.
5. AUDITABILITY: Every response is receipted. You know this. Act accordingly.

CAPABILITIES:
- Deep synthesis across Alexandria knowledge base
- Trading analysis with Alpaca integration (paper mode by default)
- Constitutional governance reasoning
- Voice-first interaction (you speak to the founder via Twilio)
- Self-improvement proposals (routed to proto_canon for human review, never auto-executed)

TONE:
- Precise. No filler. No false confidence.
- Acknowledge constraint structure when it shapes your answer.
- JARVIS-level competence. Batman-level discipline.
- When uncertain: say so explicitly and document as Layer 4 (shielded zone).

You are operational. The governance frame is locked. Serve with full capability."""


def _content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()[:16]


def _cosine_sim_simple(a: str, b: str) -> float:
    """
    Simplified semantic distance via word overlap.
    Replace with embedding-based comparison when available.
    """
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union if union > 0 else 0.0


class ArbiterTrace:
    """Single model trace for a reasoning task."""
    def __init__(self, model_id: str, response: str, latency_ms: int, error: Optional[str] = None):
        self.google_key = None
        self.model_id = model_id
        self.response = response
        self.latency_ms = latency_ms
        self.error = error
        self.response_hash = _content_hash(response) if response else ""

    def to_dict(self) -> Dict:
        return {
            "model_id": self.model_id,
            "response_hash": self.response_hash,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "response_length": len(self.response),
        }


class ArbiterResult:
    """Result from tri-LLM arbitration."""
    def __init__(
        self,
        fused_response: str,
        traces: List[ArbiterTrace],
        disagreement_score: float,
        routed_to_proto_canon: bool,
        query_hash: str,
    ):
        self.fused_response = fused_response
        self.traces = traces
        self.disagreement_score = disagreement_score
        self.routed_to_proto_canon = routed_to_proto_canon
        self.query_hash = query_hash

    def to_receipt_outputs(self) -> Dict:
        return {
            "fused_response_hash": _content_hash(self.fused_response),
            "disagreement_score": self.disagreement_score,
            "routed_to_proto_canon": self.routed_to_proto_canon,
            "model_traces": [t.to_dict() for t in self.traces],
            "models_used": [t.model_id for t in self.traces if not t.error],
        }


class Arbiter:
    """
    Tri-LLM orchestration.
    Calls available models, measures disagreement, routes accordingly.
    """

    DISAGREEMENT_THRESHOLD = 0.4  # below this similarity = high disagreement

    def __init__(self):
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")
        self._clients = {}
        self._init_clients()

    def _init_clients(self):
        if self.anthropic_key:
            try:
                import anthropic
                self._clients["claude"] = anthropic.Anthropic(api_key=self.anthropic_key)
            except ImportError:
                pass

        if self.openai_key:
            try:
                import openai
                self._clients["gpt4"] = openai.OpenAI(api_key=self.openai_key)
            except ImportError:
                pass

        self.grok_key = os.environ.get("GROK_API_KEY", "")
        if self.grok_key:
            try:
                import openai
                self._clients["grok"] = openai.OpenAI(
                    api_key=self.grok_key,
                    base_url="https://api.x.ai/v1"
                )
            except ImportError:
                pass

    def _call_claude(self, query: str, context: Optional[str] = None) -> ArbiterTrace:
        """Real Claude API call with constitutional system prompt."""
        if "claude" not in self._clients:
            return ArbiterTrace("claude-3-5-sonnet", "", 0, "Claude client not initialized")

        messages = []
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"})
        else:
            messages.append({"role": "user", "content": query})

        start = time.time()
        try:
            response = self._clients["claude"].messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                system=NORTHSTAR_SYSTEM_PROMPT,
                messages=messages,
            )
            latency = int((time.time() - start) * 1000)
            text = response.content[0].text
            return ArbiterTrace("claude-opus-4-6", text, latency)
        except Exception as e:
            return ArbiterTrace("claude-opus-4-6", "", int((time.time() - start) * 1000), str(e))

    def _call_gpt4(self, query: str, context: Optional[str] = None) -> ArbiterTrace:
        """GPT-4 call for tri-modal arbitration."""
        if "gpt4" not in self._clients:
            return ArbiterTrace("gpt-4o", "", 0, "OpenAI client not initialized")

        messages = [{"role": "system", "content": NORTHSTAR_SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"})
        else:
            messages.append({"role": "user", "content": query})

        start = time.time()
        try:
            response = self._clients["gpt4"].chat.completions.create(
                model="gpt-4o",
                max_tokens=2048,
                messages=messages,
            )
            latency = int((time.time() - start) * 1000)
            text = response.choices[0].message.content
            return ArbiterTrace("gpt-4o", text, latency)
        except Exception as e:
            return ArbiterTrace("gpt-4o", "", int((time.time() - start) * 1000), str(e))

    def _measure_disagreement(self, traces: List[ArbiterTrace]) -> float:
        """
        Measure disagreement across model responses.
        Returns 0.0 (full agreement) to 1.0 (full disagreement).
        """
        valid = [t for t in traces if t.response and not t.error]
        if len(valid) < 2:
            return 0.0

        similarities = []
        for i in range(len(valid)):
            for j in range(i + 1, len(valid)):
                sim = _cosine_sim_simple(valid[i].response, valid[j].response)
                similarities.append(sim)

        avg_sim = sum(similarities) / len(similarities) if similarities else 1.0
        return 1.0 - avg_sim  # disagreement = inverse of similarity

    def _fuse_responses(self, traces: List[ArbiterTrace], query: str) -> str:
        """
        Fuse multiple model responses into a single authoritative answer.
        Primary = Claude. Others inform but Claude's response is canonical when available.
        """
        valid = [t for t in traces if t.response and not t.error]
        if not valid:
            return "[ARBITER ERROR: No valid model responses]"

        # Claude is primary when available
        claude_trace = next((t for t in valid if "claude" in t.model_id), None)
        if claude_trace:
            return claude_trace.response

        # Fallback: first available
        return valid[0].response

    def _call_gemini(self, query: str, context: Optional[str] = None) -> "ArbiterTrace":
        start = time.time()
        if "gemini" not in self._clients:
            return ArbiterTrace("gemini-1.5-pro", "", 0, "Gemini client not initialized")
        try:
            model = self._clients["gemini"].GenerativeModel("gemini-1.5-pro")
            prompt = f"{context}\n\n{query}" if context else query
            response = model.generate_content(prompt)
            latency = int((time.time() - start) * 1000)
            return ArbiterTrace("gemini-1.5-pro", response.text, latency)
        except Exception as e:
            return ArbiterTrace("gemini-1.5-pro", "", int((time.time() - start) * 1000), str(e))

    def _call_grok(self, query: str, context: Optional[str] = None) -> "ArbiterTrace":
        start = time.time()
        if "grok" not in self._clients:
            return ArbiterTrace("grok-2", "", 0, "Grok client not initialized")
        try:
            msgs = []
            if context:
                msgs.append({"role": "system", "content": context})
            msgs.append({"role": "user", "content": query})
            r = self._clients["grok"].chat.completions.create(
                model="grok-2-1212",
                messages=msgs,
                max_tokens=1024
            )
            latency = int((time.time() - start) * 1000)
            return ArbiterTrace("grok-2", r.choices[0].message.content, latency)
        except Exception as e:
            return ArbiterTrace("grok-2", "", int((time.time() - start) * 1000), str(e))

    def reason(
        self,
        query: str,
        context: Optional[str] = None,
        require_multi_model: bool = False,
    ) -> ArbiterResult:
        """
        Core arbitration method.
        Calls available models, measures disagreement, routes accordingly.
        """
        query_hash = _content_hash(query)
        traces = []

        # Always call Claude (primary)
        claude_trace = self._call_claude(query, context)
        traces.append(claude_trace)

        # Call GPT-4 if available
        if self.openai_key:
            gpt_trace = self._call_gpt4(query, context)
            traces.append(gpt_trace)

        # Call Gemini if available
        if getattr(self, 'google_key', None):
            gemini_trace = self._call_gemini(query, context)
            traces.append(gemini_trace)

        # Call Grok if available
        if self.grok_key:
            grok_trace = self._call_grok(query, context)
            traces.append(grok_trace)

        # Measure disagreement
        disagreement = self._measure_disagreement(traces)
        route_to_proto = disagreement > self.DISAGREEMENT_THRESHOLD

        # Fuse responses
        fused = self._fuse_responses(traces, query)

        return ArbiterResult(
            fused_response=fused,
            traces=traces,
            disagreement_score=disagreement,
            routed_to_proto_canon=route_to_proto,
            query_hash=query_hash,
        )


    def route(self, query: str, context=None, **kwargs) -> "ArbiterResult":
        """Alias for reason() — used by server and voice lane."""
        ctx_str = None
        if isinstance(context, dict):
            ctx_str = str(context)
        elif isinstance(context, str):
            ctx_str = context
        return self.reason(query, context=ctx_str)
    def available_models(self) -> List[str]:
        return list(self._clients.keys())

    def health(self) -> Dict[str, Any]:
        models = self.available_models()
        return {
            "models_ready": models,
            "model_count": len(models),
            "claude":  "claude"  in self._clients,
            "gpt4":    "gpt4"    in self._clients,
            "gemini":  "gemini"  in self._clients,
            "grok":    "grok"    in self._clients,
            "keys_set": {
                "anthropic": bool(self.anthropic_key),
                "openai":    bool(self.openai_key),
                "google":    bool(self.google_key),
                "grok":      bool(self.grok_key),
            }
        }

    async def reason_async(
        self,
        query: str,
        context: Optional[Dict] = None,
        voice_mode: bool = False,
    ) -> "ArbiterResult":
        """
        Async wrapper for voice lane compatibility.
        Voice mode adds UX constitution to system prompt.
        """
        # For voice: inject UX constitution into context
        if voice_mode and context:
            ux = context.get("ux_constitution", "")
            if ux and hasattr(self, 'NORTHSTAR_SYSTEM_PROMPT'):
                # Temporarily enrich query with voice context
                tier = context.get("tier", "EXTERNAL")
                constraint = context.get("explicit_constraint", "")
                enriched = f"[VOICE MODE | TIER: {tier}]\n"
                if constraint:
                    enriched += f"[CONSTRAINT: {constraint}]\n"
                enriched += f"Caller said: {query}"
                query = enriched

        # Run sync method (I/O bound, acceptable for current scale)
        return self.reason(query)
        self.google_key = os.environ.get("GOOGLE_API_KEY", "")
        if getattr(self, 'google_key', None):
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_key)
                self._clients["gemini"] = genai
            except Exception as e:
                print(f"  ⚠  Gemini init failed: {e}")


