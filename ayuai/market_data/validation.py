from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

from .models import MarketDataError, MarketSnapshot


class SnapshotProvider(Protocol):
    def fetch_snapshot(self, symbol: str) -> MarketSnapshot: ...


class ValidatedMarketDataService:
    """Fetch validated market data and fall back when a source fails or is stale."""

    def __init__(
        self,
        primary: SnapshotProvider,
        fallback: SnapshotProvider | None = None,
        *,
        max_age_seconds: int = 120,
        max_price_difference_ratio: float = 0.10,
    ) -> None:
        if max_age_seconds < 0:
            raise ValueError("max_age_seconds cannot be negative")
        if not 0 <= max_price_difference_ratio < 1:
            raise ValueError("max_price_difference_ratio must be between 0 and 1")
        self.primary = primary
        self.fallback = fallback
        self.max_age = timedelta(seconds=max_age_seconds)
        self.max_price_difference_ratio = max_price_difference_ratio

    def _validate_freshness(self, snapshot: MarketSnapshot) -> None:
        snapshot.validate()
        fetched_at = snapshot.fetched_at
        if fetched_at.tzinfo is None:
            raise MarketDataError("Market data timestamp must include timezone information.")
        age = datetime.now(timezone.utc) - fetched_at
        if age > self.max_age:
            raise MarketDataError("Market data is stale.")

    def snapshot(self, symbol: str) -> MarketSnapshot:
        try:
            primary_snapshot = self.primary.fetch_snapshot(symbol)
            self._validate_freshness(primary_snapshot)
            return primary_snapshot
        except Exception as primary_error:
            if self.fallback is None:
                raise MarketDataError(
                    "No validated market data source is available."
                ) from primary_error

        try:
            fallback_snapshot = self.fallback.fetch_snapshot(symbol)
            self._validate_freshness(fallback_snapshot)
            return fallback_snapshot
        except Exception as fallback_error:
            raise MarketDataError(
                "No validated market data source is available."
            ) from fallback_error
