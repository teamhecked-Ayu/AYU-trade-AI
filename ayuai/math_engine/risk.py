from __future__ import annotations
import numpy as np

def returns_from_prices(prices):
    data = np.asarray(prices, dtype=float)
    if data.size < 2 or np.any(data <= 0):
        raise ValueError("at least two positive prices are required")
    return np.diff(data) / data[:-1]

def historical_var(returns, confidence=0.95):
    data = np.asarray(returns, dtype=float)
    if data.size == 0:
        raise ValueError("returns cannot be empty")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    return float(-np.quantile(data, 1 - confidence))

def max_drawdown(prices):
    data = np.asarray(prices, dtype=float)
    if data.size == 0 or np.any(data <= 0):
        raise ValueError("positive prices are required")
    peaks = np.maximum.accumulate(data)
    return float(np.min((data - peaks) / peaks))
