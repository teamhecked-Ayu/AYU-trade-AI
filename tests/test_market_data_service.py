from datetime import datetime, timedelta, timezone

import pytest

from ayuai.market_data.models import MarketCandle, MarketDataError, MarketSnapshot
from ayuai.market_data.service import MarketDataService


def snapshot(price=100.0, age=0, source="primary", symbol="BTC/USDT"):
    return MarketSnapshot(
        symbol=symbol,
        market_type="crypto",
        source=source,
        fetched_at=datetime.now(timezone.utc) - timedelta(seconds=age),
        last_price=price,
    )


def history():
    now = datetime.now(timezone.utc)
    return [
        MarketCandle(now - timedelta(hours=1), 100, 110, 95, 105, 10),
        MarketCandle(now, 105, 112, 101, 108, 12),
    ]


class FakeProvider:
    def __init__(self, snapshot_value=None, candles=None, error=None):
        self.snapshot_value = snapshot_value
        self.candles = candles
        self.error = error
        self.snapshot_calls = 0
        self.history_calls = 0

    def fetch_snapshot(self, symbol):
        self.snapshot_calls += 1
        if self.error:
            raise self.error
        return self.snapshot_value

    def fetch_ohlcv(self, symbol, timeframe, limit):
        self.history_calls += 1
        if self.error:
            raise self.error
        return self.candles


def test_market_service_uses_primary_snapshot_when_fresh():
    primary = FakeProvider(snapshot_value=snapshot())
    service = MarketDataService(primary)

    result = service.crypto_snapshot("BTC/USDT")

    assert result.source == "primary"
    assert primary.snapshot_calls == 1


def test_market_service_uses_fallback_for_stale_primary_snapshot():
    primary = FakeProvider(snapshot_value=snapshot(age=300))
    fallback = FakeProvider(snapshot_value=snapshot(source="fallback"))
    service = MarketDataService(primary, fallback, max_snapshot_age_seconds=60)

    result = service.crypto_snapshot("BTC/USDT")

    assert result.source == "fallback"
    assert primary.snapshot_calls == 1
    assert fallback.snapshot_calls == 1


def test_market_service_rejects_disagreeing_valid_sources():
    primary = FakeProvider(snapshot_value=snapshot(price=100))
    fallback = FakeProvider(snapshot_value=snapshot(price=150, source="fallback"))
    service = MarketDataService(primary, fallback, max_price_difference_ratio=0.10)

    with pytest.raises(MarketDataError, match="disagree"):
        service.crypto_snapshot("BTC/USDT")


def test_market_service_uses_valid_primary_if_optional_secondary_is_down():
    primary = FakeProvider(snapshot_value=snapshot())
    fallback = FakeProvider(error=RuntimeError("secondary down"))
    service = MarketDataService(primary, fallback)

    assert service.crypto_snapshot("BTC/USDT").source == "primary"


def test_market_service_uses_fallback_for_history_if_primary_fails():
    primary = FakeProvider(error=RuntimeError("primary down"))
    fallback = FakeProvider(candles=history())
    service = MarketDataService(primary, fallback)

    candles = service.crypto_history("BTC/USDT", "1h", 2)

    assert len(candles) == 2
    assert service.closes(candles) == [105, 108]
    assert primary.history_calls == 1
    assert fallback.history_calls == 1


def test_market_service_uses_fallback_for_invalid_primary_history():
    duplicate = history()[0]
    primary = FakeProvider(candles=[duplicate, duplicate])
    fallback_candles = history()
    fallback = FakeProvider(candles=fallback_candles)
    service = MarketDataService(primary, fallback)

    candles = service.crypto_history("BTC/USDT", "1h", 2)

    assert [c.close for c in candles] == [105, 108]
    assert primary.history_calls == 1
    assert fallback.history_calls == 1


def test_market_service_rejects_when_both_history_sources_fail():
    service = MarketDataService(
        FakeProvider(error=RuntimeError("primary down")),
        FakeProvider(error=RuntimeError("fallback down")),
    )
    with pytest.raises(MarketDataError, match="No validated historical"):
        service.crypto_history("BTC/USDT")


def test_market_service_rejects_invalid_limits():
    service = MarketDataService(FakeProvider(candles=history()))
    with pytest.raises(MarketDataError):
        service.crypto_history("BTC/USDT", limit=1)


def test_snapshot_rejects_non_finite_values():
    with pytest.raises(MarketDataError, match="finite"):
        snapshot(price=float("nan")).validate()


def test_history_rejects_non_finite_values():
    candles = history()
    bad = MarketCandle(
        candles[0].timestamp,
        float("nan"),
        110,
        95,
        105,
        10,
    )
    with pytest.raises(MarketDataError, match="finite"):
        bad.validate()
