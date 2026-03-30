"""
NORTHSTAR Overnight Ether Ingest
NS∞ / AXIOLEV Holdings

Runs as background task alongside the FastAPI server.
Continuously ingests raw signal into Alexandria/ether/.

Sources (in priority order):
  1. Market data (Polygon - prices, trades, quotes)
  2. Macro indicators (FRED - economic data)
  3. News (NewsAPI - headlines, sentiment)
  4. Twitter/X (via search API if key present)
  5. Earnings calendar (Polygon)

All ingested data → EtherStore → Alexandria SSD
Receipts emitted for each ingest batch.
Failed sources logged but do not crash the loop.

Schedule:
  Market data:    Every 60s during market hours, 5min otherwise
  FRED:           Every 4 hours
  News:           Every 15 minutes
  Earnings cal:   Every 6 hours
  Overnight syn:  Full sweep every 30 min (market closed)
"""

import os
import json
import asyncio
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nss.core.storage import get_ether, get_cas
from nss.core.receipts import ReceiptChain

# ── Keys ──────────────────────────────────────────────────────────────────────
POLYGON_KEY  = os.environ.get("POLYGON_API_KEY", "")
FRED_KEY     = os.environ.get("FRED_API_KEY", "")
NEWSAPI_KEY  = os.environ.get("NEWSAPI_KEY", "")
ALPACA_KEY   = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET= os.environ.get("ALPACA_API_SECRET", "")

# ── Watchlist (default overnight ingest targets) ──────────────────────────────
EQUITY_WATCHLIST = [
    "SPY", "QQQ", "IWM",          # Market benchmarks
    "AAPL", "MSFT", "NVDA",       # Core tech
    "TSLA", "META", "GOOGL",      # High velocity
    "GLD", "TLT", "VIX",          # Risk indicators
    "BTC-USD", "ETH-USD",         # Crypto
]

FRED_SERIES = [
    "FEDFUNDS",    # Federal funds rate
    "UNRATE",      # Unemployment rate
    "CPIAUCSL",    # CPI
    "GDP",         # GDP
    "T10Y2Y",      # Yield curve (10Y - 2Y)
    "VIXCLS",      # VIX close
    "DXY",         # Dollar index proxy
]

NEWS_QUERIES = [
    "Federal Reserve interest rates",
    "AI artificial intelligence technology",
    "market volatility recession",
    "earnings results guidance",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_market_hours() -> bool:
    """Rough check — ET market hours Mon-Fri 9:30-16:00."""
    now = datetime.now(timezone.utc)
    et_offset = timedelta(hours=-5)  # EST (not DST-aware, close enough)
    et_now = now + et_offset
    if et_now.weekday() >= 5:  # weekend
        return False
    market_open  = et_now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = et_now.replace(hour=16, minute=0,  second=0, microsecond=0)
    return market_open <= et_now <= market_close


def safe_get(url: str, params: dict = None, timeout: int = 10) -> dict:
    """HTTP GET with error handling. Returns {} on failure."""
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"_error": str(e), "_url": url}


def store_event(label: str, data: dict, receipts: ReceiptChain):
    """Store event to ether and emit receipt."""
    ether = get_ether()
    event = {
        "source": label,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    path = ether.store_event(event)
    receipts.emit(
        event_type="ETHER_INGEST",
        source={"kind": "ingest_job", "ref": label},
        inputs={"symbols_or_query": list(data.keys())[:5]},
        outputs={"stored_path": str(path), "record_count": len(data)},
    )
    return path

# ── Ingest Jobs ───────────────────────────────────────────────────────────────

async def ingest_market_prices(receipts: ReceiptChain):
    """Polygon snapshot for all watchlist tickers."""
    if not POLYGON_KEY:
        return
    tickers = ",".join(EQUITY_WATCHLIST[:20])  # Polygon limit
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
    data = safe_get(url, params={"tickers": tickers, "apiKey": POLYGON_KEY})
    if "tickers" in data:
        records = {t["ticker"]: t for t in data["tickers"]}
        store_event("polygon_snapshot", records, receipts)
        print(f"  ✓ Market prices: {len(records)} tickers")
    elif "_error" in data:
        print(f"  ✗ Market prices: {data['_error']}")


async def ingest_crypto_prices(receipts: ReceiptChain):
    """Polygon crypto snapshot."""
    if not POLYGON_KEY:
        return
    for ticker in ["X:BTCUSD", "X:ETHUSD"]:
        url = f"https://api.polygon.io/v2/snapshot/locale/global/markets/crypto/tickers/{ticker}"
        data = safe_get(url, params={"apiKey": POLYGON_KEY})
        if "ticker" in data:
            store_event(f"polygon_crypto_{ticker}", data["ticker"], receipts)
    print(f"  ✓ Crypto prices ingested")


async def ingest_fred_series(receipts: ReceiptChain):
    """FRED macro indicators."""
    if not FRED_KEY:
        return
    results = {}
    for series_id in FRED_SERIES:
        url = "https://api.stlouisfed.org/fred/series/observations"
        data = safe_get(url, params={
            "series_id": series_id,
            "api_key": FRED_KEY,
            "file_type": "json",
            "limit": 10,
            "sort_order": "desc",
        })
        if "observations" in data:
            results[series_id] = data["observations"]
    if results:
        store_event("fred_macro", results, receipts)
        print(f"  ✓ FRED macro: {len(results)} series")


async def ingest_news(receipts: ReceiptChain):
    """NewsAPI headlines across priority queries."""
    if not NEWSAPI_KEY:
        return
    all_articles = []
    for query in NEWS_QUERIES:
        url = "https://newsapi.org/v2/everything"
        data = safe_get(url, params={
            "q": query,
            "apiKey": NEWSAPI_KEY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 10,
        })
        if "articles" in data:
            all_articles.extend(data["articles"])

    if all_articles:
        # Dedupe by URL
        seen = set()
        unique = []
        for a in all_articles:
            url = a.get("url", "")
            if url not in seen:
                seen.add(url)
                unique.append(a)
        store_event("newsapi_headlines", {"articles": unique[:40]}, receipts)
        print(f"  ✓ News: {len(unique)} unique articles")


async def ingest_earnings_calendar(receipts: ReceiptChain):
    """Polygon earnings calendar — next 7 days."""
    if not POLYGON_KEY:
        return
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_out = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    # Polygon earnings endpoint
    url = "https://api.polygon.io/v2/reference/financials"
    data = safe_get(url, params={
        "apiKey": POLYGON_KEY,
        "filing_date.gte": today,
        "filing_date.lte": week_out,
        "limit": 50,
    })
    if "results" in data:
        store_event("polygon_earnings_calendar", {"results": data["results"]}, receipts)
        print(f"  ✓ Earnings calendar: {len(data['results'])} filings")


async def ingest_market_movers(receipts: ReceiptChain):
    """Polygon gainers and losers."""
    if not POLYGON_KEY:
        return
    for direction in ["gainers", "losers"]:
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/{direction}"
        data = safe_get(url, params={"apiKey": POLYGON_KEY})
        if "tickers" in data:
            store_event(f"polygon_{direction}", {"tickers": data["tickers"][:20]}, receipts)
    print(f"  ✓ Market movers ingested")

# ── Ingest Loop ───────────────────────────────────────────────────────────────

async def overnight_ether_loop():
    """
    Main overnight ingest loop.
    Runs continuously in background.
    Market hours: 60s cycle (aggressive)
    Off hours: 5min cycle (overnight accumulation)
    """
    receipts = ReceiptChain()
    cycle = 0

    print("\n  ⚡ Overnight Ether Ingest: ACTIVE")
    print(f"  Alexandria: /Volumes/NSExternal/ALEXANDRIA/ether/")
    print(f"  Watchlist: {len(EQUITY_WATCHLIST)} tickers")
    print(f"  Sources: Polygon + FRED + NewsAPI\n")

    while True:
        cycle += 1
        now = datetime.now(timezone.utc)
        market_open = is_market_hours()
        interval = 60 if market_open else 300  # 1min vs 5min

        print(f"\n  ── Ether Ingest Cycle {cycle} [{now.strftime('%H:%M:%S UTC')}] ──")
        print(f"  Market: {'OPEN' if market_open else 'CLOSED'} | Next: {interval}s")

        try:
            # Always run
            await ingest_market_prices(receipts)
            await ingest_news(receipts)

            # Every 3 cycles
            if cycle % 3 == 0:
                await ingest_crypto_prices(receipts)
                await ingest_market_movers(receipts)

            # Every 12 cycles (~1hr at 5min) or every 60 cycles at 1min
            if cycle % (12 if not market_open else 60) == 0:
                await ingest_fred_series(receipts)
                await ingest_earnings_calendar(receipts)

        except Exception as e:
            print(f"  ✗ Ingest cycle error: {e}")
            # Don't crash. Log and continue.
            receipts.emit(
                event_type="INGEST_ERROR",
                source={"kind": "ingest_job", "ref": "overnight_loop"},
                inputs={"cycle": cycle},
                outputs={"error": str(e)},
            )

        await asyncio.sleep(interval)


def start_ingest_background(app):
    """
    Register overnight ether loop as FastAPI startup task.
    Call this in server.py create_app().
    """
    import asyncio
    from fastapi import FastAPI

    @app.on_event("startup")
    async def start_ether_loop():
        asyncio.create_task(overnight_ether_loop())

    return app
