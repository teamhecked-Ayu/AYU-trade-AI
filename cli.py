import asyncio
import argparse
from loguru import logger
from core.engine import TradingEngine
from utils.logger import setup_logger

async def main():
    parser = argparse.ArgumentParser(description="AYU-trade-AI Interactive CLI")
    parser.add_argument("--mode", choices=["interactive", "daemon"], default="interactive")
    args = parser.parse_args()

    setup_logger()
    logger.info(f"Starting AYU-trade-AI in {args.mode} mode...")

    engine = TradingEngine()
    
    if args.mode == "interactive":
        from utils.dashboard import AYUDashboard
        dashboard = AYUDashboard()
        await asyncio.gather(engine.start(), dashboard.run())
    else:
        await engine.start()
        # Keep daemon alive
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
