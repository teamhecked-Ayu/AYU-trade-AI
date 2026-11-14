import ccxt.async_support as ccxt
import os
from core.paper_portfolio import PaperPortfolio


class BrokerBridge:
    def __init__(self, paper_trade=None, paper_portfolio=None):
        self.crypto_exchanges = {}
        self.equity_broker = None
        self.paper_trade = (
            os.getenv("PAPER_TRADE", "true").lower() == "true"
            if paper_trade is None else bool(paper_trade)
        )
        self.paper_portfolio = paper_portfolio or PaperPortfolio()

    async def init_crypto_exchange(self, exchange_id, api_key, secret):
        if exchange_id in ccxt.exchanges:
            exchange_class = getattr(ccxt, exchange_id)
            self.crypto_exchanges[exchange_id] = exchange_class({
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,
            })
            await self.crypto_exchanges[exchange_id].load_markets()

    def init_kite_broker(self, api_key, access_token):
        try:
            from kiteconnect import KiteConnect
        except ImportError as exc:
            raise RuntimeError(
                "Kite broker support requires the optional kiteconnect package"
            ) from exc
        self.equity_broker = KiteConnect(api_key=api_key)
        self.equity_broker.set_access_token(access_token)

    async def execute_order(self, exchange_id, symbol, side, amount, order_type="market", price=None):
        """Execute a paper order or a configured exchange order."""
        if self.paper_trade:
            if price is None:
                raise ValueError("paper trading requires a current execution price")
            trade = self.paper_portfolio.execute(symbol, side, amount, float(price))
            return {"status": "paper", "exchange": exchange_id, **trade}

        if exchange_id in self.crypto_exchanges:
            exchange = self.crypto_exchanges[exchange_id]
            try:
                if order_type == "market":
                    return await exchange.create_market_order(symbol, side, amount)
                return await exchange.create_limit_order(symbol, side, amount, price)
            except Exception as exc:
                raise RuntimeError(f"Crypto order failed: {exc}") from exc

        return None
