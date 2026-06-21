import asyncio

class ArbitrageEngine:
    def __init__(self, exchanges):
        self.exchanges = exchanges # List of ccxt exchange objects

    async def detect_spatial_arbitrage(self, symbol):
        """Detects price differences for the same asset across different exchanges."""
        prices = {}
        tasks = [self.fetch_price(ex, symbol) for ex in self.exchanges]
        results = await asyncio.gather(*tasks)
        
        for ex_id, price in results:
            if price:
                prices[ex_id] = price
                
        if len(prices) < 2:
            return None

        best_buy = min(prices, key=prices.get)
        best_sell = max(prices, key=prices.get)
        
        spread = (prices[best_sell] - prices[best_buy]) / prices[best_buy]
        
        if spread > 0.005: # 0.5% threshold
            return {
                "type": "SPATIAL",
                "symbol": symbol,
                "buy_at": best_buy,
                "sell_at": best_sell,
                "spread": spread,
                "potential_profit": spread * 100 # percentage
            }
        return None

    async def fetch_price(self, exchange, symbol):
        try:
            ticker = await exchange.fetch_ticker(symbol)
            return exchange.id, ticker['last']
        except Exception:
            return exchange.id, None

    async def detect_triangular_arbitrage(self, exchange_id, base_currency="USDT"):
        """Placeholder for triangular arbitrage (e.g., USDT -> BTC -> ETH -> USDT)"""
        # Complex logic involving order book depth and path finding
        return None
