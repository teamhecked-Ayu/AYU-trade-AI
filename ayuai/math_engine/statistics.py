from __future__ import annotations
import numpy as np

def descriptive_stats(values):
    data = np.asarray(values, dtype=float)
    if data.size == 0:
        raise ValueError("values cannot be empty")
    return {"mean": float(np.mean(data)), "median": float(np.median(data)),
            "std": float(np.std(data, ddof=1)) if data.size > 1 else 0.0,
            "minimum": float(np.min(data)), "maximum": float(np.max(data))}
