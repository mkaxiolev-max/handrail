from __future__ import annotations
from typing import Optional

class ScoreMonotoneInvariant:
    def __init__(self, min_score=35.0, max_delta_drop=-10.0):
        self.min_score=min_score; self.max_delta_drop=max_delta_drop

    def evaluate(self, current_score: float, baseline: Optional[float]=None):
        if current_score<self.min_score:
            return False,f"score {current_score:.2f} below minimum {self.min_score}"
        if baseline is not None and baseline>0:
            delta_pct=(current_score-baseline)/baseline*100
            if delta_pct<self.max_delta_drop:
                return False,f"delta {delta_pct:.2f}% < hard halt threshold {self.max_delta_drop}%"
        return True,"invariant satisfied"
