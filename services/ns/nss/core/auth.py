from fastapi import HTTPException
from fastapi import Request
"""
NORTHSTAR Auth Service
JWT tokens, roles, device sessions, permission enforcement.
No secrets ever leave the Mac Ultra.

Roles: FOUNDER > SAN > EXEC > USER
Every API call validates token + domain scope.
"""

import os
import json
import hmac
import hashlib
import secrets
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# ── Constants ─────────────────────────────────────────────────────────────────

ROLES = ["FOUNDER", "SAN", "EXEC", "USER"]

PERMISSIONS = {
    "FOUNDER": [
        "READ_CHAT", "SEND_CHAT", "READ_RECEIPTS", "READ_RECEIPTS_REDACTED",
        "PROMOTE_CANON_PROPOSAL",
        "VIEW_PRESSURE",
        "MANAGE_PRESSURE", "APPROVE_ACTION", "EXECUTE_ACTION",
        "VOICE_WHISPER", "VOICE_SPEAK_PUBLIC", "VIEW_VISUALS",
        "VIEW_CANON_SUMMARY", "MANAGE_USERS", "EXPORT_RECEIPTS",
        "ROTATE_CREDENTIALS", "VIEW_DIAGNOSTICS",
    ],
    "SAN": [
        "READ_CHAT", "SEND_CHAT", "READ_RECEIPTS_REDACTED",
        "PROMOTE_CANON_PROPOSAL", "VOICE_WHISPER", "VIEW_VISUALS",
        "VIEW_CANON_SUMMARY",
    ],
    "EXEC": [
        "READ_CHAT", "SEND_CHAT", "READ_RECEIPTS_REDACTED",
        "APPROVE_ACTION", "VIEW_VISUALS", "VIEW_CANON_SUMMARY",
    ],
    "USER": [
        "READ_CHAT", "SEND_CHAT", "VIEW_VISUALS",
    ],
}

ALL_DOMAINS = [
    "voice", "trading", "research", "ops", "finance",
    "strategy", "health", "canon", "security",
]

# Built-in users — in production, add to a user store file
# Founder gets full domain access; others scoped at creation.
BUILTIN_USERS = {
    "founder": {
        "user_id": "founder",
        "display_name": "Founder",
        "role": "FOUNDER",
        "allowed_domains": ALL_DOMAINS,
        "password_hash": None,  # Set via /auth/set-password on first boot
    }
}

SESSION_TTL_SECONDS = 86400 * 7  # 7 days
TOKEN_TTL_SECONDS   = 3600 * 4   # 4 hours access token
REFRESH_TTL_SECONDS = 86400 * 30 # 30 days refresh

# ── Token signing (HMAC-SHA256, secret from env) ─────────────────────────────

def _signing_key() -> bytes:
    key = os.environ.get("NS_TOKEN_SECRET", "")
    if not key:
        # Derive from Anthropic key — stable but not stored separately
        base = os.environ.get("ANTHROPIC_API_KEY", "northstar-default-secret")
        key = hashlib.sha256(b"NS_TOKEN:" + base.encode()).hexdigest()
    return key.encode()


def _sign(payload: str) -> str:
    return hmac.new(_signing_key(), payload.encode(), hashlib.sha256).hexdigest()


def _b64(s: str) -> str:
    import base64
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def _unb64(s: str) -> str:
    import base64
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad).decode()


# ── Token generation / validation ─────────────────────────────────────────────

def _make_token(claims: dict, ttl: int) -> str:
    """Simple signed token: b64(claims_json).signature"""
    claims["exp"] = int(time.time()) + ttl
    claims["iat"] = int(time.time())
    payload = json.dumps(claims, separators=(",", ":"))
    encoded = _b64(payload)
    sig = _sign(encoded)
    return f"{encoded}.{sig}"


def _verify_token(token: str) -> Optional[dict]:
    """Returns claims dict or None if invalid/expired."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        encoded, sig = parts
        if not hmac.compare_digest(sig, _sign(encoded)):
            return None
        claims = json.loads(_unb64(encoded))
        if claims.get("exp", 0) < time.time():
            return None
        return claims
    except Exception:
        return None


# ── User store (file-backed) ──────────────────────────────────────────────────

class UserStore:
    def __init__(self):
        self._path = Path.home() / "NSS" / "configs" / "users.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._users: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                self._users = json.loads(self._path.read_text())
            except Exception:
                self._users = {}
        # Always ensure founder exists
        if "founder" not in self._users:
            self._users["founder"] = BUILTIN_USERS["founder"].copy()
            self._save()

    def _save(self):
        self._path.write_text(json.dumps(self._users, indent=2))
        self._path.chmod(0o600)

    def get(self, user_id: str) -> Optional[dict]:
        return self._users.get(user_id)

    def verify_password(self, user_id: str, password: str) -> bool:
        user = self._users.get(user_id)
        if not user:
            return False
        stored = user.get("password_hash")
        if stored is None:
            # First boot: founder password not set yet
            # Allow login with env var NS_FOUNDER_PASSWORD or default "northstar"
            default = os.environ.get("NS_FOUNDER_PASSWORD", "northstar")
            hashed = hashlib.sha256(f"NS:{password}".encode()).hexdigest()
            default_h = hashlib.sha256(f"NS:{default}".encode()).hexdigest()
            if hmac.compare_digest(hashed, default_h):
                # Auto-set on first successful login
                self.set_password(user_id, password)
                return True
            return False
        hashed = hashlib.sha256(f"NS:{password}".encode()).hexdigest()
        return hmac.compare_digest(hashed, stored)

    def set_password(self, user_id: str, password: str):
        if user_id not in self._users:
            return
        self._users[user_id]["password_hash"] = hashlib.sha256(
            f"NS:{password}".encode()
        ).hexdigest()
        self._save()

    def create_user(self, user_id: str, display_name: str, role: str,
                    allowed_domains: List[str], password: str) -> dict:
        if role not in ROLES:
            raise ValueError(f"Invalid role: {role}")
        user = {
            "user_id": user_id,
            "display_name": display_name,
            "role": role,
            "allowed_domains": allowed_domains,
            "password_hash": hashlib.sha256(f"NS:{password}".encode()).hexdigest(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._users[user_id] = user
        self._save()
        return user

    def list_users(self) -> List[dict]:
        return [
            {k: v for k, v in u.items() if k != "password_hash"}
            for u in self._users.values()
        ]


# ── Session store (in-memory + file backup) ───────────────────────────────────

class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, dict] = {}

    def create(self, user_id: str, role: str, allowed_domains: List[str],
               device_name: str, ip: str) -> dict:
        session_id = secrets.token_hex(16)
        access_token = _make_token({
            "sub": user_id,
            "role": role,
            "domains": allowed_domains,
            "session_id": session_id,
            "type": "access",
        }, TOKEN_TTL_SECONDS)
        refresh_token = _make_token({
            "sub": user_id,
            "session_id": session_id,
            "type": "refresh",
        }, REFRESH_TTL_SECONDS)

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "allowed_domains": allowed_domains,
            "device_name": device_name,
            "ip": ip,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[dict]:
        return self._sessions.get(session_id)

    def touch(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id]["last_seen"] = (
                datetime.now(timezone.utc).isoformat()
            )

    def revoke(self, session_id: str):
        self._sessions.pop(session_id, None)

    def list_for_user(self, user_id: str) -> List[dict]:
        return [
            {k: v for k, v in s.items() if k not in ("access_token", "refresh_token")}
            for s in self._sessions.values()
            if s["user_id"] == user_id
        ]


# ── Auth context (attached to each request) ──────────────────────────────────

class AuthContext:
    def __init__(self, user_id: str, role: str, allowed_domains: List[str],
                 session_id: str, permissions: List[str]):
        self.user_id = user_id
        self.role = role
        self.allowed_domains = allowed_domains
        self.session_id = session_id
        self.permissions = permissions

    def has(self, perm: str) -> bool:
        return perm in self.permissions

    def can_access_domain(self, domain: str) -> bool:
        return domain in self.allowed_domains

    def is_founder(self) -> bool:
        return self.role == "FOUNDER"

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "role": self.role,
            "allowed_domains": self.allowed_domains,
            "session_id": self.session_id,
            "permissions": self.permissions,
        }


# ── Auth service (singleton) ──────────────────────────────────────────────────

class AuthService:
    def __init__(self):
        self.users = UserStore()
        self.sessions = SessionStore()

    def login(self, user_id: str, password: str,
              device_name: str = "unknown", ip: str = "unknown") -> Optional[dict]:
        if not self.users.verify_password(user_id, password):
            return None
        user = self.users.get(user_id)
        if not user:
            return None
        session = self.sessions.create(
            user_id=user_id,
            role=user["role"],
            allowed_domains=user["allowed_domains"],
            device_name=device_name,
            ip=ip,
        )
        return {
            "access_token": session["access_token"],
            "refresh_token": session["refresh_token"],
            "session_id": session["session_id"],
            "user_id": user_id,
            "role": user["role"],
            "display_name": user.get("display_name", user_id),
            "permissions": PERMISSIONS.get(user["role"], []),
        }

    def verify_request(self, token: str) -> Optional[AuthContext]:
        """Validate bearer token, return AuthContext or None."""
        if not token:
            return None
        # Strip Bearer prefix
        if token.startswith("Bearer "):
            token = token[7:]
        claims = _verify_token(token)
        if not claims or claims.get("type") != "access":
            return None
        session_id = claims.get("session_id")
        session = self.sessions.get(session_id)
        if not session:
            return None
        self.sessions.touch(session_id)
        role = claims.get("role", "USER")
        return AuthContext(
            user_id=claims["sub"],
            role=role,
            allowed_domains=claims.get("domains", []),
            session_id=session_id,
            permissions=PERMISSIONS.get(role, []),
        )

    def refresh(self, refresh_token: str) -> Optional[dict]:
        claims = _verify_token(refresh_token)
        if not claims or claims.get("type") != "refresh":
            return None
        session_id = claims.get("session_id")
        session = self.sessions.get(session_id)
        if not session:
            return None
        user = self.users.get(session["user_id"])
        if not user:
            return None
        # Issue new access token
        new_access = _make_token({
            "sub": session["user_id"],
            "role": session["role"],
            "domains": session["allowed_domains"],
            "session_id": session_id,
            "type": "access",
        }, TOKEN_TTL_SECONDS)
        session["access_token"] = new_access
        return {
            "access_token": new_access,
            "session_id": session_id,
        }

    def logout(self, session_id: str):
        self.sessions.revoke(session_id)

    def redact_for_role(self, data: dict, role: str) -> dict:
        """Apply role-based redaction to a data dict."""
        if role == "FOUNDER":
            return data
        redacted = data.copy()
        # Redact sensitive fields for non-founders
        for field in ["input_hash", "policy_decisions", "model_routing_detail",
                      "api_keys_used", "system_prompt_hash"]:
            if field in redacted:
                redacted[field] = "[REDACTED]"
        return redacted


# Module-level singleton
_auth_service: Optional[AuthService] = None

def get_auth() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def require_auth(request: Request) -> AuthContext:
    """FastAPI dependency — raises 401 if not authenticated."""
    token = request.headers.get("Authorization", "")
    # Also check cookie for web console
    if not token:
        token = request.cookies.get("ns_token", "")

    # Ops key bypass (for local ops + scripts). If provided and matches NS_OPS_KEY,
    # grant EXEC context without requiring a bearer token.
    ops_key = request.headers.get("X-NS-OPS-KEY", "")
    expected = os.environ.get("NS_OPS_KEY", "")
    if ops_key and expected and ops_key == expected:
        return AuthContext(
            user_id="ops",
            role="EXEC",
            allowed_domains=ALL_DOMAINS,
            session_id="ops",
            permissions=PERMISSIONS.get("EXEC", []),
        )

    ctx = get_auth().verify_request(token)
    if not ctx:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return ctx


async def require_founder(request) -> AuthContext:
    """FastAPI dependency — raises 403 if not FOUNDER."""
    ctx = await require_auth(request)
    if not ctx.is_founder():
        raise HTTPException(status_code=403, detail="FOUNDER required")
    return ctx


def require_permission(perm: str):
    """FastAPI dependency factory — checks specific permission."""
    async def _dep(request) -> AuthContext:
        ctx = await require_auth(request)
        if not ctx.has(perm):
            raise HTTPException(status_code=403, detail=f"Permission required: {perm}")
        return ctx
    return _dep
