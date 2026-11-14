from __future__ import annotations

import asyncio
from typing import Protocol

import ccxt.async_support as ccxt
import pandas as pd


class MarketDataProvider(Protocol):
    async def fetch_ohlcv(self, exchange: str, symbol: str, timeframe: str, limit: int) -> pd.DataFrame: ...


class CCXTMarketDataProvider:
    """Fetches and validates normalized OHLCV data with bounded retries."""

    def __init__(self, exchanges=None, retries: int = 3, retry_delay: float = 1.0):
        self._exchanges = exchanges or {}
        self.retries = retries
        self.retry_delay = retry_delay

    def _get_exchange(self, name: str):
        if name not in self._exchanges:
            exchange_cls = getattr(ccxt, name, None)
            if exchange_cls is None:
                raise ValueError(f"Unsupported exchange: {name}")
            self._exchanges[name] = exchange_cls({"enableRateLimit": True})
        return self._exchanges[name]

    async def fetch_ohlcv(self, exchange: str, symbol: str, timeframe: str = "1m", limit: int = 100) -> pd.DataFrame:
        client = self._get_exchange(exchange)
        last_error = None
        for attempt in range(self.retries):
            try:
                rows = await client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                frame = self._normalize(rows)
                if frame.empty:
                    raise RuntimeError("Market data provider returned no candles")
                return frame
            except Exception as exc:
                last_error = exc
                if attempt + 1 < self.retries:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        raise RuntimeError(f"Market data fetch failed after {self.retries} attempts") from last_error

    @staticmethod
    def _normalize(rows) -> pd.DataFrame:
        if not rows:
            raise RuntimeError("Market data provider returned no candles")
        frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        numeric = ["open", "high", "low", "close", "volume"]
        frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
        if frame[numeric].isna().any().any() or (frame["close"] <= 0).any():
            raise RuntimeError("Market data provider returned invalid candles")
        if not frame["timestamp"].is_monotonic_increasing:
            frame = frame.sort_values("timestamp").reset_index(drop=True)
        return frame

    async def close(self):
        for client in self._exchanges.values():
            close = getattr(client, "close", None)
            if close:
                result = close()
                if hasattr(result, "__await__"):
                    await result
