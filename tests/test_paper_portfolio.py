import unittest
from core.paper_portfolio import PaperPortfolio


class PaperPortfolioTests(unittest.TestCase):
    def test_buy_sell_and_equity(self):
        p = PaperPortfolio(cash=1000, fee_rate=0)
        p.execute("BTC/USDT", "buy", 2, 100)
        self.assertEqual(p.cash, 800)
        self.assertEqual(p.equity({"BTC/USDT": 120}), 1040)
        p.execute("BTC/USDT", "sell", 1, 120)
        self.assertEqual(p.positions["BTC/USDT"].quantity, 1)

    def test_rejects_insufficient_funds(self):
        p = PaperPortfolio(cash=10)
        with self.assertRaises(ValueError):
            p.execute("BTC/USDT", "buy", 1, 100)


if __name__ == "__main__":
    unittest.main()
