from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Dict
import hashlib, statistics

@dataclass
class ReplicaVerdict:
    replica_id: str; decision_id: str; score: float; zone: str
    signature: str; parent_hash: str; timestamp: float

class ReplicationCoordinator:
    def __init__(self, alpha_target=0.80, window_size=1000):
        self.alpha_target=alpha_target; self.window_size=window_size
        self.verdict_pairs: List[Tuple[ReplicaVerdict,ReplicaVerdict]]=[]

    def record_pair(self, primary: ReplicaVerdict, secondary: ReplicaVerdict):
        self.verdict_pairs.append((primary,secondary))
        if len(self.verdict_pairs)>self.window_size: self.verdict_pairs.pop(0)

    def krippendorff_alpha(self) -> float:
        if not self.verdict_pairs: return 1.0
        zone_pairs=[(p.zone,s.zone) for p,s in self.verdict_pairs]
        n=len(zone_pairs)
        disagreement=sum(1 for z1,z2 in zone_pairs if z1!=z2)/n
        all_zones=[z for pair in zone_pairs for z in pair]
        zone_counts={}
        for z in all_zones: zone_counts[z]=zone_counts.get(z,0)+1
        total=len(all_zones)
        expected_agreement=sum((c/total)**2 for c in zone_counts.values())
        expected_disagreement=1-expected_agreement
        if expected_disagreement==0: return 1.0
        return 1.0-(disagreement/expected_disagreement)

    def quorum_verdict(self, primary: ReplicaVerdict, secondary: ReplicaVerdict) -> Dict:
        if primary.zone==secondary.zone:
            qc=hashlib.sha256((primary.signature+secondary.signature).encode()).hexdigest()
            return {"agreement":True,"zone":primary.zone,
                    "score":(primary.score+secondary.score)/2,"quorum_cert":qc,"escalate_to_hic":False}
        return {"agreement":False,"primary_zone":primary.zone,"secondary_zone":secondary.zone,
                "quorum_cert":None,"escalate_to_hic":True,
                "reason":f"zone divergence: {primary.zone} vs {secondary.zone}"}

    def health(self) -> Dict:
        alpha=self.krippendorff_alpha()
        return {"krippendorff_alpha":alpha,"alpha_target":self.alpha_target,
                "alpha_ok":alpha>=self.alpha_target,"sample_size":len(self.verdict_pairs),
                "escalation_required":alpha<self.alpha_target and len(self.verdict_pairs)>=100}
