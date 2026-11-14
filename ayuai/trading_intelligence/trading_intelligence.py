"""Advanced deterministic trading intelligence.

Combines technical structure, risk-aware scoring and market context without
letting an LLM invent numerical signals.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import math
import pandas as pd

@dataclass(frozen=True)
class IntelligenceReport:
    action: str
    score: float
    confidence: float
    technical_score: float
    sentiment_score: float
    trend: str
    volatility: str
    risk_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class TradingIntelligence:
    @staticmethod
    def analyze(
        frame: pd.DataFrame,
        technical_score: float,
        sentiment_score: float = 0.0,
    ) -> IntelligenceReport:
        if len(frame) < 50:
            raise ValueError("At least 50 validated candles are required.")

        last = frame.iloc[-1]
        close = float(last["close"])
        ema50 = float(last.get("ema_50", close))
        ema200 = float(last.get("ema_200", ema50))
        atr = float(last.get("atr", 0.0))
        returns = frame["close"].pct_change().dropna()
        annualized_vol = float(returns.std() * math.sqrt(365 * 24 * 60))

        trend = "UPTREND" if close > ema50 and ema50 >= ema200 else (
            "DOWNTREND" if close < ema50 and ema50 <= ema200 else "MIXED"
        )
        volatility = "HIGH" if annualized_vol > 1.0 else "MODERATE" if annualized_vol > 0.5 else "LOW"

        flags: list[str] = []
        if volatility == "HIGH":
            flags.append("HIGH_VOLATILITY")
        if atr > 0 and atr / close > 0.03:
            flags.append("WIDE_ATR")
        if trend == "MIXED":
            flags.append("NO_CLEAR_TREND")

        tech = max(-1.0, min(1.0, float(technical_score)))
        sentiment = max(-1.0, min(1.0, float(sentiment_score)))
        trend_score = 0.20 if trend == "UPTREND" else -0.20 if trend == "DOWNTREND" else 0.0
        risk_penalty = min(0.30, 0.10 * len(flags))
        score = max(-1.0, min(1.0, 0.65 * tech + 0.20 * sentiment + trend_score))
        confidence = max(0.0, min(1.0, 0.75 - risk_penalty + (0.10 if trend != "MIXED" else 0.0)))

        if abs(score) < 0.20 or confidence < 0.55:
            action = "WAIT"
        elif score >= 0.20:
            action = "BUY"
        else:
            action = "SELL"

        return IntelligenceReport(
            action=action, score=round(score, 4), confidence=round(confidence, 4),
            technical_score=round(tech, 4), sentiment_score=round(sentiment, 4),
            trend=trend, volatility=volatility, risk_flags=flags,
        )
