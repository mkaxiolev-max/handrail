"""Shadow-Score Discipline — 18-metric continuous quality signal."""
from __future__ import annotations
from dataclasses import dataclass

METRIC_NAMES: list[str] = [
    "test_pass_rate", "branch_coverage", "mutation_score", "doc_coverage",
    "type_hint_coverage", "import_depth", "cyclomatic_complexity", "coupling_score",
    "cohesion_score", "code_age_days", "dependency_freshness", "api_stability",
    "error_rate", "response_time_p99", "memory_efficiency", "cpu_efficiency",
    "test_flakiness_rate", "security_scan_score",
]

# Metrics where lower is better (inverted for composite)
LOWER_IS_BETTER = {
    "import_depth", "cyclomatic_complexity", "coupling_score",
    "code_age_days", "error_rate", "response_time_p99", "test_flakiness_rate",
}


@dataclass
class ShadowMetric:
    name: str
    value: float
    lower_is_better: bool

    @property
    def normalized(self) -> float:
        """Normalize to 0–1 where 1 is best."""
        v = max(0.0, min(1.0, self.value))
        return 1.0 - v if self.lower_is_better else v


class ShadowScorer:
    def __init__(self):
        self._metrics: dict[str, ShadowMetric] = {}

    def record(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown metric '{name}'. Valid: {METRIC_NAMES}")
        self._metrics[name] = ShadowMetric(name, value, name in LOWER_IS_BETTER)

    def composite(self) -> float:
        if not self._metrics:
            return 0.0
        return sum(m.normalized for m in self._metrics.values()) / len(self._metrics)

    def get_all(self) -> dict[str, float]:
        return {name: m.value for name, m in self._metrics.items()}

    def coverage_pct(self) -> float:
        return len(self._metrics) / len(METRIC_NAMES) * 100

    def missing_metrics(self) -> list[str]:
        return [n for n in METRIC_NAMES if n not in self._metrics]
