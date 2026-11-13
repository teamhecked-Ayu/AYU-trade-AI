from __future__ import annotations
import numpy as np

def simulate_terminal_prices(prices, simulations=5000, horizon=30, seed=None):
    data = np.asarray(prices, dtype=float)
    if data.size < 3 or np.any(data <= 0):
        raise ValueError("at least three positive prices are required")
    if simulations < 1 or horizon < 1:
        raise ValueError("simulations and horizon must be positive")
    log_returns = np.diff(np.log(data))
    rng = np.random.default_rng(seed)
    paths = rng.normal(log_returns.mean(), log_returns.std(ddof=1), size=(simulations, horizon))
    return data[-1] * np.exp(paths.sum(axis=1))
