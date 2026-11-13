import asyncio
from typing import List, Optional
from loguru import logger
import pandas as pd
from pydantic import BaseModel

from core.signal_aggregator import SignalAggregator
from core.risk_manager import RiskManager
from core.arbitrage import ArbitrageEngine
from core.broker_bridge import BrokerBridge
from indicators.custom import TechnicalIndicators
from models.sentiment_fusion import SentimentFusion
from ayuai.market_data import MarketDataError, MarketDataService


class EngineConfig(BaseModel):
    exchanges: List[str] = ["binance"]
    strategies: List[str] = ["sentiment", "technical", "arbitrage"]
    update_interval: float = 5.0
    paper_trade: bool = True
    symbol: str = "BTC/USDT"
    timeframe: str = "1m"
    candle_limit: int = 200


class TradingEngine:
    """AYU-trade-AI analysis pipeline.

    Market prices come from the validated market-data layer. Synthetic market
    data is deliberately not used in the production analysis path.
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.aggregator = SignalAggregator()
        self.risk_manager = RiskManager()
        self.bridge = BrokerBridge()
        self.sentiment_fusion = SentimentFusion()
        self.market_data = MarketDataService()

        self.is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        logger.info("Initializing AYU-trade-AI subsystems...")
        self.arbitrage_engine = ArbitrageEngine(
            list(self.bridge.crypto_exchanges.values())
        )
        logger.success("Sub-systems online.")

    async def _fetch_market_frame(self) -> pd.DataFrame:
        candles = await asyncio.to_thread(
            self.market_data.crypto_history,
            self.config.symbol,
            self.config.timeframe,
            self.config.candle_limit,
        )
        frame = pd.DataFrame(
            [
                {
                    "timestamp": candle.timestamp,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                }
                for candle in candles
            ]
        )
        if frame.empty:
            raise MarketDataError("Validated market data returned an empty frame.")
        return frame

    async def _main_loop(self) -> None:
        while self.is_running:
            try:
                sentiment_task = asyncio.create_task(
                    self.sentiment_fusion.fetch_and_fuse()
                )

                market_df = await self._fetch_market_frame()
                df_with_indicators = TechnicalIndicators.compute_all(market_df)
                tech_score = TechnicalIndicators.get_signal(df_with_indicators)

                sentiment_score = await sentiment_task
                consensus = await self.aggregator.get_consensus_signal()
                fused_score = (
                    consensus["score"] + sentiment_score + tech_score
                ) / 3

                logger.debug(
                    f"Live signal | {self.config.symbol} | "
                    f"score={fused_score:.4f} "
                    f"confidence={consensus['confidence']:.2f}"
                )

                if self.risk_manager.validate_signal(
                    {
                        "score": fused_score,
                        "confidence": consensus["confidence"],
                    }
                ):
                    side = (
                        "buy"
                        if fused_score > 0.4
                        else "sell"
                        if fused_score < -0.4
                        else None
                    )
                    if side:
                        # Real execution remains disabled in this market-data step.
                        # Step 9 will connect recommendations to paper trading first.
                        logger.info(
                            f"Signal generated: {side.upper()} {self.config.symbol} "
                            "(analysis only; no live order sent)."
                        )

                await asyncio.sleep(self.config.update_interval)

            except MarketDataError as exc:
                logger.error(f"Market data failure: {exc}")
                await asyncio.sleep(max(self.config.update_interval, 5))
            except Exception as exc:
                logger.error(f"Engine failure: {exc}")
                await asyncio.sleep(5)

    async def start(self) -> None:
        logger.info("Starting engine...")
        await self.initialize()
        self.is_running = True
        self._loop_task = asyncio.create_task(self._main_loop())
        logger.info("Trading analysis engine engaged.")

    async def stop(self) -> None:
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.warning("Trading analysis engine disengaged.")
