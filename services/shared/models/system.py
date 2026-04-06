from typing import Optional
from datetime import datetime
from .base import StrictModel, TimestampedModel, utc_now
from .enums import SystemTier, RiskTier


class ServiceHealth(StrictModel):
    service: str
    healthy: bool
    url: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    checked_at: datetime = None

    def model_post_init(self, __context):
        if self.checked_at is None:
            object.__setattr__(self, "checked_at", utc_now())


class SystemState(StrictModel):
    tier: SystemTier = SystemTier.ACTIVE
    boot_id: Optional[str] = None
    boot_proof_hash: Optional[str] = None
    services: list[ServiceHealth] = []
    ops_loaded: int = 0
    programs_loaded: int = 0
    yubikey_serials: list[str] = []
    alexandria_mounted: bool = False
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


class TimelineEvent(StrictModel):
    event_id: str
    event_type: str
    summary: str
    risk_tier: RiskTier = RiskTier.R0
    receipt_id: Optional[str] = None
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


class FocusState(StrictModel):
    active_program: Optional[str] = None
    active_intent: Optional[str] = None
    pending_approvals: list[str] = []
    unresolved_risks: list[str] = []


class FailureOverlay(StrictModel):
    failure_id: str
    op: str
    error: str
    risk_tier: RiskTier = RiskTier.R0
    resolved: bool = False
    timestamp: datetime = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())
