from __future__ import annotations

import math


class RiskManager:
    """Deterministic guardrail for signal quality and basic risk limits."""

    def __init__(self, max_daily_loss: float = 0.05, min_confidence: float = 0.70, min_score: float = 0.50):
        if not 0 < max_daily_loss <= 1:
            raise ValueError("max_daily_loss must be between 0 and 1")
        self.daily_loss = 0.0
        self.max_daily_loss = max_daily_loss
        self.min_confidence = min_confidence
        self.min_score = min_score

    def validate_signal(self, signal):
        score = float(signal.get("score", 0.0))
        confidence = float(signal.get("confidence", 0.0))
        if not math.isfinite(score) or not math.isfinite(confidence):
            return False
        if self.daily_loss >= self.max_daily_loss:
            return False
        return confidence >= self.min_confidence and abs(score) >= self.min_score

    def calculate_position_size(self, balance, win_rate, risk_reward):
        balance = float(balance)
        p = float(win_rate)
        b = float(risk_reward)
        if balance <= 0 or not 0 <= p <= 1 or b <= 0:
            return 0.0
        q = 1 - p
        kelly_f = max(0.0, (p * b - q) / b)
        return balance * min(kelly_f * 0.5, 0.02)
