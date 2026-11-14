import asyncio
import argparse

from core.engine import EngineConfig, TradingEngine
from utils.logger import setup_logger


async def main():
    parser = argparse.ArgumentParser(description="AYU-trade-AI Headless Daemon")
    parser.add_argument("--exchanges", default="binance")
    parser.add_argument("--strategies", default="sentiment,technical")
    parser.add_argument("--symbol", default="BTC/USDT")
    args = parser.parse_args()

    setup_logger()
    config = EngineConfig(
        exchanges=[x for x in args.exchanges.split(",") if x],
        strategies=[x for x in args.strategies.split(",") if x],
        symbol=args.symbol,
    )
    engine = TradingEngine(config=config)
    await engine.start()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await engine.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
