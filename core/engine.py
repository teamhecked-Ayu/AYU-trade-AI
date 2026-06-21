import asyncio
import logging
from core.signal_aggregator import SignalAggregator
from core.risk_manager import RiskManager

class TradingEngine:
    def __init__(self, exchanges=None, strategies=None):
        self.logger = logging.getLogger("AYU-Engine")
        self.aggregator = SignalAggregator()
        self.risk_manager = RiskManager()
        self.exchanges = exchanges or ["binance"]
        self.strategies = strategies or ["sentiment", "technical"]

    async def run_interactive(self):
        self.logger.info("Interactive mode active. Monitoring streams...")
        while True:
            # Placeholder for real-time loop
            signal = await self.aggregator.get_consensus_signal()
            if self.risk_manager.validate_signal(signal):
                self.logger.info(f"Signal Validated: {signal}")
            await asyncio.sleep(1)

    async def run_daemon(self):
        self.logger.info("Daemon mode active. Running in background...")
        # Placeholder for background logic
        while True:
            await asyncio.sleep(60)
