import unittest

from core.market_data import CCXTMarketDataProvider


class MarketDataTests(unittest.TestCase):
    def test_normalizes_and_sorts_candles(self):
        rows = [[2000, 2, 3, 1, 2, 10], [1000, 1, 2, 0.5, 1, 20]]
        frame = CCXTMarketDataProvider._normalize(rows)
        self.assertEqual(len(frame), 2)
        self.assertLess(frame["timestamp"].iloc[0], frame["timestamp"].iloc[1])

    def test_rejects_invalid_price(self):
        with self.assertRaises(RuntimeError):
            CCXTMarketDataProvider._normalize([[1000, 1, 1, 1, 0, 1]])


if __name__ == "__main__":
    unittest.main()
