"""Paper trading ledger. No broker credentials or live orders are used."""
from __future__ import annotations
from dataclasses import dataclass
import uuid

@dataclass
class PaperPosition:
    symbol: str
    quantity: float
    average_price: float

class PaperBroker:
    def __init__(self, cash: float = 10_000.0, fee_rate: float = 0.001):
        self.cash = cash
        self.fee_rate = fee_rate
        self.positions: dict[str, PaperPosition] = {}
        self.orders: list[dict] = []

    def buy(self, symbol: str, price: float, cash_amount: float) -> dict:
        if cash_amount <= 0 or cash_amount > self.cash or price <= 0:
            raise ValueError("Invalid paper buy order.")
        qty = cash_amount * (1 - self.fee_rate) / price
        self.cash -= cash_amount
        old = self.positions.get(symbol)
        total_qty = qty + (old.quantity if old else 0.0)
        avg = ((old.average_price * old.quantity if old else 0.0) + price * qty) / total_qty
        self.positions[symbol] = PaperPosition(symbol, total_qty, avg)
        order = {"id": str(uuid.uuid4()), "side": "BUY", "symbol": symbol, "price": price, "quantity": qty}
        self.orders.append(order)
        return order

    def sell_all(self, symbol: str, price: float) -> dict:
        pos = self.positions.get(symbol)
        if not pos or price <= 0:
            raise ValueError("No paper position or invalid price.")
        proceeds = pos.quantity * price * (1 - self.fee_rate)
        self.cash += proceeds
        order = {"id": str(uuid.uuid4()), "side": "SELL", "symbol": symbol, "price": price, "quantity": pos.quantity}
        del self.positions[symbol]
        self.orders.append(order)
        return order

    def equity(self, prices: dict[str, float]) -> float:
        return self.cash + sum(p.quantity * prices.get(s, 0.0) for s, p in self.positions.items())
