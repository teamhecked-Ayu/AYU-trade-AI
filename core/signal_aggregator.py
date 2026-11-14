import asyncio
from typing import Iterable, Mapping

import numpy as np


class SignalAggregator:
    """Combines real strategy signals into one bounded, smoothed decision."""

    def __init__(self):
        self.kalman_state = 0.0
        self.kalman_uncertainty = 1.0

    def kalman_filter(self, measurement: float) -> float:
        measurement = float(np.clip(measurement, -1.0, 1.0))
        prediction = self.kalman_state
        prediction_uncertainty = self.kalman_uncertainty + 0.1

        kalman_gain = prediction_uncertainty / (prediction_uncertainty + 0.5)
        self.kalman_state = prediction + kalman_gain * (measurement - prediction)
        self.kalman_uncertainty = (1 - kalman_gain) * prediction_uncertainty
        return float(np.clip(self.kalman_state, -1.0, 1.0))

    def aggregate(self, signals: Mapping[str, float] | Iterable[float]):
        """Aggregate supplied signals. No random signal generation is used."""
        if isinstance(signals, Mapping):
            values = list(signals.values())
        else:
            values = list(signals)

        if not values:
            return {"score": 0.0, "confidence": 0.0, "action": "HOLD"}

        numeric = np.asarray(values, dtype=float)
        numeric = numeric[np.isfinite(numeric)]
        if numeric.size == 0:
            return {"score": 0.0, "confidence": 0.0, "action": "HOLD"}

        numeric = np.clip(numeric, -1.0, 1.0)
        raw_score = float(np.mean(numeric))
        score = self.kalman_filter(raw_score)

        # Confidence rewards agreement and penalizes disagreement.
        agreement = 1.0 - min(1.0, float(np.std(numeric)))
        strength = min(1.0, abs(raw_score))
        confidence = float(np.clip(0.6 * agreement + 0.4 * strength, 0.0, 1.0))

        action = "BUY" if score > 0.5 else "SELL" if score < -0.5 else "HOLD"
        return {"score": score, "confidence": confidence, "action": action}

    async def get_consensus_signal(self, signals=None):
        """Async compatibility wrapper for the engine."""
        await asyncio.sleep(0)
        return self.aggregate(signals or [])
