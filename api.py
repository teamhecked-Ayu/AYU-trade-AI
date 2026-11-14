from fastapi import FastAPI, HTTPException, Header, Request
import time
import hmac
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.paper_portfolio import PaperPortfolio
from core.portfolio_store import SQLitePortfolioStore
import os
from utils.health import HealthState

app = FastAPI(title="AYU Trade AI API", version="0.1.0")
API_KEY = os.getenv("AYU_API_KEY")
_rate_state = {}
store = SQLitePortfolioStore(os.getenv("PAPER_PORTFOLIO_DB", "data/paper_portfolio.db"))
portfolio = store.load()
health_state = HealthState()


class PaperOrder(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float


@app.get("/health")
async def health():
    return {**health_state.snapshot(), "mode": "paper"}


@app.get("/metrics")
async def metrics(x_api_key: str | None = Header(default=None)):
    await require_api_key(x_api_key)
    return {
        "trade_count": len(portfolio.trades),
        "position_count": len([p for p in portfolio.positions.values() if p.quantity != 0]),
        "cash": portfolio.cash,
    }


async def require_api_key(x_api_key: str | None = Header(default=None)):
    if not API_KEY:
        raise HTTPException(status_code=503, detail="API key is not configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    client = request.client.host if request.client else "unknown"
    now = time.time()
    hits = [t for t in _rate_state.get(client, []) if now - t < 60]
    if len(hits) >= 60:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    hits.append(now)
    _rate_state[client] = hits
    return await call_next(request)


@app.get("/portfolio")
async def get_portfolio(x_api_key: str | None = Header(default=None)):
    await require_api_key(x_api_key)
    return {
        "cash": portfolio.cash,
        "positions": {k: vars(v) for k, v in portfolio.positions.items()},
        "trades": portfolio.trades[-100:],
    }


@app.post("/paper/orders")
async def paper_order(order: PaperOrder, x_api_key: str | None = Header(default=None)):
    await require_api_key(x_api_key)
    try:
        result = portfolio.execute(
            order.symbol, order.side.lower(), order.quantity, order.price
        )
        store.save(portfolio)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
