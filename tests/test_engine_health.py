import unittest
from core.engine import EngineConfig, TradingEngine


class EngineHealthTests(unittest.TestCase):
    def test_status_exposes_safe_runtime_state(self):
        engine = TradingEngine(config=EngineConfig(paper_trade=True, symbol="ETH/USDT"))
        status = engine.status()
        self.assertFalse(status["running"])
        self.assertEqual(status["symbol"], "ETH/USDT")
        self.assertTrue(status["paper_trade"])


if __name__ == "__main__":
    unittest.main()
