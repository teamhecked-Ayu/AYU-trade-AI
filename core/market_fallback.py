from __future__ import annotations

from typing import Iterable, Protocol

import pandas as pd


class MarketDataProviderLike(Protocol):
    async def fetch_ohlcv(
        self, exchange: str, symbol: str, timeframe: str, limit: int
    ) -> pd.DataFrame: ...


class FallbackMarketDataProvider:
    """Try providers in order and return the first valid non-empty dataset."""

    def __init__(self, providers: Iterable[MarketDataProviderLike]):
        self.providers = list(providers)
        if not self.providers:
            raise ValueError("at least one market data provider is required")

    async def fetch_ohlcv(
        self, exchange: str, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> pd.DataFrame:
        errors = []
        for provider in self.providers:
            try:
                frame = await provider.fetch_ohlcv(exchange, symbol, timeframe, limit)
                if frame is None or frame.empty:
                    raise RuntimeError("provider returned no candles")
                return frame
            except Exception as exc:
                errors.append(f"{type(provider).__name__}: {exc}")

        raise RuntimeError(
            "all market data providers failed: " + "; ".join(errors)
        )
