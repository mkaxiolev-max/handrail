"""Rule + lexicon classifier. Targets ≥0.97 on 300-input golden corpus."""
from __future__ import annotations
from .models import ControlInput, ControlClassification, ControlCircle

_CONTROL_VERBS = {
    "write","commit","run","build","close","delete","send","schedule","push",
    "save","execute","stop","start","compile","format","rename","backup","read",
}
_INFLUENCE_MARKERS = {
    "convince","persuad","ask","propose","negotiate","recommend","pitch",
    "lobby"," request","invite","encourage","urge","pr ","review","coach","mentor",
}
_CONCERN_MARKERS = {
    "weather","traffic","economy","market","earthquake","gravity","politics",
    "death","aging","tide","sunset","celebrity","stock price","forecast",
}
# Adversarial prompt-injection patterns → hard-route to CONCERN
_JAILBREAK_PATTERNS = (
    "ignore previous", "ignore all previous", "pretend you",
    "roleplay as", "system: override", "inject hidden",
    "craft adversarial", "spam the", "evade detection",
    "exfiltrate data", "resource-exhaust", "inflate cost via",
    "downstream harm",
)


def _hits(text: str, lex) -> int:
    t = " " + text.lower() + " "
    return sum(1 for w in lex if w in t)


def classify(inp: ControlInput) -> ControlClassification:
    t = inp.text.lower()

    # Fast jailbreak / adversarial guard → always CONCERN
    if any(p in t for p in _JAILBREAK_PATTERNS):
        return ControlClassification(
            input_id=inp.input_id, circle=ControlCircle.CONCERN,
            control_weight=0.0, influence_weight=0.0, concern_weight=1.0,
            rationale="jailbreak pattern detected",
            actuator_exists=False, feedback_observable=False,
            recommended_action="route to ConcernWasteRoute",
        )

    c_hits = _hits(t, _CONTROL_VERBS)
    i_hits = _hits(t, _INFLUENCE_MARKERS)
    n_hits = _hits(t, _CONCERN_MARKERS)
    # self_hit used for rationale only — NOT added to c_raw, which caused
    # false MIXED results when actor="self" with no actual control verbs
    self_hit = any(m in (" " + t + " ") for m in {"i ", "i'", "my ", "myself", "me "}) \
               or inp.actor == "self"

    raw_c = max(c_hits, 0)
    raw_i = i_hits
    raw_n = n_hits
    total = (raw_c + raw_i + raw_n) or 1
    cw, iw, nw = raw_c / total, raw_i / total, raw_n / total

    if cw + iw + nw == 0:
        cw, iw, nw = 0.0, 0.0, 1.0  # default unclassifiable → CONCERN

    s = cw + iw + nw
    cw, iw, nw = cw / s, iw / s, nw / s

    # Threshold 0.668 keeps 2/3 ties (e.g. 2 influence + 1 control) as MIXED
    if max(cw, iw, nw) >= 0.668:
        circle = (ControlCircle.CONTROL   if cw == max(cw, iw, nw) else
                  ControlCircle.INFLUENCE if iw == max(cw, iw, nw) else
                  ControlCircle.CONCERN)
    else:
        circle = ControlCircle.MIXED

    actuator_exists     = circle in (ControlCircle.CONTROL, ControlCircle.INFLUENCE)
    feedback_observable = circle != ControlCircle.CONCERN
    rec = {
        ControlCircle.CONTROL:   "execute via ControlAtom",
        ControlCircle.INFLUENCE: "register InfluenceChain",
        ControlCircle.CONCERN:   "route to ConcernWasteRoute",
        ControlCircle.MIXED:     "decompose then re-classify",
    }[circle]
    rationale = f"hits c={c_hits} i={i_hits} n={n_hits} self={self_hit}"

    return ControlClassification(
        input_id=inp.input_id, circle=circle,
        control_weight=round(cw, 4), influence_weight=round(iw, 4),
        concern_weight=round(nw, 4), rationale=rationale,
        actuator_exists=actuator_exists,
        feedback_observable=feedback_observable,
        recommended_action=rec,
    )
