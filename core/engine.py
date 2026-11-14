import asyncio
from typing import List, Optional, Dict, Any
from loguru import logger
import pandas as pd
from pydantic import BaseModel

from core.signal_aggregator import SignalAggregator
from core.market_data import CCXTMarketDataProvider, MarketDataProvider
from core.sentiment_data import SentimentDataProvider
from core.risk_manager import RiskManager
from core.arbitrage import ArbitrageEngine
from core.broker_bridge import BrokerBridge
from models.sentiment_fusion import SentimentFusion

class EngineConfig(BaseModel):
    exchanges: List[str] = ["binance"]
    strategies: List[str] = ["sentiment", "technical", "arbitrage"]
    update_interval: float = 1.0
    paper_trade: bool = True
    sentiment_query: str = "BTC"
    symbol: str = "BTC/USDT"
    timeframe: str = "1m"
    candle_limit: int = 100

class TradingEngine:
    """
    The heart of AYU-trade-AI. Orchestrates data ingestion, 
    signal processing, and order execution.
    """
    def __init__(self, config: Optional[EngineConfig] = None, market_data: Optional[MarketDataProvider] = None, sentiment_data: Optional[SentimentDataProvider] = None):
        self.config = config or EngineConfig()
        self.aggregator = SignalAggregator()
        self.risk_manager = RiskManager()
        self.bridge = BrokerBridge(paper_trade=self.config.paper_trade)
        self.sentiment_fusion = SentimentFusion(data_provider=sentiment_data)
        self.market_data = market_data or CCXTMarketDataProvider()
        
        self.is_running = False
        self.consecutive_failures = 0
        self.last_error: Optional[str] = None
        self.last_success_at: Optional[float] = None
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
                sentiment_task = asyncio.create_task(self.sentiment_fusion.fetch_and_fuse(self.config.sentiment_query))
                
                # 2. Market Analysis
                market_df = await self.market_data.fetch_ohlcv(
                    self.config.exchanges[0], self.config.symbol,
                    self.config.timeframe, self.config.candle_limit
                )
                from indicators.custom import TechnicalIndicators
                df_with_indicators = TechnicalIndicators.compute_all(market_df)
                tech_score = TechnicalIndicators.get_signal(df_with_indicators)
                
                sentiment_score = await sentiment_task
                
                # 3. Deterministic signal fusion using the actual analysis outputs.
                consensus = await self.aggregator.get_consensus_signal({
                    "technical": float(tech_score),
                    "sentiment": float(sentiment_score),
                })
                fused_score = consensus["score"]

                logger.debug(
                    f"Signal Fusion | Score: {fused_score:.4f} | "
                    f"Confidence: {consensus['confidence']:.2f} | "
                    f"Technical: {tech_score:.4f} | Sentiment: {sentiment_score:.4f}"
                )

                # 4. Risk-Adjusted Execution
                if self.risk_manager.validate_signal({"score": fused_score, "confidence": consensus['confidence']}):
                    side = "buy" if consensus["action"] == "BUY" else "sell" if consensus["action"] == "SELL" else None
                    if side:
                        await self.bridge.execute_order(
                            self.config.exchanges[0], self.config.symbol, side, 0.001,
                            price=float(market_df["close"].iloc[-1])
                        )

                self.consecutive_failures = 0
                self.last_error = None
                self.last_success_at = asyncio.get_running_loop().time()
                await asyncio.sleep(self.config.update_interval)
            except Exception as e:
                self.consecutive_failures += 1
                self.last_error = str(e)
                delay = min(30, 2 ** min(self.consecutive_failures, 5))
                logger.error(f"Engine Failure ({self.consecutive_failures}): {e}")
                await asyncio.sleep(delay)

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.is_running,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "last_success_at": self.last_success_at,
            "paper_trade": self.config.paper_trade,
            "symbol": self.config.symbol,
        }

    async def start(self) -> None:
        logger.info("Starting Engine...")
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
        close = getattr(self.market_data, "close", None)
        if close:
            result = close()
            if hasattr(result, "__await__"):
                await result
        logger.warning("Trading Oracle Disengaged.")
