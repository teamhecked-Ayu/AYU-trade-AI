from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.paper_portfolio import PaperPortfolio
from core.portfolio_store import SQLitePortfolioStore
import os
from utils.health import HealthState

app = FastAPI(title="AYU Trade AI API", version="0.1.0")
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


@app.get("/portfolio")
async def get_portfolio():
    return {
        "cash": portfolio.cash,
        "positions": {k: vars(v) for k, v in portfolio.positions.items()},
        "trades": portfolio.trades[-100:],
    }


@app.post("/paper/orders")
async def paper_order(order: PaperOrder):
    try:
        result = portfolio.execute(
            order.symbol, order.side.lower(), order.quantity, order.price
        )
        store.save(portfolio)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
