from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import MarketCandle, MarketDataError, MarketSnapshot


class CCXTMarketDataProvider:
    """Read-only crypto market data provider.

    No order-placement methods are exposed here. This layer is for analysis.
    """

    def __init__(self, exchange_id: str = "binance", exchange: Any | None = None) -> None:
        self.exchange_id = exchange_id
        if exchange is not None:
            self.exchange = exchange
            return
        try:
            import ccxt
        except ImportError as exc:
            raise MarketDataError("ccxt is required for crypto market data.") from exc

        exchange_class = getattr(ccxt, exchange_id, None)
        if exchange_class is None:
            raise MarketDataError(f"Unsupported exchange: {exchange_id}")
        self.exchange = exchange_class({"enableRateLimit": True})

    def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        try:
            ticker: dict[str, Any] = self.exchange.fetch_ticker(symbol)
        except Exception as exc:
            raise MarketDataError(f"Market data request failed for {symbol}.") from exc

        price = ticker.get("last") or ticker.get("close")
        if price is None:
            raise MarketDataError(f"No last price returned for {symbol}.")

        snapshot = MarketSnapshot(
            symbol=symbol,
            market_type="crypto",
            source=self.exchange_id,
            fetched_at=datetime.now(timezone.utc),
            last_price=float(price),
            bid=float(ticker["bid"]) if ticker.get("bid") is not None else None,
            ask=float(ticker["ask"]) if ticker.get("ask") is not None else None,
            base_volume=float(ticker["baseVolume"]) if ticker.get("baseVolume") is not None else None,
        )
        snapshot.validate()
        return snapshot

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 200,
    ) -> list[MarketCandle]:
        if limit < 2 or limit > 1000:
            raise MarketDataError("limit must be between 2 and 1000.")

        try:
            rows = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as exc:
            raise MarketDataError(f"Historical market data request failed for {symbol}.") from exc

        candles: list[MarketCandle] = []
        for timestamp, open_, high, low, close, volume in rows:
            candle = MarketCandle(
                timestamp=datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc),
                open=float(open_),
                high=float(high),
                low=float(low),
                close=float(close),
                volume=float(volume or 0),
            )
            candle.validate()
            candles.append(candle)

        if len(candles) < 2:
            raise MarketDataError("Insufficient validated historical data returned.")
        return candles
