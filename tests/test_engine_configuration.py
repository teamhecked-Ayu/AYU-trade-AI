import asyncio
import unittest

import pandas as pd

from core.engine import EngineConfig, TradingEngine


class FakeMarketData:
    async def fetch_ohlcv(self, exchange, symbol, timeframe, limit):
        return pd.DataFrame({
            "timestamp": pd.date_range("2026-01-01", periods=limit, freq="min", tz="UTC"),
            "open": [100.0] * limit,
            "high": [101.0] * limit,
            "low": [99.0] * limit,
            "close": [100.0] * limit,
            "volume": [10.0] * limit,
        })


class FakeSentimentData:
    async def fetch_texts(self, query):
        return ["Strong demand and positive growth outlook."]


class EngineConfigurationTests(unittest.TestCase):
    def test_injected_data_sources_are_used(self):
        config = EngineConfig(
            exchanges=["testexchange"],
            symbol="ETH/USDT",
            paper_trade=True,
            candle_limit=5,
        )
        engine = TradingEngine(
            config=config,
            market_data=FakeMarketData(),
            sentiment_data=FakeSentimentData(),
        )
        self.assertTrue(engine.bridge.paper_trade)
        self.assertEqual(engine.config.symbol, "ETH/USDT")
        self.assertIsNotNone(engine.sentiment_fusion.data_provider)


if __name__ == "__main__":
    unittest.main()
