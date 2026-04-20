from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Zone(str, Enum):
    BLOCK="BLOCK"; REVIEW="REVIEW"; PASS="PASS"; HIGH_ASSURANCE="HIGH_ASSURANCE"

@dataclass
class ZoneDecision:
    score: float; zone: Zone; delta: Optional[float]=None
    delta_action: Optional[str]=None; drift_sigma: Optional[float]=None; reason: str=""

class ZoneClassifier:
    def __init__(self, block_max=35.0, review_max=65.0, pass_max=80.0):
        self.block_max=block_max; self.review_max=review_max; self.pass_max=pass_max

    def classify(self, score: float, prior=None, drift_sigma=None) -> ZoneDecision:
        if score<self.block_max: zone=Zone.BLOCK
        elif score<self.review_max: zone=Zone.REVIEW
        elif score<self.pass_max: zone=Zone.PASS
        else: zone=Zone.HIGH_ASSURANCE
        delta=None; delta_action=None
        if prior is not None and prior>0:
            delta=(score-prior)/prior*100
            if delta<=-10: delta_action="HARD_HALT"; zone=Zone.BLOCK
            elif delta<=-5: delta_action="BLOCK_DELTA"; zone=Zone.BLOCK
            elif delta<=-3: delta_action="ALERT"
        if drift_sigma is not None:
            if drift_sigma>3.0: zone=Zone.BLOCK
            elif drift_sigma>2.0 and zone==Zone.PASS: zone=Zone.REVIEW
        return ZoneDecision(score=score,zone=zone,delta=delta,
                            delta_action=delta_action,drift_sigma=drift_sigma)
