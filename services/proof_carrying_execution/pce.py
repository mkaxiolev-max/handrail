"""Proof-Carrying Execution — binds execution output to a verifiable proof."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class ExecutionProof:
    op_id: str
    input_hash: str
    output_hash: str
    proof_id: str
    timestamp: str


class PCEExecutor:
    def __init__(self):
        self._chain: list[ExecutionProof] = []

    @staticmethod
    def _h(obj: Any) -> str:
        return hashlib.sha256(str(obj).encode()).hexdigest()

    def execute_with_proof(self, op_id: str, input_data: Any, fn: Callable) -> tuple[Any, ExecutionProof]:
        ih = self._h(input_data)
        result = fn(input_data)
        oh = self._h(result)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        pid = hashlib.sha256(f"{op_id}{ih}{oh}{ts}".encode()).hexdigest()[:16]
        proof = ExecutionProof(op_id, ih, oh, pid, ts)
        self._chain.append(proof)
        return result, proof

    def verify_proof(self, proof: ExecutionProof, input_data: Any, result: Any) -> bool:
        return (proof.input_hash == self._h(input_data) and
                proof.output_hash == self._h(result))

    def get_proof_chain(self) -> list[ExecutionProof]:
        return list(self._chain)

    def chain_length(self) -> int:
        return len(self._chain)
