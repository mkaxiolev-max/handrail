"""L4 The Loom — reflector functor L : GradientField → Canon.

Confidence score formula (weights exact, sum = 1.0):
    score = 0.45*evidence + 0.25*(1 - contradiction) + 0.15*novelty + 0.15*stability

Loop: GENERATE → TEST → CONTRADICT → REWEIGHT → NARRATE → STORE → REENTER
I1 enforced: Loom reflects toward Canon but never writes to Canon directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ns.integrations.ether import GradientField, GradientTriple
from ns.services.loom.mode_switching import LoomMode, ModeSwitcher

# Exact weights — must sum to 1.0
_W_EVIDENCE: float = 0.45
_W_CONTRADICTION: float = 0.25
_W_NOVELTY: float = 0.15
_W_STABILITY: float = 0.15

assert abs(_W_EVIDENCE + _W_CONTRADICTION + _W_NOVELTY + _W_STABILITY - 1.0) < 1e-12


@dataclass
class ConfidenceEnvelope:
    """Confidence score for a reflected gradient triple."""

    evidence: float
    contradiction: float
    novelty: float
    stability: float

    def score(self) -> float:
        return (
            _W_EVIDENCE * self.evidence
            + _W_CONTRADICTION * (1.0 - self.contradiction)
            + _W_NOVELTY * self.novelty
            + _W_STABILITY * self.stability
        )

    @staticmethod
    def weights() -> dict[str, float]:
        return {
            "evidence": _W_EVIDENCE,
            "contradiction": _W_CONTRADICTION,
            "novelty": _W_NOVELTY,
            "stability": _W_STABILITY,
        }


@dataclass
class LoomReflection:
    """Result of running a GradientTriple through the Loom loop."""

    triple: GradientTriple
    envelope: ConfidenceEnvelope
    stage: LoomMode
    narrative: str
    stored: bool = False
    contradictions: list[str] = field(default_factory=list)


class LoomService:
    """Reflector functor L : GradientField → Canon (L4 The Loom).

    I1 — Canon precedes Conversion: this service reflects triples toward Canon
    but never promotes to Canon directly. Promotion is the responsibility of
    the Ring 4 CanonService / PromotionGuard.
    """

    def reflect(
        self,
        gradient_field: GradientField,
        *,
        min_confidence: float = 0.0,
        external_contradictions: Optional[dict[str, list[str]]] = None,
    ) -> list[LoomReflection]:
        """Surface triples from gradient_field and run each through the loop.

        Args:
            gradient_field: L2 input source.
            min_confidence: Filter triples below this raw confidence threshold.
            external_contradictions: Optional dict mapping triple keys to
                contradiction labels injected at the CONTRADICT stage.

        Returns:
            List of LoomReflections in surface order.
        """
        triples = gradient_field.surface(min_confidence=min_confidence)
        return [
            self._run_loop(t, external_contradictions or {})
            for t in triples
        ]

    # ------------------------------------------------------------------
    # Internal loop implementation
    # ------------------------------------------------------------------

    def _run_loop(
        self,
        triple: GradientTriple,
        contradictions_map: dict[str, list[str]],
    ) -> LoomReflection:
        switcher = ModeSwitcher()

        # GENERATE — derive raw evidence from the triple's confidence
        evidence = float(max(0.0, min(1.0, triple.confidence)))

        # TEST — introspect for internal consistency (baseline: always passes)
        switcher.advance()  # → TEST
        contradiction_weight = 0.0

        # CONTRADICT — apply injected contradictions if any
        switcher.advance()  # → CONTRADICT
        triple_key = f"{triple.subject}:{triple.predicate}:{triple.object_}"
        injected = contradictions_map.get(triple_key, [])
        if injected:
            # Each injected contradiction raises weight by 0.25 (capped at 1.0)
            contradiction_weight = min(1.0, len(injected) * 0.25)

        # REWEIGHT — compute novelty and stability, build envelope
        switcher.advance()  # → REWEIGHT
        novelty = self._compute_novelty(triple)
        stability = self._compute_stability(triple)
        envelope = ConfidenceEnvelope(
            evidence=evidence,
            contradiction=contradiction_weight,
            novelty=novelty,
            stability=stability,
        )

        # NARRATE — produce a human-readable summary
        switcher.advance()  # → NARRATE
        narrative = (
            f'"{triple.subject} {triple.predicate} {triple.object_}" '
            f"[score={envelope.score():.4f}, stage=NARRATE]"
        )

        # STORE — mark reflection as stored (append-only per I2)
        switcher.advance()  # → STORE

        # REENTER — ready for next cycle; loop re-entry is caller's responsibility
        switcher.advance()  # → REENTER

        return LoomReflection(
            triple=triple,
            envelope=envelope,
            stage=LoomMode.REENTER,
            narrative=narrative,
            stored=True,
            contradictions=injected,
        )

    def _compute_novelty(self, triple: GradientTriple) -> float:
        """Baseline novelty: inverse confidence (high-confidence = less novel)."""
        return 1.0 - float(max(0.0, min(1.0, triple.confidence))) * 0.5

    def _compute_stability(self, triple: GradientTriple) -> float:
        """Baseline stability tracks triple confidence directly."""
        return float(max(0.0, min(1.0, triple.confidence)))
