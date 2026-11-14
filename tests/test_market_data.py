import asyncio
import unittest

import pandas as pd

from core.market_data import CCXTMarketDataProvider


class FakeExchange:
    async def fetch_ohlcv(self, symbol, timeframe=None, limit=None):
        return [
            [1700000000000, 100, 110, 90, 105, 12],
            [1700000060000, 105, 115, 100, 110, 15],
        ]


class MarketDataTests(unittest.TestCase):
    def test_normalizes_ohlcv(self):
        provider = CCXTMarketDataProvider({"fake": FakeExchange()})
        frame = asyncio.run(provider.fetch_ohlcv("fake", "BTC/USDT"))
        self.assertIsInstance(frame, pd.DataFrame)
        self.assertEqual(list(frame.columns), ["timestamp", "open", "high", "low", "close", "volume"])
        self.assertEqual(len(frame), 2)
        self.assertTrue(str(frame["timestamp"].dtype).startswith("datetime64"))


if __name__ == "__main__":
    unittest.main()
