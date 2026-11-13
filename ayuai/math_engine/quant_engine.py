"""Deterministic calculations. This layer never asks an LLM to do the math."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .statistics import descriptive_stats
from .risk import returns_from_prices, historical_var, max_drawdown
from .monte_carlo import simulate_terminal_prices
from .time_series import moving_average

@dataclass
class QuantReport:
    statistics: dict
    annualized_volatility: float
    value_at_risk: float
    max_drawdown: float
    monte_carlo: dict
    trend: dict

class QuantEngine:
    def analyze_prices(self, prices, *, periods_per_year=365, confidence=0.95,
                       simulations=5000, horizon=30, seed=None) -> QuantReport:
        data = np.asarray(prices, dtype=float)
        returns = returns_from_prices(data)
        volatility = float(np.std(returns, ddof=1) * np.sqrt(periods_per_year)) if returns.size > 1 else 0.0
        terminal = simulate_terminal_prices(data, simulations=simulations, horizon=horizon, seed=seed)
        window = min(20, data.size)
        ma = moving_average(data, window)
        return QuantReport(
            statistics=descriptive_stats(returns),
            annualized_volatility=volatility,
            value_at_risk=historical_var(returns, confidence),
            max_drawdown=max_drawdown(data),
            monte_carlo={
                "simulations": simulations,
                "horizon": horizon,
                "median_terminal_price": float(np.median(terminal)),
                "downside_percentile_5": float(np.quantile(terminal, 0.05)),
                "upside_percentile_95": float(np.quantile(terminal, 0.95)),
            },
            trend={"moving_average_window": window, "latest_moving_average": float(ma[-1])},
        )
