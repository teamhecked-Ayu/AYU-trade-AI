import unittest
from fastapi.testclient import TestClient

from api import app


class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_rejects_invalid_paper_order(self):
        response = self.client.post("/paper/orders", json={
            "symbol": "BTC/USDT", "side": "buy",
            "quantity": 0, "price": 100
        })
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
