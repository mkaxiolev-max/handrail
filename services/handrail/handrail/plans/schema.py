from dataclasses import dataclass,field
from typing import Any,Dict,List,Optional
@dataclass
class RetryPolicy:
 max_attempts:int=1
 backoff_seconds:float=0.0
@dataclass
class StepSpec:
 id:str
 op:str
 input:Dict[str,Any]=field(default_factory=dict)
 condition:Optional[str]=None
 retry:RetryPolicy=field(default_factory=RetryPolicy)
 halt_on_fail:bool=True
@dataclass
class PlanSpec:
 plan_id:str
 version:str
 steps:List[StepSpec]
 metadata:Dict[str,Any]=field(default_factory=dict)
 @classmethod
 def from_dict(cls,data:Dict[str,Any])->"PlanSpec":
  steps=[StepSpec(id=str(raw["id"]),op=str(raw["op"]),input=dict(raw.get("input",{})),condition=raw.get("condition"),retry=RetryPolicy(max_attempts=int(raw.get("retry",{}).get("max_attempts",1)),backoff_seconds=float(raw.get("retry",{}).get("backoff_seconds",0.0))),halt_on_fail=bool(raw.get("halt_on_fail",True)))for raw in data.get("steps",[])]
  return cls(plan_id=str(data["plan_id"]),version=str(data.get("version","1")),steps=steps,metadata=dict(data.get("metadata",{})))
 def validate(self)->None:
  if not self.plan_id:raise ValueError("plan_id required")
  if not self.steps:raise ValueError("at least one step required")
  seen=set()
  for step in self.steps:
   if step.id in seen:raise ValueError(f"duplicate step id: {step.id}")
   seen.add(step.id)
   if not step.op:raise ValueError(f"step {step.id}: op required")
   if step.retry.max_attempts<1:raise ValueError(f"step {step.id}: retry.max_attempts must be >= 1")
