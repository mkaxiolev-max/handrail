"""Runtime calibration telemetry pipeline. © 2026 AXIOLEV Holdings LLC"""
from __future__ import annotations
import math, time, random, json, hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Tuple, Literal

Band = Literal["BLOCK", "REVIEW", "PASS", "HIGH_ASSURANCE"]
THRESHOLDS = {"BLOCK_MAX": 35.0, "REVIEW_MAX": 65.0, "PASS_MAX": 80.0}

def classify_band(confidence: float) -> Band:
    if confidence < THRESHOLDS["BLOCK_MAX"]:  return "BLOCK"
    if confidence < THRESHOLDS["REVIEW_MAX"]: return "REVIEW"
    if confidence < THRESHOLDS["PASS_MAX"]:   return "PASS"
    return "HIGH_ASSURANCE"

@dataclass
class CalibrationDecision:
    decision_id: str
    trace_id: str
    tenant: str = "default"
    model: str = ""
    recalibrator_hash: str = ""
    confidence: float = 0.5
    confidence_method: str = "verbalized"
    band: Band = "REVIEW"
    brier_instant: float = 0.0
    shadow_consistency: float = 1.0
    outcome_label: Optional[int] = None
    ts: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

class RunningBrier:
    def __init__(self, lam: float = 0.01):
        self.n = 0; self.sum_bs = 0.0; self.ewma = 0.0; self.lam = lam

    def update(self, confidence: float, outcome: int) -> float:
        assert 0.0 <= confidence <= 1.0
        assert outcome in (0, 1)
        bs = (confidence - outcome) ** 2
        self.n += 1; self.sum_bs += bs
        self.ewma = self.lam * bs + (1 - self.lam) * self.ewma
        return bs

    @property
    def mean(self) -> float:
        return self.sum_bs / self.n if self.n else 0.0

    @property
    def drift_signal(self) -> float:
        return self.ewma - self.mean if self.n > 100 else 0.0

class _Reservoir:
    def __init__(self, k: int = 10_000):
        self.k = k; self.seen = 0; self.store: List[Tuple[float, int]] = []

    def add(self, confidence: float, outcome: int):
        self.seen += 1
        if len(self.store) < self.k:
            self.store.append((confidence, outcome))
        else:
            j = random.randint(0, self.seen - 1)
            if j < self.k: self.store[j] = (confidence, outcome)

class BinnedECE:
    def __init__(self, n_bins: int = 15, equal_mass: bool = True, reservoir_k: int = 10_000):
        self.n_bins = n_bins; self.equal_mass = equal_mass
        self.reservoir = _Reservoir(reservoir_k)

    def update(self, confidence: float, outcome: int):
        self.reservoir.add(confidence, outcome)

    def compute(self) -> Dict:
        data = sorted(self.reservoir.store, key=lambda x: x[0])
        n = len(data)
        if n < self.n_bins:
            return {"ece": 0.0, "mce": 0.0, "n": n, "bins": []}
        if self.equal_mass:
            bin_size = n // self.n_bins
            bins = [data[i*bin_size:(i+1)*bin_size] for i in range(self.n_bins)]
            if n % self.n_bins: bins[-1].extend(data[self.n_bins * bin_size:])
        else:
            edges = [i/self.n_bins for i in range(self.n_bins + 1)]
            bins = [[(c,o) for c,o in data if edges[i] <= c < edges[i+1]] for i in range(self.n_bins)]
        ece = 0.0; mce = 0.0; bin_report = []
        for b in bins:
            if not b: bin_report.append({"n":0,"conf":0.0,"acc":0.0,"gap":0.0}); continue
            conf = sum(c for c,_ in b)/len(b); acc = sum(o for _,o in b)/len(b)
            gap = abs(conf - acc); ece += (len(b)/n)*gap; mce = max(mce, gap)
            bin_report.append({"n":len(b),"conf":conf,"acc":acc,"gap":gap})
        return {"ece": ece, "mce": mce, "n": n, "bins": bin_report}

ACE = BinnedECE

class ReliabilityDiagram:
    def __init__(self, ece_metric: BinnedECE): self.ece = ece_metric
    def data(self) -> List[Dict]: return self.ece.compute()["bins"]

class AURC:
    def __init__(self, reservoir_k: int = 10_000):
        self.reservoir = _Reservoir(reservoir_k)

    def update(self, confidence: float, outcome: int):
        self.reservoir.add(confidence, 1 - outcome)

    def compute(self) -> float:
        data = sorted(self.reservoir.store, key=lambda x: -x[0])
        if not data: return 0.0
        losses = [loss for _, loss in data]
        cum_loss = 0.0; aurc = 0.0
        for i, loss in enumerate(losses, 1):
            cum_loss += loss; aurc += cum_loss / i
        return aurc / len(losses)

class ChowThreshold:
    def __init__(self, c_error: float = 4.0, c_reject: float = 1.0,
                 min_coverage: float = 0.55, max_reject_rate: float = 0.15):
        self.c_error = c_error; self.c_reject = c_reject
        self.min_coverage = min_coverage; self.max_reject_rate = max_reject_rate
        self.prior = self.c_reject / (self.c_error + self.c_reject)

    def optimal(self, aurc: AURC) -> Dict:
        data = sorted(aurc.reservoir.store, key=lambda x: -x[0])
        if not data: return {"threshold": 1.0-self.prior, "coverage": 1.0, "risk": 0.0}
        best = {"threshold": 1.0-self.prior, "coverage": 1.0, "risk": 1.0, "score": math.inf}
        n = len(data)
        for k in range(1, n+1):
            tau = data[k-1][0]; covered = data[:k]; coverage = k/n
            if coverage < self.min_coverage: continue
            if 1-coverage > self.max_reject_rate: continue
            risk = sum(loss for _,loss in covered)/k if k else 0.0
            cost = self.c_error*risk*coverage + self.c_reject*(1-coverage)
            if cost < best["score"]:
                best = {"threshold": tau, "coverage": coverage, "risk": risk, "score": cost}
        return best

class BrierSkillScore:
    def __init__(self, brier: RunningBrier, baseline_accuracy: float = 0.5):
        self.brier = brier
        self.baseline = baseline_accuracy * (1 - baseline_accuracy)

    def compute(self) -> float:
        if self.brier.n == 0 or self.baseline == 0: return 0.0
        return 1.0 - (self.brier.mean / self.baseline)

_PIPELINE_STATE = {
    "brier": RunningBrier(lam=0.01), "brier_stable": RunningBrier(lam=0.001),
    "ece": BinnedECE(n_bins=15, equal_mass=True), "aurc": AURC(),
    "chow": ChowThreshold(), "decisions": [], "max_decisions": 1000,
}

def emit_decision(decision_id: str, trace_id: str, confidence: float,
                  outcome: Optional[int]=None, model: str="",
                  tenant: str="default", confidence_method: str="verbalized") -> CalibrationDecision:
    if confidence > 1.0: confidence = confidence / 100.0
    c_pct = confidence * 100.0; band = classify_band(c_pct)
    brier_instant = 0.0
    if outcome is not None:
        brier_instant = _PIPELINE_STATE["brier"].update(confidence, outcome)
        _PIPELINE_STATE["brier_stable"].update(confidence, outcome)
        _PIPELINE_STATE["ece"].update(confidence, outcome)
        _PIPELINE_STATE["aurc"].update(confidence, outcome)
    rec = CalibrationDecision(decision_id=decision_id, trace_id=trace_id, tenant=tenant,
        model=model, confidence=confidence, confidence_method=confidence_method,
        band=band, brier_instant=brier_instant, outcome_label=outcome)
    d_buf = _PIPELINE_STATE["decisions"]
    d_buf.append(rec)
    if len(d_buf) > _PIPELINE_STATE["max_decisions"]: d_buf.pop(0)
    return rec

def compute_metrics() -> Dict:
    brier = _PIPELINE_STATE["brier"]
    ece = _PIPELINE_STATE["ece"].compute()
    aurc_val = _PIPELINE_STATE["aurc"].compute()
    chow = _PIPELINE_STATE["chow"].optimal(_PIPELINE_STATE["aurc"])
    bss = BrierSkillScore(brier).compute()
    return {"brier_mean": brier.mean, "brier_ewma": brier.ewma,
            "brier_drift": brier.drift_signal, "brier_n": brier.n,
            "ece": ece["ece"], "mce": ece["mce"], "ece_n": ece["n"],
            "aurc": aurc_val, "chow_tau": chow["threshold"],
            "chow_coverage": chow["coverage"], "chow_risk": chow["risk"], "bss": bss}

def export_prometheus() -> str:
    m = compute_metrics()
    return "\n".join([
        f'# TYPE axiolev_brier_mean gauge',
        f'axiolev_brier_mean {m["brier_mean"]:.6f}',
        f'# TYPE axiolev_ece gauge',
        f'axiolev_ece {m["ece"]:.6f}',
        f'# TYPE axiolev_aurc gauge',
        f'axiolev_aurc {m["aurc"]:.6f}',
        f'# TYPE axiolev_bss gauge',
        f'axiolev_bss {m["bss"]:.6f}',
    ])
