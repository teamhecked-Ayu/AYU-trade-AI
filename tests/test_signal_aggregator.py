import unittest

from core.signal_aggregator import SignalAggregator


class SignalAggregatorTests(unittest.TestCase):
    def test_empty_signals_hold(self):
        result = SignalAggregator().aggregate([])
        self.assertEqual(result["action"], "HOLD")
        self.assertEqual(result["confidence"], 0.0)

    def test_positive_signals_produce_positive_score(self):
        result = SignalAggregator().aggregate({"technical": 1.0, "sentiment": 1.0})
        self.assertGreater(result["score"], 0.0)
        self.assertGreater(result["confidence"], 0.0)

    def test_invalid_values_are_ignored(self):
        result = SignalAggregator().aggregate([float("nan"), float("inf"), -1.0])
        self.assertLessEqual(result["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
