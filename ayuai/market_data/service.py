from __future__ import annotations

from .crypto_data import CCXTMarketDataProvider
from .models import MarketCandle, MarketDataError, MarketSnapshot
from .validation import ValidatedMarketDataService


class MarketDataService:
    """Single entry point for validated crypto snapshots and history.

    A fallback provider is optional so deployments do not make unexpected
    requests to another exchange unless one is configured explicitly.
    """

    def __init__(
        self,
        crypto_provider: CCXTMarketDataProvider | None = None,
        fallback_provider: CCXTMarketDataProvider | None = None,
        *,
        max_snapshot_age_seconds: int = 120,
        max_price_difference_ratio: float = 0.10,
    ) -> None:
        self.crypto_provider = crypto_provider or CCXTMarketDataProvider()
        self.fallback_provider = fallback_provider
        self.validated_snapshots = ValidatedMarketDataService(
            self.crypto_provider,
            fallback_provider,
            max_age_seconds=max_snapshot_age_seconds,
            max_price_difference_ratio=max_price_difference_ratio,
        )

    def crypto_snapshot(self, symbol: str) -> MarketSnapshot:
        return self.validated_snapshots.snapshot(symbol)

    @staticmethod
    def _validate_history(candles: list[MarketCandle]) -> list[MarketCandle]:
        if len(candles) < 2:
            raise MarketDataError("At least two validated historical candles are required.")
        previous_timestamp = None
        for candle in candles:
            candle.validate()
            if previous_timestamp is not None and candle.timestamp <= previous_timestamp:
                raise MarketDataError("Historical candle timestamps must be strictly increasing.")
            previous_timestamp = candle.timestamp
        return candles

    def crypto_history(
        self, symbol: str, timeframe: str = "1h", limit: int = 200
    ) -> list[MarketCandle]:
        if limit < 2 or limit > 1000:
            raise MarketDataError("limit must be between 2 and 1000.")

        try:
            return self._validate_history(
                self.crypto_provider.fetch_ohlcv(symbol, timeframe, limit)
            )
        except Exception as primary_error:
            if self.fallback_provider is None:
                raise MarketDataError(
                    "No validated historical market data source is available."
                ) from primary_error

        try:
            return self._validate_history(
                self.fallback_provider.fetch_ohlcv(symbol, timeframe, limit)
            )
        except Exception as fallback_error:
            raise MarketDataError(
                "No validated historical market data source is available."
            ) from fallback_error

    @staticmethod
    def closes(candles: list[MarketCandle]) -> list[float]:
        validated = MarketDataService._validate_history(candles)
        return [c.close for c in validated]
