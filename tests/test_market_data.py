from datetime import datetime, timezone

import pytest

from ayuai.market_data.models import MarketCandle, MarketDataError, MarketSnapshot
from ayuai.market_data.service import MarketDataService


def test_valid_snapshot():
    snapshot = MarketSnapshot(
        symbol="BTC/USDT",
        market_type="crypto",
        source="test",
        fetched_at=datetime.now(timezone.utc),
        last_price=100.0,
        bid=99.0,
        ask=101.0,
    )
    snapshot.validate()


def test_invalid_bid_ask_is_rejected():
    snapshot = MarketSnapshot(
        symbol="BTC/USDT",
        market_type="crypto",
        source="test",
        fetched_at=datetime.now(timezone.utc),
        last_price=100.0,
        bid=102.0,
        ask=101.0,
    )
    with pytest.raises(MarketDataError):
        snapshot.validate()


def test_invalid_candle_is_rejected():
    candle = MarketCandle(
        timestamp=datetime.now(timezone.utc),
        open=100.0,
        high=90.0,
        low=80.0,
        close=95.0,
        volume=1.0,
    )
    with pytest.raises(MarketDataError):
        candle.validate()


def test_close_extraction():
    candles = [
        MarketCandle(datetime.now(timezone.utc), 1, 2, 1, 1.5, 10),
        MarketCandle(datetime.now(timezone.utc), 1.5, 3, 1, 2.5, 20),
    ]
    assert MarketDataService.closes(candles) == [1.5, 2.5]
