"""Market data access with normalized, provider-independent output.

The first implementation uses CCXT exchanges. Network failures are surfaced as
safe errors and no exchange credentials are required for public market data.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    exchange: str
    last_price: float | None
    candles: list[Candle]
    fetched_at: datetime


class MarketDataError(RuntimeError):
    """Raised when market data cannot be fetched or normalized."""


class MarketDataService:
    def __init__(self, exchange: str = "binance") -> None:
        self.exchange_name = exchange

    def _build_exchange(self) -> Any:
        try:
            import ccxt
        except ImportError as exc:
            raise MarketDataError("CCXT is not installed") from exc

        exchange_class = getattr(ccxt, self.exchange_name, None)
        if exchange_class is None:
            raise MarketDataError(f"Unsupported exchange: {self.exchange_name}")
        return exchange_class({"enableRateLimit": True})

    async def get_snapshot(
        self,
        symbol: str,
        *,
        timeframe: str = "1h",
        limit: int = 100,
    ) -> MarketSnapshot:
        if not symbol or "/" not in symbol:
            raise MarketDataError("Symbol must use BASE/QUOTE format")
        if limit < 2 or limit > 1000:
            raise MarketDataError("Limit must be between 2 and 1000")

        exchange = self._build_exchange()
        try:
            ticker, rows = await asyncio.gather(
                asyncio.to_thread(exchange.fetch_ticker, symbol),
                asyncio.to_thread(exchange.fetch_ohlcv, symbol, timeframe, None, limit),
            )
        except Exception as exc:
            raise MarketDataError("Market data provider request failed") from exc
        finally:
            close = getattr(exchange, "close", None)
            if callable(close):
                try:
                    await asyncio.to_thread(close)
                except Exception:
                    pass

        candles = [
            Candle(
                timestamp=datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
                open=float(row[1]), high=float(row[2]), low=float(row[3]),
                close=float(row[4]), volume=float(row[5]),
            )
            for row in rows
            if len(row) >= 6
        ]
        if not candles:
            raise MarketDataError("Market data provider returned no candles")

        last = ticker.get("last") if isinstance(ticker, dict) else None
        return MarketSnapshot(
            symbol=symbol,
            exchange=self.exchange_name,
            last_price=float(last) if last is not None else candles[-1].close,
            candles=candles,
            fetched_at=datetime.now(timezone.utc),
        )
