"""
Adapter Registry
================
Routes method namespace → concrete handler.
Adding a new adapter = registering its namespace prefix here.
The CPS engine never changes. Only this registry grows.

Current drivers:
  env.*            → MacOSEnvAdapter
  window.*         → MacOSWindowAdapter
  input.*          → MacOSInputAdapter
  vision.*         → MacOSVisionAdapter
  fs.*             → MacOSFSAdapter
  network.*        → NetworkAdapter       (http_get, port_check, dns_resolve)
  proc_extended.*  → ProcExtendedAdapter  (list_processes, kill_pid, get_memory_usage)
  file_watch.*     → FileWatchAdapter     (watch_path, read_recent_changes)
"""
from __future__ import annotations
import time
from typing import Callable, Awaitable
from .contract import AdapterRequest, AdapterResponse, OperationStatus


HandlerFn = Callable[[AdapterRequest], Awaitable[AdapterResponse]]


class AdapterRegistry:
    """Namespace → handler routing table. Thread-safe (read-mostly)."""

    def __init__(self):
        self._handlers: dict[str, HandlerFn] = {}

    def register(self, method: str, fn: HandlerFn) -> None:
        """Register a handler for an exact method string."""
        self._handlers[method] = fn

    def register_all(self, mapping: dict[str, HandlerFn]) -> None:
        self._handlers.update(mapping)

    async def dispatch(self, req: AdapterRequest) -> AdapterResponse:
        """Route request to handler; wrap timing; normalize errors."""
        fn = self._handlers.get(req.method)
        if fn is None:
            return AdapterResponse(
                run_id=req.run_id,
                action_id=req.action_id,
                method=req.method,
                status=OperationStatus.FAILURE,
                error=f"UNREGISTERED_METHOD: {req.method}",
                state_hash="",
            )
        t0 = time.monotonic()
        try:
            resp = await fn(req)
            resp.latency_ms = int((time.monotonic() - t0) * 1000)
            return resp
        except Exception as exc:
            return AdapterResponse.failure(
                req,
                error=f"HANDLER_EXCEPTION: {type(exc).__name__}: {exc}",
                latency_ms=int((time.monotonic() - t0) * 1000),
            )

    def available_methods(self) -> list[str]:
        return sorted(self._handlers.keys())
