"""PAP H-layer rendering bridge. Mode-validated; rejects NARRATIVE_AS_PROOF."""
from typing import Dict, Any
from .models import HumanSurface


def render_h_layer(h: HumanSurface) -> Dict[str, Any]:
    if h.storytime_mode == "NARRATIVE_AS_PROOF":
        raise ValueError("PAP rejects H-layer with storytime_mode=NARRATIVE_AS_PROOF")
    return {
        "mode": h.storytime_mode,
        "summary": h.summary,
        "explanation": h.explanation,
        "ui_schema": h.ui_schema,
        "persuasion_flags": h.persuasion_flags,
        "rendered_by": "pap.storytime_bridge",
    }
