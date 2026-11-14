from __future__ import annotations

from .crypto_data import CCXTMarketDataProvider
from .models import MarketCandle, MarketDataError, MarketSnapshot


class MarketDataService:
    """Single entry point for verified market data used by AYUAI."""

    def __init__(self, crypto_provider: CCXTMarketDataProvider | None = None) -> None:
        self.crypto_provider = crypto_provider or CCXTMarketDataProvider()

    def crypto_snapshot(self, symbol: str) -> MarketSnapshot:
        return self.crypto_provider.fetch_snapshot(symbol)

    def crypto_history(
        self, symbol: str, timeframe: str = "1h", limit: int = 200
    ) -> list[MarketCandle]:
        return self.crypto_provider.fetch_ohlcv(symbol, timeframe, limit)

    @staticmethod
    def closes(candles: list[MarketCandle]) -> list[float]:
        if len(candles) < 2:
            raise MarketDataError("At least two candles are required.")
        return [c.close for c in candles]
