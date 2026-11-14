import os
import tempfile
os.environ["AYU_API_KEY"] = "test-secret"
os.environ["PAPER_PORTFOLIO_DB"] = os.path.join(tempfile.gettempdir(), "ayu_trade_ai_api_test.db")

import unittest
from fastapi.testclient import TestClient

from api import app


class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def headers(self):
        return {"X-API-Key": "test-secret"}

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_protected_endpoint_requires_key(self):
        response = self.client.get("/portfolio")
        self.assertEqual(response.status_code, 401)

    def test_paper_order_persists_to_portfolio(self):
        before = self.client.get("/portfolio", headers=self.headers()).json()
        response = self.client.post("/paper/orders", headers=self.headers(), json={
            "symbol": "TEST/API", "side": "buy", "quantity": 1, "price": 100
        })
        self.assertEqual(response.status_code, 200)
        after = self.client.get("/portfolio", headers=self.headers()).json()
        self.assertLess(after["cash"], before["cash"])
        self.assertGreaterEqual(len(after["trades"]), len(before["trades"]) + 1)

    def test_rejects_invalid_paper_order(self):
        response = self.client.post("/paper/orders", headers=self.headers(), json={
            "symbol": "BTC/USDT", "side": "buy", "quantity": 0, "price": 100
        })
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
