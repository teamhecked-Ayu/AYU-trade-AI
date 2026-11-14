from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    max_position_pct: float = 0.10
    max_total_exposure_pct: float = 0.50
    min_risk_reward: float = 1.5
    max_risk_per_trade_pct: float = 0.02

    def __post_init__(self):
        for value in (self.max_position_pct, self.max_total_exposure_pct, self.max_risk_per_trade_pct):
            if not 0 < value <= 1:
                raise ValueError("Percentage limits must be between 0 and 1")
        if self.min_risk_reward <= 0:
            raise ValueError("min_risk_reward must be positive")


@dataclass(frozen=True)
class TradeRequest:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    position_value: float
    risk_amount: float
    risk_reward_ratio: float | None


class RiskEngine:
    """Deterministic pre-trade checks. Rejects unsafe or malformed orders."""

    def __init__(self, limits: RiskLimits | None = None):
        self.limits = limits or RiskLimits()

    def evaluate(self, request: TradeRequest, *, portfolio_equity: float, current_exposure: float = 0.0) -> RiskDecision:
        if portfolio_equity <= 0:
            return self._reject("Portfolio equity must be positive", 0, 0, None)
        if request.side not in ("buy", "sell") or request.quantity <= 0 or request.entry_price <= 0:
            return self._reject("Invalid trade request", 0, 0, None)

        value = request.quantity * request.entry_price
        if value > portfolio_equity * self.limits.max_position_pct:
            return self._reject("Position exceeds maximum size", value, 0, None)
        if current_exposure + value > portfolio_equity * self.limits.max_total_exposure_pct:
            return self._reject("Trade exceeds maximum portfolio exposure", value, 0, None)

        if request.side == "buy":
            if not (0 < request.stop_loss < request.entry_price < request.take_profit):
                return self._reject("Invalid stop-loss or take-profit for long trade", value, 0, None)
            risk_per_unit = request.entry_price - request.stop_loss
            reward_per_unit = request.take_profit - request.entry_price
        else:
            if not (request.take_profit < request.entry_price < request.stop_loss):
                return self._reject("Invalid stop-loss or take-profit for short trade", value, 0, None)
            risk_per_unit = request.stop_loss - request.entry_price
            reward_per_unit = request.entry_price - request.take_profit

        risk_amount = risk_per_unit * request.quantity
        ratio = reward_per_unit / risk_per_unit
        if risk_amount > portfolio_equity * self.limits.max_risk_per_trade_pct:
            return self._reject("Trade risk exceeds maximum allowed loss", value, risk_amount, ratio)
        if ratio < self.limits.min_risk_reward:
            return self._reject("Risk/reward ratio is too low", value, risk_amount, ratio)
        return RiskDecision(True, "Approved", value, risk_amount, ratio)

    @staticmethod
    def _reject(reason, value, risk, ratio):
        return RiskDecision(False, reason, value, risk, ratio)
