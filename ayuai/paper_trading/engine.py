from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from core.paper_portfolio import PaperPortfolio, Position as PaperPosition
from core.portfolio_store import SQLitePortfolioStore


@dataclass(frozen=True)
class PaperTrade:
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float
    timestamp: datetime


class PaperTradingEngine:
    """Paper-only facade over the shared core portfolio rules and optional store."""

    def __init__(
        self,
        starting_cash: float = 10_000.0,
        fee_rate: float = 0.001,
        store: SQLitePortfolioStore | None = None,
    ) -> None:
        if starting_cash <= 0:
            raise ValueError("starting_cash must be positive")
        if not 0 <= fee_rate < 1:
            raise ValueError("fee_rate must be between 0 and 1")
        self.starting_cash = float(starting_cash)
        self.fee_rate = float(fee_rate)
        self.store = store
        self.portfolio = (
            store.load(initial_cash=self.starting_cash, fee_rate=self.fee_rate)
            if store is not None
            else PaperPortfolio(cash=self.starting_cash, fee_rate=self.fee_rate)
        )

    def _execute(self, symbol: str, side: str, quantity: float, price: float) -> PaperTrade:
        if self.store is not None:
            record = self.store.execute(
                symbol,
                side,
                quantity,
                price,
                initial_cash=self.starting_cash,
                fee_rate=self.fee_rate,
            )
            self.portfolio = self.store.load(
                initial_cash=self.starting_cash,
                fee_rate=self.fee_rate,
            )
        else:
            record = self.portfolio.execute(symbol, side, quantity, price)

        return PaperTrade(
            symbol=record["symbol"],
            side=record["side"],
            quantity=record["quantity"],
            price=record["price"],
            fee=record["fee"],
            timestamp=datetime.now(timezone.utc),
        )

    def buy(self, symbol: str, quantity: float, price: float) -> PaperTrade:
        return self._execute(symbol, "buy", quantity, price)

    def sell(self, symbol: str, quantity: float, price: float) -> PaperTrade:
        return self._execute(symbol, "sell", quantity, price)

    def equity(self, prices: dict[str, float]) -> float:
        if self.store is not None:
            self.portfolio = self.store.load(
                initial_cash=self.starting_cash,
                fee_rate=self.fee_rate,
            )
        return self.portfolio.equity(prices)
