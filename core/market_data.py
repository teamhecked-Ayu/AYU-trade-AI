from __future__ import annotations

from typing import Protocol

import ccxt
import pandas as pd


class MarketDataProvider(Protocol):
    async def fetch_ohlcv(self, exchange: str, symbol: str, timeframe: str, limit: int) -> pd.DataFrame: ...


class CCXTMarketDataProvider:
    """Fetches normalized OHLCV data from configured CCXT exchanges."""

    def __init__(self, exchanges=None):
        self._exchanges = exchanges or {}

    def _get_exchange(self, name: str):
        if name not in self._exchanges:
            exchange_cls = getattr(ccxt, name, None)
            if exchange_cls is None:
                raise ValueError(f"Unsupported exchange: {name}")
            self._exchanges[name] = exchange_cls({"enableRateLimit": True})
        return self._exchanges[name]

    async def fetch_ohlcv(self, exchange: str, symbol: str, timeframe: str = "1m", limit: int = 100) -> pd.DataFrame:
        client = self._get_exchange(exchange)
        rows = await client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not rows:
            raise RuntimeError("Market data provider returned no candles")
        frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        numeric = ["open", "high", "low", "close", "volume"]
        frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
        if frame[numeric].isna().any().any() or (frame["close"] <= 0).any():
            raise RuntimeError("Market data provider returned invalid candles")
        return frame
