"""
adapter.v1 Contract Layer
=========================
Normalized request/response envelopes for all macOS adapter namespaces.
All adapters MUST return AdapterResponse. No contract drift allowed.

Namespaces: env.* | window.* | input.* | vision.* | fs.*
"""
from __future__ import annotations
import hashlib, json, time, uuid
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class OperationStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    DENIED  = "denied"   # dignity_kernel blocked this op


class AdapterRequest(BaseModel):
    run_id:    str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    method:    str                      # "namespace.action"  e.g. "window.list"
    params:    dict[str, Any] = {}


class AdapterResponse(BaseModel):
    run_id:    str
    action_id: str
    method:    str
    status:    OperationStatus
    data:      Optional[dict[str, Any]] = None
    artifacts: list[str] = []           # paths to proof artifacts
    error:     Optional[str] = None
    latency_ms: int = 0
    state_hash: str = ""                # SHA-256 of data for lineage

    @classmethod
    def success(cls, req: AdapterRequest, data: dict, artifacts: list[str] = [],
                latency_ms: int = 0) -> "AdapterResponse":
        payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return cls(
            run_id=req.run_id,
            action_id=req.action_id,
            method=req.method,
            status=OperationStatus.SUCCESS,
            data=data,
            artifacts=artifacts,
            latency_ms=latency_ms,
            state_hash="sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:16],
        )

    @classmethod
    def failure(cls, req: AdapterRequest, error: str,
                latency_ms: int = 0) -> "AdapterResponse":
        return cls(
            run_id=req.run_id,
            action_id=req.action_id,
            method=req.method,
            status=OperationStatus.FAILURE,
            error=error,
            latency_ms=latency_ms,
            state_hash="",
        )

    @classmethod
    def denied(cls, req: AdapterRequest, reason: str) -> "AdapterResponse":
        return cls(
            run_id=req.run_id,
            action_id=req.action_id,
            method=req.method,
            status=OperationStatus.DENIED,
            error=f"DIGNITY_KERNEL_DENIED: {reason}",
            state_hash="",
        )
