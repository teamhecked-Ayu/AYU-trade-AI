import ccxt.async_support as ccxt
import os
from kiteconnect import KiteConnect

class BrokerBridge:
    def __init__(self, paper_trade=None):
        self.crypto_exchanges = {}
        self.equity_broker = None
        self.paper_trade = (os.getenv("PAPER_TRADE", "true").lower() == "true") if paper_trade is None else bool(paper_trade)

    async def init_crypto_exchange(self, exchange_id, api_key, secret):
        if exchange_id in ccxt.exchanges:
            exchange_class = getattr(ccxt, exchange_id)
            self.crypto_exchanges[exchange_id] = exchange_class({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
            })
            await self.crypto_exchanges[exchange_id].load_markets()

    def init_kite_broker(self, api_key, access_token):
        self.equity_broker = KiteConnect(api_key=api_key)
        self.equity_broker.set_access_token(access_token)

    async def execute_order(self, exchange_id, symbol, side, amount, order_type="market", price=None):
        """Executes order on Crypto Exchange or Equity Broker"""
        if self.paper_trade:
            print(f"[PAPER TRADE] {side.upper()} {amount} {symbol} on {exchange_id}")
            return {"status": "paper", "order_id": None, "exchange": exchange_id, "symbol": symbol, "side": side, "amount": amount}

        if exchange_id in self.crypto_exchanges:
            exchange = self.crypto_exchanges[exchange_id]
            try:
                if order_type == "market":
                    return await exchange.create_market_order(symbol, side, amount)
                else:
                    return await exchange.create_limit_order(symbol, side, amount, price)
            except Exception as e:
                print(f"Crypto Order Failed: {e}")
                return None
        
        # Placeholder for Kite Equity execution
        return None
