from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add("/home/ubuntu/AYU-trade-AI/logs/test.log", level="DEBUG")

logger.info("Test Info")
logger.debug("Test Debug")
print("Test Print")
