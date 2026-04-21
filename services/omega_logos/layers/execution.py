"""Execution layer — task graph, retry, abstention.
AXIOLEV Holdings LLC © 2026. (Maps to I₆.C3 — plan_to_execution_fidelity + receipt_completeness.)"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

@dataclass
class Task:
    id: str
    op: str                    # operation name (registered in CPS adapter registry)
    args: Dict = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"    # pending | running | ok | failed | abstained
    retries: int = 0

class Executor:
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def run(self, task: Task, fn: Callable[[Dict], Dict]) -> Dict:
        while True:
            task.status = "running"
            try:
                out = fn(task.args)
                task.status = "ok"
                return {"ok": True, "output": out, "retries": task.retries}
            except Exception as e:
                task.retries += 1
                if task.retries > self.max_retries:
                    task.status = "abstained"
                    return {"ok": False, "abstained": True, "error": str(e), "retries": task.retries}
