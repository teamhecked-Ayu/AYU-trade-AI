import os
import tempfile
import unittest

from core.paper_portfolio import PaperPortfolio
from core.portfolio_store import SQLitePortfolioStore


class PortfolioStoreTests(unittest.TestCase):
    def test_round_trip(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            store = SQLitePortfolioStore(path)
            portfolio = PaperPortfolio(cash=1000, fee_rate=0)
            portfolio.execute("BTC/USDT", "buy", 2, 100)
            store.save(portfolio)
            loaded = store.load(fee_rate=0)
            self.assertEqual(loaded.cash, 800)
            self.assertEqual(loaded.positions["BTC/USDT"].quantity, 2)
            self.assertEqual(len(loaded.trades), 1)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
