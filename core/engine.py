import asyncio
from typing import List, Optional, Dict, Any
from loguru import logger
import pandas as pd
import numpy as np
from pydantic import BaseModel

from core.signal_aggregator import SignalAggregator
from core.risk_manager import RiskManager
from core.arbitrage import ArbitrageEngine
from core.broker_bridge import BrokerBridge
from indicators.custom import TechnicalIndicators
from models.sentiment_fusion import SentimentFusion

class EngineConfig(BaseModel):
    exchanges: List[str] = ["binance"]
    strategies: List[str] = ["sentiment", "technical", "arbitrage"]
    update_interval: float = 1.0
    paper_trade: bool = True

class TradingEngine:
    """
    The heart of AYU-trade-AI. Orchestrates data ingestion, 
    signal processing, and order execution.
    """
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.aggregator = SignalAggregator()
        self.risk_manager = RiskManager()
        self.bridge = BrokerBridge()
        self.sentiment_fusion = SentimentFusion()
        
        self.is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Bootstraps all sub-systems with institutional precision."""
        logger.info("<green>Initializing AYU-trade-AI Sub-systems...</green>")
        # Initialize bridge and arbitrage engine
        self.arbitrage_engine = ArbitrageEngine(list(self.bridge.crypto_exchanges.values()))
        logger.success("Sub-systems online.")

    async def _main_loop(self) -> None:
        """The core execution pipeline."""
        while self.is_running:
            try:
                # 1. Parallel Data Ingestion
                sentiment_task = asyncio.create_task(self.sentiment_fusion.fetch_and_fuse())
                
                # 2. Market Analysis
                mock_df = self._generate_mock_market_data()
                df_with_indicators = TechnicalIndicators.compute_all(mock_df)
                tech_score = TechnicalIndicators.get_signal(df_with_indicators)
                
                sentiment_score = await sentiment_task
                
                # 3. Signal Fusion via Aggregator
                consensus = await self.aggregator.get_consensus_signal()
                fused_score = (consensus['score'] + sentiment_score + tech_score) / 3
                
                logger.debug(f"Signal Fusion | Consensus: {fused_score:.4f} | Confidence: {consensus['confidence']:.2f}")

                # 4. Risk-Adjusted Execution
                if self.risk_manager.validate_signal({"score": fused_score, "confidence": consensus['confidence']}):
                    side = "buy" if fused_score > 0.4 else "sell" if fused_score < -0.4 else None
                    if side:
                        await self.bridge.execute_order("binance", "BTC/USDT", side, 0.001)

                await asyncio.sleep(self.config.update_interval)
            except Exception as e:
                logger.error(f"Engine Failure: {e}")
                await asyncio.sleep(5)

    def _generate_mock_market_data(self) -> pd.DataFrame:
        """Internal helper for streaming simulation."""
        return pd.DataFrame({
            'open': np.random.uniform(50000, 60000, 100),
            'high': np.random.uniform(50000, 60000, 100),
            'low': np.random.uniform(50000, 60000, 100),
            'close': np.random.uniform(50000, 60000, 100),
            'volume': np.random.uniform(1, 10, 100)
        })

    async def start(self) -> None:
        await self.initialize()
        self.is_running = True
        self._loop_task = asyncio.create_task(self._main_loop())
        logger.info("Trading Oracle Engaged.")

    async def stop(self) -> None:
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.warning("Trading Oracle Disengaged.")
