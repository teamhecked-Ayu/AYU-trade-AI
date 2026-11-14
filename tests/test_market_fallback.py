import unittest
import pandas as pd

from core.market_fallback import FallbackMarketDataProvider


class FailingProvider:
    async def fetch_ohlcv(self, *args, **kwargs):
        raise RuntimeError("primary unavailable")


class WorkingProvider:
    async def fetch_ohlcv(self, *args, **kwargs):
        return pd.DataFrame({"close": [100.0]})


class FallbackProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_next_provider_after_failure(self):
        provider = FallbackMarketDataProvider([FailingProvider(), WorkingProvider()])
        frame = await provider.fetch_ohlcv("binance", "BTC/USDT", "1m", 1)
        self.assertEqual(float(frame["close"].iloc[0]), 100.0)

    async def test_raises_when_all_providers_fail(self):
        provider = FallbackMarketDataProvider([FailingProvider(), FailingProvider()])
        with self.assertRaises(RuntimeError):
            await provider.fetch_ohlcv("binance", "BTC/USDT", "1m", 1)


if __name__ == "__main__":
    unittest.main()
