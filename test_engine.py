import asyncio
from loguru import logger
import sys

# Add local path to sys.path
import os
sys.path.append(os.getcwd())

from core.engine import TradingEngine, EngineConfig

async def test():
    logger.remove()
    logger.add(sys.stdout, level="DEBUG")
    
    config = EngineConfig(update_interval=0.1)
    engine = TradingEngine(config=config)
    
    logger.info("Starting Engine Test...")
    await engine.initialize()
    engine.is_running = True
    
    # Run loop for 5 seconds
    try:
        await asyncio.wait_for(engine._main_loop(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.info("Test completed successfully.")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
