from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from ayuai.market_data.models import MarketCandle

Signal = Literal["buy", "sell", "hold"]
Strategy = Callable[[list[MarketCandle], int], Signal]


@dataclass(frozen=True)
class Trade:
    entry_time: object
    exit_time: object | None
    entry_price: float
    exit_price: float | None
    quantity: float
    pnl: float | None


@dataclass(frozen=True)
class BacktestResult:
    initial_cash: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    trades: tuple[Trade, ...]
    win_rate_pct: float


class BacktestEngine:
    """Simple deterministic long-only backtest engine.

    Signals execute at the current candle close. This assumption is explicit so
    results are not presented as live trading performance.
    """

    def __init__(self, initial_cash: float = 10_000.0, fee_rate: float = 0.001) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if not 0 <= fee_rate < 1:
            raise ValueError("fee_rate must be between 0 and 1")
        self.initial_cash = initial_cash
        self.fee_rate = fee_rate

    def run(self, candles: list[MarketCandle], strategy: Strategy) -> BacktestResult:
        if len(candles) < 2:
            raise ValueError("At least two candles are required")
        for candle in candles:
            candle.validate()

        cash = self.initial_cash
        quantity = 0.0
        entry_price = 0.0
        entry_time = None
        trades: list[Trade] = []
        peak_equity = cash
        max_drawdown = 0.0

        for index, candle in enumerate(candles):
            signal = strategy(candles, index)
            if signal not in ("buy", "sell", "hold"):
                raise ValueError("Strategy must return buy, sell, or hold")

            if signal == "buy" and quantity == 0:
                quantity = cash / (candle.close * (1 + self.fee_rate))
                cost = quantity * candle.close * (1 + self.fee_rate)
                cash -= cost
                entry_price = candle.close
                entry_time = candle.timestamp
            elif signal == "sell" and quantity > 0:
                proceeds = quantity * candle.close * (1 - self.fee_rate)
                pnl = proceeds - (quantity * entry_price * (1 + self.fee_rate))
                cash += proceeds
                trades.append(Trade(entry_time, candle.timestamp, entry_price, candle.close, quantity, pnl))
                quantity = 0.0
                entry_price = 0.0
                entry_time = None

            equity = cash + quantity * candle.close * (1 - self.fee_rate)
            peak_equity = max(peak_equity, equity)
            if peak_equity > 0:
                max_drawdown = max(max_drawdown, (peak_equity - equity) / peak_equity)

        final_price = candles[-1].close
        final_equity = cash + quantity * final_price * (1 - self.fee_rate)
        if quantity > 0:
            proceeds = quantity * final_price * (1 - self.fee_rate)
            pnl = proceeds - (quantity * entry_price * (1 + self.fee_rate))
            trades.append(Trade(entry_time, candles[-1].timestamp, entry_price, final_price, quantity, pnl))

        closed = [trade for trade in trades if trade.pnl is not None]
        wins = sum(1 for trade in closed if trade.pnl > 0)
        win_rate = (wins / len(closed) * 100) if closed else 0.0
        return BacktestResult(
            initial_cash=self.initial_cash,
            final_equity=final_equity,
            total_return_pct=(final_equity / self.initial_cash - 1) * 100,
            max_drawdown_pct=max_drawdown * 100,
            trades=tuple(trades),
            win_rate_pct=win_rate,
        )
