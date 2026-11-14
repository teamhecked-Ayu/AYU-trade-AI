from datetime import datetime, timezone

import pytest

from ayuai.market_data.crypto_data import CCXTMarketDataProvider
from ayuai.market_data.models import MarketDataError


class FakeExchange:
    def fetch_ticker(self, symbol):
        return {"last": 100.0, "bid": 99.5, "ask": 100.5, "baseVolume": 42}

    def fetch_ohlcv(self, symbol, timeframe, limit):
        return [
            [1700000000000, 90, 105, 85, 100, 10],
            [1700003600000, 100, 110, 95, 108, 12],
        ]


class BrokenExchange:
    def fetch_ticker(self, symbol):
        raise RuntimeError("network details should not leak")


def test_real_provider_normalizes_snapshot_and_history():
    provider = CCXTMarketDataProvider(exchange_id="fake", exchange=FakeExchange())
    snapshot = provider.fetch_snapshot("BTC/USDT")
    candles = provider.fetch_ohlcv("BTC/USDT", limit=2)

    assert snapshot.last_price == 100.0
    assert snapshot.fetched_at.tzinfo is not None
    assert len(candles) == 2
    assert candles[-1].close == 108.0


def test_provider_hides_internal_network_error_details():
    provider = CCXTMarketDataProvider(exchange_id="fake", exchange=BrokenExchange())
    with pytest.raises(MarketDataError) as error:
        provider.fetch_snapshot("BTC/USDT")
    assert "network details" not in str(error.value)
