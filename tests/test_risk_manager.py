import unittest

from core.risk_manager import RiskManager


class RiskManagerTests(unittest.TestCase):
    def test_requires_confidence_and_score(self):
        risk = RiskManager()
        self.assertFalse(risk.validate_signal({"score": 0.9, "confidence": 0.2}))
        self.assertFalse(risk.validate_signal({"score": 0.1, "confidence": 0.9}))
        self.assertTrue(risk.validate_signal({"score": 0.9, "confidence": 0.9}))

    def test_daily_loss_blocks_trading(self):
        risk = RiskManager(max_daily_loss=0.05)
        risk.daily_loss = 0.05
        self.assertFalse(risk.validate_signal({"score": 1, "confidence": 1}))

    def test_position_size_is_capped(self):
        risk = RiskManager()
        self.assertLessEqual(risk.calculate_position_size(1000, 0.99, 10), 20)


if __name__ == "__main__":
    unittest.main()
