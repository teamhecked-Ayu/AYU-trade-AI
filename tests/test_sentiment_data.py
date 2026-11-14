import asyncio
import unittest

from core.sentiment_data import SentimentDataProvider


class FakeSentimentProvider:
    async def fetch_texts(self, query):
        return [f"{query} sees strong institutional demand", f"Risk concerns remain for {query}"]


class SentimentDataTests(unittest.TestCase):
    def test_provider_contract(self):
        provider = FakeSentimentProvider()
        texts = asyncio.run(provider.fetch_texts("BTC"))
        self.assertEqual(len(texts), 2)
        self.assertIn("BTC", texts[0])


if __name__ == "__main__":
    unittest.main()
