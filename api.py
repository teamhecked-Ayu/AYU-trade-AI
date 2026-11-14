from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.paper_portfolio import PaperPortfolio

app = FastAPI(title="AYU Trade AI API", version="0.1.0")
portfolio = PaperPortfolio()


class PaperOrder(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "paper"}


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
        return portfolio.execute(
            order.symbol, order.side.lower(), order.quantity, order.price
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
