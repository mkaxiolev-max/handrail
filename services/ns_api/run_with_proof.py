from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable
from app.domain.models import IntentPacket, ProofReceipt
from app.infra.chain import get_chain

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def run_with_proof(
    *, event_type: str, intent_packet, actor: str,
    execute_fn: Callable[[], Awaitable[dict]],
    memory_writer_fn=None, compute_meta: dict | None = None,
) -> dict[str, Any]:
    chain = get_chain()
    prev_hash = chain.last_hash()
    result = await execute_fn()
    memory_refs: list[str] = []
    if memory_writer_fn is not None:
        memory_refs = await memory_writer_fn(result)
    payload = {"actor": actor, "event_type": event_type, "result": result,
               "memory_refs": memory_refs, "compute_meta": compute_meta or {},
               "intent_packet_id": str(intent_packet.id) if intent_packet else None}
    proof = ProofReceipt(event=event_type, payload=json.dumps(payload),
                         prev_hash=prev_hash, timestamp=utc_now_iso(), hash="")
    proof.hash = proof.content_hash()
    chain.append(proof)
    return {"result": result, "receipt_hash": proof.hash, "prev_hash": prev_hash,
            "memory_refs": memory_refs, "event_type": event_type, "actor": actor}
