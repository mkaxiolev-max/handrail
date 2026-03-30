"""
NORTHSTAR WebSocket Event Bus
Real-time streaming to all connected consoles (web + native).

Server emits:
  health.update, chat.message.new, chat.card.new,
  receipt.new, approval.pending, visual.new,
  action.status, canon.proposal.update,
  voice.partial_transcript (Phase 2), voice.coach.suggestion (Phase 2)

Client emits:
  chat.send, approval.respond, request.history

Role filtering applied before broadcast — roles never see above their tier.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, WebSocketDisconnect


# ── Connection registry ───────────────────────────────────────────────────────

class WSConnection:
    def __init__(self, ws: WebSocket, user_id: str, role: str,
                 session_id: str, allowed_domains: List[str]):
        self.ws = ws
        self.user_id = user_id
        self.role = role
        self.session_id = session_id
        self.allowed_domains = allowed_domains
        self.connected_at = datetime.now(timezone.utc).isoformat()
        self.subscriptions: Set[str] = {"*"}  # Subscribe to all by default

    async def send(self, event: str, data: dict):
        try:
            await self.ws.send_text(json.dumps({
                "event": event,
                "data": data,
                "ts": datetime.now(timezone.utc).isoformat(),
            }))
        except Exception:
            pass  # Connection may have dropped


class EventBus:
    """
    Central WebSocket event bus.
    All server-side events route through here.
    Role filtering applied before delivery.
    """

    def __init__(self):
        self._connections: Dict[str, WSConnection] = {}  # session_id → connection
        self._lock = asyncio.Lock()

    async def connect(self, conn: WSConnection):
        async with self._lock:
            self._connections[conn.session_id] = conn
        # Send welcome
        await conn.send("system.connected", {
            "user_id": conn.user_id,
            "role": conn.role,
            "connection_count": len(self._connections),
            "message": "NS Core connected. Event stream active.",
        })

    async def disconnect(self, session_id: str):
        async with self._lock:
            self._connections.pop(session_id, None)

    async def broadcast(self, event: str, data: dict,
                        min_role: Optional[str] = None,
                        user_id: Optional[str] = None,
                        domain: Optional[str] = None):
        """
        Broadcast event to all matching connections.
        Filters by role, user_id, domain as specified.
        """
        ROLE_RANK = {"FOUNDER": 4, "SAN": 3, "EXEC": 2, "USER": 1}
        min_rank = ROLE_RANK.get(min_role, 0) if min_role else 0

        dead = []
        async with self._lock:
            targets = list(self._connections.values())

        for conn in targets:
            # Filter by specific user
            if user_id and conn.user_id != user_id:
                continue
            # Filter by minimum role
            if ROLE_RANK.get(conn.role, 0) < min_rank:
                continue
            # Filter by domain access
            if domain and domain not in conn.allowed_domains:
                continue

            # Apply role-based redaction to data
            redacted_data = _redact_for_role(data, conn.role)
            try:
                await conn.send(event, redacted_data)
            except Exception:
                dead.append(conn.session_id)

        # Clean up dead connections
        if dead:
            async with self._lock:
                for sid in dead:
                    self._connections.pop(sid, None)

    async def emit_to(self, session_id: str, event: str, data: dict):
        """Send to specific connection only."""
        conn = self._connections.get(session_id)
        if conn:
            await conn.send(event, data)

    def connection_count(self) -> int:
        return len(self._connections)

    def connections_info(self) -> List[dict]:
        return [
            {
                "user_id": c.user_id,
                "role": c.role,
                "session_id": c.session_id,
                "connected_at": c.connected_at,
            }
            for c in self._connections.values()
        ]


def _redact_for_role(data: dict, role: str) -> dict:
    """Strip sensitive fields based on role."""
    if role == "FOUNDER":
        return data
    redacted = {**data}
    SENSITIVE = ["input_hash", "output_hash", "policy_decisions",
                 "model_routing_detail", "system_prompt", "raw_model_output",
                 "api_cost_estimate"]
    for field in SENSITIVE:
        if field in redacted:
            redacted[field] = "[REDACTED]"
    return redacted


# ── Chat message store (in-memory, receipted to Alexandria) ──────────────────

class ChatStore:
    def __init__(self):
        self._sessions: Dict[str, List[dict]] = {}
        self._session_meta: Dict[str, dict] = {}

    def new_session(self, session_id: str, user_id: str,
                    title: str = "New session") -> dict:
        self._sessions[session_id] = []
        meta = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "message_count": 0,
        }
        self._session_meta[session_id] = meta
        return meta

    def add_message(self, session_id: str, message: dict) -> dict:
        if session_id not in self._sessions:
            self.new_session(session_id, message.get("user_id", "system"))
        self._sessions[session_id].append(message)
        meta = self._session_meta.get(session_id, {})
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        meta["message_count"] = len(self._sessions[session_id])
        return message

    def get_session(self, session_id: str,
                    limit: int = 50, offset: int = 0) -> List[dict]:
        msgs = self._sessions.get(session_id, [])
        return msgs[-(limit + offset):][-limit:] if limit else msgs

    def list_sessions(self, user_id: Optional[str] = None) -> List[dict]:
        sessions = list(self._session_meta.values())
        if user_id:
            sessions = [s for s in sessions if s["user_id"] == user_id]
        return sorted(sessions, key=lambda s: s["updated_at"], reverse=True)

    def rename_session(self, session_id: str, title: str):
        if session_id in self._session_meta:
            self._session_meta[session_id]["title"] = title


# ── Approval store ────────────────────────────────────────────────────────────

class ApprovalStore:
    def __init__(self):
        self._approvals: Dict[str, dict] = {}

    def create(self, action_summary: str, risk_tier: str,
               domain: str, proposed_by: str,
               confirm_phrase: str, nonce: str) -> dict:
        import secrets
        approval_id = secrets.token_hex(8)
        approval = {
            "approval_id": approval_id,
            "action_summary": action_summary,
            "risk_tier": risk_tier,
            "domain": domain,
            "proposed_by": proposed_by,
            "confirm_phrase": confirm_phrase,
            "nonce": nonce,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_at": None,
            "resolved_by": None,
            "resolution": None,
        }
        self._approvals[approval_id] = approval
        return approval

    def get(self, approval_id: str) -> Optional[dict]:
        return self._approvals.get(approval_id)

    def pending(self) -> List[dict]:
        return [a for a in self._approvals.values() if a["status"] == "pending"]

    def resolve(self, approval_id: str, resolved_by: str,
                resolution: str, nonce_provided: str) -> Optional[dict]:
        approval = self._approvals.get(approval_id)
        if not approval or approval["status"] != "pending":
            return None
        if nonce_provided != approval["nonce"]:
            return None
        approval["status"] = resolution  # "approved" | "denied"
        approval["resolved_at"] = datetime.now(timezone.utc).isoformat()
        approval["resolved_by"] = resolved_by
        approval["resolution"] = resolution
        return approval


# ── Visual store ──────────────────────────────────────────────────────────────

class VisualStore:
    def __init__(self):
        self._visuals: Dict[str, dict] = {}

    def add(self, visual_id: str, visual_type: str, svg_content: str,
            session_id: str, label: str = "",
            shareable: bool = False) -> dict:
        visual = {
            "visual_id": visual_id,
            "visual_type": visual_type,
            "svg_content": svg_content,
            "session_id": session_id,
            "label": label,
            "shareable": shareable,
            "pinned": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._visuals[visual_id] = visual
        return visual

    def get(self, visual_id: str) -> Optional[dict]:
        return self._visuals.get(visual_id)

    def list_for_session(self, session_id: str) -> List[dict]:
        return [v for v in self._visuals.values() if v["session_id"] == session_id]

    def mark_shareable(self, visual_id: str):
        if visual_id in self._visuals:
            self._visuals[visual_id]["shareable"] = True

    def pin(self, visual_id: str):
        if visual_id in self._visuals:
            self._visuals[visual_id]["pinned"] = True


# ── Canon proposal store ──────────────────────────────────────────────────────

class CanonStore:
    def __init__(self):
        self._proposals: Dict[str, dict] = {}

    def propose(self, title: str, content: str, proposed_by: str,
                domains_affected: List[str]) -> dict:
        import secrets
        pid = secrets.token_hex(6)
        proposal = {
            "proposal_id": pid,
            "title": title,
            "content": content,
            "proposed_by": proposed_by,
            "domains_affected": domains_affected,
            "status": "proposed",
            "votes": {},
            "dissent_notes": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ratified_at": None,
            "expires_at": None,
        }
        self._proposals[pid] = proposal
        return proposal

    def vote(self, proposal_id: str, voter: str, vote: str, note: str = "") -> bool:
        p = self._proposals.get(proposal_id)
        if not p or p["status"] != "proposed":
            return False
        p["votes"][voter] = vote
        if vote == "dissent" and note:
            p["dissent_notes"].append({"voter": voter, "note": note,
                                       "ts": datetime.now(timezone.utc).isoformat()})
        return True

    def ratify(self, proposal_id: str, ratified_by: str) -> Optional[dict]:
        p = self._proposals.get(proposal_id)
        if not p:
            return None
        p["status"] = "canonical"
        p["ratified_at"] = datetime.now(timezone.utc).isoformat()
        p["ratified_by"] = ratified_by
        return p

    def expire(self, proposal_id: str) -> Optional[dict]:
        p = self._proposals.get(proposal_id)
        if not p:
            return None
        p["status"] = "expired"
        p["expires_at"] = datetime.now(timezone.utc).isoformat()
        return p

    def list_proposals(self, status: Optional[str] = None) -> List[dict]:
        proposals = list(self._proposals.values())
        if status:
            proposals = [p for p in proposals if p["status"] == status]
        return sorted(proposals, key=lambda p: p["created_at"], reverse=True)


# ── Module-level singletons ───────────────────────────────────────────────────

_bus: Optional[EventBus] = None
_chat: Optional[ChatStore] = None
_approvals: Optional[ApprovalStore] = None
_visuals: Optional[VisualStore] = None
_canon: Optional[CanonStore] = None


def get_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def get_chat() -> ChatStore:
    global _chat
    if _chat is None:
        _chat = ChatStore()
    return _chat


def get_approvals() -> ApprovalStore:
    global _approvals
    if _approvals is None:
        _approvals = ApprovalStore()
    return _approvals


def get_visuals() -> VisualStore:
    global _visuals
    if _visuals is None:
        _visuals = VisualStore()
    return _visuals


def get_canon_store() -> CanonStore:
    global _canon
    if _canon is None:
        _canon = CanonStore()
    return _canon
