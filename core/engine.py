import asyncio
import logging
import pandas as pd
from core.signal_aggregator import SignalAggregator
from core.risk_manager import RiskManager
from core.arbitrage import ArbitrageEngine
from core.broker_bridge import BrokerBridge
from indicators.custom import TechnicalIndicators
from models.sentiment_fusion import SentimentFusion

class TradingEngine:
    def __init__(self, exchanges=None, strategies=None):
        self.logger = logging.getLogger("AYU-Engine")
        self.aggregator = SignalAggregator()
        self.risk_manager = RiskManager()
        self.bridge = BrokerBridge()
        self.sentiment_fusion = SentimentFusion()
        
        self.exchanges_list = exchanges or ["binance"]
        self.strategies = strategies or ["sentiment", "technical", "arbitrage"]
        self.is_running = False

    async def initialize(self):
        self.logger.info("Initializing Sub-systems...")
        # In production, load API keys from .env
        # for ex in self.exchanges_list:
        #     await self.bridge.init_crypto_exchange(ex, "KEY", "SECRET")
        self.arbitrage_engine = ArbitrageEngine(list(self.bridge.crypto_exchanges.values()))

    async def run_interactive(self):
        await self.initialize()
        self.is_running = True
        self.logger.info("Interactive Mode: Listening to WebSocket streams and decoding psychology...")
        
        while self.is_running:
            try:
                # 1. Fetch Market Data & Sentiment
                sentiment_score = await self.sentiment_fusion.fetch_and_fuse()
                
                # 2. Compute Technical Indicators (Mock data for demo)
                mock_data = {
                    'open': np.random.uniform(50000, 60000, 100),
                    'high': np.random.uniform(50000, 60000, 100),
                    'low': np.random.uniform(50000, 60000, 100),
                    'close': np.random.uniform(50000, 60000, 100),
                    'volume': np.random.uniform(1, 10, 100)
                }
                df = pd.DataFrame(mock_data)
                df = TechnicalIndicators.compute_all(df)
                tech_score = TechnicalIndicators.get_signal(df)

                # 3. Aggregate Signals
                ensemble_signal = await self.aggregator.get_consensus_signal()
                # Fuse custom scores into ensemble
                fused_score = (ensemble_signal['score'] + sentiment_score + tech_score) / 3
                
                self.logger.info(f"Fused Consensus: {fused_score:.4f} | Sentiment: {sentiment_score:.2f} | Tech: {tech_score:.2f}")

                # 4. Risk Validation & Execution
                if self.risk_manager.validate_signal({"score": fused_score, "confidence": ensemble_signal['confidence']}):
                    side = "buy" if fused_score > 0.3 else "sell" if fused_score < -0.3 else None
                    if side:
                        await self.bridge.execute_order("binance", "BTC/USDT", side, 0.001)

                await asyncio.sleep(2) # Sub-second latency in production via WebSockets
            except Exception as e:
                self.logger.error(f"Engine Loop Error: {e}")
                await asyncio.sleep(5)

    async def run_daemon(self):
        await self.initialize()
        self.is_running = True
        self.logger.info("Daemon Mode: Autonomous Warfare Engaged.")
        while self.is_running:
            # Headless execution logic
            await asyncio.sleep(60)
