from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PaperPosition:
    symbol: str
    quantity: float
    average_entry_price: float


@dataclass(frozen=True)
class PaperTrade:
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float
    timestamp: datetime


@dataclass
class PaperPortfolio:
    cash: float
    positions: dict[str, PaperPosition] = field(default_factory=dict)
    trades: list[PaperTrade] = field(default_factory=list)


class PaperTradingEngine:
    """In-memory simulation only. This class never connects to a broker."""

    def __init__(self, starting_cash: float = 10_000.0, fee_rate: float = 0.001) -> None:
        if starting_cash <= 0:
            raise ValueError("starting_cash must be positive")
        if not 0 <= fee_rate < 1:
            raise ValueError("fee_rate must be between 0 and 1")
        self.fee_rate = fee_rate
        self.portfolio = PaperPortfolio(cash=starting_cash)

    def buy(self, symbol: str, quantity: float, price: float) -> PaperTrade:
        if not symbol or quantity <= 0 or price <= 0:
            raise ValueError("symbol, quantity, and price must be positive")
        fee = quantity * price * self.fee_rate
        cost = quantity * price + fee
        if cost > self.portfolio.cash:
            raise ValueError("Insufficient paper cash")
        existing = self.portfolio.positions.get(symbol)
        old_value = (existing.quantity * existing.average_entry_price) if existing else 0.0
        new_quantity = (existing.quantity if existing else 0.0) + quantity
        self.portfolio.positions[symbol] = PaperPosition(symbol, new_quantity, (old_value + quantity * price) / new_quantity)
        self.portfolio.cash -= cost
        return self._record(symbol, "buy", quantity, price, fee)

    def sell(self, symbol: str, quantity: float, price: float) -> PaperTrade:
        position = self.portfolio.positions.get(symbol)
        if not position or quantity <= 0 or quantity > position.quantity or price <= 0:
            raise ValueError("Invalid paper sell order")
        fee = quantity * price * self.fee_rate
        position.quantity -= quantity
        self.portfolio.cash += quantity * price - fee
        if position.quantity == 0:
            del self.portfolio.positions[symbol]
        return self._record(symbol, "sell", quantity, price, fee)

    def equity(self, prices: dict[str, float]) -> float:
        return self.portfolio.cash + sum(p.quantity * prices.get(symbol, 0.0) for symbol, p in self.portfolio.positions.items())

    def _record(self, symbol: str, side: str, quantity: float, price: float, fee: float) -> PaperTrade:
        trade = PaperTrade(symbol, side, quantity, price, fee, datetime.now(timezone.utc))
        self.portfolio.trades.append(trade)
        return trade
