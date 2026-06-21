import asyncio
import argparse
import logging
from core.engine import TradingEngine
from utils.logger import setup_logger

async def main():
    parser = argparse.ArgumentParser(description="AYU-trade-AI Headless Daemon")
    parser.add_argument("--exchanges", help="Comma-separated list of exchanges", default="binance")
    parser.add_argument("--strategies", help="Comma-separated list of strategies", default="sentiment,technical")
    args = parser.parse_args()

    setup_logger()
    logger = logging.getLogger("AYU-Daemon")
    logger.info("Initializing AYU-trade-AI Daemon...")
    
    exchanges = args.exchanges.split(",")
    strategies = args.strategies.split(",")

    engine = TradingEngine(exchanges=exchanges, strategies=strategies)
    await engine.run_daemon()

if __name__ == "__main__":
    asyncio.run(main())
