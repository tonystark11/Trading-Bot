import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_filename = os.path.join(LOG_DIR, f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("%(levelname)-8s | %(message)s")
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialised. Log file: {log_filename}")
    return logger
