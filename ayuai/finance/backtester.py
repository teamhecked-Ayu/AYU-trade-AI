"""Deterministic historical backtesting for AYU-trade-AI."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable, Any
import pandas as pd

@dataclass(frozen=True)
class BacktestResult:
    initial_cash: float
    final_equity: float
    total_return: float
    max_drawdown: float
    trades: int
    wins: int
    losses: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class Backtester:
    """Long-only paper model for validating signals before real execution."""
    def __init__(self, initial_cash: float = 10_000.0, fee_rate: float = 0.001):
        if initial_cash <= 0 or fee_rate < 0:
            raise ValueError("Invalid backtest configuration.")
        self.initial_cash = initial_cash
        self.fee_rate = fee_rate

    def run(self, frame: pd.DataFrame, signal_fn: Callable[[pd.DataFrame], str]) -> BacktestResult:
        if "close" not in frame or len(frame) < 3:
            raise ValueError("Backtest requires at least three rows with close prices.")
        cash, units, entry_value = self.initial_cash, 0.0, None
        peak, max_dd, trades, wins, losses = self.initial_cash, 0.0, 0, 0, 0

        for i in range(2, len(frame)):
            history = frame.iloc[: i + 1]
            price = float(history.iloc[-1]["close"])
            signal = signal_fn(history).upper()

            if signal == "BUY" and units == 0:
                units = cash * (1 - self.fee_rate) / price
                entry_value = cash
                cash = 0.0
                trades += 1
            elif signal in {"SELL", "WAIT"} and units > 0:
                cash = units * price * (1 - self.fee_rate)
                if entry_value is not None:
                    (wins if cash > entry_value else losses)
                    if cash > entry_value: wins += 1
                    else: losses += 1
                units, entry_value = 0.0, None

            equity = cash + units * price
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak if peak else 0.0)

        final_price = float(frame.iloc[-1]["close"])
        final_equity = cash + units * final_price
        return BacktestResult(self.initial_cash, final_equity,
            (final_equity / self.initial_cash) - 1, max_dd, trades, wins, losses)
