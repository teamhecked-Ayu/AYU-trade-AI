import asyncio
import unittest

from core.signal_aggregator import SignalAggregator


class DecisionFlowTests(unittest.TestCase):
    def test_positive_inputs_stay_positive(self):
        result = asyncio.run(
            SignalAggregator().get_consensus_signal(
                {"technical": 1.0, "sentiment": 1.0}
            )
        )
        self.assertGreater(result["score"], 0.0)
        self.assertIn(result["action"], {"BUY", "HOLD"})

    def test_opposing_inputs_reduce_confidence(self):
        agreeing = SignalAggregator().aggregate({"technical": 0.8, "sentiment": 0.8})
        opposing = SignalAggregator().aggregate({"technical": 0.8, "sentiment": -0.8})
        self.assertGreater(agreeing["confidence"], opposing["confidence"])


if __name__ == "__main__":
    unittest.main()
