from datetime import datetime, timedelta, timezone

import pytest

from ayuai.market_data.models import MarketDataError, MarketSnapshot
from ayuai.market_data.validation import ValidatedMarketDataService


class Provider:
    def __init__(self, snapshot=None, error=None):
        self.snapshot = snapshot
        self.error = error

    def fetch_snapshot(self, symbol):
        if self.error:
            raise self.error
        return self.snapshot


def snapshot(price=100.0, age=0, source="test"):
    return MarketSnapshot(
        symbol="BTC/USDT",
        market_type="crypto",
        source=source,
        fetched_at=datetime.now(timezone.utc) - timedelta(seconds=age),
        last_price=price,
    )


def test_uses_primary_when_data_is_valid():
    result = ValidatedMarketDataService(Provider(snapshot())).snapshot("BTC/USDT")
    assert result.source == "test"


def test_uses_fallback_when_primary_fails():
    result = ValidatedMarketDataService(
        Provider(error=RuntimeError("down")),
        Provider(snapshot(source="fallback")),
    ).snapshot("BTC/USDT")
    assert result.source == "fallback"


def test_uses_fallback_when_primary_data_is_stale():
    result = ValidatedMarketDataService(
        Provider(snapshot(age=300)),
        Provider(snapshot(source="fallback")),
        max_age_seconds=60,
    ).snapshot("BTC/USDT")
    assert result.source == "fallback"


def test_rejects_when_all_sources_fail_validation():
    service = ValidatedMarketDataService(
        Provider(snapshot(age=300)),
        Provider(error=RuntimeError("down")),
        max_age_seconds=60,
    )
    with pytest.raises(MarketDataError):
        service.snapshot("BTC/USDT")
