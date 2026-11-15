from fastapi import FastAPI, HTTPException, Header, Request
import hmac
import logging
import os

from pydantic import BaseModel

from core.portfolio_store import SQLitePortfolioStore
from utils.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("ayu_trade_ai.api")

app = FastAPI(title="AYU Trade AI Paper API", version="0.3.0")
store = SQLitePortfolioStore(os.getenv("PAPER_PORTFOLIO_DB", "data/paper_portfolio.db"))


class PaperOrder(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "paper"}


@app.get("/ready")
async def ready():
    if not os.getenv("AYU_API_KEY"):
        raise HTTPException(status_code=503, detail="API key is not configured")
    return {"status": "ready", "mode": "paper"}


async def require_api_key(request: Request, x_api_key: str | None = None):
    # Import at request time so paper_api can still be imported independently
    # without creating an api package initialization cycle.
    from api.main import enforce_rate_limit

    await enforce_rate_limit(request, scope="paper")

    configured_api_key = os.getenv("AYU_API_KEY")
    if not configured_api_key:
        raise HTTPException(status_code=503, detail="API key is not configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, configured_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/metrics")
async def metrics(
    request: Request,
    x_api_key: str | None = Header(default=None),
):
    await require_api_key(request, x_api_key)
    portfolio = store.load()
    return {
        "trade_count": len(portfolio.trades),
        "position_count": len([p for p in portfolio.positions.values() if p.quantity != 0]),
        "cash": portfolio.cash,
    }


@app.get("/portfolio")
async def get_portfolio(
    request: Request,
    x_api_key: str | None = Header(default=None),
):
    await require_api_key(request, x_api_key)
    portfolio = store.load()
    return {
        "cash": portfolio.cash,
        "positions": {k: vars(v) for k, v in portfolio.positions.items()},
        "trades": portfolio.trades[-100:],
    }


@app.post("/paper/orders")
async def paper_order(
    order: PaperOrder,
    request: Request,
    x_api_key: str | None = Header(default=None),
):
    await require_api_key(request, x_api_key)
    try:
        result = store.execute(
            order.symbol,
            order.side.lower(),
            order.quantity,
            order.price,
        )
        logger.info(
            "paper_order symbol=%s side=%s quantity=%s price=%s",
            order.symbol,
            order.side,
            order.quantity,
            order.price,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
