import sys
from loguru import logger

def setup_logger():
    # Remove default loguru handler
    logger.remove()
    
    # Add a stylish stdout handler
    logger.add(
        sys.stdout, 
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add a file handler for religious logging
    logger.add(
        "/home/ubuntu/AYU-trade-AI/logs/trading.log",
        rotation="10 MB",
        retention="10 days",
        level="DEBUG"
    )
