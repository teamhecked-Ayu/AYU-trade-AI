from __future__ import annotations
import numpy as np

def moving_average(values, window):
    data = np.asarray(values, dtype=float)
    if window < 1 or window > data.size:
        raise ValueError("window must be between 1 and the number of values")
    weights = np.ones(window) / window
    return np.convolve(data, weights, mode="valid")
