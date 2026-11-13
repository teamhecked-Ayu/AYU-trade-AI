from dataclasses import dataclass
from datetime import datetime
from typing import Literal

MarketType = Literal["crypto", "stock"]


class MarketDataError(RuntimeError):
    """Raised when market data is unavailable or fails validation."""


@dataclass(frozen=True)
class MarketCandle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def validate(self) -> None:
        values = (self.open, self.high, self.low, self.close)
        if any(value <= 0 for value in values):
            raise MarketDataError("OHLC prices must be positive.")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise MarketDataError("Invalid OHLC relationship.")
        if self.volume < 0:
            raise MarketDataError("Volume cannot be negative.")


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    market_type: MarketType
    source: str
    fetched_at: datetime
    last_price: float
    bid: float | None = None
    ask: float | None = None
    base_volume: float | None = None

    def validate(self) -> None:
        if not self.symbol:
            raise MarketDataError("Symbol is required.")
        if self.last_price <= 0:
            raise MarketDataError("Last price must be positive.")
        if self.bid is not None and self.bid <= 0:
            raise MarketDataError("Bid must be positive.")
        if self.ask is not None and self.ask <= 0:
            raise MarketDataError("Ask must be positive.")
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise MarketDataError("Bid cannot be greater than ask.")
