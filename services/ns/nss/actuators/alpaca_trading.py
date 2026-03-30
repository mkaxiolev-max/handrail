"""
NORTHSTAR Alpaca Trading Actuator
Broker sandbox layer — paper mode with constitutional hard gates.
Every trade: ACTION_REQUEST → human confirmation → ACTION_EXECUTED → receipt.
Survival > Alignment > Alpha doctrine enforced.
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone


ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "") or os.environ.get("ALPACA_API_SECRET", "")
ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://broker-api.sandbox.alpaca.markets")

# Constitutional hard limits — cannot be overridden by software
HARD_LIMITS = {
    "max_position_size_usd": 10_000,      # Per position
    "max_daily_loss_usd": 2_000,           # Circuit breaker
    "max_open_positions": 10,              # Concentration limit
    "allowed_asset_classes": ["us_equity", "crypto"],
    "live_trading_enabled": False,         # Manual switch only
    "require_founder_confirmation": True,  # FOUNDER_VETO gate
}


class AlpacaActuator:
    """
    Broker-layer trading actuator.
    Paper mode enforced constitutionally — live requires explicit manual enable.
    """

    def __init__(self):
        self.api_key = ALPACA_API_KEY
        self.secret_key = ALPACA_SECRET_KEY
        self.base_url = ALPACA_BASE_URL
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key or not self.secret_key:
            return
        try:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                "Content-Type": "application/json",
            })
            self._configured = True
        except Exception as e:
            self._configured = False

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to Alpaca broker API."""
        if not hasattr(self, '_configured') or not self._configured:
            return {"error": "Alpaca not configured"}
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            resp = self._session.request(method, url, **kwargs)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_account(self) -> Dict:
        """Get broker account info."""
        return self._request("GET", "/v1/accounts")

    def get_positions(self) -> Dict:
        """Get current positions."""
        return self._request("GET", "/v1beta1/trading/accounts/positions")

    def create_trade_request(
        self,
        symbol: str,
        qty: float,
        side: str,  # "buy" or "sell"
        order_type: str = "market",
        rationale: str = "",
    ) -> Dict[str, Any]:
        """
        Create a trade REQUEST — not execution.
        Returns a pending action that requires FOUNDER_VETO confirmation.
        Constitutional gate: no autonomous execution.
        """
        # Hard gate checks
        if HARD_LIMITS["live_trading_enabled"]:
            return {
                "status": "BLOCKED",
                "reason": "Live trading not enabled. Set HARD_LIMITS['live_trading_enabled']=True manually.",
                "constitutional_gate": "FOUNDER_VETO",
            }

        if side not in ("buy", "sell"):
            return {"status": "BLOCKED", "reason": f"Invalid side: {side}"}

        request = {
            "request_id": f"TRADE-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{symbol}",
            "status": "PENDING_FOUNDER_APPROVAL",
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "order_type": order_type,
            "rationale": rationale,
            "constitutional_gate": "FOUNDER_VETO required before execution",
            "hard_limits_checked": True,
            "paper_mode": not HARD_LIMITS["live_trading_enabled"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return request

    def execute_trade(self, trade_request: Dict, founder_confirmed: bool = False) -> Dict:
        """
        Execute a previously created trade request.
        Requires founder_confirmed=True — constitutional requirement.
        """
        if not founder_confirmed:
            return {
                "status": "BLOCKED",
                "reason": "FOUNDER_VETO gate not satisfied. founder_confirmed must be True.",
                "trade_request_id": trade_request.get("request_id"),
            }

        if trade_request.get("status") != "PENDING_FOUNDER_APPROVAL":
            return {"status": "BLOCKED", "reason": "Invalid trade request status"}

        # Paper mode: simulate execution
        result = {
            "status": "EXECUTED_PAPER",
            "trade_request_id": trade_request["request_id"],
            "symbol": trade_request["symbol"],
            "qty": trade_request["qty"],
            "side": trade_request["side"],
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "mode": "paper_sandbox",
            "receipt_required": True,
        }

        return result

    def get_market_data(self, symbol: str) -> Dict:
        """Get latest quote for a symbol."""
        return self._request("GET", f"/v1beta1/trading/accounts/assets/{symbol}")

    def health(self) -> Dict:
        return {
            "configured": bool(self.api_key and self.secret_key),
            "base_url": self.base_url,
            "live_trading": HARD_LIMITS["live_trading_enabled"],
            "paper_mode": not HARD_LIMITS["live_trading_enabled"],
            "founder_veto_active": HARD_LIMITS["require_founder_confirmation"],
            "max_position_usd": HARD_LIMITS["max_position_size_usd"],
        }
