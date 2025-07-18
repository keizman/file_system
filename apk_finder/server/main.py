#!/usr/bin/env python3
"""
APK Finder Server
Main entry point for the server application
"""

import sys
import os
import signal

# Add the current directory to Python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from src.config import Config
from src.api import app


def setup_logging():
    """Setup logging configuration"""
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stderr,
        level=Config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file logger
    logger.add(
        os.path.join(Config.LOG_DIR, "apk_finder.log"),
        rotation="10 MB",
        retention="30 days",
        level=Config.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main function"""
    # Setup logging
    setup_logging()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting APK Finder Server")
    logger.info(f"Server configuration:")
    logger.info(f"  Port: {Config.SERVER_PORT}")
    logger.info(f"  Log Level: {Config.LOG_LEVEL}")
    logger.info(f"  Update Interval: {Config.UPDATE_INTERVAL}s")
    logger.info(f"  File Servers: {len(Config.FILE_SERVERS)}")
    
    # Test Redis connection
    try:
        from src.redis_client import redis_client
        logger.info("Redis connection test passed")
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        logger.warning("Server will continue but Redis features may not work")
    
    try:
        import uvicorn
        uvicorn.run(
            "src.api:app",
            host="0.0.0.0",
            port=Config.SERVER_PORT,
            log_level=Config.LOG_LEVEL.lower(),
            access_log=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()