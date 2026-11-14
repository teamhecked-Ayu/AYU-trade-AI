from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Position:
    quantity: float = 0.0
    average_price: float = 0.0


@dataclass
class PaperPortfolio:
    cash: float = 10_000.0
    fee_rate: float = 0.001
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[dict] = field(default_factory=list)

    def execute(self, symbol: str, side: str, quantity: float, price: float) -> dict:
        if side not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")

        position = self.positions.setdefault(symbol, Position())
        gross = quantity * price
        fee = gross * self.fee_rate

        if side == "buy":
            total = gross + fee
            if total > self.cash:
                raise ValueError("insufficient paper cash")
            new_quantity = position.quantity + quantity
            position.average_price = (
                (position.average_price * position.quantity + gross) / new_quantity
            )
            position.quantity = new_quantity
            self.cash -= total
        else:
            if quantity > position.quantity:
                raise ValueError("insufficient paper position")
            position.quantity -= quantity
            self.cash += gross - fee
            if position.quantity == 0:
                position.average_price = 0.0

        trade = {
            "symbol": symbol, "side": side, "quantity": quantity,
            "price": price, "fee": fee, "cash": self.cash,
        }
        self.trades.append(trade)
        return trade

    def equity(self, prices: Dict[str, float]) -> float:
        return self.cash + sum(
            position.quantity * float(prices.get(symbol, 0.0))
            for symbol, position in self.positions.items()
        )
